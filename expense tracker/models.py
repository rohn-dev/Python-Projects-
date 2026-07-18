"""Core data models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class Expense:
    amount: float
    category: str
    description: str
    expense_date: date
    payment_method: str = "cash"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    id: int | None = None
    created_at: datetime | None = None

    def to_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "expense_date": self.expense_date.isoformat(),
            "payment_method": self.payment_method,
            "tags": json.dumps(self.tags),
            "metadata": json.dumps(self.metadata),
            "created_at": (self.created_at or datetime.now()).isoformat(),
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Expense:
        return cls(
            id=row["id"],
            amount=float(row["amount"]),
            category=row["category"],
            description=row["description"],
            expense_date=date.fromisoformat(row["expense_date"]),
            payment_method=row["payment_method"],
            tags=json.loads(row["tags"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )

    def signed_amount(self) -> float:
        return self.amount if self.category == "income" else -abs(self.amount)


@dataclass
class Budget:
    category: str
    monthly_limit: float
    id: int | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Budget:
        return cls(id=row["id"], category=row["category"], monthly_limit=float(row["monthly_limit"]))

    def to_row(self) -> dict[str, Any]:
        return asdict(self)
