"""To-do list commands for Charlie."""

import typer
from rich.console import Console

from ..core import get_assistant, require_feature
from ..utils import error, info, print_table, success

app = typer.Typer(name="todo", help="To-do list commands.", rich_markup_mode="rich")
console = Console()

VALID_PRIORITIES = ("low", "medium", "high")


@app.command("add")
def add(
    task: str = typer.Argument(..., help="Task description"),
    priority: str = typer.Option(
        "medium", "--priority", "-p", help="Priority: low, medium, high"
    ),
) -> None:
    """Add a new to-do item."""
    if priority.lower() not in VALID_PRIORITIES:
        error(f"Invalid priority '{priority}'. Choose from: {', '.join(VALID_PRIORITIES)}")
        raise typer.Exit(1)
    assistant = get_assistant()
    todo_list = require_feature(assistant, "todo_list")
    todo_list.add_todo(task, priority.lower())
    success(f"Added: {task} [{priority.lower()}]")


@app.command("list")
def list_todos(
    all_tasks: bool = typer.Option(False, "--all", "-a", help="Include completed tasks"),
) -> None:
    """List to-do items."""
    assistant = get_assistant()
    todo_list = require_feature(assistant, "todo_list")
    todos = todo_list.list_todos(show_completed=all_tasks)
    if not todos:
        info("No tasks found")
        return
    print_table(
        "To-Do List",
        ["ID", "Task", "Priority", "Status", "Created"],
        [
            [
                t["id"],
                t["task"],
                t["priority"],
                "done" if t["completed"] else "pending",
                t["created"][:16],
            ]
            for t in todos
        ],
    )


@app.command("done")
def done(
    task_id: int = typer.Argument(..., help="Task ID to mark complete"),
) -> None:
    """Mark a task as completed."""
    assistant = get_assistant()
    todo_list = require_feature(assistant, "todo_list")
    if todo_list.complete_todo(task_id):
        success(f"Task {task_id} completed")
    else:
        error(f"Task {task_id} not found")
        raise typer.Exit(1)


@app.command("remove")
def remove(
    task_id: int = typer.Argument(..., help="Task ID to remove"),
) -> None:
    """Remove a task."""
    assistant = get_assistant()
    todo_list = require_feature(assistant, "todo_list")
    if todo_list.remove_todo(task_id):
        success(f"Task {task_id} removed")
    else:
        error(f"Task {task_id} not found")
        raise typer.Exit(1)


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search text"),
) -> None:
    """Search tasks."""
    assistant = get_assistant()
    todo_list = require_feature(assistant, "todo_list")
    results = todo_list.search_todos(query)
    if not results:
        info(f"No tasks matching '{query}'")
        return
    print_table(
        f"Tasks matching '{query}'",
        ["ID", "Task", "Priority", "Status"],
        [
            [t["id"], t["task"], t["priority"], "done" if t["completed"] else "pending"]
            for t in results
        ],
    )


if __name__ == "__main__":
    app()