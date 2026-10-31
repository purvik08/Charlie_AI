import tempfile
import os
from pathlib import Path
import sys
import json
import time

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.assistant import TodoList

def test_todo_list_initialization():
    """Test that TodoList initializes correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        todo = TodoList(str(data_dir))
        expected_todo_file = data_dir / "todo.json"
        assert todo.todo_file == expected_todo_file
        assert isinstance(todo.todos, list)

def test_todo_list_add_todo():
    """Test that TodoList can add to-do items"""
    with tempfile.TemporaryDirectory() as tmpdir:
        todo = TodoList(tmpdir)

        # Add a to-do item
        todo.add_todo("Test task", "high")

        # Check that it was added
        assert len(todo.todos) == 1
        todo_item = todo.todos[0]
        assert todo_item["task"] == "Test task"
        assert todo_item["priority"] == "high"
        assert todo_item["completed"] == False
        assert "id" in todo_item
        assert "created" in todo_item
        assert todo_item["completed_at"] is None

def test_todo_list_complete_todo():
    """Test that TodoList can mark to-do items as completed"""
    with tempfile.TemporaryDirectory() as tmpdir:
        todo = TodoList(tmpdir)

        # Add a to-do item
        todo.add_todo("Test task")
        todo_id = todo.todos[0]["id"]

        # Mark it as completed
        result = todo.complete_todo(todo_id)
        assert result == True

        # Check that it's marked as completed
        assert todo.todos[0]["completed"] == True
        assert todo.todos[0]["completed_at"] is not None

def test_todo_list_remove_todo():
    """Test that TodoList can remove to-do items"""
    with tempfile.TemporaryDirectory() as tmpdir:
        todo = TodoList(tmpdir)

        # Add a to-do item
        todo.add_todo("Test task")
        todo_id = todo.todos[0]["id"]

        # Remove it
        result = todo.remove_todo(todo_id)
        assert result == True

        # Check that it's removed
        assert len(todo.todos) == 0

def test_todo_list_list_todos():
    """Test that TodoList can list to-do items"""
    with tempfile.TemporaryDirectory() as tmpdir:
        todo = TodoList(tmpdir)

        # Add some to-do items
        todo.add_todo("Task 1")
        todo.add_todo("Task 2")
        todo.add_todo("Task 3")

        # Complete one
        todo.complete_todo(todo.todos[0]["id"])

        # List active tasks
        active = todo.list_todos(show_completed=False)
        assert len(active) == 2  # Should only show incomplete tasks

        # List all tasks
        all_tasks = todo.list_todos(show_completed=True)
        assert len(all_tasks) == 3  # Should show all tasks

def test_todo_list_search_todos():
    """Test that TodoList can search to-do items"""
    with tempfile.TemporaryDirectory() as tmpdir:
        todo = TodoList(tmpdir)

        # Add some to-do items
        todo.add_todo("Buy groceries")
        todo.add_todo("Walk the dog")
        todo.add_todo("Read a book")

        # Search for "dog"
        results = todo.search_todos("dog")
        assert len(results) == 1
        assert results[0]["task"] == "Walk the dog"

        # Search for "o" (should match multiple)
        results = todo.search_todos("o")
        assert len(results) == 3  # "Buy groceries", "Walk the dog", and "Read a book"

        # Search for non-existent term
        results = todo.search_todos("xyz")
        assert len(results) == 0

def test_todo_list_save_and_load():
    """Test that TodoList can save and load from file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        todo_file = Path(tmpdir) / "todo.json"

        # Create first todo instance and add items
        todo1 = TodoList(str(todo_file))
        todo1.add_todo("Persistent task 1")
        todo1.add_todo("Persistent task 2")

        # Get the ID of the first task for later verification
        task_id = todo1.todos[0]["id"]

        # Create second todo instance loading the same file
        todo2 = TodoList(str(todo_file))

        # Check that tasks were loaded
        assert len(todo2.todos) == 2
        assert todo2.todos[0]["id"] == task_id
        assert todo2.todos[0]["task"] == "Persistent task 1"

if __name__ == "__main__":
    test_todo_list_initialization()
    test_todo_list_add_todo()
    test_todo_list_complete_todo()
    test_todo_list_remove_todo()
    test_todo_list_list_todos()
    test_todo_list_search_todos()
    test_todo_list_save_and_load()
    print("All to-do list tests passed!")