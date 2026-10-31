"""
EventBus and core event types for the Offline AI Assistant.

Provides a simple synchronous pub/sub mechanism for decoupling
features, GUI, and CLI. All events are processed on the calling thread.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Base event class with metadata."""
    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = field(default_factory=lambda: str(uuid4())[:8])
    payload: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """
    Simple synchronous event bus.

    Subscribers are callables that receive the Event object.
    All events are delivered synchronously on the emitting thread.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._wildcard: List[Callable[[Event], None]] = []

    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Subscribe to a specific event name."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)
        logger.debug("subscribed", extra={"event": event_name})

    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        """Subscribe to all events (wildcard)."""
        self._wildcard.append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]) -> bool:
        """Unsubscribe from a specific event. Returns True if removed."""
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(callback)
                return True
            except ValueError:
                return False
        return False

    def emit(self, event_name: str, **payload) -> None:
        """Emit an event with the given payload to all subscribers."""
        event = Event(name=event_name, payload=payload)
        self._emit_event(event)

    def emit_event(self, event: Event) -> None:
        """Emit a pre-constructed Event object."""
        self._emit_event(event)

    def _emit_event(self, event: Event) -> None:
        logger.debug("emit", extra={"event": event.name, "correlation_id": event.correlation_id})

        # Specific subscribers
        for callback in self._subscribers.get(event.name, []):
            try:
                callback(event)
            except Exception as exc:
                logger.exception("subscriber_error", extra={"event": event.name, "error": str(exc)})

        # Wildcard subscribers
        for callback in self._wildcard:
            try:
                callback(event)
            except Exception as exc:
                logger.exception("wildcard_subscriber_error", extra={"event": event.name, "error": str(exc)})


# Convenience event name constants
class Events:
    """Standard event names used across the application."""

    # Feature lifecycle
    FEATURE_READY = "feature.ready"
    FEATURE_SHUTDOWN = "feature.shutdown"

    # Command processing
    COMMAND_RECEIVED = "command.received"
    COMMAND_COMPLETED = "command.completed"
    COMMAND_FAILED = "command.failed"

    # Assistant responses
    RESPONSE_GENERATED = "response.generated"
    RESPONSE_SPOKEN = "response.spoken"

    # Status
    STATUS_CHANGED = "status.changed"
    MODEL_LOADED = "model.loaded"
    MODEL_UNLOADED = "model.unloaded"

    # Reminders
    REMINDER_TRIGGERED = "reminder.triggered"
    REMINDER_ADDED = "reminder.added"
    REMINDER_REMOVED = "reminder.removed"

    # Notes
    NOTE_CREATED = "note.created"
    NOTE_DELETED = "note.deleted"

    # Todos
    TODO_ADDED = "todo.added"
    TODO_COMPLETED = "todo.completed"
    TODO_REMOVED = "todo.removed"

    # Files
    FILE_FOUND = "file.found"

    # System
    SYSTEM_INFO_REQUESTED = "system.info.requested"
    BATTERY_INFO_REQUESTED = "battery.info.requested"

    # Errors
    ERROR_OCCURRED = "error.occurred"


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global EventBus instance (singleton)."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def set_event_bus(bus: EventBus) -> None:
    """Set the global EventBus instance (for testing)."""
    global _event_bus
    _event_bus = bus