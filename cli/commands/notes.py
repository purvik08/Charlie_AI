"""Note-taking commands for Charlie."""

import typer
from rich.console import Console

from ..core import get_assistant, require_feature
from ..utils import error, info, print_table, success

app = typer.Typer(name="note", help="Note-taking commands.", rich_markup_mode="rich")
console = Console()


@app.command("create")
def create(
    title: str = typer.Argument(..., help="Note title"),
    content: str = typer.Argument(..., help="Note content"),
) -> None:
    """Create a new note."""
    assistant = get_assistant()
    note_taking = require_feature(assistant, "note_taking")
    path = note_taking.create_note(title, content)
    success(f"Note created: {path}")


@app.command("list")
def list_notes(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum notes to show"),
) -> None:
    """List recent notes."""
    assistant = get_assistant()
    note_taking = require_feature(assistant, "note_taking")
    notes = note_taking.list_notes(limit=limit)
    if not notes:
        info("No notes found")
        return
    print_table(
        "Notes",
        ["Title", "Created", "Modified"],
        [[n["title"], n["created"][:16], n["modified"][:16]] for n in notes],
    )


@app.command("search")
def search_notes(
    query: str = typer.Argument(..., help="Search text"),
) -> None:
    """Search notes by content."""
    assistant = get_assistant()
    note_taking = require_feature(assistant, "note_taking")
    results = note_taking.search_notes(query)
    if not results:
        info(f"No notes matching '{query}'")
        return
    print_table(
        f"Notes matching '{query}'",
        ["Title", "Path", "Modified"],
        [[r["title"], r["path"], r["modified"][:16]] for r in results],
    )


@app.command("show")
def show_note(
    path: str = typer.Argument(..., help="Path to the note file"),
) -> None:
    """Display the contents of a note."""
    from pathlib import Path

    note_path = Path(path)
    if not note_path.exists():
        error(f"Note not found: {path}")
        raise typer.Exit(1)
    try:
        content = note_path.read_text(encoding="utf-8")
    except OSError as exc:
        error(f"Could not read note: {exc}")
        raise typer.Exit(1)
    console.print(content)


if __name__ == "__main__":
    app()