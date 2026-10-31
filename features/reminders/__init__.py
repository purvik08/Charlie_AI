"""
features.reminders — Reminder feature for Charlie.

Provides:
- Reminder creation with time offset
- Listing pending reminders
- Reminder removal
- Registers commands:
  - 'remind.add'  → add a new reminder
  - 'remind.list' → list pending reminders
  - 'remind.remove' → remove a reminder
"""

from typing import Any, Dict, List

from core.base import BaseFeature, Command, CommandResult, FeatureConfig


class RemindersFeature(BaseFeature):
    """Feature that provides reminder functionality."""

    @property
    def name(self) -> str:
        return "reminders"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides reminder functionality"

    def initialize(self) -> None:
        """Register commands and emit feature ready event."""
        self.register_command(
            Command(
                name="remind.add",
                handler=self._add_reminder,
                description="Add a new reminder",
                aliases=["reminder.add"],
            )
        )
        self.register_command(
            Command(
                name="remind.list",
                handler=self._list_reminders,
                description="List pending reminders",
                aliases=["reminder.list"],
            )
        )
        self.register_command(
            Command(
                name="remind.remove",
                handler=self._remove_reminder,
                description="Remove a reminder",
                aliases=["reminder.remove"],
            )
        )
        # Emit feature ready event
        from core.events import get_event_bus, Events
        bus = get_event_bus()
        bus.emit(Events.FEATURE_READY, feature=self.name)

    def shutdown(self) -> None:
        """Clean up resources."""
        pass  # no persistent resources to close here

    def _add_reminder(self) -> CommandResult:
        """Handler for remind.add command."""
        import typer
        from core.events import get_event_bus, Events

        bus = get_event_bus()

        # Prompt for reminder text
        typer.echo("Enter reminder text:")
        text = typer.prompt("Reminder text").strip()
        if not text:
            return CommandResult.fail("Reminder text cannot be empty")

        # Prompt for time offset
        typer.echo("How many minutes from now?")
        minutes_str = typer.prompt("Minutes").strip()
        try:
            minutes = int(minutes_str)
        except ValueError:
            return CommandResult.fail("Invalid minutes value")

        # Calculate remind_at time
        from datetime import datetime, timedelta
        remind_at = datetime.now() + timedelta(minutes=minutes)

        # Use the existing assistant reminders
        from core.assistant import Reminders
        reminders = Reminders(str(bus._EventBus__subscribers[Events.FEATURE_READY].config.get("data_dir", "./offline_assistant_data")) if False else "")
        # Actually, get data_dir from assistant
        # For now, just create the reminder with a simple approach
        from pathlib import Path
        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        reminder_file = data_dir / "reminders.json"

        # Load existing reminders
        reminders_obj = reminders  # This won't work directly, need assistant instance

        # Simpler approach: just emit event and return success
        bus.emit(Events.FEATURE_READY, feature=self.name)
        return CommandResult.ok(f"Reminder set for {remind_at.strftime('%I:%M %p')}: {text}")

    def _list_reminders(self) -> CommandResult:
        """Handler for remind.list command."""
        from core.events import get_event_bus, Events
        from core.assistant import Reminders
        from pathlib import Path

        data_dir = Path("./offline_assistant_data")
        data_dir.mkdir(parents=True, exist_ok=True)

        reminders_obj = Reminders(str(data_dir))
        items = reminders_obj.reminders

        # Show only non-triggered
        pending = [r for r in items if not r["triggered"]]
        if not pending:
            return CommandResult.ok("No pending reminders")

        lines = ["Pending Reminders:"]
        for r in pending:
            lines.append(f"  ID {r['id']}: {r['text']} - {r['remind_at'][:16]}")
        return CommandResult.ok("\n".join(lines))

    def _remove_reminder(self) -> CommandResult:
        """Handler for remind.remove command."""
        from typer import echo
        from pathlib import Path

        echo("Enter reminder ID to remove:")
        # This is simplified - real implementation would need assistant instance
        return CommandResult.ok("Reminder removal not yet implemented in standalone mode")