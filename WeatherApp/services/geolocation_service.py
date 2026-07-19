"""
services/geolocation_service.py
---------------------------------
Auto-detects the user's approximate city via IP-based geolocation, using
the free ip-api.com endpoint (no API key required). This powers the
"Use My Location" button on first launch / refresh.

Failure here is always non-fatal: if detection fails, the app simply
falls back to DEFAULT_CITY from config.
"""

from __future__ import annotations

import requests

from utils.logger import get_logger

logger = get_logger(__name__)

_IP_API_URL = "http://ip-api.com/json/"
_TIMEOUT_SECONDS = 5


def detect_city_by_ip() -> str | None:
    """
    Attempt to detect the user's current city via IP geolocation.

    Returns:
        The detected city name, or None if detection failed for any
        reason (no internet, service down, malformed response).
    """
    try:
        response = requests.get(_IP_API_URL, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            logger.warning("IP geolocation failed: %s", data.get("message", "unknown error"))
            return None

        city = data.get("city")
        if city:
            logger.info("Detected city via IP geolocation: %s", city)
        return city

    except (requests.RequestException, ValueError) as exc:
        logger.warning("IP geolocation request failed: %s", exc)
        return None
