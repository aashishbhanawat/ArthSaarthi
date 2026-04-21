from functools import lru_cache
from typing import Optional

from app.cache.base import CacheClient
from app.cache.disk_client import DiskCacheClient
from app.cache.redis_client import RedisCacheClient
from app.core.config import settings


@lru_cache(maxsize=None)
def get_cache_client() -> Optional[CacheClient]:
    """
    Factory function to get the configured cache client instance.

    Uses LRU cache to ensure a singleton pattern, so the cache client is
    initialized only once per application lifecycle.

    Returns:
        An instance of a class that implements the CacheClient interface,
        or None if caching is disabled or fails to initialize.
    """
    if settings.CACHE_TYPE == "redis":
        return RedisCacheClient(redis_url=settings.REDIS_URL)
    elif settings.CACHE_TYPE == "disk":
        return DiskCacheClient()
    else:
        # This case should ideally not be reached if config validation is in place
        print(
            f"WARNING: Unknown CACHE_TYPE '{settings.CACHE_TYPE}'. "
            "Caching will be disabled."
        )
        return None
