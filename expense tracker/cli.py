"""CLI entry point — commands for tracking expenses across domains."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, Prompt
from rich.table import Table

from expense_tracker.categories import (
    CATEGORIES,
    PAYMENT_METHODS,
    get_category,
    resolve_category,
)
from expense_tracker.models import Budget, Expense
from expense_tracker.reports import (
    fmt_money,
    month_range,
    render_budget_status,
    render_categories,
    render_category_breakdown,
    render_expense_table,
)
from expense_tracker.storage import Storage

app = typer.Typer(
    name="expense-tracker",
    help="Sharp CLI expense tracker — food, transport, housing, travel, and more.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
budget_app = typer.Typer(help="Set and monitor monthly category budgets.")
app.add_typer(budget_app, name="budget")

console = Console()


def _configure_stdio() -> None:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            reconfigure = getattr(stream, "reconfigure", None)
            if reconfigure:
                try:
                    reconfigure(encoding="utf-8")
                except (OSError, ValueError):
                    pass


_configure_stdio()


def get_storage(db: Path | None) -> Storage:
    return Storage(db)


def parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise typer.BadParameter(f"Invalid date '{value}'. Use YYYY-MM-DD.")


def parse_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [t.strip().lstrip("#") for t in value.replace(",", " ").split() if t.strip()]


def collect_metadata(category_key: str, interactive: bool, meta_json: str | None) -> dict[str, str]:
    if meta_json:
        try:
            data = json.loads(meta_json)
            if not isinstance(data, dict):
                raise typer.BadParameter("metadata must be a JSON object.")
            return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"Invalid metadata JSON: {exc}") from exc

    cat = get_category(category_key)
    metadata: dict[str, str] = {}
    if not interactive or not cat.fields:
        return metadata

    console.print(f"\n[bold cyan]{cat.icon} {cat.label}[/bold cyan] — category fields")
    for field in cat.fields:
        suffix = " *" if field.required else ""
        if field.choices:
            choice_str = "/".join(field.choices)
            value = Prompt.ask(f"  {field.label}{suffix}", default="" if not field.required else field.choices[0])
            if value and value not in field.choices:
                close = [c for c in field.choices if value.lower() in c.lower()]
                value = close[0] if len(close) == 1 else value
        else:
            value = Prompt.ask(f"  {field.label}{suffix}", default="")
        if field.required and not value.strip():
            console.print(f"[red]{field.label} is required.[/red]")
            raise typer.Exit(1)
        if value.strip():
            metadata[field.key] = value.strip()
    return metadata


def build_expense(
    *,
    amount: float,
    category: str,
    description: str,
    expense_date: date,
    payment: str,
    tags: list[str],
    metadata: dict[str, str],
) -> Expense:
    cat = resolve_category(category)
    if payment not in PAYMENT_METHODS:
        raise typer.BadParameter(f"Invalid payment method. Choose: {', '.join(PAYMENT_METHODS)}")
    for field in cat.fields:
        if field.required and not metadata.get(field.key):
            raise typer.BadParameter(f"Missing required field '{field.key}' for category '{cat.key}'.")
        if field.key in metadata and field.choices and metadata[field.key] not in field.choices:
            raise typer.BadParameter(
                f"Invalid {field.key} '{metadata[field.key]}'. Choices: {', '.join(field.choices)}"
            )
    return Expense(
        amount=abs(amount),
        category=cat.key,
        description=description.strip(),
        expense_date=expense_date,
        payment_method=payment,
        tags=tags,
        metadata=metadata,
    )


@app.command("add")
def add_expense(
    amount: Annotated[float, typer.Option("--amount", "-a", help="Amount in your currency.")],
    category: Annotated[str, typer.Option("--category", "-c", help="Category key or label.")],
    description: Annotated[str, typer.Option("--description", "-d", help="What was this for?")],
    expense_date: Annotated[
        Optional[str], typer.Option("--date", help="Expense date (YYYY-MM-DD). Defaults to today.")
    ] = None,
    payment: Annotated[str, typer.Option("--payment", "-p", help="Payment method.")] = "cash",
    tags: Annotated[Optional[str], typer.Option("--tags", "-t", help="Comma/space separated tags.")] = None,
    metadata: Annotated[
        Optional[str], typer.Option("--meta", help='Category fields as JSON, e.g. {"subcategory":"groceries"}')
    ] = None,
    interactive: Annotated[bool, typer.Option("--interactive/--no-interactive", "-i", help="Prompt for category fields.")] = True,
    db: Annotated[Optional[Path], typer.Option("--db", help="Custom database path.")] = None,
) -> None:
    """Record a new expense (or income)."""
    parsed_date = parse_date(expense_date) if expense_date else date.today()
    meta = collect_metadata(resolve_category(category).key, interactive and not metadata, metadata)
    expense = build_expense(
        amount=amount,
        category=category,
        description=description,
        expense_date=parsed_date,
        payment=payment,
        tags=parse_tags(tags),
        metadata=meta,
    )
    storage = get_storage(db)
    saved = storage.add_expense(expense)
    cat = get_category(saved.category)
    signed = saved.signed_amount()
    console.print(
        f"[green]✓[/green] Saved #{saved.id} — {cat.icon} [bold]{saved.description}[/bold] "
        f"[{('green' if signed > 0 else 'red')}]{fmt_money(signed, signed=True)}[/{('green' if signed > 0 else 'red')}] "
        f"on {saved.expense_date}"
    )


@app.command("quick")
def quick_add(
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Interactive wizard — fastest way to log an expense."""
    console.print("\n[bold]Quick Add Expense[/bold]\n")

    table = Table(show_header=False, box=None, padding=(0, 2))
    for cat in CATEGORIES.values():
        table.add_row(f"[cyan]{cat.key:12}[/cyan]", cat.icon, cat.label)
    console.print(table)

    category = Prompt.ask("\nCategory")
    amount = FloatPrompt.ask("Amount")
    description = Prompt.ask("Description")
    date_str = Prompt.ask("Date (YYYY-MM-DD)", default=date.today().isoformat())
    payment = Prompt.ask("Payment method", choices=PAYMENT_METHODS, default="cash")
    tags_raw = Prompt.ask("Tags (optional)", default="")

    meta = collect_metadata(resolve_category(category).key, True, None)
    expense = build_expense(
        amount=amount,
        category=category,
        description=description,
        expense_date=parse_date(date_str),
        payment=payment,
        tags=parse_tags(tags_raw),
        metadata=meta,
    )
    saved = get_storage(db).add_expense(expense)
    console.print(f"\n[green]✓ Logged expense #{saved.id}[/green]")


@app.command("list")
def list_expenses(
    category: Annotated[Optional[str], typer.Option("--category", "-c")] = None,
    month: Annotated[Optional[str], typer.Option("--month", "-m", help="Filter by YYYY-MM.")] = None,
    from_date: Annotated[Optional[str], typer.Option("--from", help="Start date YYYY-MM-DD.")] = None,
    to_date: Annotated[Optional[str], typer.Option("--to", help="End date YYYY-MM-DD.")] = None,
    search: Annotated[Optional[str], typer.Option("--search", "-s")] = None,
    min_amount: Annotated[Optional[float], typer.Option("--min")] = None,
    max_amount: Annotated[Optional[float], typer.Option("--max")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 50,
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """List expenses with filters."""
    start = parse_date(from_date) if from_date else None
    end = parse_date(to_date) if to_date else None
    if month:
        try:
            y, m = map(int, month.split("-"))
            start, end = month_range(y, m)
            end = end.fromordinal(end.toordinal() - 1)
        except ValueError as exc:
            raise typer.BadParameter("Month must be YYYY-MM.") from exc

    cat_key = resolve_category(category).key if category else None
    expenses = get_storage(db).list_expenses(
        category=cat_key,
        start=start,
        end=end,
        search=search,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit,
    )
    title = "Expenses"
    if month:
        title += f" — {month}"
    elif start or end:
        title += f" — {start or '…'} → {end or '…'}"
    render_expense_table(expenses, title=title)


@app.command("show")
def show_expense(
    expense_id: Annotated[int, typer.Argument(help="Expense ID.")],
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Show full details for one expense."""
    expense = get_storage(db).get_expense(expense_id)
    if not expense:
        console.print(f"[red]Expense #{expense_id} not found.[/red]")
        raise typer.Exit(1)
    render_expense_table([expense], title=f"Expense #{expense_id}")


@app.command("delete")
def delete_expense(
    expense_id: Annotated[int, typer.Argument()],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation.")] = False,
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Delete an expense by ID."""
    storage = get_storage(db)
    expense = storage.get_expense(expense_id)
    if not expense:
        console.print(f"[red]Expense #{expense_id} not found.[/red]")
        raise typer.Exit(1)
    if not force and not Confirm.ask(f"Delete #{expense_id} '{expense.description}' ({fmt_money(expense.amount)})?"):
        raise typer.Exit(0)
    storage.delete_expense(expense_id)
    console.print(f"[green]✓ Deleted expense #{expense_id}[/green]")


@app.command("summary")
def summary(
    month: Annotated[Optional[str], typer.Option("--month", "-m", help="YYYY-MM (default: current month).")] = None,
    from_date: Annotated[Optional[str], typer.Option("--from")] = None,
    to_date: Annotated[Optional[str], typer.Option("--to")] = None,
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Category breakdown and net totals."""
    start = parse_date(from_date) if from_date else None
    end = parse_date(to_date) if to_date else None
    label = "Summary"

    if month:
        y, m = map(int, month.split("-"))
        start, end_exclusive = month_range(y, m)
        end = end_exclusive.fromordinal(end_exclusive.toordinal() - 1)
        label = f"Summary — {month}"
    elif not start and not end:
        today = date.today()
        start, end_exclusive = month_range(today.year, today.month)
        end = end_exclusive.fromordinal(end_exclusive.toordinal() - 1)
        label = f"Summary — {today.year}-{today.month:02d}"

    totals = get_storage(db).category_totals(start=start, end=end)
    render_category_breakdown(totals, title=label)


@app.command("categories")
def categories_cmd() -> None:
    """Show all expense domains and their fields."""
    render_categories()


@app.command("export")
def export_data(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output JSON file.")],
    month: Annotated[Optional[str], typer.Option("--month", "-m")] = None,
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Export expenses to JSON."""
    start = end = None
    if month:
        y, m = map(int, month.split("-"))
        start, end_exclusive = month_range(y, m)
        end = end_exclusive.fromordinal(end_exclusive.toordinal() - 1)

    expenses = get_storage(db).list_expenses(start=start, end=end)
    payload = [
        {
            "id": e.id,
            "amount": e.amount,
            "category": e.category,
            "description": e.description,
            "date": e.expense_date.isoformat(),
            "payment_method": e.payment_method,
            "tags": e.tags,
            "metadata": e.metadata,
        }
        for e in expenses
    ]
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    console.print(f"[green]✓ Exported {len(payload)} records → {output}[/green]")


@budget_app.command("set")
def budget_set(
    category: Annotated[str, typer.Argument(help="Category key.")],
    limit: Annotated[float, typer.Argument(help="Monthly spending limit.")],
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Set a monthly budget for a category."""
    cat = resolve_category(category)
    if cat.key == "income":
        raise typer.BadParameter("Budgets don't apply to income.")
    budget = get_storage(db).set_budget(Budget(category=cat.key, monthly_limit=limit))
    console.print(f"[green]✓[/green] {cat.icon} {cat.label} budget → {fmt_money(budget.monthly_limit)}/month")


@budget_app.command("list")
def budget_list(
    month: Annotated[Optional[str], typer.Option("--month", "-m")] = None,
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Show budget limits and current month spend."""
    today = date.today()
    if month:
        y, m = map(int, month.split("-"))
    else:
        y, m = today.year, today.month
    render_budget_status(get_storage(db), y, m)


@budget_app.command("remove")
def budget_remove(
    category: Annotated[str, typer.Argument()],
    db: Annotated[Optional[Path], typer.Option("--db")] = None,
) -> None:
    """Remove a category budget."""
    cat = resolve_category(category)
    if get_storage(db).delete_budget(cat.key):
        console.print(f"[green]✓ Removed budget for {cat.label}[/green]")
    else:
        console.print(f"[yellow]No budget set for {cat.label}[/yellow]")


def main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled.[/dim]")
        sys.exit(130)


if __name__ == "__main__":
    main()
