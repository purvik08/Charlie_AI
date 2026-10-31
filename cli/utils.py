"""Rich output helpers for the Charlie CLI."""

from typing import Any, Dict, List, Optional, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_table(
    title: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> None:
    """Render a table with the given columns and rows."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(str(col), overflow="fold")
    for row in rows:
        table.add_row(*(str(cell) for cell in row))
    console.print(table)


def print_kv(data: Dict[str, Any], title: Optional[str] = None) -> None:
    """Render a dict as labeled key/value lines."""
    if title:
        console.print(f"[bold]{title}[/bold]")
    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")


def print_panel(content: str, title: Optional[str] = None, style: str = "green") -> None:
    """Render a panel with the given content."""
    console.print(Panel(content, title=title, border_style=style, expand=False))


def success(msg: str) -> None:
    console.print(f"[green][+] {msg}[/green]")


def error(msg: str) -> None:
    console.print(f"[red][x] {msg}[/red]")


def warning(msg: str) -> None:
    console.print(f"[yellow][!] {msg}[/yellow]")


def info(msg: str) -> None:
    console.print(f"[blue][i] {msg}[/blue]")