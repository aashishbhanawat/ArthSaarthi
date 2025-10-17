from typing import Optional

import redis

from app.cache.base import CacheClient


class RedisCacheClient(CacheClient):
    """A cache client implementation for Redis."""

    def __init__(self, redis_url: str):
        self._client: Optional[redis.Redis] = None
        try:
            self._client = redis.from_url(redis_url, decode_responses=True)
            self._client.ping()
            print("Successfully connected to Redis for caching.")
        except redis.exceptions.ConnectionError as e:
            print(
                f"WARNING: Could not connect to Redis at {redis_url}. "
                f"Caching will be disabled. Error: {e}"
            )
            self._client = None

    def get(self, key: str) -> Optional[str]:
        if not self._client:
            return None
        return self._client.get(key)

    def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        if not self._client:
            return
        self._client.set(key, value, ex=expire)

    def delete(self, key: str) -> None:
        if not self._client:
            return
        self._client.delete(key)

    def clear(self) -> None:
        """Clears the entire cache (flushes the current Redis DB)."""
        if not self._client:
            return
        self._client.flushdb()
        print("Redis cache cleared.")
