"""Time and date commands for Charlie."""

import typer

time_app = typer.Typer(name="time", help="Show current time.", rich_markup_mode="rich")
date_app = typer.Typer(name="date", help="Show current date.", rich_markup_mode="rich")


@time_app.command("now")
def now() -> None:
    """Show the current time."""
    from datetime import datetime

    from rich.console import Console

    console = Console()
    console.print(f"[cyan]{datetime.now().strftime('%I:%M %p')}[/cyan]")


@time_app.command("full")
def time_full() -> None:
    """Show the current time including seconds."""
    from datetime import datetime

    from rich.console import Console

    console = Console()
    console.print(f"[cyan]{datetime.now().strftime('%I:%M:%S %p')}[/cyan]")


@date_app.command("today")
def today() -> None:
    """Show today's date."""
    from datetime import datetime

    from rich.console import Console

    console = Console()
    console.print(f"[cyan]{datetime.now().strftime('%A, %B %d, %Y')}[/cyan]")


@date_app.command("full")
def date_full() -> None:
    """Show today's date with time."""
    from datetime import datetime

    from rich.console import Console

    console = Console()
    console.print(
        f"[cyan]{datetime.now().strftime('%A, %B %d, %Y %I:%M %p')}[/cyan]"
    )