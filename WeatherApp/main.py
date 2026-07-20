"""
main.py
-------
Application entry point.

Kept intentionally minimal: its only jobs are to log the startup event
and hand control to the UI layer. All configuration validation already
happened when `config.py` was imported (it fails fast on bad config),
so if we get here, the app is ready to run.
"""

from __future__ import annotations

import sys

from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> int:
    """Start the WeatherApp GUI. Returns a process exit code."""
    logger.info("=" * 60)
    logger.info("WeatherApp starting up.")

    try:
        from ui.app import WeatherApp

        app = WeatherApp()
        app.mainloop()
        logger.info("WeatherApp closed normally.")
        return 0

    except Exception:  # noqa: BLE001 - top-level guard, must not silently crash
        logger.exception("Fatal error during application startup.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
