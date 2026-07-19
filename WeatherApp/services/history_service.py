"""
services/history_service.py
----------------------------
Manages the user's recently-searched-cities list, persisted to
data/history.json. Most-recent-first, deduplicated, capped in length.
"""

from __future__ import annotations

from constants import HISTORY_FILE, MAX_HISTORY_ITEMS
from services.json_store import JSONListStore
from utils.logger import get_logger

logger = get_logger(__name__)


class HistoryService:
    """Tracks recently searched cities."""

    def __init__(self) -> None:
        self._store = JSONListStore(HISTORY_FILE)
        self._history: list[str] = self._store.load()

    def add(self, city: str) -> None:
        """
        Record a search, moving `city` to the front if it already exists
        and trimming the list to `MAX_HISTORY_ITEMS`.
        """
        normalized = city.strip()
        if not normalized:
            return

        self._history = [
            c for c in self._history if c.lower() != normalized.lower()
        ]
        self._history.insert(0, normalized)
        self._history = self._history[:MAX_HISTORY_ITEMS]
        self._store.save(self._history)
        logger.info("Added '%s' to search history.", normalized)

    def get_all(self) -> list[str]:
        """Return the history list, most recent first."""
        return list(self._history)

    def clear(self) -> None:
        """Clear all search history."""
        self._history = []
        self._store.save(self._history)
        logger.info("Search history cleared.")
