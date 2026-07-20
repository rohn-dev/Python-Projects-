"""Unit tests for utils/validators.py."""

import pytest

from utils.validators import ValidationError, is_valid_temperature_unit, validate_city_name


class TestValidateCityName:
    def test_accepts_simple_city_name(self):
        assert validate_city_name("London") == "London"

    def test_trims_whitespace(self):
        assert validate_city_name("  New York  ") == "New York"

    def test_accepts_hyphenated_city_name(self):
        assert validate_city_name("Winston-Salem") == "Winston-Salem"

    def test_accepts_apostrophe_in_city_name(self):
        assert validate_city_name("N'Djamena") == "N'Djamena"

    def test_accepts_city_with_country_code(self):
        assert validate_city_name("London, GB") == "London, GB"

    def test_rejects_empty_string(self):
        with pytest.raises(ValidationError):
            validate_city_name("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValidationError):
            validate_city_name("     ")

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            validate_city_name(None)

    def test_rejects_too_short(self):
        with pytest.raises(ValidationError):
            validate_city_name("A")

    def test_rejects_too_long(self):
        with pytest.raises(ValidationError):
            validate_city_name("A" * 200)

    def test_rejects_numbers(self):
        with pytest.raises(ValidationError):
            validate_city_name("London123")

    def test_rejects_special_characters(self):
        with pytest.raises(ValidationError):
            validate_city_name("<script>alert(1)</script>")

    def test_rejects_sql_injection_attempt(self):
        with pytest.raises(ValidationError):
            validate_city_name("London'; DROP TABLE users;--")


class TestIsValidTemperatureUnit:
    def test_accepts_metric(self):
        assert is_valid_temperature_unit("metric") is True

    def test_accepts_imperial(self):
        assert is_valid_temperature_unit("imperial") is True

    def test_rejects_invalid_unit(self):
        assert is_valid_temperature_unit("kelvin") is False

    def test_rejects_empty_string(self):
        assert is_valid_temperature_unit("") is False
