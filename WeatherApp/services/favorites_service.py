"""
services/favorites_service.py
------------------------------
Manages the user's favorite/pinned cities, persisted to data/favorites.json.
"""

from __future__ import annotations

from constants import FAVORITES_FILE, MAX_FAVORITES
from services.json_store import JSONListStore
from utils.logger import get_logger

logger = get_logger(__name__)


class FavoritesLimitReachedError(Exception):
    """Raised when the user tries to add more than MAX_FAVORITES cities."""


class FavoritesService:
    """Manages the set of cities the user has marked as favorites."""

    def __init__(self) -> None:
        self._store = JSONListStore(FAVORITES_FILE)
        self._favorites: list[str] = self._store.load()

    def add(self, city: str) -> None:
        """
        Add `city` to favorites.

        Raises:
            FavoritesLimitReachedError: If MAX_FAVORITES would be exceeded.
        """
        normalized = city.strip()
        if not normalized or self.is_favorite(normalized):
            return

        if len(self._favorites) >= MAX_FAVORITES:
            raise FavoritesLimitReachedError(
                f"You can only save up to {MAX_FAVORITES} favorite cities."
            )

        self._favorites.append(normalized)
        self._store.save(self._favorites)
        logger.info("Added '%s' to favorites.", normalized)

    def remove(self, city: str) -> None:
        """Remove `city` from favorites, if present (case-insensitive)."""
        before = len(self._favorites)
        self._favorites = [
            c for c in self._favorites if c.lower() != city.strip().lower()
        ]
        if len(self._favorites) != before:
            self._store.save(self._favorites)
            logger.info("Removed '%s' from favorites.", city)

    def toggle(self, city: str) -> bool:
        """
        Add `city` if not favorited, remove it if it is.

        Returns:
            True if the city is now a favorite, False if it was just removed.
        """
        if self.is_favorite(city):
            self.remove(city)
            return False
        self.add(city)
        return True

    def is_favorite(self, city: str) -> bool:
        """Check whether `city` is currently favorited (case-insensitive)."""
        return city.strip().lower() in {c.lower() for c in self._favorites}

    def get_all(self) -> list[str]:
        """Return all favorite cities."""
        return list(self._favorites)
