"""Web search and research commands for Charlie using GPT Researcher."""

import typer
from rich.console import Console

from ..core import get_assistant, require_feature
from ..utils import error, info

app = typer.Typer(name="search", help="Web search and research commands.", rich_markup_mode="rich")
console = Console()


@app.callback(invoke_without_command=True)
def default_search(
    ctx: typer.Context,
    query: str = typer.Argument(None, help="The query or topic to search for on the web"),
) -> None:
    """Search the web for up-to-date information."""
    if query is None:
        if ctx.invoked_subcommand is None:
            query = typer.prompt("Search query").strip()
        else:
            return

    assistant = get_assistant()
    web_search = require_feature(assistant, "web_search")

    with console.status(f"[bold cyan]Searching the web for '{query}'...[/bold cyan]"):
        result = web_search.search(query, model_manager=getattr(assistant, "model_manager", None))

    console.print(result)
