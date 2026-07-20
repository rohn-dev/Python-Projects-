"""
utils/logger.py
----------------
Centralized logging configuration for WeatherApp.

Every module obtains its logger via `get_logger(__name__)` instead of
calling `logging.getLogger` directly. This guarantees consistent
formatting, consistent handlers (console + rotating file), and a single
place to change logging behavior for the whole application.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from constants import LOGS_DIR

# --------------------------------------------------------------------------
# Module-level state
# --------------------------------------------------------------------------
_LOG_FILE = LOGS_DIR / "weatherapp.log"
_MAX_BYTES = 2 * 1024 * 1024  # 2 MB per log file before rotation
_BACKUP_COUNT = 5
_configured = False  # guards against attaching duplicate handlers


def _resolve_log_level() -> int:
    """
    Resolve the desired log level from the LOG_LEVEL environment variable.

    Falls back to INFO if the variable is missing or invalid. We read the
    raw environment variable here (rather than importing config.py) to
    avoid a circular import, since config.py itself may want to log.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def _configure_root_logger() -> None:
    """
    Attach a console handler and a rotating file handler to the root
    'weatherapp' logger exactly once per process.
    """
    global _configured
    if _configured:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("weatherapp")
    root.setLevel(_resolve_log_level())
    root.propagate = False  # don't double-log through the default root logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(_resolve_log_level())

    file_handler = RotatingFileHandler(
        filename=_LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # file keeps everything; console is filtered

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    _configured = True


def get_logger(module_name: str) -> logging.Logger:
    """
    Return a namespaced logger for the given module.

    Args:
        module_name: Typically passed as `__name__` from the calling module.

    Returns:
        A configured `logging.Logger` instance that writes to both the
        console and a rotating log file under `logs/weatherapp.log`.

    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Weather fetched successfully")
    """
    _configure_root_logger()
    return logging.getLogger(f"weatherapp.{module_name}")
