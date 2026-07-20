"""
config.py
---------
Loads, validates, and exposes application configuration sourced from
environment variables (via a local .env file).

This is the ONLY module that should call `os.getenv` for application
settings. Every other module imports the `settings` singleton defined
here rather than touching environment variables directly. This keeps
secret-handling and validation in one auditable place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from constants import TemperatureUnit
from utils.logger import get_logger

logger = get_logger(__name__)

# Load variables from a .env file in the project root into the environment.
# If .env is absent, this is a no-op and we fall back to whatever is
# already in the environment (useful for CI/CD or containerized deploys).
load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """
    Immutable application settings, populated once at startup.

    Using a frozen dataclass prevents accidental mutation of config
    values at runtime from elsewhere in the codebase.
    """

    openweather_api_key: str
    openweather_base_url: str
    default_units: str
    default_city: str
    api_timeout: int
    log_level: str


def _require_env(key: str) -> str:
    """
    Fetch a required environment variable or raise a clear, actionable error.

    Args:
        key: The environment variable name.

    Returns:
        The variable's value as a string.

    Raises:
        ConfigError: If the variable is missing, empty, or still set to
            the placeholder value from .env.example.
    """
    value = os.getenv(key, "").strip()
    if not value or value == "your_api_key_here":
        raise ConfigError(
            f"Missing or invalid required environment variable: '{key}'. "
            f"Copy .env.example to .env and set a real value."
        )
    return value


def _validate_units(raw_units: str) -> str:
    """Ensure DEFAULT_UNITS is one of the supported TemperatureUnit values."""
    valid_values = {unit.value for unit in TemperatureUnit}
    if raw_units not in valid_values:
        logger.warning(
            "Invalid DEFAULT_UNITS '%s' in .env; falling back to 'metric'.",
            raw_units,
        )
        return TemperatureUnit.CELSIUS.value
    return raw_units


def _safe_int(raw_value: str, fallback: int, field_name: str) -> int:
    """Parse an integer from the environment, logging and falling back on failure."""
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid integer for '%s' ('%s'); falling back to %d.",
            field_name,
            raw_value,
            fallback,
        )
        return fallback


def load_settings() -> Settings:
    """
    Build and validate a `Settings` instance from the current environment.

    Raises:
        ConfigError: If required settings (like the API key) are missing.

    Returns:
        A fully populated, validated `Settings` object.
    """
    api_key = _require_env("OPENWEATHER_API_KEY")

    settings = Settings(
        openweather_api_key=api_key,
        openweather_base_url=os.getenv(
            "OPENWEATHER_BASE_URL", "https://api.openweathermap.org"
        ).rstrip("/"),
        default_units=_validate_units(os.getenv("DEFAULT_UNITS", "metric")),
        default_city=os.getenv("DEFAULT_CITY", "London").strip() or "London",
        api_timeout=_safe_int(os.getenv("API_TIMEOUT", "10"), 10, "API_TIMEOUT"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

    logger.info(
        "Configuration loaded successfully (units=%s, default_city=%s, timeout=%ds).",
        settings.default_units,
        settings.default_city,
        settings.api_timeout,
    )
    return settings


# --------------------------------------------------------------------------
# Singleton settings instance.
#
# NOTE: Instantiated lazily rather than at import time would be "safer"
# in some architectures, but for a desktop app with a single entry point
# (main.py), failing fast at import time is preferable: a missing API
# key should stop the app before any UI is drawn, not mid-interaction.
# --------------------------------------------------------------------------
try:
    settings = load_settings()
except ConfigError as exc:
    logger.error("Startup failed due to configuration error: %s", exc)
    raise
