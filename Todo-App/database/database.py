"""
database/database.py
---------------------
Low-level SQLite access layer. Responsible ONLY for talking to the
database: schema creation, connections, and raw CRUD statements.

Business rules (validation, filtering semantics, undo stacks, etc.)
deliberately do NOT live here — see services/task_manager.py.
"""

from __future__ import annotations

import sqlite3
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from utils.constants import DB_PATH, BACKUP_DIR, DEFAULT_CATEGORIES


class DatabaseError(Exception):
    """Raised when a database operation fails, wrapping the underlying cause."""


class Database:
    """Thin, defensive wrapper around a single SQLite database file."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------
    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(f"Database operation failed: {exc}") from exc
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    title         TEXT NOT NULL,
                    description   TEXT DEFAULT '',
                    category      TEXT DEFAULT 'Uncategorized',
                    priority      TEXT DEFAULT 'Medium',
                    due_date      TEXT,
                    due_time      TEXT,
                    completed     INTEGER DEFAULT 0,
                    pinned        INTEGER DEFAULT 0,
                    favorite      INTEGER DEFAULT 0,
                    created_at    TEXT NOT NULL,
                    updated_at    TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    name  TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#5B8DEF'
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);
                CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
                CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
                """
            )
            self._migrate_add_missing_columns(conn)
            self._seed_default_categories(conn)

    def _migrate_add_missing_columns(self, conn: sqlite3.Connection) -> None:
        """Lightweight forward-migration: add columns introduced in later
        versions if an older tasks.db is opened, without wiping data."""
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
        migrations = {
            "pinned": "ALTER TABLE tasks ADD COLUMN pinned INTEGER DEFAULT 0",
            "favorite": "ALTER TABLE tasks ADD COLUMN favorite INTEGER DEFAULT 0",
        }
        for col, statement in migrations.items():
            if col not in existing_cols:
                conn.execute(statement)

    def _seed_default_categories(self, conn: sqlite3.Connection) -> None:
        count = conn.execute("SELECT COUNT(*) AS c FROM categories").fetchone()["c"]
        if count == 0:
            from utils.constants import CATEGORY_COLORS
            for name in DEFAULT_CATEGORIES:
                conn.execute(
                    "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
                    (name, CATEGORY_COLORS.get(name, "#5B8DEF")),
                )

    # ------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------
    def insert_task(self, data: dict) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks
                    (title, description, category, priority, due_date, due_time,
                     completed, pinned, favorite, created_at, updated_at)
                VALUES (:title, :description, :category, :priority, :due_date, :due_time,
                        :completed, :pinned, :favorite, :created_at, :updated_at)
                """,
                data,
            )
            return int(cur.lastrowid)

    def update_task(self, task_id: int, data: dict) -> None:
        data = dict(data)
        data["id"] = task_id
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tasks SET
                    title = :title,
                    description = :description,
                    category = :category,
                    priority = :priority,
                    due_date = :due_date,
                    due_time = :due_time,
                    completed = :completed,
                    pinned = :pinned,
                    favorite = :favorite,
                    updated_at = :updated_at
                WHERE id = :id
                """,
                data,
            )

    def delete_task(self, task_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def bulk_delete(self, task_ids: list[int]) -> None:
        if not task_ids:
            return
        with self._connect() as conn:
            placeholders = ",".join("?" for _ in task_ids)
            conn.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", task_ids)

    def clear_completed(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE completed = 1")
            return cur.rowcount

    def get_all_tasks(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def get_task(self, task_id: int) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def reinsert_task(self, data: dict) -> int:
        """Used by 'undo delete' to restore a task with its original id if possible."""
        with self._connect() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO tasks
                        (id, title, description, category, priority, due_date, due_time,
                         completed, pinned, favorite, created_at, updated_at)
                    VALUES (:id, :title, :description, :category, :priority, :due_date, :due_time,
                            :completed, :pinned, :favorite, :created_at, :updated_at)
                    """,
                    data,
                )
                return int(cur.lastrowid)
            except sqlite3.IntegrityError:
                # id already reused — insert as a new row instead
                data = dict(data)
                data.pop("id", None)
                cur = conn.execute(
                    """
                    INSERT INTO tasks
                        (title, description, category, priority, due_date, due_time,
                         completed, pinned, favorite, created_at, updated_at)
                    VALUES (:title, :description, :category, :priority, :due_date, :due_time,
                            :completed, :pinned, :favorite, :created_at, :updated_at)
                    """,
                    data,
                )
                return int(cur.lastrowid)

    # ------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------
    def get_categories(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM categories ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    def add_category(self, name: str, color: str = "#5B8DEF") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
                (name.strip(), color),
            )

    def delete_category(self, name: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM categories WHERE name = ?", (name,))

    # ------------------------------------------------------------
    # Backup / Restore
    # ------------------------------------------------------------
    def backup(self, destination: Optional[Path] = None) -> Path:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if destination is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination = BACKUP_DIR / f"tasks_backup_{stamp}.db"
        try:
            shutil.copy2(self.db_path, destination)
        except OSError as exc:
            raise DatabaseError(f"Backup failed: {exc}") from exc
        return destination

    def restore(self, backup_path: Path) -> None:
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise DatabaseError(f"Backup file not found: {backup_path}")
        try:
            shutil.copy2(backup_path, self.db_path)
        except OSError as exc:
            raise DatabaseError(f"Restore failed: {exc}") from exc
