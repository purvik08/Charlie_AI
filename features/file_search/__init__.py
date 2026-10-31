"""
features.file_search — File search feature for Charlie.

Provides:
- Search for files in the data directory by name
- Search for text within a single file
- Registers commands:
  - 'file.find'    → search for files by name
  - 'file.search'  → search for text within a file
"""

from typing import Any, Dict, List

from core.base import BaseFeature, Command, CommandResult, FeatureConfig


class FileSearchFeature(BaseFeature):
    """Feature that provides file search functionality."""

    @property
    def name(self) -> str:
        return "file_search"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides file search functionality"

    def initialize(self) -> None:
        """Register commands and emit feature ready event."""
        self.register_command(
            Command(
                name="file.find",
                handler=self._find_files,
                description="Search for files by name",
                aliases=["file.find"],
            )
        )
        self.register_command(
            Command(
                name="file.search",
                handler=self._search_in_file,
                description="Search for text within a file",
                aliases=["file.search"],
            )
        )
        # Emit feature ready event
        from core.events import get_event_bus, Events
        bus = get_event_bus()
        bus.emit(Events.FEATURE_READY, feature=self.name)

    def shutdown(self) -> None:
        """Clean up resources."""
        pass  # no persistent resources

    def _find_files(self) -> CommandResult:
        """Handler for file.find command."""
        import typer
        from core.assistant import FileSearch
        from pathlib import Path
        from core.events import get_event_bus, Events

        typer.echo("Search query:")
        query = typer.prompt("Query").strip()

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        file_search = FileSearch(str(data_dir))

        results = file_search.search_files(query)
        if not results:
            return CommandResult.ok(f"No files found matching '{query}'")

        lines = [f"Found {len(results)} files matching '{query}':"]
        for r in results[:10]:
            lines.append(f"  {r['name']} - {r['modified'][:16]}")
        return CommandResult.ok("\n".join(lines))

    def _search_in_file(self) -> CommandResult:
        """Handler for file.search command."""
        import typer
        from core.assistant import FileSearch
        from pathlib import Path

        typer.echo("File path:")
        file_path = typer.prompt("File path").strip()

        typer.echo("Search query:")
        query = typer.prompt("Query").strip()

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        file_search = FileSearch(str(data_dir))

        # Check if file exists in data_dir
        full_path = Path(file_path)
        if not full_path.exists():
            # Try in data_dir
            alternative = data_dir / full_path.name
            if alternative.exists():
                full_path = alternative
            else:
                return CommandResult.ok(f"File not found: {file_path}")

        results = file_search.search_in_file(str(full_path), query)
        if not results:
            return CommandResult.ok(f"No matches found in {full_path.name}")

        lines = [f"Matches in {full_path.name}:"]
        for r in results[:10]:
            lines.append(f"  Line {r['line']}: {r['text'][:60]}")
        return CommandResult.ok("\n".join(lines))