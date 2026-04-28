import json
from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheClient(ABC):
    """Abstract base class for a cache client."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Gets a value from the cache. Returns it as a string."""
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        """Sets a value in the cache with an optional TTL."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """Deletes a key from the cache."""
        raise NotImplementedError

    def get_json(self, key: str) -> Optional[Any]:
        """Gets a JSON value from the cache and deserializes it."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Handle cases where the value is not valid JSON
                return None
        return None

    def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Serializes a value to JSON and stores it in the cache."""
        self.set(key, json.dumps(value), expire)
