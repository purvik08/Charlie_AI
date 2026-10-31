"""
Core infrastructure for the Offline AI Assistant.

Exports:
- EventBus, Events, get_event_bus
- FeatureRegistry, get_feature_registry
- BaseFeature, Command, CommandResult, FeatureConfig
- Tool, ToolParameter, ToolSchema, ToolResult, ToolRegistry, get_tool_registry, create_tools_from_features
"""

from .base import BaseFeature, Command, CommandResult, FeatureConfig
from .events import EventBus, Events, get_event_bus, set_event_bus
from .registry import FeatureRegistry, get_feature_registry, set_feature_registry
from .tools import (
    Tool,
    ToolParameter,
    ToolSchema,
    ToolResult,
    ToolRegistry,
    get_tool_registry,
    set_tool_registry,
    create_tools_from_features,
)

__all__ = [
    "EventBus",
    "Events",
    "get_event_bus",
    "set_event_bus",
    "FeatureRegistry",
    "get_feature_registry",
    "set_feature_registry",
    "BaseFeature",
    "Command",
    "CommandResult",
    "FeatureConfig",
    "Tool",
    "ToolParameter",
    "ToolSchema",
    "ToolResult",
    "ToolRegistry",
    "get_tool_registry",
    "set_tool_registry",
    "create_tools_from_features",
]