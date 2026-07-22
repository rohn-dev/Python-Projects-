"""
ui/home.py
----------
The main application window. Composes the Sidebar, dashboard, task
list, categories, settings, and about views. Wires up TaskManager
(the service layer) to the UI and owns keyboard shortcuts, toast
notifications, and the status bar.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from models.task import Task
from services.task_manager import TaskManager, TaskManagerError
from ui.dialogs import TaskDialog, ConfirmDialog, CategoryDialog
from ui.sidebar import Sidebar
from ui.widgets import StatCard, TaskCard, Toast, ProgressRing
from utils.constants import (
    APP_NAME, APP_VERSION, FilterMode, SortMode, ACCENT_COLORS, SHORTCUTS, SHORTCUT_LABELS,
)
from utils.helpers import load_settings, save_settings
from utils.themes import apply_appearance, get_accent_hex, Palette


class TodoApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.settings = load_settings()
        apply_appearance(self.settings.get("theme", "Dark"))
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME} — Professional Task Manager")
        self.geometry(self.settings.get("window_geometry", "1200x750"))
        self.minsize(980, 620)

        self.task_manager = TaskManager()
        self.task_manager.on_change(self._refresh_current_view)

        self.current_view = self.settings.get("startup_page", "Dashboard")
        self.search_query = ctk.StringVar(value="")
        self.sort_mode = ctk.StringVar(value=SortMode.DUE_DATE.value)
        self.category_filter: Optional[str] = None
        self.selected_ids: set[int] = set()
        self.bulk_mode = False

        self._build_layout()
        self._bind_shortcuts()
        self._render_view(self.current_view)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==================================================================
    # Layout scaffolding
    # ==================================================================
    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self._render_view, on_new_task=self._open_new_task_dialog)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.main_area = ctk.CTkFrame(self, fg_color=Palette.SURFACE, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self._build_topbar()

        self.content_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 8))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.status_bar = ctk.CTkLabel(
            self.main_area, text="Ready", anchor="w", font=ctk.CTkFont(size=11),
            text_color=Palette.TEXT_SECONDARY,
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 6))

    def _build_topbar(self) -> None:
        topbar = ctk.CTkFrame(self.main_area, fg_color="transparent", height=64)
        topbar.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        topbar.grid_columnconfigure(1, weight=1)

        self.view_title = ctk.CTkLabel(
            topbar, text=self.current_view, font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.view_title.grid(row=0, column=0, sticky="w")

        search_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="e")

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="🔍  Search tasks…", width=240,
            textvariable=self.search_query,
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_query.trace_add("write", lambda *_: self._refresh_current_view())

        self.sort_menu = ctk.CTkOptionMenu(
            search_frame, values=[m.value for m in SortMode], variable=self.sort_mode,
            width=140, command=lambda *_: self._refresh_current_view(),
        )
        self.sort_menu.pack(side="left")

    # ==================================================================
    # Keyboard shortcuts
    # ==================================================================
    def _bind_shortcuts(self) -> None:
        self.bind(SHORTCUTS["new_task"], lambda e: self._open_new_task_dialog())
        self.bind(SHORTCUTS["search"], lambda e: self.search_entry.focus_set())
        self.bind(SHORTCUTS["undo"], lambda e: self._handle_undo())
        self.bind(SHORTCUTS["save"], lambda e: self._save_settings_now())

    # ==================================================================
    # View routing
    # ==================================================================
    def _render_view(self, view_name: str) -> None:
        self.current_view = view_name
        self.sidebar.set_active(view_name)
        self.view_title.configure(text=view_name)
        self.bulk_mode = False
        self.selected_ids.clear()

        for child in self.content_frame.winfo_children():
            child.destroy()

        show_search_sort = view_name in (
            "Dashboard", "Today's Tasks", "All Tasks", "Completed",
        )
        if show_search_sort:
            self.search_entry.master.pack_configure() if False else None

        renderers = {
            "Dashboard": self._render_dashboard,
            "Today's Tasks": lambda: self._render_task_list(FilterMode.TODAY),
            "All Tasks": lambda: self._render_task_list(FilterMode.ALL),
            "Categories": self._render_categories,
            "Completed": lambda: self._render_task_list(FilterMode.COMPLETED),
            "Settings": self._render_settings,
            "About": self._render_about,
        }
        renderer = renderers.get(view_name, self._render_dashboard)
        renderer()

    def _refresh_current_view(self) -> None:
        self._render_view(self.current_view)

    # ==================================================================
    # Dashboard
    # ==================================================================
    def _render_dashboard(self) -> None:
        wrapper = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats = self.task_manager.get_stats()
        accent = get_accent_hex(self.settings.get("accent_color", "Blue"))

        cards = [
            ("Total Tasks", str(stats["total"]), accent, "📋"),
            ("Completed", str(stats["completed"]), Palette.SUCCESS[1], "✅"),
            ("Pending", str(stats["pending"]), "#F2994A", "🕓"),
            ("Overdue", str(stats["overdue"]), Palette.DANGER[1], "⚠"),
        ]
        for i, (title, value, color, icon) in enumerate(cards):
            card = StatCard(wrapper, title, value, color, icon)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(0, 16))

        # Progress + goals row
        mid_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        mid_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 16))
        mid_row.grid_columnconfigure((0, 1), weight=1)

        progress_card = ctk.CTkFrame(mid_row, corner_radius=14, fg_color=Palette.SURFACE_ALT)
        progress_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            progress_card, text="Overall Completion", font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(16, 6))
        ring_wrap = ctk.CTkFrame(progress_card, fg_color="transparent")
        ring_wrap.pack(pady=(0, 18))
        ring = ProgressRing(ring_wrap, size=110, color=accent, bg=self._canvas_bg())
        ring.pack()
        ring.animate_to(stats["completion_pct"])

        streak_card = ctk.CTkFrame(mid_row, corner_radius=14, fg_color=Palette.SURFACE_ALT)
        streak_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        streak = self.task_manager.get_completion_streak()
        daily_goal = self.settings.get("daily_goal", 5)
        weekly_goal = self.settings.get("weekly_goal", 25)

        ctk.CTkLabel(
            streak_card, text="Productivity", font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(16, 10))
        ctk.CTkLabel(
            streak_card, text=f"🔥 {streak}-day completion streak",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=18, pady=2)
        ctk.CTkLabel(
            streak_card, text=f"🎯 Daily goal: {daily_goal} tasks",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=18, pady=2)
        ctk.CTkLabel(
            streak_card, text=f"📆 Weekly goal: {weekly_goal} tasks",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=18, pady=(2, 16))

        # Recently completed
        ctk.CTkLabel(
            wrapper, text="Recently Completed", font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 8))

        recent = self.task_manager.get_recently_completed(limit=5)
        if not recent:
            ctk.CTkLabel(
                wrapper, text="Nothing completed yet — finish a task to see it here.",
                text_color=Palette.TEXT_SECONDARY,
            ).grid(row=3, column=0, columnspan=4, sticky="w")
        else:
            for i, t in enumerate(recent):
                card = TaskCard(
                    wrapper, t,
                    on_toggle_complete=self._toggle_complete,
                    on_edit=self._open_edit_dialog,
                    on_delete=self._confirm_delete,
                    on_duplicate=self._duplicate_task,
                    on_toggle_pin=self._toggle_pin,
                    on_toggle_favorite=self._toggle_favorite,
                )
                card.grid(row=3 + i, column=0, columnspan=4, sticky="ew", pady=4)

    def _canvas_bg(self) -> str:
        mode = ctk.get_appearance_mode()
        return "#262832" if mode == "Dark" else "#FFFFFF"

    # ==================================================================
    # Task list views (Today / All / Completed / filtered)
    # ==================================================================
    def _render_task_list(self, mode: FilterMode) -> None:
        toolbar = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.content_frame.grid_rowconfigure(1, weight=1)

        filter_var = ctk.StringVar(value=mode.value)
        filter_menu = ctk.CTkOptionMenu(
            toolbar, values=[m.value for m in FilterMode], variable=filter_var,
            width=160,
            command=lambda v: self._render_task_list(FilterMode(v)),
        )
        filter_menu.pack(side="left")

        categories = ["All Categories"] + [c["name"] for c in self.task_manager.get_categories()]
        cat_var = ctk.StringVar(value=self.category_filter or "All Categories")
        cat_menu = ctk.CTkOptionMenu(
            toolbar, values=categories, variable=cat_var, width=160,
            command=lambda v: self._set_category_filter(v, mode),
        )
        cat_menu.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            toolbar, text="Select Multiple", width=130, fg_color="transparent", border_width=1,
            text_color=Palette.TEXT_PRIMARY, command=lambda: self._toggle_bulk_mode(mode),
        ).pack(side="left", padx=(8, 0))

        if self.bulk_mode:
            ctk.CTkButton(
                toolbar, text=f"Delete Selected ({len(self.selected_ids)})", width=160,
                fg_color=Palette.DANGER, command=self._confirm_bulk_delete,
            ).pack(side="left", padx=(8, 0))

        if mode == FilterMode.COMPLETED:
            ctk.CTkButton(
                toolbar, text="Clear Completed", width=140, fg_color=Palette.DANGER,
                command=self._confirm_clear_completed,
            ).pack(side="right")

        list_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)

        tasks = self.task_manager.get_view(
            mode=mode,
            category=self.category_filter,
            query=self.search_query.get(),
            sort=SortMode(self.sort_mode.get()),
        )

        if not tasks:
            ctk.CTkLabel(
                list_frame, text="No tasks match your current filters.",
                text_color=Palette.TEXT_SECONDARY, font=ctk.CTkFont(size=14),
            ).pack(pady=40)
        else:
            for t in tasks:
                card = TaskCard(
                    list_frame, t,
                    on_toggle_complete=self._toggle_complete,
                    on_edit=self._open_edit_dialog,
                    on_delete=self._confirm_delete,
                    on_duplicate=self._duplicate_task,
                    on_toggle_pin=self._toggle_pin,
                    on_toggle_favorite=self._toggle_favorite,
                    on_select=self._handle_selection,
                    selectable=self.bulk_mode,
                )
                card.pack(fill="x", pady=4)

        self._set_status(f"{len(tasks)} task(s) shown")

    def _set_category_filter(self, value: str, mode: FilterMode) -> None:
        self.category_filter = None if value == "All Categories" else value
        self._render_task_list(mode)

    def _toggle_bulk_mode(self, mode: FilterMode) -> None:
        self.bulk_mode = not self.bulk_mode
        self.selected_ids.clear()
        self._render_task_list(mode)

    def _handle_selection(self, task_id: int, selected: bool) -> None:
        if selected:
            self.selected_ids.add(task_id)
        else:
            self.selected_ids.discard(task_id)

    # ==================================================================
    # Categories view
    # ==================================================================
    def _render_categories(self) -> None:
        wrapper = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")

        ctk.CTkButton(
            wrapper, text="+ New Category", command=self._open_category_dialog, width=150,
        ).pack(anchor="w", pady=(0, 16))

        for cat in self.task_manager.get_categories():
            row = ctk.CTkFrame(wrapper, corner_radius=10, fg_color=Palette.SURFACE_ALT)
            row.pack(fill="x", pady=4)

            count = sum(1 for t in self.task_manager.tasks if t.category == cat["name"])

            ctk.CTkLabel(
                row, text="  ", fg_color=cat["color"], width=18, height=18, corner_radius=9,
            ).pack(side="left", padx=(14, 10), pady=12)
            ctk.CTkLabel(
                row, text=cat["name"], font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=f"{count} task(s)", text_color=Palette.TEXT_SECONDARY,
            ).pack(side="left", padx=(10, 0))

            if cat["name"] not in ("Personal", "Work", "College", "Shopping", "Health", "Coding", "Uncategorized"):
                ctk.CTkButton(
                    row, text="Delete", width=70, fg_color="transparent", border_width=1,
                    text_color=Palette.DANGER,
                    command=lambda n=cat["name"]: self._delete_category(n),
                ).pack(side="right", padx=14, pady=8)

    def _open_category_dialog(self) -> None:
        CategoryDialog(self, on_save=self._create_category)

    def _create_category(self, name: str, color: str) -> None:
        try:
            self.task_manager.add_category(name, color)
            self._toast(f"Category '{name}' created.", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")
        self._render_view("Categories")

    def _delete_category(self, name: str) -> None:
        self.task_manager.delete_category(name)
        self._toast(f"Category '{name}' deleted.", "info")
        self._render_view("Categories")

    # ==================================================================
    # Settings view
    # ==================================================================
    def _render_settings(self) -> None:
        wrapper = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")

        def section(title: str) -> ctk.CTkFrame:
            ctk.CTkLabel(wrapper, text=title, font=ctk.CTkFont(size=15, weight="bold")).pack(
                anchor="w", pady=(16, 6)
            )
            f = ctk.CTkFrame(wrapper, corner_radius=12, fg_color=Palette.SURFACE_ALT)
            f.pack(fill="x", pady=(0, 4))
            return f

        # Appearance
        appearance = section("Appearance")
        row = ctk.CTkFrame(appearance, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row, text="Theme").pack(side="left")
        theme_var = ctk.StringVar(value=self.settings.get("theme", "Dark"))
        ctk.CTkOptionMenu(
            row, values=["Dark", "Light", "System"], variable=theme_var,
            command=lambda v: self._update_setting("theme", v, apply_theme=True),
        ).pack(side="right")

        row2 = ctk.CTkFrame(appearance, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(row2, text="Accent Color").pack(side="left")
        accent_var = ctk.StringVar(value=self.settings.get("accent_color", "Blue"))
        ctk.CTkOptionMenu(
            row2, values=list(ACCENT_COLORS.keys()), variable=accent_var,
            command=lambda v: self._update_setting("accent_color", v),
        ).pack(side="right")

        row3 = ctk.CTkFrame(appearance, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(row3, text="Font Scale").pack(side="left")
        scale_slider = ctk.CTkSlider(
            row3, from_=0.8, to=1.4, number_of_steps=6,
            command=lambda v: self._update_setting("font_scale", round(float(v), 2)),
        )
        scale_slider.set(self.settings.get("font_scale", 1.0))
        scale_slider.pack(side="right", padx=(10, 0))

        # Behavior
        behavior = section("Behavior")
        row4 = ctk.CTkFrame(behavior, fg_color="transparent")
        row4.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row4, text="Startup Page").pack(side="left")
        startup_var = ctk.StringVar(value=self.settings.get("startup_page", "Dashboard"))
        ctk.CTkOptionMenu(
            row4, values=["Dashboard", "Today's Tasks", "All Tasks", "Completed"],
            variable=startup_var, command=lambda v: self._update_setting("startup_page", v),
        ).pack(side="right")

        row5 = ctk.CTkFrame(behavior, fg_color="transparent")
        row5.pack(fill="x", padx=16, pady=(0, 14))
        auto_save_var = ctk.BooleanVar(value=self.settings.get("auto_save", True))
        ctk.CTkCheckBox(
            row5, text="Auto-save settings", variable=auto_save_var,
            command=lambda: self._update_setting("auto_save", auto_save_var.get()),
        ).pack(side="left")

        row6 = ctk.CTkFrame(behavior, fg_color="transparent")
        row6.pack(fill="x", padx=16, pady=(0, 14))
        sound_var = ctk.BooleanVar(value=self.settings.get("sound_on_complete", False))
        ctk.CTkCheckBox(
            row6, text="Play sound on task completion", variable=sound_var,
            command=lambda: self._update_setting("sound_on_complete", sound_var.get()),
        ).pack(side="left")

        # Goals
        goals = section("Productivity Goals")
        row7 = ctk.CTkFrame(goals, fg_color="transparent")
        row7.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row7, text="Daily Goal (tasks)").pack(side="left")
        daily_entry = ctk.CTkEntry(row7, width=60)
        daily_entry.insert(0, str(self.settings.get("daily_goal", 5)))
        daily_entry.pack(side="right")
        daily_entry.bind("<FocusOut>", lambda e: self._update_int_setting("daily_goal", daily_entry.get()))

        row8 = ctk.CTkFrame(goals, fg_color="transparent")
        row8.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(row8, text="Weekly Goal (tasks)").pack(side="left")
        weekly_entry = ctk.CTkEntry(row8, width=60)
        weekly_entry.insert(0, str(self.settings.get("weekly_goal", 25)))
        weekly_entry.pack(side="right")
        weekly_entry.bind("<FocusOut>", lambda e: self._update_int_setting("weekly_goal", weekly_entry.get()))

        # Data
        data_section = section("Data Management")
        row9 = ctk.CTkFrame(data_section, fg_color="transparent")
        row9.pack(fill="x", padx=16, pady=14)
        ctk.CTkButton(row9, text="Export to CSV", width=140, command=self._export_csv).pack(side="left")
        ctk.CTkButton(row9, text="Import from CSV", width=140, command=self._import_csv).pack(side="left", padx=8)

        row10 = ctk.CTkFrame(data_section, fg_color="transparent")
        row10.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(row10, text="Backup Database", width=140, command=self._backup_db).pack(side="left")
        ctk.CTkButton(row10, text="Restore Database", width=140, command=self._restore_db).pack(side="left", padx=8)

        # Keyboard shortcuts reference
        shortcuts_section = section("Keyboard Shortcuts")
        for key, label in SHORTCUT_LABELS.items():
            row = ctk.CTkFrame(shortcuts_section, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=key.replace("_", " ").title()).pack(side="left")
            ctk.CTkLabel(row, text=label, text_color=Palette.TEXT_SECONDARY).pack(side="right")

    def _update_setting(self, key: str, value, apply_theme: bool = False) -> None:
        self.settings[key] = value
        if self.settings.get("auto_save", True):
            save_settings(self.settings)
        if apply_theme:
            apply_appearance(value)
        if key == "accent_color":
            self._render_view("Dashboard") if self.current_view == "Dashboard" else None

    def _update_int_setting(self, key: str, raw_value: str) -> None:
        try:
            value = max(0, int(raw_value))
        except ValueError:
            self._toast("Please enter a whole number.", "error")
            return
        self._update_setting(key, value)

    def _save_settings_now(self) -> None:
        save_settings(self.settings)
        self._toast("Settings saved.", "success")

    # ------------------------------------------------------------
    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Export Tasks to CSV",
        )
        if not path:
            return
        try:
            self.task_manager.export_csv(Path(path))
            self._toast("Tasks exported successfully.", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")], title="Import Tasks from CSV")
        if not path:
            return
        try:
            count = self.task_manager.import_csv(Path(path))
            self._toast(f"Imported {count} task(s).", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _backup_db(self) -> None:
        try:
            path = self.task_manager.backup_database()
            self._toast(f"Backup saved: {path.name}", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _restore_db(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")], title="Restore Database")
        if not path:
            return

        def do_restore():
            try:
                self.task_manager.restore_database(Path(path))
                self._toast("Database restored.", "success")
            except TaskManagerError as exc:
                self._toast(str(exc), "error")

        ConfirmDialog(
            self, "Restore Database",
            "This will overwrite your current tasks with the selected backup. Continue?",
            on_confirm=do_restore,
        )

    # ==================================================================
    # About view
    # ==================================================================
    def _render_about(self) -> None:
        wrapper = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")

        card = ctk.CTkFrame(wrapper, corner_radius=16, fg_color=Palette.SURFACE_ALT)
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card, text=f"{APP_NAME}", font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(
            card, text=f"Version {APP_VERSION}", text_color=Palette.TEXT_SECONDARY,
        ).pack(anchor="w", padx=24)
        ctk.CTkLabel(
            card,
            text=(
                "A modern, professional desktop task manager built with Python and "
                "CustomTkinter, following clean architecture (MVC), SOLID principles, "
                "and a fully typed, tested codebase."
            ),
            wraplength=600, justify="left",
        ).pack(anchor="w", padx=24, pady=(12, 24))

        stack_card = ctk.CTkFrame(wrapper, corner_radius=16, fg_color=Palette.SURFACE_ALT)
        stack_card.pack(fill="x")
        ctk.CTkLabel(
            stack_card, text="Built With", font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(20, 8))
        for item in ["Python 3.12+", "CustomTkinter", "SQLite3", "Pillow"]:
            ctk.CTkLabel(stack_card, text=f"•  {item}").pack(anchor="w", padx=24, pady=2)
        ctk.CTkLabel(stack_card, text="").pack(pady=6)

    # ==================================================================
    # Task actions
    # ==================================================================
    def _open_new_task_dialog(self) -> None:
        categories = [c["name"] for c in self.task_manager.get_categories()] or ["Uncategorized"]
        TaskDialog(self, categories=categories, on_save=self._create_task)

    def _open_edit_dialog(self, task_id: int) -> None:
        task = self.task_manager.get_task(task_id)
        if task is None:
            self._toast("Task not found — it may have been deleted.", "error")
            return
        categories = [c["name"] for c in self.task_manager.get_categories()] or ["Uncategorized"]
        TaskDialog(self, categories=categories, on_save=self._update_task, task=task)

    def _create_task(self, task: Task) -> None:
        try:
            self.task_manager.add_task(task)
            self._toast(f"Task '{task.title}' added.", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")
            raise

    def _update_task(self, task: Task) -> None:
        try:
            self.task_manager.update_task(task)
            self._toast(f"Task '{task.title}' updated.", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")
            raise

    def _toggle_complete(self, task_id: int) -> None:
        try:
            task = self.task_manager.toggle_completed(task_id)
            msg = "Task completed! 🎉" if task.completed else "Marked as pending."
            self._toast(msg, "success" if task.completed else "info")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _toggle_pin(self, task_id: int) -> None:
        try:
            self.task_manager.toggle_pinned(task_id)
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _toggle_favorite(self, task_id: int) -> None:
        try:
            self.task_manager.toggle_favorite(task_id)
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _duplicate_task(self, task_id: int) -> None:
        try:
            self.task_manager.duplicate_task(task_id)
            self._toast("Task duplicated.", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    def _confirm_delete(self, task_id: int) -> None:
        task = self.task_manager.get_task(task_id)
        if task is None:
            return

        def do_delete():
            try:
                self.task_manager.delete_task(task_id)
                self._toast("Task deleted. Press Ctrl+Z to undo.", "info")
            except TaskManagerError as exc:
                self._toast(str(exc), "error")

        ConfirmDialog(
            self, "Delete Task", f"Delete '{task.title}'? This can be undone with Ctrl+Z.",
            on_confirm=do_delete,
        )

    def _confirm_bulk_delete(self) -> None:
        if not self.selected_ids:
            self._toast("No tasks selected.", "warning")
            return

        def do_delete():
            self.task_manager.bulk_delete(list(self.selected_ids))
            self._toast(f"Deleted {len(self.selected_ids)} task(s).", "info")
            self.selected_ids.clear()

        ConfirmDialog(
            self, "Delete Selected Tasks",
            f"Delete {len(self.selected_ids)} selected task(s)? This cannot be undone.",
            on_confirm=do_delete,
        )

    def _confirm_clear_completed(self) -> None:
        def do_clear():
            count = self.task_manager.clear_completed()
            self._toast(f"Cleared {count} completed task(s).", "info")

        ConfirmDialog(
            self, "Clear Completed", "Remove all completed tasks? This cannot be undone.",
            on_confirm=do_clear,
        )

    def _handle_undo(self) -> None:
        if not self.task_manager.can_undo():
            self._toast("Nothing to undo.", "warning")
            return
        try:
            restored = self.task_manager.undo()
            if restored:
                self._toast(f"Restored '{restored.title}'.", "success")
        except TaskManagerError as exc:
            self._toast(str(exc), "error")

    # ==================================================================
    # Misc helpers
    # ==================================================================
    def _toast(self, message: str, kind: str = "info") -> None:
        try:
            Toast(self, message, kind=kind)
        except Exception:
            pass  # never let a notification failure crash the app
        self._set_status(message)

    def _set_status(self, message: str) -> None:
        self.status_bar.configure(text=message)

    def _on_close(self) -> None:
        self.settings["window_geometry"] = self.geometry()
        save_settings(self.settings)
        self.destroy()
