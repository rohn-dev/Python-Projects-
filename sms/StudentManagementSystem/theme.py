"""
theme.py
--------
Shared visual constants and small validation helpers used across every
GUI module, so the whole app keeps one consistent professional blue/white
look and feel.
"""

import re

# ---------------------------------------------------------------------- #
# Color palette (professional blue & white theme)
# ---------------------------------------------------------------------- #
PRIMARY = "#1E4FA3"          # main brand blue
PRIMARY_HOVER = "#163C7E"
SECONDARY = "#3B7DD8"
ACCENT = "#4CAF50"           # success green
DANGER = "#E5484D"
DANGER_HOVER = "#C93A3E"
WARNING = "#F5A623"

SIDEBAR_BG_LIGHT = "#0F2C5C"
SIDEBAR_BG_DARK = "#0B1E3D"

CARD_LIGHT = "#FFFFFF"
CARD_DARK = "#1B1F2A"

BG_LIGHT = "#F2F5FA"
BG_DARK = "#12151C"

TEXT_MUTED = "#8A93A6"

FONT_FAMILY = "Segoe UI"

HEADING_FONT = (FONT_FAMILY, 22, "bold")
SUBHEADING_FONT = (FONT_FAMILY, 15, "bold")
BODY_FONT = (FONT_FAMILY, 13)
SMALL_FONT = (FONT_FAMILY, 11)
CARD_VALUE_FONT = (FONT_FAMILY, 26, "bold")

CORNER_RADIUS = 12
BUTTON_RADIUS = 8


# ---------------------------------------------------------------------- #
# Validation helpers
# ---------------------------------------------------------------------- #
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{7,15}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip())) if email else False


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone.strip())) if phone else False


def not_empty(*values) -> bool:
    """Return True only if every given value is a non-empty (stripped) string."""
    return all(str(v).strip() != "" for v in values)
