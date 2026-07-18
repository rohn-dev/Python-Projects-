"""SQLite persistence layer."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator

from expense_tracker.models import Budget, Expense

DEFAULT_DB = Path.home() / ".expense-tracker" / "expenses.db"


class Storage:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    payment_method TEXT NOT NULL DEFAULT 'cash',
                    tags TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL UNIQUE,
                    monthly_limit REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
                CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
                """
            )

    def add_expense(self, expense: Expense) -> Expense:
        row = expense.to_row()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses (amount, category, description, expense_date,
                                      payment_method, tags, metadata, created_at)
                VALUES (:amount, :category, :description, :expense_date,
                        :payment_method, :tags, :metadata, :created_at)
                """,
                row,
            )
            expense.id = cursor.lastrowid
        return expense

    def delete_expense(self, expense_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cursor.rowcount > 0

    def get_expense(self, expense_id: int) -> Expense | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        return Expense.from_row(dict(row)) if row else None

    def list_expenses(
        self,
        *,
        category: str | None = None,
        start: date | None = None,
        end: date | None = None,
        search: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        limit: int | None = None,
    ) -> list[Expense]:
        clauses: list[str] = []
        params: list[object] = []

        if category:
            clauses.append("category = ?")
            params.append(category)
        if start:
            clauses.append("expense_date >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append("expense_date <= ?")
            params.append(end.isoformat())
        if search:
            clauses.append("(description LIKE ? OR tags LIKE ? OR metadata LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
        if min_amount is not None:
            clauses.append("amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            clauses.append("amount <= ?")
            params.append(max_amount)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        limit_clause = f"LIMIT {int(limit)}" if limit else ""

        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM expenses {where} ORDER BY expense_date DESC, id DESC {limit_clause}",
                params,
            ).fetchall()
        return [Expense.from_row(dict(r)) for r in rows]

    def category_totals(
        self,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> dict[str, float]:
        clauses: list[str] = []
        params: list[object] = []
        if start:
            clauses.append("expense_date >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append("expense_date <= ?")
            params.append(end.isoformat())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT category,
                       SUM(CASE WHEN category = 'income' THEN amount ELSE -ABS(amount) END) AS total
                FROM expenses {where}
                GROUP BY category
                ORDER BY total ASC
                """,
                params,
            ).fetchall()
        return {row["category"]: float(row["total"]) for row in rows}

    def monthly_net(self, year: int, month: int) -> float:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT SUM(CASE WHEN category = 'income' THEN amount ELSE -ABS(amount) END) AS net
                FROM expenses
                WHERE expense_date >= ? AND expense_date < ?
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchone()
        return float(row["net"] or 0)

    def category_spend(self, category: str, year: int, month: int) -> float:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT SUM(ABS(amount)) AS spent
                FROM expenses
                WHERE category = ? AND category != 'income'
                  AND expense_date >= ? AND expense_date < ?
                """,
                (category, start.isoformat(), end.isoformat()),
            ).fetchone()
        return float(row["spent"] or 0)

    def set_budget(self, budget: Budget) -> Budget:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO budgets (category, monthly_limit)
                VALUES (?, ?)
                ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit
                """,
                (budget.category, budget.monthly_limit),
            )
            row = conn.execute(
                "SELECT * FROM budgets WHERE category = ?", (budget.category,)
            ).fetchone()
        return Budget.from_row(dict(row))

    def list_budgets(self) -> list[Budget]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()
        return [Budget.from_row(dict(r)) for r in rows]

    def delete_budget(self, category: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
            return cursor.rowcount > 0
