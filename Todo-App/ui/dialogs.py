"""
ui/dialogs.py
-------------
Modal dialog windows: adding/editing a task, confirming destructive
actions, and creating a new category. Each dialog validates its own
input and reports errors inline rather than crashing the app.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from models.task import Task
from utils.constants import Priority
from utils.helpers import parse_date_safe, parse_time_safe
from utils.themes import Palette


class TaskDialog(ctk.CTkToplevel):
    """Add or edit a task. Pass an existing Task to edit; omit to create."""

    def __init__(
        self,
        master,
        categories: list[str],
        on_save: Callable[[Task], None],
        task: Optional[Task] = None,
    ):
        super().__init__(master)
        self.title("Edit Task" if task else "New Task")
        self.geometry("460x620")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.on_save = on_save
        self.editing_task = task
        self.categories = categories or ["Uncategorized"]

        self._build_ui()
        if task:
            self._populate(task)

        self.after(50, self.title_entry.focus_set)

    # ------------------------------------------------------------
    def _build_ui(self) -> None:
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Title *", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.title_entry = ctk.CTkEntry(container, placeholder_text="e.g. Finish project report")
        self.title_entry.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(container, text="Description", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.desc_text = ctk.CTkTextbox(container, height=80)
        self.desc_text.pack(fill="x", pady=(4, 12))

        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.grid_columnconfigure((0, 1), weight=1)

        cat_col = ctk.CTkFrame(row1, fg_color="transparent")
        cat_col.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(cat_col, text="Category", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.category_menu = ctk.CTkOptionMenu(cat_col, values=self.categories)
        self.category_menu.pack(fill="x", pady=(4, 0))

        prio_col = ctk.CTkFrame(row1, fg_color="transparent")
        prio_col.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(prio_col, text="Priority", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.priority_menu = ctk.CTkOptionMenu(prio_col, values=Priority.values())
        self.priority_menu.set(Priority.MEDIUM.value)
        self.priority_menu.pack(fill="x", pady=(4, 0))

        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 4))
        row2.grid_columnconfigure((0, 1), weight=1)

        date_col = ctk.CTkFrame(row2, fg_color="transparent")
        date_col.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(date_col, text="Due Date (YYYY-MM-DD)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.date_entry = ctk.CTkEntry(date_col, placeholder_text="2026-08-01")
        self.date_entry.pack(fill="x", pady=(4, 0))

        time_col = ctk.CTkFrame(row2, fg_color="transparent")
        time_col.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(time_col, text="Due Time (HH:MM)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        self.time_entry = ctk.CTkEntry(time_col, placeholder_text="17:30")
        self.time_entry.pack(fill="x", pady=(4, 0))

        self.error_label = ctk.CTkLabel(container, text="", text_color=Palette.DANGER, wraplength=400)
        self.error_label.pack(anchor="w", pady=(12, 0))

        self.pinned_var = ctk.BooleanVar(value=False)
        self.favorite_var = ctk.BooleanVar(value=False)
        toggles = ctk.CTkFrame(container, fg_color="transparent")
        toggles.pack(fill="x", pady=(8, 0))
        ctk.CTkCheckBox(toggles, text="Pin this task", variable=self.pinned_var).pack(side="left")
        ctk.CTkCheckBox(toggles, text="Mark as favorite", variable=self.favorite_var).pack(side="left", padx=(16, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(
            btn_row, text="Cancel", fg_color="transparent", border_width=1,
            text_color=Palette.TEXT_PRIMARY, command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_row, text="Save Task", command=self._handle_save).pack(side="right")

        self.bind("<Return>", lambda e: self._handle_save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _populate(self, task: Task) -> None:
        self.title_entry.insert(0, task.title)
        if task.description:
            self.desc_text.insert("1.0", task.description)
        if task.category in self.categories:
            self.category_menu.set(task.category)
        self.priority_menu.set(task.priority)
        if task.due_date:
            self.date_entry.insert(0, task.due_date)
        if task.due_time:
            self.time_entry.insert(0, task.due_time)
        self.pinned_var.set(task.pinned)
        self.favorite_var.set(task.favorite)

    # ------------------------------------------------------------
    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            self.error_label.configure(text="Title cannot be empty.")
            return

        date_ok, date_val = parse_date_safe(self.date_entry.get())
        if not date_ok:
            self.error_label.configure(text=date_val)
            return

        time_ok, time_val = parse_time_safe(self.time_entry.get())
        if not time_ok:
            self.error_label.configure(text=time_val)
            return

        if self.editing_task:
            task = self.editing_task
            task.title = title
            task.description = self.desc_text.get("1.0", "end").strip()
            task.category = self.category_menu.get()
            task.priority = self.priority_menu.get()
            task.due_date = date_val or None
            task.due_time = time_val or None
            task.pinned = self.pinned_var.get()
            task.favorite = self.favorite_var.get()
        else:
            task = Task(
                title=title,
                description=self.desc_text.get("1.0", "end").strip(),
                category=self.category_menu.get(),
                priority=self.priority_menu.get(),
                due_date=date_val or None,
                due_time=time_val or None,
                pinned=self.pinned_var.get(),
                favorite=self.favorite_var.get(),
            )

        errors = task.validate()
        if errors:
            self.error_label.configure(text=" ".join(errors))
            return

        try:
            self.on_save(task)
        except Exception as exc:  # noqa: BLE001 - surface any service-layer error to the user
            self.error_label.configure(text=str(exc))
            return

        self.destroy()


class ConfirmDialog(ctk.CTkToplevel):
    """A generic Yes/No confirmation dialog for destructive actions."""

    def __init__(self, master, title: str, message: str, on_confirm: Callable[[], None], danger: bool = True):
        super().__init__(master)
        self.title(title)
        self.geometry("380x180")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self, text=message, wraplength=320, justify="left", font=ctk.CTkFont(size=14),
        ).pack(padx=24, pady=(28, 20), fill="both", expand=True)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        def confirm():
            on_confirm()
            self.destroy()

        ctk.CTkButton(
            btn_row, text="Cancel", fg_color="transparent", border_width=1,
            text_color=Palette.TEXT_PRIMARY, command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_row, text="Confirm", fg_color=Palette.DANGER if danger else None,
            command=confirm,
        ).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())


class CategoryDialog(ctk.CTkToplevel):
    """Create a new custom category with a chosen accent color."""

    PRESET_COLORS = ["#3B8ED0", "#9B59B6", "#2ECC71", "#E67E22", "#E74C3C", "#16A085", "#F1C40F"]

    def __init__(self, master, on_save: Callable[[str, str], None]):
        super().__init__(master)
        self.title("New Category")
        self.geometry("340x260")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.on_save = on_save
        self.selected_color = self.PRESET_COLORS[0]

        ctk.CTkLabel(self, text="Category Name", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 4)
        )
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Finance")
        self.name_entry.pack(fill="x", padx=20)

        ctk.CTkLabel(self, text="Color", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=20, pady=(16, 4)
        )
        swatch_row = ctk.CTkFrame(self, fg_color="transparent")
        swatch_row.pack(padx=20, fill="x")
        for color in self.PRESET_COLORS:
            b = ctk.CTkButton(
                swatch_row, text="", width=28, height=28, corner_radius=14,
                fg_color=color, hover_color=color,
                command=lambda c=color: self._select_color(c),
            )
            b.pack(side="left", padx=3)

        self.error_label = ctk.CTkLabel(self, text="", text_color=Palette.DANGER)
        self.error_label.pack(anchor="w", padx=20, pady=(10, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(16, 20), side="bottom")
        ctk.CTkButton(
            btn_row, text="Cancel", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_row, text="Create", command=self._handle_save).pack(side="right")

        self.after(50, self.name_entry.focus_set)
        self.bind("<Return>", lambda e: self._handle_save())

    def _select_color(self, color: str) -> None:
        self.selected_color = color

    def _handle_save(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            self.error_label.configure(text="Category name cannot be empty.")
            return
        try:
            self.on_save(name, self.selected_color)
        except Exception as exc:  # noqa: BLE001
            self.error_label.configure(text=str(exc))
            return
        self.destroy()
