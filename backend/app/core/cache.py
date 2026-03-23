"""Cache decorators and utilities for performance optimization.

@MX:NOTE
Simple in-memory cache for development. For production, use Redis.
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, TypeVar, ParamSpec
from collections import OrderedDict

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class InMemoryCache:
    """Simple in-memory cache with TTL support.

    @MX:NOTE
    Development-only cache. Not suitable for production.
    Use Redis for production deployments.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        """Initialize in-memory cache.

        Args:
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl

    def _is_expired(self, expiry: float) -> bool:
        """Check if cache entry has expired.

        Args:
            expiry: Expiry timestamp

        Returns:
            True if expired, False otherwise
        """
        return time.time() > expiry

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        import time

        if key not in self.cache:
            return None

        value, expiry = self.cache[key]

        # Check if expired
        if self._is_expired(expiry):
            del self.cache[key]
            return None

        # Move to end (LRU)
        self.cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        import time

        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)

        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self.cache[key] = (value, expiry)
        self.cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def delete(self, key: str) -> None:
        """Delete specific cache entry.

        Args:
            key: Cache key to delete
        """
        if key in self.cache:
            del self.cache[key]


# Global cache instance
_cache = InMemoryCache()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Callable[..., str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Cache decorator for functions.

    @MX:ANCHOR: Cache decorator
    @MX:REASON: High fan-in utility function

    Caches function results in memory. For production, use Redis.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys
        key_builder: Custom function to build cache key

    Returns:
        Decorated function with caching

    Example:
        @code-block:: python

        @cached(ttl=600, key_prefix="user:")
        async def get_user(user_id: str) -> User:
            return await db.fetch_user(user_id)
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder using function name and arguments
                key_parts = [key_prefix, func.__name__]
                if args:
                    key_parts.extend(str(a) for a in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_str = ":".join(key_parts)
                cache_key = hashlib.md5(key_str.encode()).hexdigest()

            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss: {cache_key}")

            return result

        # Add cache management methods to wrapper
        wrapper.cache_clear = lambda: _cache.clear()  # type: ignore[attr-defined]
        wrapper.cache_delete = lambda k: _cache.delete(k)  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator


class RedisCache:
    """Redis cache interface stub for production.

    @MX:NOTE: Production-only implementation
    To use Redis, install redis package and configure REDIS_URL.

    Example:
        @code-block:: python

        import redis
        from app.core.config import settings

        _redis_client = redis.from_url(settings.redis_url)

        def get_from_cache(key: str) -> Any | None:
            value = _redis_client.get(key)
            return json.loads(value) if value else None

        def set_in_cache(key: str, value: Any, ttl: int) -> None:
            _redis_client.setex(key, ttl, json.dumps(value))
    """

    pass


def cache_invalidate(*patterns: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to invalidate cache patterns after function execution.

    @MX:NOTE: Pattern-based cache invalidation

    Invalidates cache entries matching patterns after function executes.
    Useful for write operations that should invalidate related read caches.

    Args:
        *patterns: Cache key patterns to invalidate

    Returns:
        Decorated function

    Example:
        @code-block:: python

        @cache_invalidate("user:*", "profile:*")
        async def update_user(user_id: str, data: dict) -> User:
            return await db.update_user(user_id, data)
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            result = await func(*args, **kwargs)

            # Invalidate matching cache entries
            for pattern in patterns:
                # Simple implementation - in production use Redis SCAN with MATCH
                keys_to_delete = [k for k in _cache.cache.keys() if pattern in k]
                for key in keys_to_delete:
                    _cache.delete(key)
                    logger.debug(f"Cache invalidated: {key}")

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


async def get_cache() -> InMemoryCache:
    """Get cache instance.

    @MX:ANCHOR
    Cache dependency injection for services.
    Returns global in-memory cache instance.

    Returns:
        Cache instance
    """
    return _cache


# Import time at module level
import time
