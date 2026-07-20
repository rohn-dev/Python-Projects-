"""Unit tests for services/history_service.py, favorites_service.py, and cache_service.py."""

import time

import pytest

from services.cache_service import CacheService
from services.favorites_service import FavoritesLimitReachedError, FavoritesService
from services.history_service import HistoryService


@pytest.fixture
def history_service(tmp_path, monkeypatch):
    import constants

    monkeypatch.setattr(constants, "HISTORY_FILE", tmp_path / "history.json")
    # HistoryService reads HISTORY_FILE at import time via the constants module,
    # so we patch the reference it actually uses.
    import services.history_service as hs_module

    monkeypatch.setattr(hs_module, "HISTORY_FILE", tmp_path / "history.json")
    return HistoryService()


@pytest.fixture
def favorites_service(tmp_path, monkeypatch):
    import services.favorites_service as fs_module

    monkeypatch.setattr(fs_module, "FAVORITES_FILE", tmp_path / "favorites.json")
    monkeypatch.setattr(fs_module, "MAX_FAVORITES", 3)
    return FavoritesService()


class TestHistoryService:
    def test_starts_empty(self, history_service):
        assert history_service.get_all() == []

    def test_adds_city_to_front(self, history_service):
        history_service.add("London")
        history_service.add("Paris")
        assert history_service.get_all() == ["Paris", "London"]

    def test_deduplicates_case_insensitively(self, history_service):
        history_service.add("London")
        history_service.add("london")
        assert history_service.get_all() == ["london"]

    def test_moves_repeated_city_to_front(self, history_service):
        history_service.add("London")
        history_service.add("Paris")
        history_service.add("London")
        assert history_service.get_all() == ["London", "Paris"]

    def test_ignores_empty_input(self, history_service):
        history_service.add("   ")
        assert history_service.get_all() == []

    def test_clear_empties_history(self, history_service):
        history_service.add("London")
        history_service.clear()
        assert history_service.get_all() == []

    def test_caps_at_max_history_items(self, history_service, monkeypatch):
        import services.history_service as hs_module

        monkeypatch.setattr(hs_module, "MAX_HISTORY_ITEMS", 3)
        for city in ["A", "B", "C", "D"]:
            history_service.add(city)
        assert len(history_service.get_all()) == 3
        assert history_service.get_all() == ["D", "C", "B"]


class TestFavoritesService:
    def test_starts_empty(self, favorites_service):
        assert favorites_service.get_all() == []

    def test_add_and_check(self, favorites_service):
        favorites_service.add("Tokyo")
        assert favorites_service.is_favorite("tokyo") is True

    def test_remove(self, favorites_service):
        favorites_service.add("Tokyo")
        favorites_service.remove("Tokyo")
        assert favorites_service.is_favorite("Tokyo") is False

    def test_toggle_adds_then_removes(self, favorites_service):
        assert favorites_service.toggle("Berlin") is True
        assert favorites_service.toggle("Berlin") is False

    def test_raises_when_limit_reached(self, favorites_service):
        favorites_service.add("A")
        favorites_service.add("B")
        favorites_service.add("C")
        with pytest.raises(FavoritesLimitReachedError):
            favorites_service.add("D")

    def test_adding_duplicate_is_noop(self, favorites_service):
        favorites_service.add("Rome")
        favorites_service.add("Rome")
        assert favorites_service.get_all().count("Rome") == 1


class TestCacheService:
    def test_returns_none_for_missing_key(self, tmp_path):
        cache = CacheService(cache_file=tmp_path / "cache.json")
        assert cache.get("Nowhere") is None

    def test_stores_and_retrieves_payload(self, tmp_path):
        cache = CacheService(cache_file=tmp_path / "cache.json")
        cache.set("London", {"temp": 20})
        assert cache.get("London") == {"temp": 20}

    def test_expired_entry_returns_none_by_default(self, tmp_path, monkeypatch):
        import services.cache_service as cs_module

        monkeypatch.setattr(cs_module, "CACHE_EXPIRY_SECONDS", 0)
        cache = CacheService(cache_file=tmp_path / "cache.json")
        cache.set("London", {"temp": 20})
        time.sleep(0.01)
        assert cache.get("London") is None

    def test_expired_entry_returned_with_allow_stale(self, tmp_path, monkeypatch):
        import services.cache_service as cs_module

        monkeypatch.setattr(cs_module, "CACHE_EXPIRY_SECONDS", 0)
        cache = CacheService(cache_file=tmp_path / "cache.json")
        cache.set("London", {"temp": 20})
        time.sleep(0.01)
        assert cache.get("London", allow_stale=True) == {"temp": 20}

    def test_key_lookup_is_case_insensitive(self, tmp_path):
        cache = CacheService(cache_file=tmp_path / "cache.json")
        cache.set("London", {"temp": 20})
        assert cache.get("LONDON") == {"temp": 20}
