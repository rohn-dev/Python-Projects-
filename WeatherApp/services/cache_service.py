"""
services/cache_service.py
--------------------------
Caches the last-known weather report per city so the app can:
    1. Avoid redundant API calls within a short time window.
    2. Fall back to "offline mode" showing stale-but-labeled data when
       the network is unavailable, instead of just erroring out.

Cache entries are stored as plain dicts (not domain objects) because
`WeatherReport` and friends are immutable dataclasses without built-in
JSON serialization — services/cache_service.py owns the (de)serialization
boundary so api/ and models/ stay free of persistence concerns.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from constants import CACHE_EXPIRY_SECONDS, CACHE_FILE
from utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """Simple TTL-based JSON cache, keyed by city name (lowercased)."""

    def __init__(self, cache_file: Path | None = None) -> None:
        self._cache_file = cache_file or CACHE_FILE
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if not self._cache_file.exists():
            return {}
        try:
            with self._cache_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache file unreadable (%s); starting empty.", exc)
            return {}

    def _persist(self) -> None:
        try:
            with self._cache_file.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.error("Failed to persist cache: %s", exc)

    def set(self, city: str, payload: dict) -> None:
        """Store `payload` (raw, JSON-serializable dict) for `city` with a timestamp."""
        key = city.strip().lower()
        self._data[key] = {"cached_at": time.time(), "payload": payload}
        self._persist()
        logger.debug("Cached weather payload for '%s'.", city)

    def get(self, city: str, allow_stale: bool = False) -> dict | None:
        """
        Retrieve a cached payload for `city`.

        Args:
            city: City name to look up.
            allow_stale: If True, return the cached value even if it has
                expired (used for offline-mode fallback). If False,
                expired entries return None.

        Returns:
            The cached payload dict, or None if absent (or expired and
            `allow_stale` is False).
        """
        key = city.strip().lower()
        entry = self._data.get(key)
        if entry is None:
            return None

        age = time.time() - entry["cached_at"]
        if age > CACHE_EXPIRY_SECONDS and not allow_stale:
            return None

        return entry["payload"]

    def get_age_seconds(self, city: str) -> float | None:
        """Return how many seconds old the cached entry for `city` is, or None."""
        entry = self._data.get(city.strip().lower())
        if entry is None:
            return None
        return time.time() - entry["cached_at"]
