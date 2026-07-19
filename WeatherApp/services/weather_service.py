"""
services/weather_service.py
-----------------------------
Orchestration layer sitting between the UI and the API client.

Responsibilities:
    - Validate input.
    - Try the live API first.
    - On network failure, fall back to cached (offline) data if available.
    - Keep the cache warm on every successful fetch.

The UI layer should only ever talk to `WeatherService`, never directly
to `WeatherAPIClient` — this is what makes offline mode, caching, and
future features (e.g. request de-duplication) transparent to the UI.
"""

from __future__ import annotations

from dataclasses import asdict

from api.exceptions import NoInternetConnectionError, RequestTimeoutError, WeatherAPIError
from api.weather_api import WeatherAPIClient
from models.weather import WeatherReport
from services.cache_service import CacheService
from utils.logger import get_logger
from utils.validators import ValidationError, validate_city_name

logger = get_logger(__name__)


class OfflineDataUnavailableError(Exception):
    """Raised when the network is unreachable AND no cached data exists."""


class WeatherService:
    """High-level facade used by the UI to fetch weather data."""

    def __init__(
        self,
        api_client: WeatherAPIClient | None = None,
        cache_service: CacheService | None = None,
    ) -> None:
        self._api_client = api_client or WeatherAPIClient()
        self._cache = cache_service or CacheService()

    def get_weather(self, city: str, units: str) -> tuple[WeatherReport, bool]:
        """
        Fetch a weather report for `city`, using the cache as an
        offline fallback if the live request fails due to connectivity.

        Args:
            city: Raw city name from user input (will be validated).
            units: 'metric' or 'imperial'.

        Returns:
            A tuple of (WeatherReport, is_stale). `is_stale` is True
            when the data came from cache due to a network failure.

        Raises:
            ValidationError: If `city` fails input validation.
            WeatherAPIError: For non-connectivity API failures (bad city,
                bad key, rate limit) where no sensible fallback exists.
            OfflineDataUnavailableError: If offline and nothing cached.
        """
        clean_city = validate_city_name(city)
        cache_key = f"{clean_city.lower()}:{units}"

        try:
            report = self._api_client.get_weather_report(clean_city, units)
            self._cache.set(cache_key, self._serialize(report))
            return report, False

        except (NoInternetConnectionError, RequestTimeoutError) as exc:
            logger.warning(
                "Live fetch failed for '%s' (%s); attempting offline cache.",
                clean_city,
                exc,
            )
            cached = self._cache.get(cache_key, allow_stale=True)
            if cached is None:
                raise OfflineDataUnavailableError(
                    f"No internet connection and no cached data for '{clean_city}'."
                ) from exc
            logger.info("Serving stale cached data for '%s'.", clean_city)
            return self._deserialize(cached), True

    @staticmethod
    def _serialize(report: WeatherReport) -> dict:
        """Convert a WeatherReport dataclass tree into a JSON-safe dict."""
        raw = asdict(report)
        raw["current"]["sunrise"] = report.current.sunrise.isoformat()
        raw["current"]["sunset"] = report.current.sunset.isoformat()
        raw["current"]["observed_at"] = report.current.observed_at.isoformat()
        for day in raw["daily_forecast"]:
            day["date"] = day["date"].isoformat() if hasattr(day["date"], "isoformat") else day["date"]
            for entry in day["entries"]:
                entry["timestamp"] = (
                    entry["timestamp"].isoformat()
                    if hasattr(entry["timestamp"], "isoformat")
                    else entry["timestamp"]
                )
        return raw

    @staticmethod
    def _deserialize(raw: dict) -> WeatherReport:
        """Reconstruct a WeatherReport from a cached JSON-safe dict."""
        from datetime import datetime

        from models.weather import (
            AirQuality,
            Coordinates,
            CurrentWeather,
            DailyForecast,
            ForecastEntry,
            WeatherCondition,
        )

        c = raw["current"]
        current = CurrentWeather(
            city=c["city"],
            country=c["country"],
            coordinates=Coordinates(**c["coordinates"]),
            temperature=c["temperature"],
            feels_like=c["feels_like"],
            temp_min=c["temp_min"],
            temp_max=c["temp_max"],
            humidity=c["humidity"],
            pressure=c["pressure"],
            wind_speed=c["wind_speed"],
            wind_degrees=c["wind_degrees"],
            visibility_meters=c["visibility_meters"],
            cloud_coverage=c["cloud_coverage"],
            condition=WeatherCondition(**c["condition"]),
            sunrise=datetime.fromisoformat(c["sunrise"]),
            sunset=datetime.fromisoformat(c["sunset"]),
            timezone_offset_seconds=c["timezone_offset_seconds"],
            observed_at=datetime.fromisoformat(c["observed_at"]),
            units=c["units"],
        )

        daily_forecast = []
        for day in raw["daily_forecast"]:
            entries = [
                ForecastEntry(
                    timestamp=datetime.fromisoformat(e["timestamp"]),
                    temperature=e["temperature"],
                    temp_min=e["temp_min"],
                    temp_max=e["temp_max"],
                    condition=WeatherCondition(**e["condition"]),
                    humidity=e["humidity"],
                    wind_speed=e["wind_speed"],
                    chance_of_rain=e["chance_of_rain"],
                )
                for e in day["entries"]
            ]
            daily_forecast.append(
                DailyForecast(
                    date=datetime.fromisoformat(day["date"]),
                    temp_min=day["temp_min"],
                    temp_max=day["temp_max"],
                    condition=WeatherCondition(**day["condition"]),
                    avg_humidity=day["avg_humidity"],
                    max_chance_of_rain=day["max_chance_of_rain"],
                    entries=entries,
                )
            )

        air_quality = AirQuality(**raw["air_quality"]) if raw.get("air_quality") else None

        return WeatherReport(
            current=current, daily_forecast=daily_forecast, air_quality=air_quality
        )
