"""
utils/validators.py
--------------------
Pure input-validation functions. No side effects, no I/O — these are
easy to unit test in isolation and are used by both the UI layer
(before firing a request) and the API layer (defense in depth).
"""

from __future__ import annotations

import re

# City names: letters (incl. accented), spaces, hyphens, apostrophes, commas
# (commas allow "City, Country Code" style queries like "London, GB").
_CITY_NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-',.]+$")

MIN_CITY_LENGTH = 2
MAX_CITY_LENGTH = 85


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


def validate_city_name(raw_input: str) -> str:
    """
    Validate and normalize a city name entered by the user.

    Args:
        raw_input: The raw text from the search bar.

    Returns:
        A trimmed, validated city name safe to pass to the API layer.

    Raises:
        ValidationError: If the input is empty, too short, too long, or
            contains characters that cannot plausibly belong to a city name.

    Example:
        >>> validate_city_name("  new york  ")
        'new york'
        >>> validate_city_name("")
        Traceback (most recent call last):
            ...
        utils.validators.ValidationError: City name cannot be empty.
    """
    if raw_input is None:
        raise ValidationError("City name cannot be empty.")

    trimmed = raw_input.strip()

    if not trimmed:
        raise ValidationError("City name cannot be empty.")

    if len(trimmed) < MIN_CITY_LENGTH:
        raise ValidationError(
            f"City name must be at least {MIN_CITY_LENGTH} characters long."
        )

    if len(trimmed) > MAX_CITY_LENGTH:
        raise ValidationError(
            f"City name must be shorter than {MAX_CITY_LENGTH} characters."
        )

    if not _CITY_NAME_PATTERN.match(trimmed):
        raise ValidationError(
            "City name contains invalid characters. "
            "Use letters, spaces, hyphens, or apostrophes only."
        )

    return trimmed


def is_valid_temperature_unit(unit: str) -> bool:
    """Check whether `unit` is a supported OpenWeatherMap unit system string."""
    from constants import TemperatureUnit

    return unit in {u.value for u in TemperatureUnit}
