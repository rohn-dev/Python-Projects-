"""
models/task.py
--------------
The Task model: a single, well-typed source of truth for what a task
"is". Pure data + computed properties — no database or UI code lives
here (separation of concerns / MVC's "Model").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time as dtime
from typing import Optional

from utils.constants import (
    Priority,
    DATE_FORMAT,
    TIME_FORMAT,
    DISPLAY_DATE_FORMAT,
    DISPLAY_TIME_FORMAT,
)


@dataclass
class Task:
    """Represents a single to-do item."""

    id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: str = "Uncategorized"
    priority: str = Priority.MEDIUM.value
    due_date: Optional[str] = None      # stored as "YYYY-MM-DD"
    due_time: Optional[str] = None      # stored as "HH:MM" (24h)
    completed: bool = False
    pinned: bool = False
    favorite: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # ----------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------
    def validate(self) -> list[str]:
        """Return a list of human-readable validation errors (empty = valid)."""
        errors: list[str] = []

        if not self.title or not self.title.strip():
            errors.append("Task title cannot be empty.")
        if len(self.title) > 200:
            errors.append("Task title is too long (max 200 characters).")
        if self.priority not in Priority.values():
            errors.append(f"Invalid priority: {self.priority}")
        if self.due_date:
            try:
                datetime.strptime(self.due_date, DATE_FORMAT)
            except ValueError:
                errors.append("Invalid due date format (expected YYYY-MM-DD).")
        if self.due_time:
            try:
                datetime.strptime(self.due_time, TIME_FORMAT)
            except ValueError:
                errors.append("Invalid due time format (expected HH:MM).")
        return errors

    # ----------------------------------------------------------------
    # Computed properties
    # ----------------------------------------------------------------
    @property
    def due_datetime(self) -> Optional[datetime]:
        """Combine due_date + due_time into a single datetime, if present."""
        if not self.due_date:
            return None
        try:
            d = datetime.strptime(self.due_date, DATE_FORMAT).date()
            t = dtime(23, 59, 59)
            if self.due_time:
                t = datetime.strptime(self.due_time, TIME_FORMAT).time()
            return datetime.combine(d, t)
        except ValueError:
            return None

    @property
    def is_overdue(self) -> bool:
        dt = self.due_datetime
        if dt is None or self.completed:
            return False
        return dt < datetime.now()

    @property
    def is_due_today(self) -> bool:
        if not self.due_date:
            return False
        try:
            d = datetime.strptime(self.due_date, DATE_FORMAT).date()
            return d == date.today()
        except ValueError:
            return False

    @property
    def is_due_this_week(self) -> bool:
        if not self.due_date:
            return False
        try:
            d = datetime.strptime(self.due_date, DATE_FORMAT).date()
            today = date.today()
            start = today
            end = today.fromordinal(today.toordinal() + (6 - today.weekday()))
            return start <= d <= end
        except ValueError:
            return False

    @property
    def display_due_date(self) -> str:
        if not self.due_date:
            return "No due date"
        try:
            d = datetime.strptime(self.due_date, DATE_FORMAT)
            text = d.strftime(DISPLAY_DATE_FORMAT)
            if self.due_time:
                t = datetime.strptime(self.due_time, TIME_FORMAT)
                text += f" · {t.strftime(DISPLAY_TIME_FORMAT)}"
            return text
        except ValueError:
            return "Invalid date"

    # ----------------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "due_date": self.due_date,
            "due_time": self.due_time,
            "completed": int(self.completed),
            "pinned": int(self.pinned),
            "favorite": int(self.favorite),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Task":
        """Build a Task from a sqlite3.Row (already converted to dict)."""
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            category=row["category"] or "Uncategorized",
            priority=row["priority"] or Priority.MEDIUM.value,
            due_date=row["due_date"],
            due_time=row["due_time"],
            completed=bool(row["completed"]),
            pinned=bool(row["pinned"]),
            favorite=bool(row["favorite"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def clone_as_duplicate(self) -> "Task":
        """Return a new Task representing 'Copy of <title>' — no id, fresh timestamps."""
        now = datetime.now().isoformat(timespec="seconds")
        return Task(
            id=None,
            title=f"{self.title} (Copy)",
            description=self.description,
            category=self.category,
            priority=self.priority,
            due_date=self.due_date,
            due_time=self.due_time,
            completed=False,
            pinned=False,
            favorite=False,
            created_at=now,
            updated_at=now,
        )
