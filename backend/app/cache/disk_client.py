from typing import Optional

import diskcache
from platformdirs import user_cache_dir

from app.cache.base import CacheClient


class DiskCacheClient(CacheClient):
    """A cache client implementation using a local disk cache."""

    def __init__(self):
        # Use platformdirs to find the appropriate user-specific cache directory
        cache_dir = user_cache_dir("arthsaarthi", "arthsaarthi-app")
        self._cache = diskcache.Cache(cache_dir)
        print(f"Initialized disk-based cache at: {cache_dir}")

    def get(self, key: str) -> Optional[str]:
        # .get() returns None if the key doesn't exist, which matches our interface
        return self._cache.get(key)

    def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        # The 'expire' parameter in diskcache.set is equivalent to Redis's 'ex'
        self._cache.set(key, value, expire=expire)

    def delete(self, key: str) -> None:
        # Use `__delitem__` for deletion, which is more idiomatic for cache/dict objects
        try:
            del self._cache[key]
        except KeyError:
            # Key was not in the cache, which is fine for a delete operation
            pass

    def clear(self) -> None:
        """Clears the entire disk cache."""
        self._cache.clear()
        print("Disk cache cleared.")
