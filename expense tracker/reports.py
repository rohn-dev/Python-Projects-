"""Terminal reports and formatting helpers."""

from __future__ import annotations

import os
from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from expense_tracker.categories import CATEGORIES, get_category
from expense_tracker.models import Expense
from expense_tracker.storage import Storage

console = Console()

CURRENCY = os.environ.get("EXPENSE_CURRENCY", "Rs.")


def fmt_money(amount: float, *, signed: bool = False) -> str:
    if amount == 0:
        return f"{CURRENCY}0.00"
    if signed:
        if amount > 0:
            return f"+{CURRENCY}{amount:,.2f}"
        return f"-{CURRENCY}{abs(amount):,.2f}"
    if amount < 0:
        return f"-{CURRENCY}{abs(amount):,.2f}"
    return f"{CURRENCY}{amount:,.2f}"


def money_style(amount: float) -> str:
    if amount > 0:
        return "green"
    if amount < 0:
        return "red"
    return "dim"


def render_expense_table(expenses: list[Expense], *, title: str = "Expenses") -> None:
    if not expenses:
        console.print("[dim]No expenses found.[/dim]")
        return

    table = Table(title=title, show_lines=False, header_style="bold cyan")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Date", width=11)
    table.add_column("Category", width=18)
    table.add_column("Description", min_width=20)
    table.add_column("Amount", justify="right", width=12)
    table.add_column("Pay", width=8)
    table.add_column("Details", min_width=16)

    for exp in expenses:
        cat = get_category(exp.category)
        details = ", ".join(f"{k}={v}" for k, v in exp.metadata.items() if v)
        if exp.tags:
            details = (details + " | " if details else "") + f"#{', #'.join(exp.tags)}"
        signed = exp.signed_amount()
        table.add_row(
            str(exp.id),
            exp.expense_date.isoformat(),
            f"{cat.icon} {cat.label}",
            exp.description,
            Text(fmt_money(signed, signed=True), style=money_style(signed)),
            exp.payment_method,
            details or "—",
        )
    console.print(table)


def render_category_breakdown(totals: dict[str, float], *, title: str) -> None:
    if not totals:
        console.print("[dim]No data for this period.[/dim]")
        return

    table = Table(title=title, header_style="bold magenta")
    table.add_column("Category", min_width=22)
    table.add_column("Net", justify="right", width=14)
    table.add_column("Share", justify="right", width=8)
    table.add_column("", width=28)

    expense_total = sum(abs(v) for k, v in totals.items() if k != "income" and v < 0)
    income_total = totals.get("income", 0)
    net = sum(totals.values())

    for category_key in sorted(totals, key=lambda k: totals[k]):
        amount = totals[category_key]
        cat = get_category(category_key)
        share = (abs(amount) / expense_total * 100) if expense_total and category_key != "income" else 0
        bar_len = int(share / 4) if category_key != "income" else 0
        bar = "█" * bar_len
        table.add_row(
            f"{cat.icon} {cat.label}",
            Text(fmt_money(amount, signed=True), style=money_style(amount)),
            f"{share:.0f}%" if category_key != "income" else "—",
            f"[red]{bar}[/red]" if bar else "",
        )

    console.print(table)
    console.print(
        Panel(
            f"[bold]Spent:[/bold] {fmt_money(expense_total)}  "
            f"[bold]Income:[/bold] [green]{fmt_money(income_total)}[/green]  "
            f"[bold]Net:[/bold] [{money_style(net)}]{fmt_money(net, signed=True)}[/{money_style(net)}]",
            title="Period Summary",
            border_style="blue",
        )
    )


def render_budget_status(storage: Storage, year: int, month: int) -> None:
    budgets = storage.list_budgets()
    if not budgets:
        console.print("[dim]No budgets set. Use [bold]expense-tracker budget set[/bold].[/dim]")
        return

    table = Table(title=f"Budget Status — {year}-{month:02d}", header_style="bold yellow")
    table.add_column("Category", min_width=22)
    table.add_column("Limit", justify="right")
    table.add_column("Spent", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Status", width=12)

    for budget in budgets:
        spent = storage.category_spend(budget.category, year, month)
        remaining = budget.monthly_limit - spent
        cat = get_category(budget.category)
        if spent > budget.monthly_limit:
            status = Text("OVER", style="bold red")
        elif spent >= budget.monthly_limit * 0.85:
            status = Text("WARN", style="bold yellow")
        else:
            status = Text("OK", style="bold green")
        table.add_row(
            f"{cat.icon} {cat.label}",
            fmt_money(budget.monthly_limit),
            fmt_money(spent),
            fmt_money(max(remaining, 0)),
            status,
        )
    console.print(table)


def render_categories() -> None:
    table = Table(title="Expense Domains", header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("", width=3)
    table.add_column("Category")
    table.add_column("Fields")
    table.add_column("Description", style="dim")

    for cat in CATEGORIES.values():
        fields = ", ".join(
            f"{f.label}{'*' if f.required else ''}" + (f" [{'/'.join(f.choices)}]" if f.choices else "")
            for f in cat.fields
        )
        table.add_row(cat.key, cat.icon, cat.label, fields, cat.description)
    console.print(table)


def month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end
