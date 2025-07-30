"""
skpmem - Smart Key-Value Persistent Memory

A high-performance, thread-safe persistent memory library that supports
both synchronous and asynchronous operations with automatic eviction,
reference counting, and background VACUUM optimization.

Main Classes:
    PersistentMemory: The main persistent memory implementation
    
Usage:
    # Basic usage
    from skpmem import PersistentMemory
    
    # Synchronous usage
    mem = PersistentMemory('data.db')
    mem.initialize_sync()
    mem['key'] = 'value'
    value = mem['key']
    mem.close_sync()
    
    # Asynchronous usage  
    async with PersistentMemory('data.db') as mem:
        await mem.save('key', 'value')
        value = await mem.load('key')
    
    # Mixed usage
    mem = PersistentMemory('data.db')
    await mem.initialize()
    mem.initialize_sync()
    
    # Use both sync and async operations
    mem['sync_key'] = 'sync_value'
    await mem.save('async_key', 'async_value')
    
    sync_value = mem['sync_key']
    async_value = await mem.load('async_key')
    
    await mem.close()

Features:
    - Synchronous and asynchronous operation support
    - Automatic LRU-style eviction with reference counting
    - Background VACUUM for database optimization
    - Thread-safe mixed sync/async usage
    - Dict-like interface for synchronous operations
    - Context manager support for both paradigms
    - Configurable memory limits and optimization thresholds
"""

from .pmem import PersistentMemory

__version__ = '0.2.0'
__author__ = 'skpmem'
__email__ = 'skpmem@example.com'
__description__ = 'Smart Key-Value Persistent Memory with sync/async support'

__all__ = [
    'PersistentMemory',
]

# For backward compatibility during transition
from .pmem import PersistentMemory as AsyncPersistentMemory

# Version info
VERSION_INFO = {
    'major': 0,
    'minor': 2,
    'patch': 0,
    'release': 'stable'
}

def get_version():
    """Get version string"""
    return __version__

def get_version_info():
    """Get detailed version information"""
    return VERSION_INFO.copy()