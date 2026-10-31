import tempfile
import os
from pathlib import Path
import sys
import datetime
import time

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.assistant import Reminders

def test_reminders_initialization():
    """Test that Reminders initializes correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        reminders = Reminders(str(data_dir))
        expected_reminder_file = data_dir / "reminders.json"
        assert reminders.reminder_file == expected_reminder_file
        assert isinstance(reminders.reminders, list)
        assert reminders.running == False

def test_reminders_add_reminder():
    """Test that Reminders can add reminder items"""
    with tempfile.TemporaryDirectory() as tmpdir:
        reminders = Reminders(tmpdir)

        # Add a reminder
        reminder_text = "Test reminder"
        remind_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        reminders.add_reminder(reminder_text, remind_at)

        # Check that it was added
        assert len(reminders.reminders) == 1
        reminder = reminders.reminders[0]
        assert reminder["text"] == reminder_text
        assert reminder["remind_at"] == remind_at.isoformat()
        assert reminder["triggered"] == False
        assert "id" in reminder
        assert "created" in reminder

def test_reminders_check_reminders():
    """Test that Reminders can check for triggered reminders"""
    with tempfile.TemporaryDirectory() as tmpdir:
        reminders = Reminders(tmpdir)

        # Add a reminder that's already past due
        reminder_text = "Overdue reminder"
        remind_at = datetime.datetime.now() - datetime.timedelta(minutes=5)
        reminders.add_reminder(reminder_text, remind_at)

        # Add a reminder that's in the future
        reminder_text2 = "Future reminder"
        remind_at2 = datetime.datetime.now() + datetime.timedelta(minutes=5)
        reminders.add_reminder(reminder_text2, remind_at2)

        # Check for triggered reminders
        triggered = reminders.check_reminders()
        assert len(triggered) == 1
        assert triggered[0]["text"] == "Overdue reminder"
        assert triggered[0]["triggered"] == True

        # Check again - should be empty now since it was marked as triggered
        triggered2 = reminders.check_reminders()
        assert len(triggered2) == 0

def test_reminders_start_stop_checking():
    """Test that Reminders can start and stop the background checking thread"""
    with tempfile.TemporaryDirectory() as tmpdir:
        reminders = Reminders(tmpdir)

        # Initially not running
        assert reminders.running == False

        # Start checking
        reminders.start_checking()
        assert reminders.running == True
        assert reminders.thread is not None

        # Stop checking
        reminders.stop_checking()
        assert reminders.running == False

def test_reminders_save_and_load():
    """Test that Reminders can save and load from file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        reminder_file = Path(tmpdir) / "reminders.json"

        # Create first reminders instance and add items
        reminders1 = Reminders(str(reminder_file))
        reminders1.add_reminder("Persistent reminder 1",
                               datetime.datetime.now() + datetime.timedelta(hours=1))
        reminders1.add_reminder("Persistent reminder 2",
                               datetime.datetime.now() + datetime.timedelta(hours=2))

        # Get the ID of the first reminder for later verification
        reminder_id = reminders1.reminders[0]["id"]

        # Create second reminders instance loading the same file
        reminders2 = Reminders(str(reminder_file))

        # Check that reminders were loaded
        assert len(reminders2.reminders) == 2
        assert reminders2.reminders[0]["id"] == reminder_id
        assert reminders2.reminders[0]["text"] == "Persistent reminder 1"

if __name__ == "__main__":
    test_reminders_initialization()
    test_reminders_add_reminder()
    test_reminders_check_reminders()
    test_reminders_start_stop_checking()
    test_reminders_save_and_load()
    print("All reminders tests passed!")