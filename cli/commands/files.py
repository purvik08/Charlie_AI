"""File search commands for Charlie."""

from typing import List, Optional

import typer
from rich.console import Console

from ..core import get_assistant, require_feature
from ..utils import error, info, print_table

app = typer.Typer(name="file", help="File search commands.", rich_markup_mode="rich")
console = Console()


@app.command("find")
def find(
    query: str = typer.Argument(..., help="Filename substring to search for"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
    file_types: Optional[List[str]] = typer.Option(
        None, "--type", "-t", help="File extensions to include, e.g. .txt"
    ),
) -> None:
    """Search the data directory for files matching query."""
    assistant = get_assistant()
    file_search = require_feature(assistant, "file_search")
    results = file_search.search_files(query, file_types=file_types, max_results=limit)
    if not results:
        info(f"No files found matching '{query}'")
        return
    print_table(
        f"Files matching '{query}'",
        ["Name", "Path", "Size", "Modified"],
        [
            [r["name"], r["path"], r["size"], r["modified"][:16]]
            for r in results
        ],
    )


@app.command("search")
def search_in_file(
    file_path: str = typer.Argument(..., help="Path to the file to search"),
    query: str = typer.Argument(..., help="Text to search for"),
) -> None:
    """Search for text within a single file."""
    assistant = get_assistant()
    require_feature(assistant, "file_search")
    from core.assistant import FileSearch

    file_search = FileSearch(str(assistant.data_dir))
    matches = file_search.search_in_file(file_path, query)
    if not matches:
        info(f"No matches for '{query}' in {file_path}")
        return
    print_table(
        f"Matches in {file_path}",
        ["Line", "Content"],
        [[m["line"], m["text"]] for m in matches],
    )


if __name__ == "__main__":
    app()