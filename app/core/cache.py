from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class CacheItem:
    value: Any
    expires_at: float

class TTLCache:
    def __init__(self, ttl_seconds: int = 60, max_items: int = 2000):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._data: dict[str, CacheItem] = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.time()

    def _cleanup(self) -> None:
        now = self._now()
        # remove expired
        expired = [k for k, v in self._data.items() if v.expires_at <= now]
        for k in expired:
            self._data.pop(k, None)

        # cap size (simple eviction: remove oldest expiry first)
        if len(self._data) > self.max_items:
            keys_by_exp = sorted(self._data.items(), key=lambda kv: kv[1].expires_at)
            for k, _ in keys_by_exp[: len(self._data) - self.max_items]:
                self._data.pop(k, None)

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            if item.expires_at <= self._now():
                self._data.pop(key, None)
                return None
            return item.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None):
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        with self._lock:
            self._cleanup()
            self._data[key] = CacheItem(value=value, expires_at=self._now() + ttl)

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl_seconds: int | None = None):
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value, ttl_seconds=ttl_seconds)
        return value

    def delete_prefix(self, prefix: str):
        with self._lock:
            keys = [k for k in self._data.keys() if k.startswith(prefix)]
            for k in keys:
                self._data.pop(k, None)

