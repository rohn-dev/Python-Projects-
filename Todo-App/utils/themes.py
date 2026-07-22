"""
utils/themes.py
----------------
Centralizes CustomTkinter appearance-mode and accent-color application
so ui/*.py modules never call customtkinter's global setters directly.
"""

from __future__ import annotations

import customtkinter as ctk

from utils.constants import ACCENT_COLORS


def apply_appearance(mode: str) -> None:
    """mode: 'Dark' | 'Light' | 'System'"""
    ctk.set_appearance_mode(mode)


def get_accent_hex(name: str) -> str:
    return ACCENT_COLORS.get(name, ACCENT_COLORS["Blue"])


# Semantic color helpers that adapt to light/dark mode using CTk's
# tuple-based color convention: (light_value, dark_value)
class Palette:
    SURFACE = ("#F5F6FA", "#1E1F26")
    SURFACE_ALT = ("#FFFFFF", "#262832")
    SIDEBAR = ("#EDEFF5", "#181920")
    BORDER = ("#E0E2EA", "#32333D")
    TEXT_PRIMARY = ("#1A1B22", "#F2F2F5")
    TEXT_SECONDARY = ("#6B6E79", "#9A9CA8")
    DANGER = ("#E74C3C", "#EB5757")
    SUCCESS = ("#2ECC71", "#4CAF50")
    CARD_HOVER = ("#EAEBF2", "#2E3039")
