"""Shared assistant instance for CLI commands."""

import logging
import sys
from pathlib import Path

# Ensure core is importable (it's a sibling directory of cli)
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.assistant import OfflineAssistant

logging.basicConfig(level=logging.WARNING)

_assistant = None


def get_assistant() -> OfflineAssistant:
    """Return the lazily-initialized singleton assistant."""
    global _assistant
    if _assistant is None:
        _assistant = OfflineAssistant()
    return _assistant


def shutdown_assistant() -> None:
    """Shut down background threads and release the singleton."""
    global _assistant
    if _assistant is not None:
        if _assistant.reminders:
            _assistant.reminders.stop_checking()
        if _assistant.model_manager:
            _assistant.model_manager.shutdown()
        _assistant = None


def require_feature(assistant: OfflineAssistant, name: str):
    """Return the feature instance or exit with a clear error."""
    feature = getattr(assistant, name, None)
    if feature is None:
        import typer

        typer.secho(
            f"Feature '{name}' is not enabled in config.json.", fg=typer.colors.RED
        )
        raise typer.Exit(1)
    return feature
