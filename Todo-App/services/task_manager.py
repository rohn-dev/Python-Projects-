"""
services/task_manager.py
-------------------------
The application's business-logic layer (the "Controller" in MVC).

The UI never touches sqlite directly — it calls into TaskManager, which
owns validation, filtering, sorting, search, undo stacks, statistics,
and import/export. This keeps ui/*.py focused purely on presentation.
"""

from __future__ import annotations

import csv
from dataclasses import replace
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Callable, Optional

from database.database import Database, DatabaseError
from models.task import Task
from utils.constants import (
    Priority,
    PRIORITY_ORDER,
    FilterMode,
    SortMode,
)


class TaskManagerError(Exception):
    """Raised for business-rule violations (e.g. invalid task data)."""


class TaskManager:
    """Owns the in-memory task cache and all task-related operations."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or Database()
        self._tasks: list[Task] = []
        self._undo_stack: list[tuple[str, Task]] = []  # ("delete", task) etc.
        self._on_change_callbacks: list[Callable[[], None]] = []
        self.reload()

    # ------------------------------------------------------------
    # Change notification (so UI can auto-refresh)
    # ------------------------------------------------------------
    def on_change(self, callback: Callable[[], None]) -> None:
        self._on_change_callbacks.append(callback)

    def _notify(self) -> None:
        for cb in self._on_change_callbacks:
            cb()

    # ------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------
    def reload(self) -> None:
        try:
            rows = self.db.get_all_tasks()
        except DatabaseError as exc:
            raise TaskManagerError(str(exc)) from exc
        self._tasks = [Task.from_row(r) for r in rows]

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks)

    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------
    def add_task(self, task: Task) -> Task:
        errors = task.validate()
        if errors:
            raise TaskManagerError(" ".join(errors))
        now = datetime.now().isoformat(timespec="seconds")
        task.created_at = now
        task.updated_at = now
        try:
            new_id = self.db.insert_task(task.to_dict())
        except DatabaseError as exc:
            raise TaskManagerError(f"Could not save task: {exc}") from exc
        task.id = new_id
        self.reload()
        self._notify()
        return task

    def update_task(self, task: Task) -> Task:
        if task.id is None:
            raise TaskManagerError("Cannot update a task with no id.")
        errors = task.validate()
        if errors:
            raise TaskManagerError(" ".join(errors))
        task.updated_at = datetime.now().isoformat(timespec="seconds")
        try:
            self.db.update_task(task.id, task.to_dict())
        except DatabaseError as exc:
            raise TaskManagerError(f"Could not update task: {exc}") from exc
        self.reload()
        self._notify()
        return task

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        if task is None:
            raise TaskManagerError("Task not found. It may have already been removed.")
        try:
            self.db.delete_task(task_id)
        except DatabaseError as exc:
            raise TaskManagerError(f"Could not delete task: {exc}") from exc
        self._undo_stack.append(("delete", task))
        self.reload()
        self._notify()

    def bulk_delete(self, task_ids: list[int]) -> None:
        try:
            self.db.bulk_delete(task_ids)
        except DatabaseError as exc:
            raise TaskManagerError(f"Could not delete tasks: {exc}") from exc
        self.reload()
        self._notify()

    def clear_completed(self) -> int:
        try:
            count = self.db.clear_completed()
        except DatabaseError as exc:
            raise TaskManagerError(f"Could not clear completed tasks: {exc}") from exc
        self.reload()
        self._notify()
        return count

    def duplicate_task(self, task_id: int) -> Task:
        original = self.get_task(task_id)
        if original is None:
            raise TaskManagerError("Task not found.")
        return self.add_task(original.clone_as_duplicate())

    def get_task(self, task_id: int) -> Optional[Task]:
        return next((t for t in self._tasks if t.id == task_id), None)

    # ------------------------------------------------------------
    # Toggle helpers
    # ------------------------------------------------------------
    def toggle_completed(self, task_id: int) -> Task:
        task = self.get_task(task_id)
        if task is None:
            raise TaskManagerError("Task not found.")
        updated = replace(task, completed=not task.completed)
        return self.update_task(updated)

    def toggle_pinned(self, task_id: int) -> Task:
        task = self.get_task(task_id)
        if task is None:
            raise TaskManagerError("Task not found.")
        updated = replace(task, pinned=not task.pinned)
        return self.update_task(updated)

    def toggle_favorite(self, task_id: int) -> Task:
        task = self.get_task(task_id)
        if task is None:
            raise TaskManagerError("Task not found.")
        updated = replace(task, favorite=not task.favorite)
        return self.update_task(updated)

    # ------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def undo(self) -> Optional[Task]:
        """Undo the most recent delete. Returns the restored Task, or None."""
        if not self._undo_stack:
            return None
        action, task = self._undo_stack.pop()
        if action == "delete":
            try:
                new_id = self.db.reinsert_task(task.to_dict())
            except DatabaseError as exc:
                raise TaskManagerError(f"Could not undo delete: {exc}") from exc
            task.id = new_id
            self.reload()
            self._notify()
            return task
        return None

    # ------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------
    def get_categories(self) -> list[dict]:
        return self.db.get_categories()

    def add_category(self, name: str, color: str = "#5B8DEF") -> None:
        name = name.strip()
        if not name:
            raise TaskManagerError("Category name cannot be empty.")
        self.db.add_category(name, color)
        self._notify()

    def delete_category(self, name: str) -> None:
        self.db.delete_category(name)
        self._notify()

    # ------------------------------------------------------------
    # Filtering, searching, sorting
    # ------------------------------------------------------------
    def filter_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        mode: FilterMode = FilterMode.ALL,
        category: Optional[str] = None,
    ) -> list[Task]:
        pool = tasks if tasks is not None else self._tasks

        if mode == FilterMode.TODAY:
            pool = [t for t in pool if t.is_due_today and not t.completed]
        elif mode == FilterMode.THIS_WEEK:
            pool = [t for t in pool if t.is_due_this_week and not t.completed]
        elif mode == FilterMode.COMPLETED:
            pool = [t for t in pool if t.completed]
        elif mode == FilterMode.PENDING:
            pool = [t for t in pool if not t.completed]
        elif mode == FilterMode.OVERDUE:
            pool = [t for t in pool if t.is_overdue]
        elif mode == FilterMode.HIGH_PRIORITY:
            pool = [t for t in pool if t.priority in (Priority.HIGH.value, Priority.CRITICAL.value)]
        elif mode == FilterMode.FAVORITES:
            pool = [t for t in pool if t.favorite]
        elif mode == FilterMode.PINNED:
            pool = [t for t in pool if t.pinned]
        # FilterMode.ALL -> no filtering

        if category:
            pool = [t for t in pool if t.category == category]

        return pool

    def search_tasks(self, tasks: list[Task], query: str) -> list[Task]:
        """Live-search across title, category, and priority (case-insensitive)."""
        query = (query or "").strip().lower()
        if not query:
            return tasks
        return [
            t for t in tasks
            if query in t.title.lower()
            or query in t.category.lower()
            or query in t.priority.lower()
            or query in (t.description or "").lower()
        ]

    def sort_tasks(self, tasks: list[Task], mode: SortMode, reverse: bool = False) -> list[Task]:
        def due_key(t: Task):
            return (t.due_datetime is None, t.due_datetime or datetime.max)

        key_funcs = {
            SortMode.DUE_DATE: due_key,
            SortMode.PRIORITY: lambda t: PRIORITY_ORDER.get(t.priority, 99),
            SortMode.ALPHABETICAL: lambda t: t.title.lower(),
            SortMode.DATE_CREATED: lambda t: t.created_at,
            SortMode.COMPLETED: lambda t: t.completed,
        }
        key_func = key_funcs.get(mode, due_key)
        # Pinned tasks always bubble to the top regardless of sort mode.
        sorted_tasks = sorted(tasks, key=key_func, reverse=reverse)
        pinned = [t for t in sorted_tasks if t.pinned]
        unpinned = [t for t in sorted_tasks if not t.pinned]
        return pinned + unpinned

    def get_view(
        self,
        mode: FilterMode = FilterMode.ALL,
        category: Optional[str] = None,
        query: str = "",
        sort: SortMode = SortMode.DUE_DATE,
        reverse: bool = False,
    ) -> list[Task]:
        """One-stop shop: filter -> search -> sort, in that order."""
        result = self.filter_tasks(self._tasks, mode, category)
        result = self.search_tasks(result, query)
        result = self.sort_tasks(result, sort, reverse)
        return result

    # ------------------------------------------------------------
    # Statistics / Dashboard
    # ------------------------------------------------------------
    def get_stats(self) -> dict:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.completed)
        pending = total - completed
        overdue = sum(1 for t in self._tasks if t.is_overdue)
        completion_pct = round((completed / total) * 100, 1) if total else 0.0
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_pct": completion_pct,
        }

    def get_completion_streak(self) -> int:
        """Consecutive days (ending today) with at least one task completed,
        based on each task's updated_at timestamp."""
        completed_dates = set()
        for t in self._tasks:
            if t.completed:
                try:
                    d = datetime.fromisoformat(t.updated_at).date()
                    completed_dates.add(d)
                except ValueError:
                    continue

        streak = 0
        cursor = date.today()
        while cursor in completed_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def get_recently_completed(self, limit: int = 5) -> list[Task]:
        done = [t for t in self._tasks if t.completed]
        done.sort(key=lambda t: t.updated_at, reverse=True)
        return done[:limit]

    # ------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------
    def export_csv(self, path: Path) -> Path:
        path = Path(path)
        fieldnames = [
            "id", "title", "description", "category", "priority",
            "due_date", "due_time", "completed", "pinned", "favorite",
            "created_at", "updated_at",
        ]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in self._tasks:
                    writer.writerow(t.to_dict())
        except OSError as exc:
            raise TaskManagerError(f"Could not export CSV: {exc}") from exc
        return path

    def import_csv(self, path: Path) -> int:
        path = Path(path)
        if not path.exists():
            raise TaskManagerError(f"File not found: {path}")
        imported = 0
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    task = Task(
                        title=row.get("title", "").strip(),
                        description=row.get("description", ""),
                        category=row.get("category") or "Uncategorized",
                        priority=row.get("priority") or Priority.MEDIUM.value,
                        due_date=row.get("due_date") or None,
                        due_time=row.get("due_time") or None,
                        completed=str(row.get("completed", "0")) in ("1", "True", "true"),
                    )
                    if task.title:
                        errors = task.validate()
                        if not errors:
                            self.db.insert_task(task.to_dict())
                            imported += 1
        except (OSError, csv.Error) as exc:
            raise TaskManagerError(f"Could not import CSV: {exc}") from exc
        self.reload()
        self._notify()
        return imported

    def backup_database(self) -> Path:
        try:
            return self.db.backup()
        except DatabaseError as exc:
            raise TaskManagerError(str(exc)) from exc

    def restore_database(self, backup_path: Path) -> None:
        try:
            self.db.restore(backup_path)
        except DatabaseError as exc:
            raise TaskManagerError(str(exc)) from exc
        self.reload()
        self._notify()
