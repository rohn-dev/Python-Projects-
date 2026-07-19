"""
models/weather.py
------------------
Typed domain models representing weather data.

These classes decouple the rest of the application (UI, services) from
the raw JSON shape returned by the weather provider. If we ever switch
from OpenWeatherMap to WeatherAPI.com, only `api/weather_api.py` needs
to change how it *builds* these objects — everything downstream stays
identical.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Coordinates:
    """Geographic coordinates for a location."""

    latitude: float
    longitude: float


@dataclass(frozen=True)
class WeatherCondition:
    """A single weather condition entry (e.g. 'Clear', 'clear sky', icon code)."""

    main: str
    description: str
    icon_code: str

    @property
    def icon_url(self) -> str:
        """Return the full URL for this condition's icon on OpenWeatherMap's CDN."""
        from constants import ICON_URL_TEMPLATE

        return ICON_URL_TEMPLATE.format(icon_code=self.icon_code)


@dataclass(frozen=True)
class CurrentWeather:
    """Current weather snapshot for a single location."""

    city: str
    country: str
    coordinates: Coordinates
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    pressure: int
    wind_speed: float
    wind_degrees: int
    visibility_meters: int
    cloud_coverage: int
    condition: WeatherCondition
    sunrise: datetime
    sunset: datetime
    timezone_offset_seconds: int
    observed_at: datetime
    units: str

    @property
    def visibility_km(self) -> float:
        """Visibility converted from meters to kilometers, rounded to 1 decimal."""
        return round(self.visibility_meters / 1000, 1)


@dataclass(frozen=True)
class ForecastEntry:
    """A single forecast data point (3-hour resolution from OpenWeatherMap)."""

    timestamp: datetime
    temperature: float
    temp_min: float
    temp_max: float
    condition: WeatherCondition
    humidity: int
    wind_speed: float
    chance_of_rain: float  # 0.0 - 1.0, straight from the API's "pop" field


@dataclass(frozen=True)
class DailyForecast:
    """Aggregated forecast for a single calendar day, built from ForecastEntry items."""

    date: datetime
    temp_min: float
    temp_max: float
    condition: WeatherCondition
    avg_humidity: int
    max_chance_of_rain: float
    entries: list[ForecastEntry] = field(default_factory=list)


@dataclass(frozen=True)
class AirQuality:
    """Air Quality Index data for a location."""

    aqi: int  # 1 (Good) - 5 (Very Poor), per OpenWeatherMap's scale
    co: float
    no2: float
    o3: float
    pm2_5: float
    pm10: float

    @property
    def label(self) -> str:
        """Human-readable label for the numeric AQI value."""
        from constants import AQI_LABELS

        return AQI_LABELS.get(self.aqi, "Unknown")


@dataclass(frozen=True)
class WeatherReport:
    """
    Complete weather report bundling current conditions, forecast, and
    air quality for a single location. This is the top-level object
    passed from services to the UI layer.
    """

    current: CurrentWeather
    daily_forecast: list[DailyForecast]
    air_quality: AirQuality | None = None
