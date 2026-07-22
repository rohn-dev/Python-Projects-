"""
utils/helpers.py
-----------------
Small, reusable utility functions: settings persistence (JSON),
date parsing/validation, and misc formatting helpers. Nothing here
depends on the UI or database layers.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from utils.constants import SETTINGS_PATH, DATE_FORMAT, TIME_FORMAT


DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "Dark",              # "Dark" | "Light" | "System"
    "accent_color": "Blue",
    "auto_save": True,
    "startup_page": "Dashboard",
    "font_scale": 1.0,
    "daily_goal": 5,
    "weekly_goal": 25,
    "sound_on_complete": False,
    "window_geometry": "1200x750",
}


def load_settings() -> dict[str, Any]:
    """Load persisted settings, falling back to defaults on any failure."""
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        # Corrupted settings file — don't crash the app, just reset it.
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass  # Non-fatal: settings simply won't persist this run.


def parse_date_safe(value: str) -> tuple[bool, str]:
    """Validate a date string. Returns (is_valid, normalized_or_error)."""
    value = (value or "").strip()
    if not value:
        return True, ""
    try:
        d = datetime.strptime(value, DATE_FORMAT)
        return True, d.strftime(DATE_FORMAT)
    except ValueError:
        return False, "Invalid date. Use YYYY-MM-DD."


def parse_time_safe(value: str) -> tuple[bool, str]:
    """Validate a time string. Returns (is_valid, normalized_or_error)."""
    value = (value or "").strip()
    if not value:
        return True, ""
    try:
        t = datetime.strptime(value, TIME_FORMAT)
        return True, t.strftime(TIME_FORMAT)
    except ValueError:
        return False, "Invalid time. Use HH:MM (24-hour)."


def truncate(text: str, max_len: int = 60) -> str:
    text = text or ""
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"
