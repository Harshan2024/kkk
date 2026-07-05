"""
app/cache/redis_adapter.py — Redis-Ready Cache Adapter
=======================================================
Phase 15: Future-Ready Redis Integration

Drop-in replacement for the existing in-process cache.
Uses Redis when REDIS_URL is configured; falls back to the existing
in-memory dict cache transparently.

Usage:
    from app.cache.redis_adapter import get_cache

    cache = get_cache()
    cache.set("dashboard:user_123", dashboard_data, ttl=300)
    data = cache.get("dashboard:user_123")
    cache.delete("dashboard:user_123")

To enable Redis:
    Set REDIS_URL=redis://localhost:6379/0 in your .env file.
    Install: pip install redis

Architecture:
    CacheAdapter (ABC)
    ├── InMemoryCacheAdapter  ← current default (zero dependencies)
    └── RedisCacheAdapter     ← activated by REDIS_URL env var
"""

import os
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger("carbontracker.cache.adapter")


# ─── Abstract Base ────────────────────────────────────────────────────────────
class CacheAdapter(ABC):
    """Abstract cache interface. All adapters must implement these methods."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key. Returns None if missing or expired."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Store a value. TTL in seconds. Returns True on success."""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove a key. Returns True if the key existed."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists without retrieving the value."""
        ...

    @abstractmethod
    def clear(self, pattern: str = "*") -> int:
        """Delete all keys matching a pattern. Returns count of deleted keys."""
        ...

    @abstractmethod
    def ping(self) -> bool:
        """Health check. Returns True if the cache is available."""
        ...

    @abstractmethod
    def stats(self) -> dict:
        """Return cache statistics."""
        ...


# ─── In-Memory Adapter (default, zero dependencies) ──────────────────────────
class InMemoryCacheAdapter(CacheAdapter):
    """
    Thread-safe in-memory cache with TTL support.
    This is the production default until Redis is configured.
    """

    def __init__(self):
        self._store: dict = {}
        self._expiry: dict = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None
            if key in self._expiry and time.monotonic() > self._expiry[key]:
                del self._store[key]
                del self._expiry[key]
                self._misses += 1
                return None
            self._hits += 1
            return self._store[key]

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        with self._lock:
            self._store[key] = value
            if ttl > 0:
                self._expiry[key] = time.monotonic() + ttl
            elif key in self._expiry:
                del self._expiry[key]
            self._sets += 1
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
            self._expiry.pop(key, None)
            if existed:
                self._deletes += 1
            return existed

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self, pattern: str = "*") -> int:
        with self._lock:
            if pattern == "*":
                count = len(self._store)
                self._store.clear()
                self._expiry.clear()
                return count
            # Simple prefix matching (no full glob support)
            prefix = pattern.rstrip("*")
            to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in to_delete:
                self._store.pop(k, None)
                self._expiry.pop(k, None)
            return len(to_delete)

    def ping(self) -> bool:
        return True

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "adapter": "in-memory",
                "keys": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "sets": self._sets,
                "deletes": self._deletes,
                "hit_ratio_pct": round(self._hits / total * 100, 2) if total > 0 else None,
            }


# ─── Redis Adapter (activated by REDIS_URL) ───────────────────────────────────
class RedisCacheAdapter(CacheAdapter):
    """
    Redis-backed cache adapter.
    Activated automatically when REDIS_URL is set.

    Requires: pip install redis
    """

    def __init__(self, redis_url: str):
        try:
            import redis as redis_lib
            self._client = redis_lib.from_url(
                redis_url,
                decode_responses=False,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
            )
            # Test connection
            self._client.ping()
            self._available = True
            logger.info(f"[RedisCache] Connected to Redis at {redis_url}")
        except ImportError:
            logger.error("[RedisCache] 'redis' package not installed. Run: pip install redis")
            self._available = False
        except Exception as e:
            logger.error(f"[RedisCache] Connection failed: {e}. Falling back to in-memory.")
            self._available = False

    def get(self, key: str) -> Optional[Any]:
        if not self._available:
            return None
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"[RedisCache] get({key}) error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self._available:
            return False
        try:
            serialized = json.dumps(value, default=str)
            if ttl > 0:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"[RedisCache] set({key}) error: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.warning(f"[RedisCache] delete({key}) error: {e}")
            return False

    def exists(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception:
            return False

    def clear(self, pattern: str = "*") -> int:
        if not self._available:
            return 0
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"[RedisCache] clear({pattern}) error: {e}")
            return 0

    def ping(self) -> bool:
        if not self._available:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False

    def stats(self) -> dict:
        if not self._available:
            return {"adapter": "redis", "status": "unavailable"}
        try:
            info = self._client.info()
            return {
                "adapter": "redis",
                "status": "connected",
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {"adapter": "redis", "status": f"error: {e}"}


# ─── Factory ──────────────────────────────────────────────────────────────────
_cache_instance: Optional[CacheAdapter] = None
_cache_lock = threading.Lock()


def get_cache() -> CacheAdapter:
    """
    Returns the active cache adapter singleton.

    - If REDIS_URL is set and redis package is installed → RedisCacheAdapter
    - Otherwise → InMemoryCacheAdapter (default)
    """
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance

    with _cache_lock:
        if _cache_instance is not None:
            return _cache_instance

        redis_url = os.getenv("REDIS_URL", "")
        if redis_url:
            adapter = RedisCacheAdapter(redis_url)
            if adapter._available:
                _cache_instance = adapter
                return _cache_instance
            logger.warning("[CacheFactory] Redis failed, falling back to in-memory cache")

        _cache_instance = InMemoryCacheAdapter()
        logger.info("[CacheFactory] Using in-memory cache adapter")
        return _cache_instance
