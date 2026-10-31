"""Reminder commands for Charlie."""

from datetime import datetime, timedelta

import typer
from rich.console import Console

from ..core import get_assistant, require_feature
from ..utils import error, info, print_table, success

app = typer.Typer(name="remind", help="Reminder commands.", rich_markup_mode="rich")
console = Console()


@app.command("add")
def add(
    text: str = typer.Argument(..., help="Reminder message"),
    minutes: int = typer.Option(
        5, "--in", "-m", help="Minutes from now until the reminder fires"
    ),
    hours: int = typer.Option(0, "--hours", "-h", help="Additional hours from now"),
) -> None:
    """Add a new reminder."""
    assistant = get_assistant()
    reminders = require_feature(assistant, "reminders")
    try:
        remind_at = reminders.schedule_in(text, minutes=minutes, hours=hours)
    except ValueError as exc:
        error(str(exc))
        raise typer.Exit(1)
    success(f"Reminder set for {remind_at.strftime('%I:%M %p')}: {text}")


@app.command("list")
def list_reminders(
    all_items: bool = typer.Option(False, "--all", "-a", help="Include triggered reminders"),
) -> None:
    """List reminders."""
    assistant = get_assistant()
    reminders = require_feature(assistant, "reminders")
    items = reminders.reminders
    if not all_items:
        items = [r for r in items if not r["triggered"]]
    if not items:
        info("No reminders found")
        return
    print_table(
        "Reminders",
        ["ID", "Text", "When", "Status"],
        [
            [r["id"], r["text"], r["remind_at"][:16], "done" if r["triggered"] else "pending"]
            for r in items
        ],
    )


if __name__ == "__main__":
    app()