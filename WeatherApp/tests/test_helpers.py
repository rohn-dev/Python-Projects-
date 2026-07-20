"""Unit tests for utils/helpers.py."""

from datetime import datetime

from utils.helpers import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    format_percentage,
    format_temperature,
    format_wind_speed,
    truncate_text,
    unix_to_local_datetime,
)


class TestFormatTemperature:
    def test_formats_celsius(self):
        assert format_temperature(21.4, "metric") == "21°C"

    def test_formats_fahrenheit(self):
        assert format_temperature(70.2, "imperial") == "70°F"

    def test_rounds_to_nearest_integer(self):
        assert format_temperature(21.6, "metric") == "22°C"

    def test_handles_negative_temperatures(self):
        assert format_temperature(-5.3, "metric") == "-5°C"


class TestFormatWindSpeed:
    def test_formats_metric_wind_speed(self):
        assert format_wind_speed(4.123, "metric") == "4.1 m/s"

    def test_formats_imperial_wind_speed(self):
        assert format_wind_speed(10.0, "imperial") == "10.0 mph"


class TestFormatPercentage:
    def test_converts_fraction_to_percentage(self):
        assert format_percentage(0.42) == "42%"

    def test_handles_zero(self):
        assert format_percentage(0.0) == "0%"

    def test_handles_full_probability(self):
        assert format_percentage(1.0) == "100%"


class TestUnixToLocalDatetime:
    def test_applies_positive_timezone_offset(self):
        # 2024-01-01 00:00:00 UTC + 3600s (UTC+1) = 01:00:00 local
        result = unix_to_local_datetime(1704067200, 3600)
        assert result.hour == 1

    def test_applies_negative_timezone_offset(self):
        # 2024-01-01 00:00:00 UTC - 18000s (UTC-5) = previous day 19:00
        result = unix_to_local_datetime(1704067200, -18000)
        assert result.hour == 19
        assert result.day == 31

    def test_returns_naive_datetime(self):
        result = unix_to_local_datetime(1704067200, 0)
        assert result.tzinfo is None


class TestTemperatureConversion:
    def test_celsius_to_fahrenheit_freezing(self):
        assert celsius_to_fahrenheit(0) == 32

    def test_celsius_to_fahrenheit_boiling(self):
        assert celsius_to_fahrenheit(100) == 212

    def test_fahrenheit_to_celsius_freezing(self):
        assert fahrenheit_to_celsius(32) == 0

    def test_roundtrip_conversion(self):
        original = 23.5
        converted = fahrenheit_to_celsius(celsius_to_fahrenheit(original))
        assert round(converted, 5) == original


class TestTruncateText:
    def test_leaves_short_text_unchanged(self):
        assert truncate_text("Clear sky", max_length=40) == "Clear sky"

    def test_truncates_long_text_with_ellipsis(self):
        result = truncate_text("A" * 50, max_length=10)
        assert len(result) == 10
        assert result.endswith("…")
