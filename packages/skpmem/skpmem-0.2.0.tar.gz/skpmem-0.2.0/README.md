# skpmem - Smart Key-Value Persistent Memory

A high-performance, thread-safe persistent memory library that supports both synchronous and asynchronous operations with automatic eviction, reference counting, and background VACUUM optimization.

## Installation

```bash
pip install skpmem
```

## Features

- **Synchronous and asynchronous operation support**
- **Automatic LRU-style eviction with reference counting** 
- **Background VACUUM for database optimization**
- **Thread-safe mixed sync/async usage**
- **Dict-like interface for synchronous operations**
- **Context manager support for both paradigms**
- **Configurable memory limits and optimization thresholds**

## Quick Start

### Synchronous Usage

```python
from skpmem import PersistentMemory

# Basic synchronous usage
mem = PersistentMemory('data.db')
mem.initialize_sync()
mem['key'] = 'value'
value = mem['key']
mem.close_sync()
```

### Asynchronous Usage

```python
import asyncio
from skpmem import PersistentMemory

async def main():
    # Using async context manager
    async with PersistentMemory('data.db') as mem:
        await mem.save('key', 'value')
        value = await mem.load('key')
        print(f"Loaded value: {value}")

asyncio.run(main())
```

### Mixed Sync/Async Usage

```python
import asyncio
from skpmem import PersistentMemory

async def main():
    mem = PersistentMemory('data.db')
    await mem.initialize()
    mem.initialize_sync()
    
    # Use both sync and async operations
    mem['sync_key'] = 'sync_value'
    await mem.save('async_key', 'async_value')
    
    sync_value = mem['sync_key']
    async_value = await mem.load('async_key')
    
    await mem.close()

asyncio.run(main())
```

## API Reference

### PersistentMemory

The main class for persistent memory operations.

#### Methods

- `initialize_sync()`: Initialize for synchronous operations
- `initialize()`: Initialize for asynchronous operations (async)
- `save(key, value)`: Save data asynchronously (async)
- `load(key, default=None)`: Load data asynchronously (async)
- `close_sync()`: Close synchronous connections
- `close()`: Close asynchronous connections (async)

#### Dict-like Interface

- `mem[key] = value`: Store value synchronously
- `value = mem[key]`: Retrieve value synchronously
- `del mem[key]`: Delete key synchronously

#### Context Manager Support

```python
# Async context manager
async with PersistentMemory('data.db') as mem:
    await mem.save('key', 'value')

# Sync context manager
with PersistentMemory('data.db').sync_context() as mem:
    mem['key'] = 'value'
```

## Advanced Features

### Automatic Eviction

The library automatically manages memory usage by evicting least recently used items when memory limits are reached.

### Background Optimization

Database VACUUM operations run in the background to maintain optimal performance.

### Thread Safety

All operations are thread-safe, allowing mixed synchronous and asynchronous usage from multiple threads.

## Requirements

- Python 3.10+
- aiosqlite

## License

MIT License