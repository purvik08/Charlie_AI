"""
Base classes for features: BaseFeature, Command, CommandResult, FeatureConfig.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Command:
    """Represents a feature command with metadata."""
    name: str
    handler: Callable
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)


@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    output: str = ""
    data: Any = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, output: str = "", data: Any = None) -> "CommandResult":
        return cls(success=True, output=output, data=data)

    @classmethod
    def fail(cls, error: str, output: str = "") -> "CommandResult":
        return cls(success=False, error=error, output=output)


@dataclass
class FeatureConfig:
    """Configuration container for a feature."""
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)


class BaseFeature(ABC):
    """
    Abstract base class for all features.

    Features are self-contained modules that register commands,
    handle their own lifecycle, and communicate via EventBus.
    """

    def __init__(self, config: FeatureConfig, event_bus: Any) -> None:
        self.config = config
        self.event_bus = event_bus
        self._commands: Dict[str, Command] = {}
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique feature name (e.g., 'system_info')."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Feature version."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass

    def register_command(self, command: Command) -> None:
        """Register a command this feature provides."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def get_commands(self) -> Dict[str, Command]:
        """Return all commands this feature provides."""
        return self._commands.copy()

    def has_command(self, name: str) -> bool:
        return name in self._commands

    def execute_command(self, name: str, *args, **kwargs) -> CommandResult:
        """Execute a registered command by name."""
        if name not in self._commands:
            return CommandResult.fail(f"Unknown command: {name}")

        command = self._commands[name]
        try:
            result = command.handler(*args, **kwargs)
            if isinstance(result, CommandResult):
                return result
            return CommandResult.ok(str(result))
        except Exception as exc:
            return CommandResult.fail(str(exc))

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the feature (called once on startup)."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up resources (called on app exit)."""
        pass

    def is_initialized(self) -> bool:
        return self._initialized

    def _mark_initialized(self) -> None:
        self._initialized = True

    def _emit(self, event_name: str, **payload) -> None:
        """Convenience to emit events."""
        if self.event_bus:
            self.event_bus.emit(event_name, **payload)