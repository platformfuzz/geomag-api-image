"""Tests for cache service."""
import time

import pytest

from app.services.cache import CacheService


class TestCacheService:
    """Tests for CacheService."""

    def test_cache_initialization(self):
        """Test cache service initialization."""
        cache = CacheService(ttl_latest=100, ttl_historical=200, maxsize=50)
        assert cache.ttl_latest == 100
        assert cache.ttl_historical == 200
        assert cache.maxsize == 50

    def test_cache_get_set_latest(self):
        """Test getting and setting values in latest cache."""
        cache = CacheService(ttl_latest=1, ttl_historical=3600)

        # Set and get value
        cache.set("key1", "value1", is_latest=True)
        assert cache.get("key1", is_latest=True) == "value1"

        # Get non-existent key
        assert cache.get("key2", is_latest=True) is None

    def test_cache_get_set_historical(self):
        """Test getting and setting values in historical cache."""
        cache = CacheService(ttl_latest=300, ttl_historical=1)

        # Set and get value
        cache.set("key1", "value1", is_latest=False)
        assert cache.get("key1", is_latest=False) == "value1"

        # Get non-existent key
        assert cache.get("key2", is_latest=False) is None

    def test_cache_ttl_expiration_latest(self):
        """Test that latest cache entries expire after TTL."""
        cache = CacheService(ttl_latest=1, ttl_historical=3600)

        cache.set("key1", "value1", is_latest=True)
        # Verify value is cached immediately
        assert cache.get("key1", is_latest=True) == "value1"

        # Wait for expiration (TTL is 1 second, wait 1.1 seconds)
        time.sleep(1.1)
        assert cache.get("key1", is_latest=True) is None

    def test_cache_ttl_expiration_historical(self):
        """Test that historical cache entries expire after TTL."""
        cache = CacheService(ttl_latest=300, ttl_historical=1)

        cache.set("key1", "value1", is_latest=False)
        # Verify value is cached immediately
        assert cache.get("key1", is_latest=False) == "value1"

        # Wait for expiration (TTL is 1 second, wait 1.1 seconds)
        time.sleep(1.1)
        assert cache.get("key1", is_latest=False) is None

    def test_cache_clear(self):
        """Test clearing all caches."""
        cache = CacheService()

        cache.set("key1", "value1", is_latest=True)
        cache.set("key2", "value2", is_latest=False)

        assert cache.get("key1", is_latest=True) == "value1"
        assert cache.get("key2", is_latest=False) == "value2"

        cache.clear()

        assert cache.get("key1", is_latest=True) is None
        assert cache.get("key2", is_latest=False) is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheService(ttl_latest=300, ttl_historical=3600, maxsize=100)

        cache.set("key1", "value1", is_latest=True)
        cache.set("key2", "value2", is_latest=False)

        stats = cache.get_stats()

        assert stats["latest_cache"]["size"] == 1
        assert stats["latest_cache"]["maxsize"] == 100
        assert stats["latest_cache"]["ttl"] == 300
        assert stats["historical_cache"]["size"] == 1
        assert stats["historical_cache"]["maxsize"] == 100
        assert stats["historical_cache"]["ttl"] == 3600
