"""Application commands for Charlie."""

import typer
from rich.console import Console

from ..core import get_assistant
from ..utils import error, success

app = typer.Typer(name="app", help="Application commands.", rich_markup_mode="rich")
console = Console()


@app.command("open")
def open_app(
    app_name: str = typer.Argument(..., help="Application or folder name from the allowlist"),
) -> None:
    """Open an allowlisted application or folder."""
    assistant = get_assistant()
    name = app_name.strip().lower()
    if name in assistant.ALLOWED_FOLDERS:
        message = assistant._open_folder(name)
    else:
        message = assistant._launch_application(name)
    if message.startswith(("Opening",)):
        success(message)
    else:
        error(message)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
