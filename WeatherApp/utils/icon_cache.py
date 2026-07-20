"""
utils/icon_cache.py
--------------------
Downloads weather condition icons from OpenWeatherMap's CDN and caches
them locally under assets/icons/, so repeated views of the same
condition (e.g. re-searching the same city) don't re-download the icon.
"""

from __future__ import annotations

import requests
from PIL import Image

from constants import ICONS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def get_icon_image(icon_code: str, size: tuple[int, int] = (100, 100)) -> Image.Image | None:
    """
    Return a PIL Image for the given OpenWeatherMap icon code, using a
    local cache when available and falling back to a network fetch.

    Args:
        icon_code: OpenWeatherMap icon code, e.g. '01d', '10n'.
        size: Desired (width, height) to resize the icon to.

    Returns:
        A PIL `Image`, or None if the icon could not be obtained
        (e.g. no network and not cached) — callers should handle None
        by falling back to a placeholder/text label instead of crashing.
    """
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    local_path = ICONS_DIR / f"{icon_code}.png"

    if local_path.exists():
        try:
            return Image.open(local_path).resize(size)
        except OSError as exc:
            logger.warning("Cached icon %s is corrupted (%s); refetching.", local_path, exc)

    from constants import ICON_URL_TEMPLATE

    url = ICON_URL_TEMPLATE.format(icon_code=icon_code)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        local_path.write_bytes(response.content)
        return Image.open(local_path).resize(size)
    except (requests.RequestException, OSError) as exc:
        logger.warning("Could not fetch icon '%s': %s", icon_code, exc)
        return None
