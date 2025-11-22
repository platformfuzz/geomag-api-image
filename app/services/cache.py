"""Caching service for API responses."""
import os
from typing import Any, Optional

from cachetools import TTLCache


class CacheService:
    """TTL-based cache service for API responses."""

    def __init__(
        self,
        ttl_latest: int = 300,
        ttl_historical: int = 86400,  # Increased to 24 hours for historical data
        maxsize: int = 1000,
    ):
        """
        Initialize cache service.

        Args:
            ttl_latest: TTL in seconds for latest data (default: 5 minutes)
            ttl_historical: TTL in seconds for historical data (default: 24 hours)
            maxsize: Maximum number of cache entries
        """
        self.ttl_latest = int(os.getenv("CACHE_TTL_LATEST", ttl_latest))
        self.ttl_historical = int(os.getenv("CACHE_TTL_HISTORICAL", ttl_historical))
        self.maxsize = maxsize

        # Separate caches for latest and historical data
        self.latest_cache: TTLCache[str, Any] = TTLCache(
            maxsize=maxsize, ttl=self.ttl_latest
        )
        self.historical_cache: TTLCache[str, Any] = TTLCache(
            maxsize=maxsize, ttl=self.ttl_historical
        )

    def _get_cache(self, is_latest: bool) -> TTLCache[str, Any]:
        """Get the appropriate cache based on data type."""
        return self.latest_cache if is_latest else self.historical_cache

    def get(self, key: str, is_latest: bool = False) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            is_latest: Whether this is latest data (uses shorter TTL)

        Returns:
            Cached value or None if not found
        """
        cache = self._get_cache(is_latest)
        return cache.get(key)

    def set(self, key: str, value: Any, is_latest: bool = False) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            is_latest: Whether this is latest data (uses shorter TTL)
        """
        cache = self._get_cache(is_latest)
        cache[key] = value

    def clear(self) -> None:
        """Clear all caches."""
        self.latest_cache.clear()
        self.historical_cache.clear()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "latest_cache": {
                "size": len(self.latest_cache),
                "maxsize": self.latest_cache.maxsize,
                "ttl": self.ttl_latest,
            },
            "historical_cache": {
                "size": len(self.historical_cache),
                "maxsize": self.historical_cache.maxsize,
                "ttl": self.ttl_historical,
            },
        }


# Global cache instance
cache_service = CacheService()
