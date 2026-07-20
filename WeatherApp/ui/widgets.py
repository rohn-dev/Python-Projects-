"""
ui/widgets.py
-------------
Reusable, self-contained UI components built on CustomTkinter.

Keeping these separate from ui/app.py means the main App class stays
focused on layout and orchestration, while these classes own their own
rendering logic and can be reused or unit-tested independently.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk
from PIL import Image

from models.weather import DailyForecast
from utils.helpers import (
    format_date,
    format_percentage,
    format_temperature,
)
from utils.icon_cache import get_icon_image


class SearchBar(ctk.CTkFrame):
    """Search input + search button + favorite-toggle button, as one unit."""

    def __init__(
        self,
        master,
        on_search: Callable[[str], None],
        on_toggle_favorite: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_search = on_search
        self._on_toggle_favorite = on_toggle_favorite

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Search for a city...",
            height=44,
            font=ctk.CTkFont(size=15),
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry.bind("<Return>", lambda _event: self._trigger_search())

        self.search_button = ctk.CTkButton(
            self, text="Search", width=90, height=44, command=self._trigger_search
        )
        self.search_button.grid(row=0, column=1, padx=(0, 8))

        self.favorite_button = ctk.CTkButton(
            self, text="☆", width=44, height=44, command=self._on_toggle_favorite
        )
        self.favorite_button.grid(row=0, column=2)

    def _trigger_search(self) -> None:
        self._on_search(self.entry.get())

    def set_favorite_state(self, is_favorite: bool) -> None:
        """Update the star icon to reflect whether the current city is favorited."""
        self.favorite_button.configure(text="★" if is_favorite else "☆")

    def get_city(self) -> str:
        """Return the current raw text in the search entry."""
        return self.entry.get()

    def set_city(self, city: str) -> None:
        """Programmatically set the search entry's text (e.g. from history click)."""
        self.entry.delete(0, "end")
        self.entry.insert(0, city)


class CurrentWeatherPanel(ctk.CTkFrame):
    """Large panel showing the current conditions for the searched city."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, corner_radius=16, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.location_label = ctk.CTkLabel(
            self, text="--", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.location_label.grid(row=0, column=0, pady=(20, 0), sticky="w", padx=24)

        self.datetime_label = ctk.CTkLabel(
            self, text="--", font=ctk.CTkFont(size=13), text_color="gray70"
        )
        self.datetime_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 10))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        body.grid_columnconfigure(1, weight=1)

        self.icon_label = ctk.CTkLabel(body, text="", width=100, height=100)
        self.icon_label.grid(row=0, column=0, rowspan=2, sticky="w")

        self.temp_label = ctk.CTkLabel(
            body, text="--°", font=ctk.CTkFont(size=52, weight="bold")
        )
        self.temp_label.grid(row=0, column=1, sticky="w", padx=(16, 0))

        self.condition_label = ctk.CTkLabel(
            body, text="--", font=ctk.CTkFont(size=16), text_color="gray70"
        )
        self.condition_label.grid(row=1, column=1, sticky="w", padx=(16, 0))

        self.details_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.details_grid.grid(row=3, column=0, sticky="ew", padx=24, pady=(4, 20))
        for i in range(4):
            self.details_grid.grid_columnconfigure(i, weight=1)

        self._detail_labels: dict[str, ctk.CTkLabel] = {}
        detail_keys = [
            "feels_like", "humidity", "pressure", "wind",
            "visibility", "clouds", "sunrise", "sunset",
        ]
        for idx, key in enumerate(detail_keys):
            row, col = divmod(idx, 4)
            cell = ctk.CTkFrame(self.details_grid, fg_color="gray17", corner_radius=10)
            cell.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
            ctk.CTkLabel(
                cell, text=key.replace("_", " ").title(), font=ctk.CTkFont(size=11), text_color="gray60"
            ).pack(anchor="w", padx=10, pady=(8, 0))
            value_label = ctk.CTkLabel(cell, text="--", font=ctk.CTkFont(size=15, weight="bold"))
            value_label.pack(anchor="w", padx=10, pady=(0, 8))
            self._detail_labels[key] = value_label

        self._icon_ref: ctk.CTkImage | None = None  # keep a reference to avoid GC

    def set_detail(self, key: str, value: str) -> None:
        """Update one of the small detail cells (feels_like, humidity, etc.)."""
        if key in self._detail_labels:
            self._detail_labels[key].configure(text=value)

    def set_icon(self, icon_code: str | None) -> None:
        """Load and display the weather condition icon, or clear it on failure."""
        if not icon_code:
            self.icon_label.configure(image=None, text="")
            return
        pil_image = get_icon_image(icon_code, size=(100, 100))
        if pil_image is None:
            self.icon_label.configure(image=None, text="🌦")
            return
        self._icon_ref = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
        self.icon_label.configure(image=self._icon_ref, text="")


class ForecastCard(ctk.CTkFrame):
    """A single day's summary within the 5-day forecast row."""

    def __init__(self, master, day: DailyForecast, units: str, **kwargs) -> None:
        super().__init__(master, corner_radius=14, width=130, **kwargs)
        self.grid_propagate(False)
        self.configure(height=190)

        ctk.CTkLabel(
            self, text=format_date(day.date), font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(14, 6))

        pil_image = get_icon_image(day.condition.icon_code, size=(56, 56))
        if pil_image is not None:
            icon = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(56, 56))
            icon_label = ctk.CTkLabel(self, image=icon, text="")
            icon_label.image = icon  # keep reference
            icon_label.pack(pady=4)
        else:
            ctk.CTkLabel(self, text="🌦", font=ctk.CTkFont(size=32)).pack(pady=4)

        ctk.CTkLabel(
            self,
            text=f"{format_temperature(day.temp_max, units)} / {format_temperature(day.temp_min, units)}",
            font=ctk.CTkFont(size=13),
        ).pack(pady=(2, 2))

        ctk.CTkLabel(
            self,
            text=f"💧 {format_percentage(day.max_chance_of_rain)}",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        ).pack(pady=(0, 12))


class SidebarList(ctk.CTkFrame):
    """Scrollable list used for both 'History' and 'Favorites' sidebar panels."""

    def __init__(self, master, title: str, on_item_click: Callable[[str], None], **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_item_click = on_item_click

        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="gray17", height=160)
        self.scroll_frame.pack(fill="both", expand=True)

        self._empty_label = ctk.CTkLabel(
            self.scroll_frame, text="Nothing here yet", text_color="gray50", font=ctk.CTkFont(size=12)
        )
        self._empty_label.pack(pady=10)

    def set_items(self, items: list[str]) -> None:
        """Rebuild the list's contents from `items`."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not items:
            self._empty_label = ctk.CTkLabel(
                self.scroll_frame, text="Nothing here yet", text_color="gray50", font=ctk.CTkFont(size=12)
            )
            self._empty_label.pack(pady=10)
            return

        for item in items:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=item,
                anchor="w",
                fg_color="transparent",
                hover_color="gray25",
                command=lambda c=item: self._on_item_click(c),
            )
            btn.pack(fill="x", pady=2)


class StatusBar(ctk.CTkFrame):
    """Bottom status bar showing connection state, last update time, and messages."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, height=30, corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.message_label = ctk.CTkLabel(self, text="Ready.", font=ctk.CTkFont(size=11), anchor="w")
        self.message_label.grid(row=0, column=0, sticky="w", padx=12, pady=4)

        self.units_label = ctk.CTkLabel(self, text="°C", font=ctk.CTkFont(size=11), anchor="e")
        self.units_label.grid(row=0, column=1, sticky="e", padx=12, pady=4)

    def set_message(self, message: str, is_error: bool = False) -> None:
        """Display a status message, colored red if it represents an error."""
        self.message_label.configure(text=message, text_color="#ff6b6b" if is_error else "gray70")

    def set_units_display(self, units_symbol: str) -> None:
        """Update the small unit indicator on the right side of the status bar."""
        self.units_label.configure(text=units_symbol)
