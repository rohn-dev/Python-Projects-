"""
services/json_store.py
-----------------------
Small shared base class for services that persist a list of strings to
a JSON file (history, favorites). Extracted here so `HistoryService`
and `FavoritesService` don't duplicate load/save/error-handling logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


class JSONListStore:
    """Generic, crash-safe persistence for an ordered list of strings."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[str]:
        """
        Load the list from disk.

        Returns an empty list (rather than raising) if the file is
        missing, empty, or corrupted — persistence failures should
        never crash the app; they should just mean "start fresh".
        """
        if not self._file_path.exists():
            return []

        try:
            with self._file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                logger.warning(
                    "Expected a list in %s, got %s. Resetting.",
                    self._file_path,
                    type(data).__name__,
                )
                return []
            return [str(item) for item in data]
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read %s: %s. Starting with an empty list.", self._file_path, exc)
            return []

    def save(self, items: list[str]) -> None:
        """Persist `items` to disk, logging (but not raising) on failure."""
        try:
            with self._file_path.open("w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.error("Failed to write %s: %s", self._file_path, exc)
