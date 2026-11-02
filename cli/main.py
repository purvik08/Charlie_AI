#!/usr/bin/env python3
"""
Main entry point for the Offline AI Assistant.
"""

import sys
import os
from pathlib import Path
import typer

# Ensure core is importable (it's a sibling directory of cli)
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

app = typer.Typer(name="charlie")

# Register time and date subcommands
from cli.commands.time_date import time_app, date_app
app.add_typer(time_app, name="time")
app.add_typer(date_app, name="date")

# Register system subcommand
from cli.commands.system import app as system_app
app.add_typer(system_app, name="system")

# Register todo subcommand
from cli.commands.todos import app as todo_app
app.add_typer(todo_app, name="todo")

# Register reminder subcommand
from cli.commands.reminders import app as remind_app
app.add_typer(remind_app, name="remind")

# Register file subcommand
from cli.commands.files import app as file_app
app.add_typer(file_app, name="file")

# Register note subcommand
from cli.commands.notes import app as note_app
app.add_typer(note_app, name="note")

# Register app subcommand
from cli.commands.apps import app as apps_app
app.add_typer(apps_app, name="app")

# Register chat subcommand
from cli.commands.chat import app as chat_app
app.add_typer(chat_app, name="chat")

# Register search subcommand (GPT Researcher)
from cli.commands.search import app as search_app
app.add_typer(search_app, name="search")

# Register OCR subcommand (PaddleOCR)
from cli.commands.ocr import app as ocr_app
app.add_typer(ocr_app, name="ocr")

# Register document parsing subcommand (Docling)
from cli.commands.parse import app as parse_app
app.add_typer(parse_app, name="parse")

# Register Colibri local LLM subcommand
from cli.commands.colibri import app as colibri_app
app.add_typer(colibri_app, name="colibri")


# Version command
@app.command()
def version():
    """Show the version."""
    from cli import __version__
    print(f"Charlie v{__version__}")

from ui import FloatingAssistantGUI
from core.assistant import OfflineAssistant
from config.config import Config
from ui.onboarding import run_first_launch_wizard


def run_gui():
    """Run the GUI application."""
    try:
        config = Config()
        if not run_first_launch_wizard(config):
            return

        # Load the assistant after first-launch paths/profile are saved.
        assistant = OfflineAssistant(config_path=str(config.config_file))

        # Create and run the GUI
        gui_app = FloatingAssistantGUI(assistant)
        gui_app.run()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # If no arguments provided, run GUI; otherwise run CLI commands
    if len(sys.argv) == 1:
        run_gui()
    else:
        app()
