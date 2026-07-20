"""
ui/app.py
---------
Main application window. Orchestrates widgets (ui/widgets.py) and
services (services/*.py) but contains no business logic itself — its
job is layout, event wiring, and thread-safe UI updates.

All network calls run on a background thread via `threading.Thread` so
the Tkinter mainloop never freezes; results are marshalled back to the
UI thread with `self.after(0, ...)`, which is the standard safe pattern
for updating Tkinter widgets from worker threads.
"""

from __future__ import annotations

import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from typing import Optional

import customtkinter as ctk

from api.exceptions import WeatherAPIError
from config import settings
from constants import (
    APP_MIN_HEIGHT,
    APP_MIN_WIDTH,
    APP_NAME,
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COLOR_THEME,
    UNIT_SYMBOLS,
)
from models.weather import WeatherReport
from services.export_service import ExportService
from services.favorites_service import FavoritesLimitReachedError, FavoritesService
from services.geolocation_service import detect_city_by_ip
from services.history_service import HistoryService
from services.weather_service import OfflineDataUnavailableError, WeatherService
from ui.widgets import (
    CurrentWeatherPanel,
    ForecastCard,
    SearchBar,
    SidebarList,
    StatusBar,
)
from utils.helpers import (
    format_full_datetime,
    format_temperature,
    format_time,
    format_wind_speed,
)
from utils.logger import get_logger
from utils.validators import ValidationError

logger = get_logger(__name__)

ctk.set_appearance_mode(DEFAULT_APPEARANCE_MODE)
ctk.set_default_color_theme(DEFAULT_COLOR_THEME)


class WeatherApp(ctk.CTk):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title(APP_NAME)
        self.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        self.geometry(f"{APP_MIN_WIDTH}x{APP_MIN_HEIGHT}")

        # Services (dependency composition happens here, once, at the top)
        self._weather_service = WeatherService()
        self._history_service = HistoryService()
        self._favorites_service = FavoritesService()
        self._export_service = ExportService()

        # Mutable UI state
        self._units: str = settings.default_units
        self._current_report: Optional[WeatherReport] = None
        self._current_city: str = settings.default_city

        self._build_layout()
        self._bind_shortcuts()
        self._refresh_sidebars()

        logger.info("WeatherApp UI initialized.")
        self.after(200, lambda: self._search_city(settings.default_city))

    # ----------------------------------------------------------------
    # Layout
    # ----------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_panel()
        self._build_status_bar()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=16, pady=(20, 16))

        self.theme_switch = ctk.CTkSwitch(
            sidebar, text="Dark Mode", command=self._toggle_theme
        )
        self.theme_switch.select() if DEFAULT_APPEARANCE_MODE == "dark" else self.theme_switch.deselect()
        self.theme_switch.pack(anchor="w", padx=16, pady=(0, 12))

        self.units_switch = ctk.CTkSwitch(
            sidebar, text="Fahrenheit (°F)", command=self._toggle_units
        )
        self.units_switch.pack(anchor="w", padx=16, pady=(0, 20))

        location_btn = ctk.CTkButton(
            sidebar, text="📍 Use My Location", command=self._use_my_location
        )
        location_btn.pack(fill="x", padx=16, pady=(0, 20))

        self.history_panel = SidebarList(
            sidebar, title="Recent Searches", on_item_click=self._search_city
        )
        self.history_panel.pack(fill="x", padx=16, pady=(0, 20))

        self.favorites_panel = SidebarList(
            sidebar, title="Favorites", on_item_click=self._search_city
        )
        self.favorites_panel.pack(fill="x", padx=16)

    def _build_main_panel(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        self.search_bar = SearchBar(
            main, on_search=self._search_city, on_toggle_favorite=self._toggle_favorite
        )
        self.search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        top_row = ctk.CTkFrame(main, fg_color="transparent")
        top_row.grid(row=1, column=0, sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        self.refresh_button = ctk.CTkButton(
            top_row, text="⟳ Refresh", width=100, command=self._refresh
        )
        self.refresh_button.grid(row=0, column=1, sticky="e")

        self.current_panel = CurrentWeatherPanel(main)
        self.current_panel.grid(row=2, column=0, sticky="new", pady=(12, 16))

        ctk.CTkLabel(
            main, text="5-Day Forecast", font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=3, column=0, sticky="w")

        self.forecast_row = ctk.CTkScrollableFrame(
            main, orientation="horizontal", height=210, fg_color="transparent"
        )
        self.forecast_row.grid(row=4, column=0, sticky="ew", pady=(8, 16))

        export_row = ctk.CTkFrame(main, fg_color="transparent")
        export_row.grid(row=5, column=0, sticky="e")
        ctk.CTkButton(
            export_row, text="Export PDF", width=110, command=self._export_pdf
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            export_row, text="Export JSON", width=110, command=self._export_json
        ).pack(side="left")

    def _build_status_bar(self) -> None:
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.set_units_display(UNIT_SYMBOLS[self._units])

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-r>", lambda _e: self._refresh())
        self.bind("<Control-f>", lambda _e: self.search_bar.entry.focus_set())
        self.bind("<Control-d>", lambda _e: self._toggle_theme(force=True))
        self.bind("<Escape>", lambda _e: self.search_bar.entry.delete(0, "end"))

    # ----------------------------------------------------------------
    # Actions
    # ----------------------------------------------------------------

    def _search_city(self, raw_city: str) -> None:
        """Kick off a (background-threaded) weather fetch for `raw_city`."""
        self.status_bar.set_message(f"Searching for '{raw_city.strip()}'...")
        self.refresh_button.configure(state="disabled", text="Loading...")
        self.search_bar.set_city(raw_city)

        thread = threading.Thread(
            target=self._fetch_weather_worker, args=(raw_city,), daemon=True
        )
        thread.start()

    def _fetch_weather_worker(self, raw_city: str) -> None:
        """Runs on a background thread — must not touch widgets directly."""
        try:
            report, is_stale = self._weather_service.get_weather(raw_city, self._units)
            self.after(0, self._on_fetch_success, report, is_stale)
        except ValidationError as exc:
            self.after(0, self._on_fetch_error, str(exc))
        except OfflineDataUnavailableError as exc:
            self.after(0, self._on_fetch_error, str(exc))
        except WeatherAPIError as exc:
            self.after(0, self._on_fetch_error, str(exc))
        except Exception as exc:  # noqa: BLE001 - last line of defense, must not crash UI
            logger.exception("Unexpected error while fetching weather.")
            self.after(0, self._on_fetch_error, f"Unexpected error: {exc}")

    def _on_fetch_success(self, report: WeatherReport, is_stale: bool) -> None:
        self._current_report = report
        self._current_city = report.current.city
        self._render_report(report)
        self._history_service.add(report.current.city)
        self._refresh_sidebars()
        self.search_bar.set_favorite_state(
            self._favorites_service.is_favorite(report.current.city)
        )

        if is_stale:
            self.status_bar.set_message(
                "⚠ Showing cached data (offline mode) — no internet connection.",
                is_error=True,
            )
        else:
            self.status_bar.set_message(f"Updated: {format_full_datetime(report.current.observed_at)}")

        self.refresh_button.configure(state="normal", text="⟳ Refresh")

    def _on_fetch_error(self, message: str) -> None:
        self.status_bar.set_message(message, is_error=True)
        self.refresh_button.configure(state="normal", text="⟳ Refresh")
        messagebox.showerror("Weather App - Error", message)

    def _refresh(self) -> None:
        self._search_city(self._current_city)

    def _render_report(self, report: WeatherReport) -> None:
        current = report.current
        units = current.units

        self.current_panel.location_label.configure(
            text=f"{current.city}, {current.country}"
        )
        self.current_panel.datetime_label.configure(
            text=format_full_datetime(current.observed_at)
        )
        self.current_panel.temp_label.configure(
            text=format_temperature(current.temperature, units)
        )
        self.current_panel.condition_label.configure(text=current.condition.description)
        self.current_panel.set_icon(current.condition.icon_code)

        self.current_panel.set_detail("feels_like", format_temperature(current.feels_like, units))
        self.current_panel.set_detail("humidity", f"{current.humidity}%")
        self.current_panel.set_detail("pressure", f"{current.pressure} hPa")
        self.current_panel.set_detail("wind", format_wind_speed(current.wind_speed, units))
        self.current_panel.set_detail("visibility", f"{current.visibility_km} km")
        self.current_panel.set_detail("clouds", f"{current.cloud_coverage}%")
        self.current_panel.set_detail("sunrise", format_time(current.sunrise))
        self.current_panel.set_detail("sunset", format_time(current.sunset))

        for widget in self.forecast_row.winfo_children():
            widget.destroy()
        for day in report.daily_forecast:
            card = ForecastCard(self.forecast_row, day=day, units=units)
            card.pack(side="left", padx=6, pady=4)

    def _toggle_favorite(self) -> None:
        if not self._current_report:
            return
        city = self._current_report.current.city
        try:
            is_now_favorite = self._favorites_service.toggle(city)
            self.search_bar.set_favorite_state(is_now_favorite)
            self._refresh_sidebars()
        except FavoritesLimitReachedError as exc:
            messagebox.showwarning("Favorites Limit Reached", str(exc))

    def _refresh_sidebars(self) -> None:
        self.history_panel.set_items(self._history_service.get_all())
        self.favorites_panel.set_items(self._favorites_service.get_all())

    def _toggle_theme(self, force: bool = False) -> None:
        if force:
            self.theme_switch.toggle()
        is_dark = self.theme_switch.get() == 1
        ctk.set_appearance_mode("dark" if is_dark else "light")

    def _toggle_units(self) -> None:
        self._units = "imperial" if self.units_switch.get() == 1 else "metric"
        self.status_bar.set_units_display(UNIT_SYMBOLS[self._units])
        if self._current_city:
            self._refresh()

    def _use_my_location(self) -> None:
        self.status_bar.set_message("Detecting your location...")

        def worker() -> None:
            city = detect_city_by_ip()
            if city:
                self.after(0, self._search_city, city)
            else:
                self.after(
                    0,
                    self.status_bar.set_message,
                    "Could not detect location. Try searching manually.",
                    True,
                )

        threading.Thread(target=worker, daemon=True).start()

    def _export_pdf(self) -> None:
        if not self._current_report:
            messagebox.showinfo("Export PDF", "Search for a city first.")
            return
        try:
            path = self._export_service.export_pdf(self._current_report)
            self.status_bar.set_message(f"Exported PDF to {path}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("PDF export failed.")
            messagebox.showerror("Export Failed", str(exc))

    def _export_json(self) -> None:
        if not self._current_report:
            messagebox.showinfo("Export JSON", "Search for a city first.")
            return
        try:
            path = self._export_service.export_json(self._current_report)
            self.status_bar.set_message(f"Exported JSON to {path}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("JSON export failed.")
            messagebox.showerror("Export Failed", str(exc))
