import subprocess
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PYTHON = sys.executable


def run_cli(*args):
    """Run the Charlie CLI and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [PYTHON, "-m", "cli.main", *args],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_imports():
    """Test that the CLI app can be built."""
    from cli.main import app
    assert app.info.name == "charlie"


def test_version():
    """Test the version command."""
    code, out, _ = run_cli("version")
    assert code == 0
    assert "Charlie" in out


def test_time_now():
    """Test the time command."""
    code, out, _ = run_cli("time", "now")
    assert code == 0
    assert "AM" in out or "PM" in out


def test_date_today():
    """Test the date command."""
    code, out, _ = run_cli("date", "today")
    assert code == 0
    assert "," in out


def test_system_info():
    """Test the system info command."""
    code, out, _ = run_cli("system", "info")
    assert code == 0
    assert "System" in out


def test_todo_lifecycle():
    """Test the todo add/list/done/remove cycle."""
    code, out, _ = run_cli("todo", "add", "cli test task", "--priority", "low")
    assert code == 0
    assert "cli test task" in out

    code, out, _ = run_cli("todo", "list")
    assert code == 0
    assert "cli test task" in out

    code, out, _ = run_cli("todo", "search", "cli test task")
    assert code == 0
    assert "cli test task" in out

    # Clean up: remove the test task
    code, out, _ = run_cli("todo", "list")
    lines = [line for line in out.splitlines() if "cli test task" in line]
    assert lines, "test task should be visible"
    parts = [p.strip() for p in lines[0].split("|")]
    task_id = int(parts[1])
    code, out, _ = run_cli("todo", "remove", str(task_id))
    assert code == 0
    assert f"Task {task_id} removed" in out


def test_reminder_lifecycle():
    """Test the reminder add/list cycle."""
    code, out, _ = run_cli("remind", "add", "cli test reminder", "--in", "120")
    assert code == 0
    assert "cli test reminder" in out

    code, out, _ = run_cli("remind", "list")
    assert code == 0
    assert "cli test reminder" in out

    # Clean up: remove the test reminder
    code, out, _ = run_cli("remind", "list")
    lines = [line for line in out.splitlines() if "cli test reminder" in line]
    assert lines, "test reminder should be visible"
    parts = [p.strip() for p in lines[0].split("|")]
    reminder_id = int(parts[1])

    from core.assistant import OfflineAssistant
    assistant = OfflineAssistant()
    if assistant.reminders:
        assistant.reminders.reminders = [
            r for r in assistant.reminders.reminders if r["id"] != reminder_id
        ]
        assistant.reminders.save_reminders()
        assistant.reminders.stop_checking()


if __name__ == "__main__":
    test_cli_imports()
    print("CLI imports test passed!")

    test_version()
    print("Version test passed!")

    test_time_now()
    print("Time test passed!")

    test_date_today()
    print("Date test passed!")

    test_system_info()
    print("System info test passed!")

    test_todo_lifecycle()
    print("Todo lifecycle test passed!")

    test_reminder_lifecycle()
    print("Reminder lifecycle test passed!")

    print("All CLI tests passed!")