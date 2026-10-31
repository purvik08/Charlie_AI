"""
features.notes — Note-taking feature for Charlie.

Provides:
- Create notes with title and content
- List recent notes
- Search notes by content
- Show note contents
- Registers commands:
  - 'note.create'  → create a new note
  - 'note.list'    → list recent notes
  - 'note.search'  → search notes by content
  - 'note.show'    → show note contents
"""

from typing import Any, Dict, List

from core.base import BaseFeature, Command, CommandResult, FeatureConfig


class NotesFeature(BaseFeature):
    """Feature that provides note-taking functionality."""

    @property
    def name(self) -> str:
        return "notes"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides note-taking functionality"

    def initialize(self) -> None:
        """Register commands and emit feature ready event."""
        self.register_command(
            Command(
                name="note.create",
                handler=self._create_note,
                description="Create a new note",
                aliases=["note.create"],
            )
        )
        self.register_command(
            Command(
                name="note.list",
                handler=self._list_notes,
                description="List recent notes",
                aliases=["note.list"],
            )
        )
        self.register_command(
            Command(
                name="note.search",
                handler=self._search_notes,
                description="Search notes by content",
                aliases=["note.search"],
            )
        )
        self.register_command(
            Command(
                name="note.show",
                handler=self._show_note,
                description="Show note contents",
                aliases=["note.show"],
            )
        )
        # Emit feature ready event
        from core.events import get_event_bus, Events
        bus = get_event_bus()
        bus.emit(Events.FEATURE_READY, feature=self.name)

    def shutdown(self) -> None:
        """Clean up resources."""
        pass  # no persistent resources

    def _create_note(self) -> CommandResult:
        """Handler for note.create command."""
        import typer
        from core.events import get_event_bus, Events

        typer.echo("Enter note title:")
        title = typer.prompt("Title").strip()
        if not title:
            return CommandResult.fail("Title cannot be empty")

        typer.echo("Enter note content:")
        content = typer.prompt("Content").strip()

        # Use the existing assistant NoteTaking
        from core.assistant import NoteTaking
        from pathlib import Path

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        note_taking = NoteTaking(str(data_dir))

        file_path = note_taking.create_note(title, content)
        return CommandResult.ok(f"Note created: {Path(file_path).name}")

    def _list_notes(self) -> CommandResult:
        """Handler for note.list command."""
        from core.assistant import NoteTaking
        from pathlib import Path

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        note_taking = NoteTaking(str(data_dir))

        notes = note_taking.list_notes()
        if not notes:
            return CommandResult.ok("No notes found")

        lines = ["Your Notes:"]
        for n in notes[:5]:
            lines.append(f"  {n['title']} - {n['created'][:16]}")
        return CommandResult.ok("\n".join(lines))

    def _search_notes(self) -> CommandResult:
        """Handler for note.search command."""
        import typer
        from core.assistant import NoteTaking
        from pathlib import Path

        typer.echo("Search text:")
        query = typer.prompt("Search query").strip()

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        note_taking = NoteTaking(str(data_dir))

        results = note_taking.search_notes(query)
        if not results:
            return CommandResult.ok(f"No notes matching '{query}'")

        lines = [f"Notes matching '{query}':"]
        for r in results[:5]:
            lines.append(f"  {r['title']} - {r['modified'][:16]}")
        return CommandResult.ok("\n".join(lines))

    def _show_note(self) -> CommandResult:
        """Handler for note.show command."""
        import typer
        from pathlib import Path

        typer.echo("Enter note path or title:")
        path_or_title = typer.prompt("Path or title").strip()

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)

        # Try to find the note file
        note_path = data_dir / path_or_title
        if not note_path.exists():
            # Try as title search
            from core.assistant import NoteTaking
            note_taking = NoteTaking(str(data_dir))
            notes = note_taking.list_notes(limit=50)
            found = None
            for n in notes:
                if n["title"] == path_or_title:
                    found = n
                    break
            if not found:
                return CommandResult.ok(f"Note not found: {path_or_title}")
            note_path = Path(found["path"])

        try:
            content = note_path.read_text(encoding="utf-8")
            return CommandResult.ok(content)
        except Exception as exc:
            return CommandResult.fail(f"Could not read note: {exc}")