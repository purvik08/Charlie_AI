"""Tool registry construction for the Intelligence Layer.

Builds a ToolRegistry whose tools wrap the feature objects of one
OfflineAssistant instance.  Every tool has a typed parameter schema and is
validated (required parameters, enumerations) before it runs.  The language
model does not call these tools yet; they are used by code and by tests.
"""

from core.tools import ToolRegistry, create_standard_tools


def build_registry(assistant) -> ToolRegistry:
    """Return a new ToolRegistry populated from the given assistant."""
    registry = ToolRegistry()
    create_standard_tools(registry, assistant)
    return registry
