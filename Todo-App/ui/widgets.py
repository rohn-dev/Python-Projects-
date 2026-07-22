"""
ui/widgets.py
-------------
Reusable, self-contained CustomTkinter widgets used across the app:
StatCard (dashboard KPI cards), TaskCard (a single task row), a Toast
notification, and a simple animated ProgressRing canvas.

Keeping these in one module lets ui/home.py and ui/sidebar.py stay
focused on layout/composition rather than widget internals.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from models.task import Task
from utils.constants import PRIORITY_COLORS, CATEGORY_COLORS, DEFAULT_CATEGORY_COLOR
from utils.themes import Palette


# ======================================================================
# StatCard — dashboard KPI tile
# ======================================================================
class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, accent: str, icon: str = "", **kwargs):
        super().__init__(master, corner_radius=14, fg_color=Palette.SURFACE_ALT, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 0))
        if icon:
            ctk.CTkLabel(header, text=icon, font=ctk.CTkFont(size=18)).pack(side="left")
        ctk.CTkLabel(
            header, text=title, font=ctk.CTkFont(size=13),
            text_color=Palette.TEXT_SECONDARY,
        ).pack(side="left", padx=(6, 0))

        self.value_label = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=accent,
        )
        self.value_label.pack(anchor="w", padx=16, pady=(2, 14))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)


# ======================================================================
# ProgressRing — small canvas-based circular progress indicator
# ======================================================================
class ProgressRing(tk.Canvas):
    def __init__(self, master, size: int = 90, thickness: int = 9, color: str = "#3B8ED0", **kwargs):
        bg = kwargs.pop("bg", "#1E1F26")
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.color = color
        self._percent = 0
        self.text_id = None
        self.draw(0)

    def draw(self, percent: float) -> None:
        self._percent = max(0, min(100, percent))
        self.delete("all")
        pad = self.thickness
        self.create_oval(
            pad, pad, self.size - pad, self.size - pad,
            outline="#3A3C46", width=self.thickness,
        )
        extent = -360 * (self._percent / 100)
        if self._percent > 0:
            self.create_arc(
                pad, pad, self.size - pad, self.size - pad,
                start=90, extent=extent, style="arc",
                outline=self.color, width=self.thickness,
            )
        self.create_text(
            self.size / 2, self.size / 2,
            text=f"{int(self._percent)}%",
            fill="#F2F2F5", font=("Segoe UI", 14, "bold"),
        )

    def animate_to(self, target_percent: float, steps: int = 20) -> None:
        start = self._percent
        delta = (target_percent - start) / steps

        def step(i=0):
            if i >= steps:
                self.draw(target_percent)
                return
            self.draw(start + delta * i)
            self.after(12, lambda: step(i + 1))

        step()


# ======================================================================
# TaskCard — a single task row
# ======================================================================
class TaskCard(ctk.CTkFrame):
    """
    A single task's visual representation. Purely presentational — all
    click handlers are supplied as callbacks so this widget has zero
    knowledge of TaskManager / database internals.
    """

    def __init__(
        self,
        master,
        task: Task,
        on_toggle_complete: Callable[[int], None],
        on_edit: Callable[[int], None],
        on_delete: Callable[[int], None],
        on_duplicate: Callable[[int], None],
        on_toggle_pin: Callable[[int], None],
        on_toggle_favorite: Callable[[int], None],
        on_select: Optional[Callable[[int, bool], None]] = None,
        selectable: bool = False,
        **kwargs,
    ):
        fg = Palette.CARD_HOVER if task.pinned else Palette.SURFACE_ALT
        super().__init__(master, corner_radius=12, fg_color=fg, **kwargs)
        self.task = task
        self.on_select = on_select
        self.selectable = selectable
        self._selected = tk.BooleanVar(value=False)

        self.grid_columnconfigure(2, weight=1)

        col = 0
        if selectable:
            chk = ctk.CTkCheckBox(
                self, text="", variable=self._selected, width=20,
                command=lambda: on_select and on_select(task.id, self._selected.get()),
            )
            chk.grid(row=0, column=col, rowspan=2, padx=(12, 0), pady=12)
            col += 1

        # Completion checkbox
        self.complete_var = tk.BooleanVar(value=task.completed)
        complete_chk = ctk.CTkCheckBox(
            self, text="", variable=self.complete_var, width=20,
            command=lambda: on_toggle_complete(task.id),
        )
        complete_chk.grid(row=0, column=col, rowspan=2, padx=(12, 6), pady=12)
        col += 1

        # Priority color strip
        strip = ctk.CTkFrame(self, width=4, fg_color=PRIORITY_COLORS.get(task.priority, "#3B8ED0"))
        strip.grid(row=0, column=col, rowspan=2, sticky="ns", pady=8)
        col += 1

        # Title + meta
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=col, rowspan=2, sticky="ew", padx=10, pady=8)
        text_frame.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(text_frame, fg_color="transparent")
        title_row.pack(fill="x", anchor="w")

        title_color = Palette.TEXT_SECONDARY if task.completed else Palette.TEXT_PRIMARY
        title_font = ctk.CTkFont(size=14, weight="bold", overstrike=task.completed)
        ctk.CTkLabel(
            title_row, text=task.title, font=title_font, text_color=title_color, anchor="w",
        ).pack(side="left")

        if task.pinned:
            ctk.CTkLabel(title_row, text="📌", font=ctk.CTkFont(size=12)).pack(side="left", padx=(6, 0))
        if task.favorite:
            ctk.CTkLabel(title_row, text="⭐", font=ctk.CTkFont(size=12)).pack(side="left", padx=(4, 0))

        meta_row = ctk.CTkFrame(text_frame, fg_color="transparent")
        meta_row.pack(fill="x", anchor="w", pady=(4, 0))

        cat_color = CATEGORY_COLORS.get(task.category, DEFAULT_CATEGORY_COLOR)
        cat_badge = ctk.CTkLabel(
            meta_row, text=f"  {task.category}  ", font=ctk.CTkFont(size=11),
            fg_color=cat_color, text_color="#FFFFFF", corner_radius=8,
        )
        cat_badge.pack(side="left")

        prio_badge = ctk.CTkLabel(
            meta_row, text=f"  {task.priority}  ", font=ctk.CTkFont(size=11),
            fg_color=PRIORITY_COLORS.get(task.priority, "#3B8ED0"), text_color="#FFFFFF",
            corner_radius=8,
        )
        prio_badge.pack(side="left", padx=(6, 0))

        due_color = Palette.DANGER if task.is_overdue else Palette.TEXT_SECONDARY
        due_prefix = "⚠ Overdue: " if task.is_overdue else "🕒 "
        ctk.CTkLabel(
            meta_row, text=f"{due_prefix}{task.display_due_date}",
            font=ctk.CTkFont(size=11), text_color=due_color,
        ).pack(side="left", padx=(8, 0))

        # Action buttons
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=col + 1, rowspan=2, padx=(4, 12), pady=8, sticky="e")

        def icon_btn(parent, text, command, tooltip=""):
            return ctk.CTkButton(
                parent, text=text, width=30, height=28, corner_radius=8,
                fg_color="transparent", hover_color=Palette.CARD_HOVER,
                text_color=Palette.TEXT_SECONDARY, font=ctk.CTkFont(size=14),
                command=command,
            )

        icon_btn(actions, "⭐" if not task.favorite else "★",
                  lambda: on_toggle_favorite(task.id)).pack(side="left")
        icon_btn(actions, "📌", lambda: on_toggle_pin(task.id)).pack(side="left")
        icon_btn(actions, "✎", lambda: on_edit(task.id)).pack(side="left")
        icon_btn(actions, "⧉", lambda: on_duplicate(task.id)).pack(side="left")
        icon_btn(actions, "🗑", lambda: on_delete(task.id)).pack(side="left")


# ======================================================================
# Toast — lightweight transient notification
# ======================================================================
class Toast(ctk.CTkToplevel):
    """A small auto-dismissing notification bubble (bottom-right)."""

    def __init__(self, master, message: str, kind: str = "info", duration_ms: int = 2600):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.97)
        except tk.TclError:
            pass

        colors = {
            "info": "#3B8ED0",
            "success": "#2ECC71",
            "error": "#E74C3C",
            "warning": "#F2994A",
        }
        color = colors.get(kind, colors["info"])

        frame = ctk.CTkFrame(self, corner_radius=12, fg_color=Palette.SURFACE_ALT,
                              border_width=2, border_color=color)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            frame, text=message, font=ctk.CTkFont(size=13), text_color=Palette.TEXT_PRIMARY,
            wraplength=280, justify="left",
        ).pack(padx=16, pady=12)

        self.update_idletasks()
        self._position(master)
        self.after(duration_ms, self._fade_out)

    def _position(self, master) -> None:
        try:
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            x = mx + mw - w - 24
            y = my + mh - h - 24
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def _fade_out(self) -> None:
        try:
            alpha = self.attributes("-alpha")
            if alpha and alpha > 0.05:
                self.attributes("-alpha", alpha - 0.08)
                self.after(20, self._fade_out)
            else:
                self.destroy()
        except tk.TclError:
            self.destroy()
