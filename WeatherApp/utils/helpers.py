"""
utils/helpers.py
-----------------
Small, pure, reusable helper functions for formatting and conversions.
Kept separate from validators.py (input correctness) and the API/service
layers (I/O) to maintain a clean separation of concerns.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from constants import UNIT_SYMBOLS, WIND_SPEED_UNITS


def format_temperature(value: float, units: str) -> str:
    """
    Format a numeric temperature with its correct unit symbol.

    Args:
        value: The temperature value.
        units: One of 'metric' or 'imperial' (see TemperatureUnit).

    Returns:
        A string like "21°C" or "70°F".
    """
    symbol = UNIT_SYMBOLS.get(units, "°")
    return f"{round(value)}{symbol}"


def format_wind_speed(value: float, units: str) -> str:
    """Format wind speed with the correct unit for the given system."""
    unit_label = WIND_SPEED_UNITS.get(units, "")
    return f"{value:.1f} {unit_label}"


def format_percentage(value: float) -> str:
    """Format a 0.0-1.0 fraction (e.g. chance of rain) as a whole-number percentage."""
    return f"{round(value * 100)}%"


def unix_to_local_datetime(unix_timestamp: int, timezone_offset_seconds: int) -> datetime:
    """
    Convert a UTC unix timestamp plus a timezone offset into a naive
    local `datetime` representing the location's local time.

    OpenWeatherMap returns all timestamps in UTC alongside a per-city
    `timezone` offset (seconds from UTC). This reconstructs local time
    without relying on the host machine's timezone.

    Args:
        unix_timestamp: Seconds since epoch, UTC.
        timezone_offset_seconds: Offset from UTC, in seconds, for the target city.

    Returns:
        A naive `datetime` representing local time at that location.
    """
    utc_dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    local_dt = utc_dt + timedelta(seconds=timezone_offset_seconds)
    return local_dt.replace(tzinfo=None)


def format_time(dt: datetime) -> str:
    """Format a datetime as a 12-hour clock string, e.g. '06:42 AM'."""
    return dt.strftime("%I:%M %p").lstrip("0")


def format_date(dt: datetime) -> str:
    """Format a datetime as 'Mon, 21 Jul'."""
    return dt.strftime("%a, %d %b")


def format_full_datetime(dt: datetime) -> str:
    """Format a datetime as 'Monday, 21 July 2026 - 06:42 AM'."""
    return f"{dt.strftime('%A, %d %B %Y')} - {format_time(dt)}"


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a Celsius value to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert a Fahrenheit value to Celsius."""
    return (fahrenheit - 32) * 5 / 9


def truncate_text(text: str, max_length: int = 40) -> str:
    """Truncate text to `max_length` characters, appending an ellipsis if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"
