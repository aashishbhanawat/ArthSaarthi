import logging
from typing import List, Optional

import diskcache
from platformdirs import user_cache_dir

from app.cache.base import CacheClient

logger = logging.getLogger(__name__)


class DiskCacheClient(CacheClient):
    """A cache client implementation using a local disk cache."""

    def __init__(self):
        # Use platformdirs to find the appropriate user-specific cache directory
        cache_dir = user_cache_dir("arthsaarthi", "arthsaarthi-app")
        self._cache = diskcache.Cache(cache_dir)
        logger.info("Initialized disk-based cache at: %s", cache_dir)

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

    def delete_multi(self, keys: List[str]) -> None:
        with self._cache.transact():
            for key in keys:
                try:
                    del self._cache[key]
                except KeyError:
                    pass

    def incr(self, key: str, expire: Optional[int] = None) -> int:
        with self._cache.transact():
            current = self._cache.get(key, default=0)
            try:
                new_val = int(current) + 1
            except ValueError:
                new_val = 1
            self._cache.set(key, str(new_val), expire=expire)
            return new_val

    def clear(self) -> None:
        """Clears the entire disk cache."""
        self._cache.clear()
        logger.info("Disk cache cleared.")
