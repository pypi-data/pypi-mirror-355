import time
from typing import Any


class TimedCache:
    def __init__(self, ttl_minutes: int = 180):
        self.ttl = ttl_minutes * 60  # Convert to seconds
        self._cache: dict[str, (float, Any)] = {}

    def get(self, key: str) -> Any | None:
        item = self._cache.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            # Expired
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any):
        expires_at = time.time() + self.ttl
        self._cache[key] = (expires_at, value)

    def clear(self):
        self._cache.clear()
