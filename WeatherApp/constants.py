"""
constants.py
------------
Centralized, immutable values used across the WeatherApp.

Rule of thumb: if a value never changes at runtime and is used in more
than one place (or even just deserves a name instead of a magic literal),
it belongs here — not sprinkled through business logic.
"""

from enum import Enum
from pathlib import Path


# --------------------------------------------------------------------------
# Filesystem paths
# --------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
ASSETS_DIR: Path = BASE_DIR / "assets"
ICONS_DIR: Path = ASSETS_DIR / "icons"
LOGS_DIR: Path = BASE_DIR / "logs"
CACHE_DIR: Path = BASE_DIR / "cache"
EXPORTS_DIR: Path = BASE_DIR / "exports"

HISTORY_FILE: Path = DATA_DIR / "history.json"
FAVORITES_FILE: Path = DATA_DIR / "favorites.json"
CACHE_FILE: Path = CACHE_DIR / "weather_cache.json"

# --------------------------------------------------------------------------
# API endpoints (OpenWeatherMap)
# --------------------------------------------------------------------------
CURRENT_WEATHER_ENDPOINT: str = "/data/2.5/weather"
FORECAST_ENDPOINT: str = "/data/2.5/forecast"
AIR_POLLUTION_ENDPOINT: str = "/data/2.5/air_pollution"
GEOCODING_ENDPOINT: str = "/geo/1.0/direct"
ICON_URL_TEMPLATE: str = "https://openweathermap.org/img/wn/{icon_code}@2x.png"

# --------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------
class TemperatureUnit(str, Enum):
    """Supported temperature unit systems, matching OpenWeatherMap's API values."""

    CELSIUS = "metric"
    FAHRENHEIT = "imperial"


UNIT_SYMBOLS: dict[str, str] = {
    TemperatureUnit.CELSIUS.value: "°C",
    TemperatureUnit.FAHRENHEIT.value: "°F",
}

WIND_SPEED_UNITS: dict[str, str] = {
    TemperatureUnit.CELSIUS.value: "m/s",
    TemperatureUnit.FAHRENHEIT.value: "mph",
}

# --------------------------------------------------------------------------
# Limits & thresholds
# --------------------------------------------------------------------------
MAX_HISTORY_ITEMS: int = 15
MAX_FAVORITES: int = 20
CACHE_EXPIRY_SECONDS: int = 600  # 10 minutes
FORECAST_DAYS: int = 5
REQUEST_RETRY_ATTEMPTS: int = 3
REQUEST_RETRY_BACKOFF_SECONDS: float = 1.5

# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
APP_NAME: str = "WeatherApp"
APP_MIN_WIDTH: int = 900
APP_MIN_HEIGHT: int = 600
DEFAULT_APPEARANCE_MODE: str = "dark"  # "dark" | "light" | "system"
DEFAULT_COLOR_THEME: str = "blue"

# --------------------------------------------------------------------------
# Air Quality Index labels (per OpenWeatherMap's 1-5 AQI scale)
# --------------------------------------------------------------------------
AQI_LABELS: dict[int, str] = {
    1: "Good",
    2: "Fair",
    3: "Moderate",
    4: "Poor",
    5: "Very Poor",
}
