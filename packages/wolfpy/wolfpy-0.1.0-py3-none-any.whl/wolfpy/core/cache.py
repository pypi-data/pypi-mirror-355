"""
WolfPy Advanced Caching System.

This module provides comprehensive caching capabilities including
multi-level caching, cache warming, invalidation strategies,
and distributed caching support.
"""

import time
import threading
import hashlib
import pickle
import gzip
import json
import weakref
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps
import asyncio


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, max_memory: int = 100 * 1024 * 1024):
        """
        Initialize memory cache backend.
        
        Args:
            max_size: Maximum number of entries
            max_memory: Maximum memory usage in bytes
        """
        self.max_size = max_size
        self.max_memory = max_memory
        self._cache = OrderedDict()
        self._entries = {}  # key -> CacheEntry
        self._current_memory = 0
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._entries[key]
            
            # Check expiration
            if entry.expires_at and time.time() > entry.expires_at:
                self._remove_entry(key)
                self._stats['misses'] += 1
                return None
            
            # Update access info
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._stats['hits'] += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            # Calculate size
            try:
                size = len(pickle.dumps(value))
            except:
                size = sys.getsizeof(value)
            
            # Check if we need to evict
            while (len(self._cache) >= self.max_size or 
                   self._current_memory + size > self.max_memory):
                if not self._evict_lru():
                    break
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Create new entry
            expires_at = time.time() + ttl if ttl else None
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                size=size
            )
            
            self._cache[key] = True
            self._entries[key] = entry
            self._current_memory += size
            
            self._stats['sets'] += 1
            return True
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._entries.clear()
            self._current_memory = 0
            return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._entries[key]
            if entry.expires_at and time.time() > entry.expires_at:
                self._remove_entry(key)
                return False
            
            return True
    
    def _remove_entry(self, key: str):
        """Remove entry from cache."""
        if key in self._cache:
            entry = self._entries[key]
            self._current_memory -= entry.size
            del self._cache[key]
            del self._entries[key]
    
    def _evict_lru(self) -> bool:
        """Evict least recently used entry."""
        if not self._cache:
            return False
        
        # Get least recently used key
        lru_key = next(iter(self._cache))
        self._remove_entry(lru_key)
        self._stats['evictions'] += 1
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'hit_rate': hit_rate,
                'size': len(self._cache),
                'memory_usage': self._current_memory,
                'memory_usage_mb': self._current_memory / 1024 / 1024
            }


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for distributed caching."""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0', 
                 key_prefix: str = 'wolfpy:cache:'):
        """
        Initialize Redis cache backend.
        
        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for cache keys
        """
        try:
            import redis
            self.redis = redis.from_url(redis_url)
            self.key_prefix = key_prefix
            
            # Test connection
            self.redis.ping()
            
        except ImportError:
            raise ImportError("redis package is required for RedisCacheBackend")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.key_prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            redis_key = self._make_key(key)
            data = self.redis.get(redis_key)
            
            if data is None:
                return None
            
            # Deserialize
            return pickle.loads(data)
            
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(value)
            
            if ttl:
                return self.redis.setex(redis_key, ttl, data)
            else:
                return self.redis.set(redis_key, data)
                
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            redis_key = self._make_key(key)
            return bool(self.redis.delete(redis_key))
        except Exception:
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            pattern = f"{self.key_prefix}*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            redis_key = self._make_key(key)
            return bool(self.redis.exists(redis_key))
        except Exception:
            return False


class MultiLevelCache:
    """Multi-level cache with L1 (memory) and L2 (persistent) backends."""
    
    def __init__(self, l1_backend: CacheBackend, l2_backend: CacheBackend = None):
        """
        Initialize multi-level cache.
        
        Args:
            l1_backend: Fast cache backend (usually memory)
            l2_backend: Slower but persistent cache backend (optional)
        """
        self.l1 = l1_backend
        self.l2 = l2_backend
        self._stats = defaultdict(int)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, checking L1 then L2."""
        # Try L1 first
        value = self.l1.get(key)
        if value is not None:
            self._stats['l1_hits'] += 1
            return value
        
        self._stats['l1_misses'] += 1
        
        # Try L2 if available
        if self.l2:
            value = self.l2.get(key)
            if value is not None:
                # Promote to L1
                self.l1.set(key, value)
                self._stats['l2_hits'] += 1
                return value
            
            self._stats['l2_misses'] += 1
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in both cache levels."""
        l1_success = self.l1.set(key, value, ttl)
        l2_success = True
        
        if self.l2:
            l2_success = self.l2.set(key, value, ttl)
        
        self._stats['sets'] += 1
        return l1_success and l2_success
    
    def delete(self, key: str) -> bool:
        """Delete value from both cache levels."""
        l1_success = self.l1.delete(key)
        l2_success = True
        
        if self.l2:
            l2_success = self.l2.delete(key)
        
        self._stats['deletes'] += 1
        return l1_success and l2_success
    
    def clear(self) -> bool:
        """Clear both cache levels."""
        l1_success = self.l1.clear()
        l2_success = True
        
        if self.l2:
            l2_success = self.l2.clear()
        
        return l1_success and l2_success
    
    def exists(self, key: str) -> bool:
        """Check if key exists in either cache level."""
        return self.l1.exists(key) or (self.l2 and self.l2.exists(key))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = dict(self._stats)
        
        # Calculate hit rates
        total_l1 = stats.get('l1_hits', 0) + stats.get('l1_misses', 0)
        total_l2 = stats.get('l2_hits', 0) + stats.get('l2_misses', 0)
        
        if total_l1 > 0:
            stats['l1_hit_rate'] = stats.get('l1_hits', 0) / total_l1
        
        if total_l2 > 0:
            stats['l2_hit_rate'] = stats.get('l2_hits', 0) / total_l2
        
        # Add backend stats if available
        if hasattr(self.l1, 'get_stats'):
            stats['l1_backend_stats'] = self.l1.get_stats()
        
        if self.l2 and hasattr(self.l2, 'get_stats'):
            stats['l2_backend_stats'] = self.l2.get_stats()
        
        return stats


class CacheManager:
    """Central cache management system."""
    
    def __init__(self, default_backend: CacheBackend = None):
        """
        Initialize cache manager.
        
        Args:
            default_backend: Default cache backend
        """
        self.default_backend = default_backend or MemoryCacheBackend()
        self._caches = {'default': self.default_backend}
        self._cache_groups = defaultdict(set)
        self._invalidation_callbacks = defaultdict(list)
        self._lock = threading.RLock()
    
    def register_cache(self, name: str, backend: CacheBackend):
        """Register a named cache backend."""
        with self._lock:
            self._caches[name] = backend
    
    def get_cache(self, name: str = 'default') -> CacheBackend:
        """Get cache backend by name."""
        return self._caches.get(name, self.default_backend)
    
    def cache_function(self, ttl: int = 300, cache_name: str = 'default', 
                      key_func: Callable = None):
        """Decorator for caching function results."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cache = self.get_cache(cache_name)
                result = cache.get(cache_key)
                
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def invalidate_group(self, group: str):
        """Invalidate all cache entries in a group."""
        with self._lock:
            if group in self._cache_groups:
                for cache_key in self._cache_groups[group]:
                    for cache in self._caches.values():
                        cache.delete(cache_key)
                
                self._cache_groups[group].clear()
                
                # Call invalidation callbacks
                for callback in self._invalidation_callbacks[group]:
                    try:
                        callback(group)
                    except Exception:
                        pass
    
    def add_to_group(self, group: str, cache_key: str):
        """Add cache key to a group for batch invalidation."""
        with self._lock:
            self._cache_groups[group].add(cache_key)
    
    def register_invalidation_callback(self, group: str, callback: Callable):
        """Register callback for group invalidation."""
        with self._lock:
            self._invalidation_callbacks[group].append(callback)
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        stats = {}
        
        with self._lock:
            for name, cache in self._caches.items():
                if hasattr(cache, 'get_stats'):
                    stats[name] = cache.get_stats()
                else:
                    stats[name] = {'type': type(cache).__name__}
        
        return stats
    
    def warm_cache(self, warming_functions: List[Callable]):
        """Warm cache with predefined data."""
        for func in warming_functions:
            try:
                func()
            except Exception:
                pass  # Continue warming other functions
    
    def cleanup_expired(self):
        """Clean up expired entries from all caches."""
        with self._lock:
            for cache in self._caches.values():
                if hasattr(cache, 'cleanup_expired'):
                    cache.cleanup_expired()


# Global cache manager instance
cache_manager = CacheManager()
