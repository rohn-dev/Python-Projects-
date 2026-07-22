"""
ui/sidebar.py
-------------
Left-hand navigation sidebar: app branding, primary navigation items,
and a "New Task" call-to-action button.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from utils.constants import APP_NAME, SIDEBAR_WIDTH
from utils.themes import Palette


NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Today's Tasks", "📅"),
    ("All Tasks", "📋"),
    ("Categories", "🏷"),
    ("Completed", "✅"),
    ("Settings", "⚙"),
    ("About", "ℹ"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate: Callable[[str], None], on_new_task: Callable[[], None], **kwargs):
        super().__init__(master, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=Palette.SIDEBAR, **kwargs)
        self.grid_propagate(False)
        self.on_navigate = on_navigate
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.active_item = "Dashboard"

        self._build_header()
        self._build_new_task_button(on_new_task)
        self._build_nav()
        self._build_footer()

    # ------------------------------------------------------------
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(24, 16))
        ctk.CTkLabel(
            header, text="✓", font=ctk.CTkFont(size=22, weight="bold"),
            fg_color="#3B8ED0", text_color="white", corner_radius=8, width=36, height=36,
        ).pack(side="left")
        ctk.CTkLabel(
            header, text=APP_NAME, font=ctk.CTkFont(size=19, weight="bold"),
        ).pack(side="left", padx=(10, 0))

    def _build_new_task_button(self, on_new_task: Callable[[], None]) -> None:
        ctk.CTkButton(
            self, text="+  New Task", height=40, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"), command=on_new_task,
        ).pack(fill="x", padx=20, pady=(0, 20))

    def _build_nav(self) -> None:
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=12)
        for label, icon in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}   {label}",
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                hover_color=Palette.CARD_HOVER,
                text_color=Palette.TEXT_PRIMARY,
                font=ctk.CTkFont(size=13),
                command=lambda nav_label=label: self._handle_click(nav_label),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[label] = btn
        self.set_active("Dashboard")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=16)
        ctk.CTkLabel(
            footer, text="v1.0.0", font=ctk.CTkFont(size=11), text_color=Palette.TEXT_SECONDARY,
        ).pack(anchor="w")

    # ------------------------------------------------------------
    def _handle_click(self, label: str) -> None:
        self.set_active(label)
        self.on_navigate(label)

    def set_active(self, label: str) -> None:
        self.active_item = label
        for name, btn in self.nav_buttons.items():
            if name == label:
                btn.configure(fg_color=("#DCE4F5", "#2A2D3A"), text_color=("#1A1B22", "#FFFFFF"))
            else:
                btn.configure(fg_color="transparent", text_color=Palette.TEXT_PRIMARY)
