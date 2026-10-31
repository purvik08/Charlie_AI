"""
features.todos — To-do list feature for Charlie.

Provides:
- Add a new to-do item with optional priority
- List all pending (or completed) to-do items
- Mark a task as completed
- Remove a to-do item
- Search to-do items by text
- Registers commands:
  - 'todo.add'      → add a new to-do item
  - 'todo.list'     → list pending to-do items
  - 'todo.done'     → mark a task as completed
  - 'todo.remove'   → remove a to-do item
  - 'todo.search'   → search to-do items
"""

from typing import Any, Dict, List

from core.base import BaseFeature, Command, CommandResult, FeatureConfig


class TodosFeature(BaseFeature):
    """Feature that provides to-do list functionality."""

    @property
    def name(self) -> str:
        return "todo_list"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides to-do list functionality"

    def initialize(self) -> None:
        """Register commands and emit feature ready event."""
        self.register_command(
            Command(
                name="todo.add",
                handler=self._add_todo,
                description="Add a new to-do item",
                aliases=["todo.add"],
            )
        )
        self.register_command(
            Command(
                name="todo.list",
                handler=self._list_todos,
                description="List pending to-do items",
                aliases=["todo.list"],
            )
        )
        self.register_command(
            Command(
                name="todo.done",
                handler=self._mark_done,
                description="Mark a task as completed",
                aliases=["todo.done"],
            )
        )
        self.register_command(
            Command(
                name="todo.remove",
                handler=self._remove_todo,
                description="Remove a to-do item",
                aliases=["todo.remove"],
            )
        )
        self.register_command(
            Command(
                name="todo.search",
                handler=self._search_todos,
                description="Search to-do items",
                aliases=["todo.search"],
            )
        )
        # Emit feature ready event
        from core.events import get_event_bus, Events
        bus = get_event_bus()
        bus.emit(Events.FEATURE_READY, feature=self.name)

    def shutdown(self) -> None:
        """Clean up resources."""
        pass  # no persistent resources

    def _add_todo(self) -> CommandResult:
        """Handler for todo.add command."""
        import typer
        from core.events import get_event_bus, Events

        typer.echo("Enter task description:")
        task = typer.prompt("Task").strip()
        if not task:
            return CommandResult.fail("Task description cannot be empty")

        typer.echo("Priority (low/medium/high):")
        priority = typer.prompt("Priority").strip().lower()
        if priority not in ("low", "medium", "high"):
            priority = "medium"

        from core.assistant import TodoList
        from pathlib import Path

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        todo_list = TodoList(str(data_dir))
        todo_list.add_todo(task, priority)
        return CommandResult.ok(f"Added: {task} [{priority}]")

    def _list_todos(self) -> CommandResult:
        """Handler for todo.list command."""
        from core.assistant import TodoList
        from pathlib import Path

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        todo_list = TodoList(str(data_dir))

        todos = todo_list.list_todos()
        if not todos:
            return CommandResult.ok("No tasks found")

        lines = ["Your Tasks:"]
        for t in todos:
            status = "done" if t["completed"] else "pending"
            lines.append(f"  ID {t['id']}: {t['task']} [{t['priority']}] - {status}")
        return CommandResult.ok("\n".join(lines))

    def _mark_done(self) -> CommandResult:
        """Handler for todo.done command."""
        import typer
        from core.assistant import TodoList
        from pathlib import Path

        typer.echo("Enter task ID to mark as done:")
        task_id_str = typer.prompt("Task ID").strip()
        try:
            task_id = int(task_id_str)
        except ValueError:
            return CommandResult.fail("Invalid task ID")

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        todo_list = TodoList(str(data_dir))

        if todo_list.complete_todo(task_id):
            return CommandResult.ok(f"Task {task_id} completed")
        else:
            return CommandResult.fail(f"Task {task_id} not found")

    def _remove_todo(self) -> CommandResult:
        """Handler for todo.remove command."""
        import typer
        from core.assistant import TodoList
        from pathlib import Path

        typer.echo("Enter task ID to remove:")
        task_id_str = typer.prompt("Task ID").strip()
        try:
            task_id = int(task_id_str)
        except ValueError:
            return CommandResult.fail("Invalid task ID")

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        todo_list = TodoList(str(data_dir))

        if todo_list.remove_todo(task_id):
            return CommandResult.ok(f"Task {task_id} removed")
        else:
            return CommandResult.fail(f"Task {task_id} not found")

    def _search_todos(self) -> CommandResult:
        """Handler for todo.search command."""
        import typer
        from core.assistant import TodoList
        from pathlib import Path

        typer.echo("Search text:")
        query = typer.prompt("Search query").strip()

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        todo_list = TodoList(str(data_dir))

        results = todo_list.search_todos(query)
        if not results:
            return CommandResult.ok(f"No tasks matching '{query}'")

        lines = [f"Tasks matching '{query}':"]
        for t in results:
            status = "done" if t["completed"] else "pending"
            lines.append(f"  ID {t['id']}: {t['task']} [{t['priority']}] - {status}")
        return CommandResult.ok("\n".join(lines))