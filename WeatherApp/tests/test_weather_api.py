"""
Unit tests for api/weather_api.py.

Uses the `responses` library to mock HTTP calls, so these tests run
fully offline and deterministically.
"""

import pytest
import responses as responses_lib

from api.exceptions import (
    CityNotFoundError,
    InvalidAPIKeyError,
    NoInternetConnectionError,
    RateLimitExceededError,
    RequestTimeoutError,
    UnexpectedAPIResponseError,
)
from api.weather_api import WeatherAPIClient

BASE_URL = "https://api.test-weather.com"

VALID_CURRENT_PAYLOAD = {
    "coord": {"lon": -0.13, "lat": 51.51},
    "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
    "main": {"temp": 20.0, "feels_like": 19.5, "temp_min": 18.0, "temp_max": 22.0, "humidity": 55, "pressure": 1015},
    "visibility": 10000,
    "wind": {"speed": 3.5, "deg": 180},
    "clouds": {"all": 10},
    "dt": 1721390400,
    "sys": {"country": "GB", "sunrise": 1721360000, "sunset": 1721410000},
    "timezone": 0,
    "name": "London",
}

VALID_FORECAST_PAYLOAD = {
    "list": [
        {
            "dt": 1721390400,
            "main": {"temp": 20.0, "temp_min": 18.0, "temp_max": 22.0, "humidity": 55},
            "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
            "wind": {"speed": 3.0},
            "pop": 0.2,
        }
    ]
}


@pytest.fixture
def client():
    return WeatherAPIClient(api_key="test_key", base_url=BASE_URL, timeout=5)


class TestGetWeatherReportSuccess:
    @responses_lib.activate
    def test_returns_populated_weather_report(self, client):
        responses_lib.add(responses_lib.GET, f"{BASE_URL}/data/2.5/weather", json=VALID_CURRENT_PAYLOAD, status=200)
        responses_lib.add(responses_lib.GET, f"{BASE_URL}/data/2.5/forecast", json=VALID_FORECAST_PAYLOAD, status=200)
        responses_lib.add(responses_lib.GET, f"{BASE_URL}/data/2.5/air_pollution", status=500)  # AQI fails, non-fatal

        report = client.get_weather_report("London", "metric")

        assert report.current.city == "London"
        assert report.current.country == "GB"
        assert report.current.temperature == 20.0
        assert report.air_quality is None  # AQI failure was swallowed gracefully
        assert len(report.daily_forecast) == 1


class TestGetWeatherReportErrors:
    @responses_lib.activate
    def test_raises_city_not_found_on_404(self, client):
        responses_lib.add(responses_lib.GET, f"{BASE_URL}/data/2.5/weather", status=404)
        with pytest.raises(CityNotFoundError):
            client.get_weather_report("Nonexistentville", "metric")

    @responses_lib.activate
    def test_raises_invalid_api_key_on_401(self, client):
        responses_lib.add(responses_lib.GET, f"{BASE_URL}/data/2.5/weather", status=401)
        with pytest.raises(InvalidAPIKeyError):
            client.get_weather_report("London", "metric")

    @responses_lib.activate
    def test_raises_rate_limit_on_429(self, client):
        responses_lib.add(responses_lib.GET, f"{BASE_URL}/data/2.5/weather", status=429)
        with pytest.raises(RateLimitExceededError):
            client.get_weather_report("London", "metric")

    @responses_lib.activate
    def test_raises_unexpected_error_on_malformed_json(self, client):
        responses_lib.add(
            responses_lib.GET, f"{BASE_URL}/data/2.5/weather", body="not valid json", status=200,
            content_type="application/json",
        )
        with pytest.raises(UnexpectedAPIResponseError):
            client.get_weather_report("London", "metric")

    @responses_lib.activate
    def test_raises_unexpected_error_on_missing_fields(self, client):
        responses_lib.add(
            responses_lib.GET, f"{BASE_URL}/data/2.5/weather",
            json={"name": "London"},  # missing "weather", "main", etc.
            status=200,
        )
        with pytest.raises(UnexpectedAPIResponseError):
            client.get_weather_report("London", "metric")

    @responses_lib.activate
    def test_raises_no_internet_on_connection_error(self, client):
        responses_lib.add(
            responses_lib.GET, f"{BASE_URL}/data/2.5/weather",
            body=responses_lib.ConnectionError("simulated network failure"),
        )
        with pytest.raises(NoInternetConnectionError):
            client.get_weather_report("London", "metric")

    def test_does_not_retry_on_city_not_found(self, client, monkeypatch):
        """404 is a definitive failure, not transient — should not retry 3x."""
        call_count = {"n": 0}

        def fake_get(*args, **kwargs):
            call_count["n"] += 1
            import requests

            resp = requests.Response()
            resp.status_code = 404
            resp._content = b"{}"
            return resp

        monkeypatch.setattr(client._session, "get", fake_get)

        with pytest.raises(CityNotFoundError):
            client.get_weather_report("Nowhere", "metric")

        assert call_count["n"] == 1
