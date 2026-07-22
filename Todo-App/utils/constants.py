"""
constants.py
------------
Centralized application constants: priorities, default categories, color
palette, fonts, keyboard shortcuts, and file paths.

Keeping these in one module means the UI, services, and database layers
never hard-code "magic strings" — a single change here propagates
everywhere.
"""

from __future__ import annotations

from pathlib import Path
from enum import Enum


# --------------------------------------------------------------------------
# Filesystem paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
DB_PATH = DATA_DIR / "tasks.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
BACKUP_DIR = DATA_DIR / "backups"


# --------------------------------------------------------------------------
# Priorities
# --------------------------------------------------------------------------
class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    @classmethod
    def values(cls) -> list[str]:
        return [p.value for p in cls]


PRIORITY_ORDER = {
    Priority.CRITICAL.value: 0,
    Priority.HIGH.value: 1,
    Priority.MEDIUM.value: 2,
    Priority.LOW.value: 3,
}

PRIORITY_COLORS = {
    Priority.LOW.value: "#4CAF50",       # green
    Priority.MEDIUM.value: "#3B8ED0",    # blue
    Priority.HIGH.value: "#F2994A",      # orange
    Priority.CRITICAL.value: "#EB5757",  # red
}


# --------------------------------------------------------------------------
# Categories (defaults — user can add custom ones, persisted in DB)
# --------------------------------------------------------------------------
DEFAULT_CATEGORIES = [
    "Personal",
    "Work",
    "College",
    "Shopping",
    "Health",
    "Coding",
]

CATEGORY_COLORS = {
    "Personal": "#9B59B6",
    "Work": "#3B8ED0",
    "College": "#16A085",
    "Shopping": "#E67E22",
    "Health": "#E74C3C",
    "Coding": "#2ECC71",
    "Uncategorized": "#7F8C8D",
}
DEFAULT_CATEGORY_COLOR = "#5B8DEF"


# --------------------------------------------------------------------------
# Filters / Sort options
# --------------------------------------------------------------------------
class FilterMode(str, Enum):
    ALL = "All Tasks"
    TODAY = "Today's Tasks"
    THIS_WEEK = "This Week"
    COMPLETED = "Completed"
    PENDING = "Pending"
    OVERDUE = "Overdue"
    HIGH_PRIORITY = "High Priority"
    FAVORITES = "Favorites"
    PINNED = "Pinned"


class SortMode(str, Enum):
    DUE_DATE = "Due Date"
    PRIORITY = "Priority"
    ALPHABETICAL = "Alphabetical"
    DATE_CREATED = "Date Created"
    COMPLETED = "Completed"


# --------------------------------------------------------------------------
# Theme / palette
# --------------------------------------------------------------------------
ACCENT_COLORS = {
    "Blue": "#3B8ED0",
    "Purple": "#9B59B6",
    "Green": "#2ECC71",
    "Orange": "#E67E22",
    "Red": "#E74C3C",
    "Teal": "#16A085",
}

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_FALLBACK = "Helvetica"

SIDEBAR_WIDTH = 230
CARD_CORNER_RADIUS = 14
BUTTON_CORNER_RADIUS = 10

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DISPLAY_DATE_FORMAT = "%b %d, %Y"
DISPLAY_TIME_FORMAT = "%I:%M %p"


# --------------------------------------------------------------------------
# Keyboard shortcuts (Tkinter bind sequences)
# --------------------------------------------------------------------------
SHORTCUTS = {
    "new_task": "<Control-n>",
    "search": "<Control-f>",
    "delete": "<Delete>",
    "edit": "<Control-e>",
    "duplicate": "<Control-d>",
    "save": "<Control-s>",
    "undo": "<Control-z>",
}

SHORTCUT_LABELS = {
    "new_task": "Ctrl+N",
    "search": "Ctrl+F",
    "delete": "Delete",
    "edit": "Ctrl+E",
    "duplicate": "Ctrl+D",
    "save": "Ctrl+S",
    "undo": "Ctrl+Z",
}


APP_NAME = "TaskFlow"
APP_VERSION = "1.0.0"
