import aiosqlite
import sqlite3
import hashlib
import pickle
import asyncio
import threading
import queue
import time
from typing import Any, Optional
import logging
from datetime import datetime


class PersistentMemory:
    def __init__(self, database_file: str = 'persistent_memory.db', key_error: bool = False, max_records: int = 10000):
        self.logger = logging.getLogger('skpmem')
        self.database_file = database_file
        self.memory_store: dict = {}
        self.write_queue: asyncio.Queue = asyncio.Queue()
        self.initialized: bool = False
        self._init_task: Optional[asyncio.Task] = None
        
        # 同期操作用のバックグラウンドスレッド関連
        self.sync_write_queue: queue.Queue = queue.Queue()
        self.sync_read_queue: queue.Queue = queue.Queue()
        self.sync_response_queue: queue.Queue = queue.Queue()
        self.daemon_thread: Optional[threading.Thread] = None
        self.daemon_running: bool = False
        self.sync_initialized: bool = False
        self._lock = threading.Lock()
        self.deleted_keys: set = set()  # 削除されたキーを追跡

        # KeyErrorの発生を抑制するかどうか
        self.key_error = key_error
        
        # 最大レコード数
        self.max_records = max_records
        
        # VACUUM設定
        self.vacuum_threshold = 100  # 削除回数がこの値に達したらVACUUM実行
        self.delete_count = 0  # 削除回数カウンター
        self.last_vacuum_time = time.time()  # 最後のVACUUM実行時刻
        self.vacuum_interval = 3600  # 最低1時間間隔でVACUUM
        self.background_vacuum = True  # バックグラウンドVACUUMを有効にするか
        self.vacuum_thread = None  # VACUUM専用スレッド
        self.vacuum_pending = False  # VACUUM実行中フラグ

    def __getitem__(self, key: str) -> Any:
        """同期版の load_sync を呼び出す（存在しない場合はKeyErrorを発生）"""
        # 特別なセンチネル値を使用してキーの存在を確認
        _sentinel = object()
        result = self.load_sync(key, _sentinel)
        if result is _sentinel:
            if self.key_error:
                raise KeyError(key)
            else:
                return None
        return result

    def __setitem__(self, key: str, value: Any):
        """同期版の save_sync を呼び出す"""
        self.save_sync(key, value)

    def __delitem__(self, key: str):
        """同期版の delete_sync を呼び出す"""
        self.delete_sync(key)

    def delete_sync(self, key: str):
        """同期版の削除メソッド - バックグラウンドスレッドで削除"""
        hash_key = self._name_hash(key)
        
        # メモリキャッシュから即座に削除し、削除済みマークを付ける
        with self._lock:
            if hash_key in self.memory_store:
                del self.memory_store[hash_key]
            self.deleted_keys.add(hash_key)  # 削除済みマークを追加
        
        # バックグラウンドスレッドに削除を依頼
        try:
            self.sync_write_queue.put(('delete', hash_key), timeout=1.0)
            self.logger.debug(f"Queued {key} for background deletion")
        except queue.Full:
            self.logger.warning(f"Write queue full, falling back to direct delete for {key}")
            # フォールバック：直接削除
            try:
                with sqlite3.connect(self.database_file) as db:
                    db.execute('DELETE FROM memory WHERE key = ?', (hash_key,))
                    db.commit()
                    self.delete_count += 1
                    self.logger.debug(f"Direct deleted {key} from DB")
            except Exception as e:
                self.logger.error(f"Error in direct delete fallback: {e}")

    async def _delete_from_db(self, hash_key: str):
        if not self.initialized:
            await self.initialize()
        try:
            async with aiosqlite.connect(self.database_file) as db:
                await db.execute('DELETE FROM memory WHERE key = ?', (hash_key,))
                await db.commit()
                self.delete_count += 1
                self.logger.debug(f"Deleted {hash_key} from DB")
        except Exception as e:
            self.logger.error(f"Error deleting from DB: {e}")

    async def initialize(self):
        if self.initialized:
            return

        # データベースの初期化
        async with aiosqlite.connect(self.database_file) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    reference_count INTEGER DEFAULT 0,
                    last_write_date REAL DEFAULT 0
                )
            ''')
            # 既存のテーブルに新しいカラムを追加（存在しない場合のみ）
            try:
                await db.execute('ALTER TABLE memory ADD COLUMN reference_count INTEGER DEFAULT 0')
            except:
                pass  # カラムが既に存在する場合
            try:
                await db.execute('ALTER TABLE memory ADD COLUMN last_write_date REAL DEFAULT 0')
            except:
                pass  # カラムが既に存在する場合
            await db.commit()

        # データベースへの非同期書き込みタスク開始
        self._init_task = asyncio.create_task(self._async_db_writer())
        self.initialized = True
        self._start_daemon_thread()

    def _start_daemon_thread(self):
        """バックグラウンドデーモンスレッドを開始"""
        if not self.daemon_running:
            self.daemon_running = True
            self.daemon_thread = threading.Thread(target=self._daemon_worker, daemon=True)
            self.daemon_thread.start()
            self.logger.debug("Daemon thread started")

    def _daemon_worker(self):
        """バックグラウンドでデータベース操作を処理するデーモンワーカー"""
        try:
            with sqlite3.connect(self.database_file) as db:
                self.logger.debug("Daemon worker connected to database")
                
                while self.daemon_running:
                    try:
                        # 書き込み操作をチェック
                        try:
                            operation, data = self.sync_write_queue.get(timeout=0.1)
                            if operation == 'save':
                                hash_key, value = data
                                write_time = time.time()
                                db.execute(
                                    'REPLACE INTO memory (key, value, reference_count, last_write_date) VALUES (?, ?, ?, ?)',
                                    (hash_key, pickle.dumps(value), 0, write_time)
                                )
                                db.commit()
                                self.logger.debug(f"Daemon saved {hash_key} to DB")
                            elif operation == 'delete':
                                hash_key = data
                                db.execute('DELETE FROM memory WHERE key = ?', (hash_key,))
                                db.commit()
                                self.delete_count += 1
                                self.logger.debug(f"Daemon deleted {hash_key} from DB")
                            elif operation == 'increment_ref':
                                hash_key = data
                                db.execute(
                                    'UPDATE memory SET reference_count = reference_count + 1 WHERE key = ?',
                                    (hash_key,)
                                )
                                db.commit()
                                self.logger.debug(f"Daemon incremented reference count for {hash_key}")
                            elif operation == 'check_evict':
                                # レコード数チェックと削除処理
                                cursor = db.execute('SELECT COUNT(*) FROM memory')
                                row = cursor.fetchone()
                                record_count = row[0] if row else 0
                                
                                if record_count > self.max_records:
                                    # 削除する数を計算（10%の余裕を持たせる）
                                    delete_count = record_count - int(self.max_records * 0.9)
                                    # 最も古くて参照回数の少ないレコードを選択
                                    cursor = db.execute('''
                                        SELECT key FROM memory 
                                        ORDER BY reference_count ASC, last_write_date ASC 
                                        LIMIT ?
                                    ''', (delete_count,))
                                    keys_to_delete = [row[0] for row in cursor.fetchall()]
                                    
                                    # メモリキャッシュからも削除
                                    with self._lock:
                                        for key in keys_to_delete:
                                            if key in self.memory_store:
                                                del self.memory_store[key]
                                            self.deleted_keys.add(key)
                                    
                                    # データベースから削除
                                    if keys_to_delete:
                                        placeholders = ','.join(['?' for _ in keys_to_delete])
                                        db.execute(f'DELETE FROM memory WHERE key IN ({placeholders})', keys_to_delete)
                                        db.commit()
                                        self.delete_count += len(keys_to_delete)
                                        self.logger.info(f"Daemon evicted {len(keys_to_delete)} records from memory")
                                        
                                        # VACUUM判定
                                        if self._should_vacuum():
                                            if self.background_vacuum:
                                                self._schedule_background_vacuum()
                                            else:
                                                self.logger.info("Executing VACUUM to reclaim space")
                                                db.execute('VACUUM')
                                                self.delete_count = 0
                                                self.last_vacuum_time = time.time()
                                                self.logger.info("VACUUM completed")
                            self.sync_write_queue.task_done()
                        except queue.Empty:
                            pass
                        
                        # 読み込み操作をチェック
                        try:
                            request_id, hash_key = self.sync_read_queue.get(timeout=0.1)
                            cursor = db.execute(
                                'SELECT value FROM memory WHERE key = ?',
                                (hash_key,)
                            )
                            row = cursor.fetchone()
                            result = pickle.loads(row[0]) if row is not None else None
                            self.sync_response_queue.put((request_id, result))
                            self.sync_read_queue.task_done()
                            self.logger.debug(f"Daemon loaded {hash_key} from DB")
                        except queue.Empty:
                            pass
                            
                    except Exception as e:
                        self.logger.error(f"Error in daemon worker: {e}")
                        time.sleep(0.1)
                        
        except Exception as e:
            self.logger.error(f"Fatal error in daemon worker: {e}")
        finally:
            self.logger.debug("Daemon worker stopped")

    def initialize_sync(self):
        """同期版の初期化メソッド"""
        if self.sync_initialized:
            return

        # データベースの初期化（同期版）
        with sqlite3.connect(self.database_file) as db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    reference_count INTEGER DEFAULT 0,
                    last_write_date REAL DEFAULT 0
                )
            ''')
            # 既存のテーブルに新しいカラムを追加（存在しない場合のみ）
            try:
                db.execute('ALTER TABLE memory ADD COLUMN reference_count INTEGER DEFAULT 0')
            except:
                pass  # カラムが既に存在する場合
            try:
                db.execute('ALTER TABLE memory ADD COLUMN last_write_date REAL DEFAULT 0')
            except:
                pass  # カラムが既に存在する場合
            db.commit()

        self.sync_initialized = True
        self._start_daemon_thread()

    def _name_hash(self, name: str) -> str:
        return hashlib.sha512(name.encode()).hexdigest()
    
    async def _increment_reference_count(self, hash_key: str):
        """非同期版の参照回数インクリメント"""
        if not self.initialized:
            await self.initialize()
        try:
            async with aiosqlite.connect(self.database_file) as db:
                await db.execute(
                    'UPDATE memory SET reference_count = reference_count + 1 WHERE key = ?',
                    (hash_key,)
                )
                await db.commit()
        except Exception as e:
            self.logger.error(f"Error incrementing reference count: {e}")
    
    def _increment_reference_count_sync(self, hash_key: str):
        """同期版の参照回数インクリメント"""
        try:
            self.sync_write_queue.put(('increment_ref', hash_key), timeout=0.1)
        except queue.Full:
            # フォールバック：直接更新
            try:
                with sqlite3.connect(self.database_file) as db:
                    db.execute(
                        'UPDATE memory SET reference_count = reference_count + 1 WHERE key = ?',
                        (hash_key,)
                    )
                    db.commit()
            except Exception as e:
                self.logger.error(f"Error in direct reference count increment: {e}")
    
    async def _check_and_evict(self):
        """非同期版のレコード数チェックと削除処理"""
        if not self.initialized:
            await self.initialize()
        try:
            async with aiosqlite.connect(self.database_file) as db:
                async with db.execute('SELECT COUNT(*) FROM memory') as cursor:
                    row = await cursor.fetchone()
                    record_count = row[0] if row else 0
                
                if record_count > self.max_records:
                    # 削除する数を計算（10%の余裕を持たせる）
                    delete_count = record_count - int(self.max_records * 0.9)
                    await self._evict_records(delete_count)
        except Exception as e:
            self.logger.error(f"Error in check and evict: {e}")
    
    def _check_and_evict_sync(self):
        """同期版のレコード数チェックと削除処理"""
        try:
            with sqlite3.connect(self.database_file) as db:
                cursor = db.execute('SELECT COUNT(*) FROM memory')
                row = cursor.fetchone()
                record_count = row[0] if row else 0
                
                if record_count > self.max_records:
                    # 削除する数を計算（10%の余裕を持たせる）
                    delete_count = record_count - int(self.max_records * 0.9)
                    self._evict_records_sync(delete_count)
        except Exception as e:
            self.logger.error(f"Error in sync check and evict: {e}")
    
    async def _evict_records(self, count: int):
        """非同期版のレコード削除処理（最も古くて参照回数の少ないものから削除）"""
        try:
            async with aiosqlite.connect(self.database_file) as db:
                # 最も古くて参照回数の少ないレコードを選択
                async with db.execute('''
                    SELECT key FROM memory 
                    ORDER BY reference_count ASC, last_write_date ASC 
                    LIMIT ?
                ''', (count,)) as cursor:
                    keys_to_delete = [row[0] for row in await cursor.fetchall()]
                
                # メモリキャッシュからも削除
                for key in keys_to_delete:
                    if key in self.memory_store:
                        del self.memory_store[key]
                
                # データベースから削除
                if keys_to_delete:
                    placeholders = ','.join(['?' for _ in keys_to_delete])
                    await db.execute(f'DELETE FROM memory WHERE key IN ({placeholders})', keys_to_delete)
                    await db.commit()
                    self.logger.info(f"Evicted {len(keys_to_delete)} records from memory")
        except Exception as e:
            self.logger.error(f"Error in evict records: {e}")
    
    def _evict_records_sync(self, count: int):
        """同期版のレコード削除処理（最も古くて参照回数の少ないものから削除）"""
        try:
            with sqlite3.connect(self.database_file) as db:
                # 最も古くて参照回数の少ないレコードを選択
                cursor = db.execute('''
                    SELECT key FROM memory 
                    ORDER BY reference_count ASC, last_write_date ASC 
                    LIMIT ?
                ''', (count,))
                keys_to_delete = [row[0] for row in cursor.fetchall()]
                
                # メモリキャッシュからも削除
                with self._lock:
                    for key in keys_to_delete:
                        if key in self.memory_store:
                            del self.memory_store[key]
                        self.deleted_keys.add(key)
                
                # データベースから削除
                if keys_to_delete:
                    placeholders = ','.join(['?' for _ in keys_to_delete])
                    db.execute(f'DELETE FROM memory WHERE key IN ({placeholders})', keys_to_delete)
                    db.commit()
                    self.delete_count += len(keys_to_delete)
                    self.logger.info(f"Evicted {len(keys_to_delete)} records from memory (sync)")
                    
                    # VACUUM判定
                    if self._should_vacuum():
                        if self.background_vacuum:
                            self._schedule_background_vacuum()
                        else:
                            self.logger.info("Executing VACUUM to reclaim space")
                            db.execute('VACUUM')
                            self.delete_count = 0
                            self.last_vacuum_time = time.time()
                            self.logger.info("VACUUM completed")
        except Exception as e:
            self.logger.error(f"Error in sync evict records: {e}")
    
    def _should_vacuum(self) -> bool:
        """VACUUM実行の判定"""
        current_time = time.time()
        return (self.delete_count >= self.vacuum_threshold and 
                current_time - self.last_vacuum_time >= self.vacuum_interval)
    
    def force_vacuum_sync(self):
        """手動でVACUUMを実行（同期版）"""
        if not self.sync_initialized:
            self.initialize_sync()
        
        try:
            with sqlite3.connect(self.database_file) as db:
                self.logger.info("Manually executing VACUUM")
                db.execute('VACUUM')
                self.delete_count = 0
                self.last_vacuum_time = time.time()
                self.logger.info("Manual VACUUM completed")
        except Exception as e:
            self.logger.error(f"Error in manual VACUUM: {e}")
    
    async def force_vacuum(self):
        """手動でVACUUMを実行（非同期版）"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.database_file) as db:
                self.logger.info("Manually executing VACUUM")
                await db.execute('VACUUM')
                self.delete_count = 0
                self.last_vacuum_time = time.time()
                self.logger.info("Manual VACUUM completed")
        except Exception as e:
            self.logger.error(f"Error in manual VACUUM: {e}")
    
    async def wait_for_vacuum_completion(self, timeout: float = 10.0) -> bool:
        """バックグラウンドVACUUMの完了を待機（非同期版）"""
        start_time = time.time()
        while self.vacuum_pending and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        return not self.vacuum_pending
    
    def get_db_stats(self) -> dict:
        """データベースの統計情報を取得"""
        if not self.sync_initialized:
            self.initialize_sync()
        
        try:
            with sqlite3.connect(self.database_file) as db:
                # ファイルサイズ
                cursor = db.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                cursor = db.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor = db.execute("PRAGMA freelist_count")
                freelist_count = cursor.fetchone()[0]
                
                # レコード数
                cursor = db.execute("SELECT COUNT(*) FROM memory")
                record_count = cursor.fetchone()[0]
                
                file_size = page_size * page_count
                unused_space = page_size * freelist_count
                
                return {
                    'file_size_bytes': file_size,
                    'unused_space_bytes': unused_space,
                    'record_count': record_count,
                    'delete_count_since_vacuum': self.delete_count,
                    'last_vacuum_time': self.last_vacuum_time,
                    'vacuum_recommended': self._should_vacuum()
                }
        except Exception as e:
            self.logger.error(f"Error getting DB stats: {e}")
            return {}
    
    def _schedule_background_vacuum(self):
        """バックグラウンドでVACUUMをスケジュールする"""
        if self.vacuum_pending:
            self.logger.debug("VACUUM already pending, skipping")
            return
        
        self.vacuum_pending = True
        self.vacuum_thread = threading.Thread(target=self._background_vacuum_worker, daemon=True)
        self.vacuum_thread.start()
        self.logger.info("Scheduled background VACUUM")
    
    def _background_vacuum_worker(self):
        """バックグラウンドVACUUMワーカー"""
        try:
            self.logger.info("Starting background VACUUM")
            
            # 専用のデータベース接続でVACUUM実行
            with sqlite3.connect(self.database_file) as db:
                # VACUUMは排他ロックを取るので、他の操作をブロックしないようにタイムアウトを設定
                db.execute('PRAGMA busy_timeout = 5000')  # 5秒タイムアウト
                
                start_time = time.time()
                db.execute('VACUUM')
                end_time = time.time()
                
                self.delete_count = 0
                self.last_vacuum_time = time.time()
                
                self.logger.info(f"Background VACUUM completed in {end_time - start_time:.2f} seconds")
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                self.logger.warning("Could not execute VACUUM: database is busy, will retry later")
            else:
                self.logger.error(f"Error in background VACUUM: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in background VACUUM: {e}")
        finally:
            self.vacuum_pending = False
    
    def set_vacuum_mode(self, background: bool = True):
        """
VACUUM実行モードを設定
        
        Args:
            background: True=バックグラウンド実行, False=同期実行
        """
        self.background_vacuum = background
        self.logger.info(f"VACUUM mode set to {'background' if background else 'synchronous'}")
    
    def is_vacuum_pending(self) -> bool:
        """バックグラウンドVACUUMが実行中かどうかを確認"""
        return self.vacuum_pending

    async def save(self, key: str, val: Any):
        if not self.initialized:
            await self.initialize()
        
        self.logger.debug(f"Saving {key} to memory")

        hash_key = self._name_hash(key)
        
        # メモリキャッシュへの安全な書き込み
        with self._lock:
            self.memory_store[hash_key] = val
            self.deleted_keys.discard(hash_key)
        
        await self.write_queue.put((hash_key, val))
        
        # レコード数チェックと削除処理は書き込み後に実行される

    def save_sync(self, key: str, val: Any):
        """同期版の save メソッド - バックグラウンドスレッドで永続化"""
        if not self.sync_initialized:
            self.initialize_sync()
        
        self.logger.debug(f"Saving {key} to memory (sync)")

        hash_key = self._name_hash(key)
        
        # メモリキャッシュに即座に保存（高速応答）
        with self._lock:
            self.memory_store[hash_key] = val
            # 保存時に削除済みマークを削除
            self.deleted_keys.discard(hash_key)
        
        # レコード数チェックは書き込み後にバックグラウンドで実行
        try:
            self.sync_write_queue.put(('check_evict', None), timeout=0.1)
        except queue.Full:
            # フォールバック：直接チェック
            self._check_and_evict_sync()
        
        # バックグラウンドスレッドに永続化を依頼（非ブロッキング）
        try:
            self.sync_write_queue.put(('save', (hash_key, val)), timeout=1.0)
            self.logger.debug(f"Queued {key} for background save")
        except queue.Full:
            self.logger.warning(f"Write queue full, falling back to direct save for {key}")
            # キューが満杯の場合は直接保存にフォールバック
            try:
                with sqlite3.connect(self.database_file) as db:
                    write_time = time.time()
                    db.execute(
                        'REPLACE INTO memory (key, value, reference_count, last_write_date) VALUES (?, ?, ?, ?)',
                        (hash_key, pickle.dumps(val), 0, write_time)
                    )
                    db.commit()
                    self.logger.debug(f"Direct saved {key} to DB (sync)")
            except Exception as e:
                self.logger.error(f"Error in direct save fallback: {e}")

    async def _async_db_writer(self):
        if not self.initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.database_file) as db:
            while True:
                await asyncio.sleep(0.1)
                hash_key, val = await self.write_queue.get()
                try:
                    self.logger.debug(f"Writing {hash_key} to DB")
                    write_time = time.time()
                    await db.execute(
                        'REPLACE INTO memory (key, value, reference_count, last_write_date) VALUES (?, ?, ?, ?)',
                        (hash_key, pickle.dumps(val), 0, write_time)
                    )
                    await db.commit()
                    self.logger.debug(f"Write complete for {hash_key}")
                    
                    # 書き込み後にレコード数チェックと削除処理
                    async with db.execute('SELECT COUNT(*) FROM memory') as cursor:
                        row = await cursor.fetchone()
                        record_count = row[0] if row else 0
                    
                    if record_count > self.max_records:
                        # 削除する数を計算（10%の余裕を持たせる）
                        delete_count = record_count - int(self.max_records * 0.9)
                        # 最も古くて参照回数の少ないレコードを選択
                        async with db.execute('''
                            SELECT key FROM memory 
                            ORDER BY reference_count ASC, last_write_date ASC 
                            LIMIT ?
                        ''', (delete_count,)) as cursor:
                            keys_to_delete = [row[0] for row in await cursor.fetchall()]
                        
                        # メモリキャッシュからも削除
                        for key in keys_to_delete:
                            if key in self.memory_store:
                                del self.memory_store[key]
                        
                        # データベースから削除
                        if keys_to_delete:
                            placeholders = ','.join(['?' for _ in keys_to_delete])
                            await db.execute(f'DELETE FROM memory WHERE key IN ({placeholders})', keys_to_delete)
                            await db.commit()
                            self.delete_count += len(keys_to_delete)
                            self.logger.info(f"Async evicted {len(keys_to_delete)} records from memory")
                            
                            # VACUUM判定
                            if self._should_vacuum():
                                if self.background_vacuum:
                                    self._schedule_background_vacuum()
                                else:
                                    self.logger.info("Executing VACUUM to reclaim space")
                                    await db.execute('VACUUM')
                                    self.delete_count = 0
                                    self.last_vacuum_time = time.time()
                                    self.logger.info("VACUUM completed")
                    
                except Exception as e:
                    self.logger.error(f"Error writing to DB: {e}")
                finally:
                    self.write_queue.task_done()

    async def load(self, key: str, defval: Any = None) -> Any:
        if not self.initialized:
            await self.initialize()
        
        hash_key = self._name_hash(key)
        
        # メモリキャッシュからの安全な読み込み
        with self._lock:
            if hash_key in self.memory_store and hash_key not in self.deleted_keys:
                cached_value = self.memory_store[hash_key]
                self.logger.debug(f"Loaded {key} from memory")
                # 参照回数をインクリメント
                await self._increment_reference_count(hash_key)
                return cached_value

        try:
            async with aiosqlite.connect(self.database_file) as db:
                async with db.execute(
                    'SELECT value FROM memory WHERE key = ?',
                    (hash_key,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row is not None:
                        value = pickle.loads(row[0])
                        
                        # メモリキャッシュへの安全な追加
                        with self._lock:
                            if hash_key not in self.deleted_keys:
                                self.memory_store[hash_key] = value
                        
                        # 参照回数をインクリメント
                        await self._increment_reference_count(hash_key)
                        self.logger.debug(f"Loaded {key} from DB")
                        return value
        except Exception as e:
            self.logger.error(f"Error reading from DB: {e}")
        
        return defval

    def load_sync(self, key: str, defval: Any = None) -> Any:
        """同期版の load メソッド - バックグラウンドスレッドで読み込み"""
        if not self.sync_initialized:
            self.initialize_sync()
        
        hash_key = self._name_hash(key)
        
        # 削除済みキーのチェック
        with self._lock:
            if hash_key in self.deleted_keys:
                self.logger.debug(f"Key {key} was deleted")
                return defval
            
            # メモリキャッシュから高速読み込み
            if hash_key in self.memory_store:
                self.logger.debug(f"Loaded {key} from memory (sync)")
                # 参照回数をインクリメント
                self._increment_reference_count_sync(hash_key)
                return self.memory_store[hash_key]

        # 直接データベースから読み込み
        try:
            with sqlite3.connect(self.database_file) as db:
                cursor = db.execute(
                    'SELECT value FROM memory WHERE key = ?',
                    (hash_key,)
                )
                row = cursor.fetchone()
                if row is not None:
                    value = pickle.loads(row[0])
                    with self._lock:
                        if hash_key not in self.deleted_keys:
                            self.memory_store[hash_key] = value
                    # 参照回数をインクリメント
                    self._increment_reference_count_sync(hash_key)
                    self.logger.debug(f"Direct loaded {key} from DB (sync)")
                    return value
        except Exception as e:
            self.logger.error(f"Error in direct read fallback: {e}")
        
        return defval

    async def close(self):
        """残りのキュー項目を処理し、リソースをクリーンアップします"""
        if self._init_task:
            await self.write_queue.join()
            self._init_task.cancel()
        
        # 同期操作のクリーンアップ
        self.close_sync()

    def close_sync(self):
        """同期版のクリーンアップ"""
        if self.daemon_running:
            self.logger.debug("Stopping daemon thread...")
            self.daemon_running = False
            
            # 残りの書き込み操作を完了させる
            if self.daemon_thread and self.daemon_thread.is_alive():
                try:
                    # 最大5秒待機
                    self.daemon_thread.join(timeout=5.0)
                    if self.daemon_thread.is_alive():
                        self.logger.warning("Daemon thread did not stop gracefully")
                    else:
                        self.logger.debug("Daemon thread stopped successfully")
                except Exception as e:
                    self.logger.error(f"Error stopping daemon thread: {e}")
        
        # VACUUMスレッドの停止
        if self.vacuum_thread and self.vacuum_thread.is_alive():
            self.logger.debug("Waiting for background VACUUM to complete...")
            try:
                self.vacuum_thread.join(timeout=10.0)  # 最大10秒待機
                if self.vacuum_thread.is_alive():
                    self.logger.warning("Background VACUUM did not complete within timeout")
                else:
                    self.logger.debug("Background VACUUM completed")
            except Exception as e:
                self.logger.error(f"Error waiting for VACUUM thread: {e}")

    def flush_sync(self):
        """同期版のフラッシュ - 全ての保留中の書き込み操作を完了"""
        if not self.daemon_running:
            return
            
        # 書き込みキューが空になるまで待機
        start_time = time.time()
        initial_size = self.sync_write_queue.qsize()
        
        while not self.sync_write_queue.empty() and time.time() - start_time < 5.0:
            time.sleep(0.05)  # より短い間隔でチェック
        
        final_size = self.sync_write_queue.qsize()
        
        if not self.sync_write_queue.empty():
            self.logger.warning(f"Flush timeout: {final_size} writes may not be completed (started with {initial_size})")
        else:
            self.logger.debug(f"All {initial_size} pending writes completed")
    
    async def flush(self):
        await self.write_queue.join()
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        # バックグラウンドVACUUMの完了を待機
        if self.vacuum_pending:
            self.logger.debug("Waiting for background VACUUM to complete...")
            vacuum_completed = await self.wait_for_vacuum_completion(10.0)
            if not vacuum_completed:
                self.logger.warning("Background VACUUM did not complete within timeout")
            else:
                self.logger.debug("Background VACUUM completed")
        
        await self.close()


# 使用例
async def main():

    logging.basicConfig(level=logging.INFO)

    # インスタンス作成
    async with PersistentMemory('my_custom_database.db') as mem:
        # メモリに保存
        await mem.save("test_key", "test_value")
        # メモリから読み込み
        value = await mem.load("test_key")
        print(f"Loaded value1: {value}")

        counter = await mem.load("counter", 0)
        print(f"Counter: {counter}")
        counter += 1
        await mem.save("counter", counter)
        
        # 非同期版では辞書インターフェースは使用しない（同期版で使用）
        await mem.save("test_key 3", "test_value 3")
        value = await mem.load("test_key 3")
        print(f"test_key 3: {value}")

        
    # インスタンス作成
    async with PersistentMemory('my_custom_database2.db') as mem:
        # メモリに保存
        await mem.save("test_key2", "test_value2")
        # メモリから読み込み
        value = await mem.load("test_key2")
        print(f"Loaded value3: {value}")

        value = await mem.load("test_key3", {})
        print(f"Loaded value2: {value}")
        value["count"] = value.get("count", 0) + 1
        await mem.save("test_key3", value)

    # 同期版の使用例（辞書インターフェース使用）
    print("\n--- 同期版の使用例（辞書インターフェース） ---")
    mem_sync = PersistentMemory('sync_test.db')
    
    try:
        # 辞書のようにデータを保存
        mem_sync["sync_key"] = "sync_value"
        mem_sync["sync_counter"] = 100
        mem_sync["user_data"] = {"name": "Bob", "age": 30}
        
        # 辞書のようにデータを読み込み
        sync_value = mem_sync["sync_key"]
        print(f"Sync loaded value: {sync_value}")
        
        sync_counter = mem_sync["sync_counter"]
        print(f"Sync counter: {sync_counter}")
        
        user_data = mem_sync["user_data"]
        print(f"User data: {user_data}")
        
        # カウンターを増加
        mem_sync["sync_counter"] = sync_counter + 1
        print(f"Updated counter: {mem_sync['sync_counter']}")
        
        # 存在しないキーのデフォルト値テスト
        default_value = mem_sync.load_sync("nonexistent_key", "default")
        print(f"Default value: {default_value}")
        
        # 削除のテスト
        print(f"Before deletion: {mem_sync['sync_key']}")
        del mem_sync["sync_key"]
        
        try:
            deleted_value = mem_sync["sync_key"]
            if deleted_value is not None:
                print(f"⚠️ 削除されたキーから値が取得されました: {deleted_value}")
            else:
                print("✓ 削除されたキーから値が取得されませんでした (None)")
        except KeyError:
            print("✓ 削除されたキーでKeyErrorが発生（期待通り）")
        
        # 全ての書き込み操作が完了するまで待機
        print("Flushing pending operations...")
        mem_sync.flush_sync()
        print("Flush completed")
        
    finally:
        # クリーンアップ
        print("Cleaning up...")
        mem_sync.close_sync()
        print("Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())