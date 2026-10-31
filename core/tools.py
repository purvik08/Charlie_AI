"""
Tool abstraction for the Intelligence Layer.

Provides a unified interface for LLM tool calling, compatible with existing
FeatureRegistry and BaseFeature architecture.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from core.base import BaseFeature, Command, CommandResult, FeatureConfig
from core.events import EventBus, get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Describes a single tool parameter for LLM function calling."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolSchema:
    """Complete schema for a tool, suitable for LLM function calling."""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format for LLM function calling."""
        properties = {}
        required = []
        for param in self.parameters:
            prop = {"type": param.type, "description": param.description}
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        }


class ToolResult:
    """Standardized result of tool execution."""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        message: str = "",
        error: Optional[str] = None,
    ):
        self.success = success
        self.data = data
        self.message = message
        self.error = error

    @classmethod
    def ok(cls, data: Any = None, message: str = "") -> "ToolResult":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, error: str, message: str = "", data: Any = None) -> "ToolResult":
        return cls(success=False, error=error, message=message, data=data)

    def to_command_result(self) -> CommandResult:
        """Convert to existing CommandResult for CLI/GUI compatibility."""
        if self.success:
            output = self.message
            if self.data is not None and not isinstance(self.data, str):
                output += f"\nData: {json.dumps(self.data, default=str)}"
            elif self.data is not None:
                output += f"\nData: {self.data}"
            return CommandResult.ok(output=output, data=self.data)
        return CommandResult.fail(self.error or "Tool execution failed")


# Tool safety classifications
TOOL_SAFETY_SAFE = "safe"
TOOL_SAFETY_MODERATE = "moderate"
TOOL_SAFETY_SENSITIVE = "sensitive"


class Tool(ABC):
    """
    Abstract base class for tools.

    Tools provide structured interfaces for LLM function calling while
    remaining compatible with the existing FeatureRegistry/Command system.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        safety_level: str = TOOL_SAFETY_SAFE,
        handler: Optional[Callable] = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.safety_level = safety_level
        self._handler = handler

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    def validate_args(self, args: Dict[str, Any]) -> Optional[str]:
        """Validate arguments against schema. Returns error message or None."""
        schema_params = {p.name: p for p in self.parameters}
        for param_name, param in schema_params.items():
            if param.required and param_name not in args:
                return f"Missing required parameter: {param_name}"
            if param_name in args:
                value = args[param_name]
                if param.enum and value not in param.enum:
                    return f"Invalid value for {param_name}: {value}. Must be one of {param.enum}"
        return None

    def to_json_schema(self) -> Dict[str, Any]:
        """Get JSON schema for LLM function calling."""
        return self.schema.to_json_schema()


class FunctionTool(Tool):
    """
    Tool that wraps a simple function.

    Useful for converting existing feature methods to tools.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        function: Callable,
        safety_level: str = TOOL_SAFETY_SAFE,
    ):
        super().__init__(name, description, parameters, safety_level, function)
        self._function = function

    def execute(self, **kwargs) -> ToolResult:
        error = self.validate_args(kwargs)
        if error:
            return ToolResult.fail(error)
        try:
            result = self._function(**kwargs)
            if isinstance(result, ToolResult):
                return result
            if isinstance(result, CommandResult):
                return ToolResult.ok(
                    data=result.data,
                    message=result.output,
                )
            return ToolResult.ok(data=result, message=str(result))
        except Exception as exc:
            logger.exception("tool_execution_failed", extra={"tool": self.name})
            return ToolResult.fail(str(exc))


class ToolRegistry:
    """
    Registry for tool discovery and management.

    Works alongside FeatureRegistry - tools can be derived from features
    or registered independently for LLM function calling.
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        if tool.name in self._tools:
            logger.warning("tool_override", extra={"name": tool.name})
        self._tools[tool.name] = tool
        self.event_bus.emit("tool.registered", tool=tool.name)
        logger.debug("tool_registered", extra={"name": tool.name})

    def register_function(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter],
        function: Callable,
        safety_level: str = TOOL_SAFETY_SAFE,
    ) -> Tool:
        """Create and register a FunctionTool."""
        tool = FunctionTool(name, description, parameters, function, safety_level)
        self.register(tool)
        return tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_safe(self) -> List[Tool]:
        """Get all SAFE-classified tools."""
        return [t for t in self._tools.values() if t.safety_level == TOOL_SAFETY_SAFE]

    def get_moderate(self) -> List[Tool]:
        """Get all MODERATE-classified tools."""
        return [t for t in self._tools.values() if t.safety_level == TOOL_SAFETY_MODERATE]

    def get_sensitive(self) -> List[Tool]:
        """Get all SENSITIVE-classified tools."""
        return [t for t in self._tools.values() if t.safety_level == TOOL_SAFETY_SENSITIVE]

    def list_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all tools (for LLM function calling)."""
        return [tool.to_json_schema() for tool in self._tools.values()]

    def list_schemas_for_safety(self, safety_levels: List[str]) -> List[Dict[str, Any]]:
        """Get JSON schemas for tools of specified safety levels."""
        return [
            tool.to_json_schema()
            for tool in self._tools.values()
            if tool.safety_level in safety_levels
        ]

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult.fail(f"Unknown tool: {tool_name}")
        return tool.execute(**kwargs)

    def has_tool(self, name: str) -> bool:
        return name in self._tools


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global ToolRegistry instance (singleton)."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def set_tool_registry(registry: ToolRegistry) -> None:
    """Set the global ToolRegistry instance (for testing)."""
    global _tool_registry
    _tool_registry = registry


def create_tools_from_features(registry: ToolRegistry) -> int:
    """
    Create tools from existing FeatureRegistry.

    Discovers all registered features and converts their commands to tools.
    """
    from core.registry import get_feature_registry

    feature_registry = get_feature_registry()
    count = 0

    for feature in feature_registry.get_enabled():
        for cmd_name, command in feature.get_commands().items():
            # Skip if already registered
            if registry.has_tool(cmd_name):
                continue

            # Infer parameters from command
            parameters = []
            for param_name, param_info in command.parameters.items():
                parameters.append(
                    ToolParameter(
                        name=param_name,
                        type=param_info.get("type", "string"),
                        description=param_info.get("description", ""),
                        required=param_info.get("required", True),
                        default=param_info.get("default"),
                        enum=param_info.get("enum"),
                    )
                )

            tool = FunctionTool(
                name=cmd_name,
                description=command.description or f"Execute {cmd_name}",
                parameters=parameters,
                function=command.handler,
                safety_level=TOOL_SAFETY_SAFE,
            )
            registry.register(tool)
            count += 1

    logger.info("tools_created_from_features", extra={"count": count})
    return count


def create_standard_tools(registry: ToolRegistry, assistant: Any = None) -> int:
    """
    Create standard tools for the Intelligence Layer from OfflineAssistant utilities.
    
    Creates tools for:
    - get_time, get_date, get_system_info, get_battery
    - search_files, open_path, create_note, search_notes
    - list_todos, add_todo, complete_todo, delete_todo
    - create_reminder, list_reminders
    """
    from core.assistant import SystemInfo
    from datetime import datetime

    if assistant is None:
        from cli.core import get_assistant
        assistant = get_assistant()
    count = 0
    
    # Time and Date tools
    def get_time_handler() -> str:
        from datetime import datetime
        return datetime.now().strftime("%I:%M %p")
    
    time_tool = FunctionTool(
        name="get_time",
        description="Get the current time",
        parameters=[
            ToolParameter(
                name="format",
                type="string",
                description="Output format (default: %I:%M %p)",
                required=False,
                default="%I:%M %p",
            ),
        ],
        function=get_time_handler,
        safety_level=TOOL_SAFETY_SAFE,
    )
    registry.register(time_tool)
    count += 1
    
    def get_date_handler() -> str:
        from datetime import datetime
        return datetime.now().strftime("%A, %B %d, %Y")
    
    date_tool = FunctionTool(
        name="get_date",
        description="Get the current date",
        parameters=[
            ToolParameter(
                name="format",
                type="string",
                description="Output format (default: %A, %B %d, %Y)",
                required=False,
                default="%A, %B %d, %Y",
            ),
        ],
        function=get_date_handler,
        safety_level=TOOL_SAFETY_SAFE,
    )
    registry.register(date_tool)
    count += 1
    
    # System Info tools
    def get_system_info_handler() -> str:
        try:
            info = SystemInfo.get_system_info()
            if not info:
                return "System information not available"
            parts = []
            for k, v in info.items():
                parts.append(f"  {k}: {v}")
            output = "System Information:\n" + "\n".join(parts)
            return output
        except Exception as e:
            return f"Error getting system info: {str(e)}"
    
    system_info_tool = FunctionTool(
        name="get_system_info",
        description="Get system information (OS, CPU, memory)",
        parameters=[],
        function=get_system_info_handler,
        safety_level=TOOL_SAFETY_SAFE,
    )
    registry.register(system_info_tool)
    count += 1
    
    def get_battery_handler() -> str:
        try:
            info = SystemInfo.get_battery_info()
            if info:
                return f"Battery: {info['percent']}% {'charging' if info['power_plugged'] else 'discharging'}"
            return "Battery information not available"
        except Exception as e:
            return f"Error getting battery info: {str(e)}"
    
    battery_tool = FunctionTool(
        name="get_battery",
        description="Get battery status",
        parameters=[],
        function=get_battery_handler,
        safety_level=TOOL_SAFETY_SAFE,
    )
    registry.register(battery_tool)
    count += 1
    
    # File Search tools
    if assistant.file_search:
        def search_files_handler(query: str, limit: int = 10) -> str:
            try:
                results = assistant.file_search.search_files(query, max_results=limit)
                if results:
                    lines = []
                    for r in results[:5]:
                        lines.append(f"  {r['name']} ({r['size']} bytes)")
                    return f"Found {len(results)} files:\n" + "\n".join(lines)
                return f"No files found matching '{query}'"
            except Exception as e:
                return f"Search error: {str(e)}"
        
        search_files_tool = FunctionTool(
            name="search_files",
            description="Search for files in the data directory",
            parameters=[
                ToolParameter(name="query", type="string", description="Search query", required=True),
                ToolParameter(
                    name="limit", type="integer", description="Max results", required=False, default=10
                ),
            ],
            function=search_files_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(search_files_tool)
        count += 1
    
    # Note Taking tools
    if assistant.note_taking:
        def create_note_handler(title: str, content: str) -> str:
            try:
                file_path = assistant.note_taking.create_note(title, content)
                return f"Note created: {file_path}"
            except Exception as e:
                return f"Failed to create note: {str(e)}"
        
        create_note_tool = FunctionTool(
            name="create_note",
            description="Create a new note",
            parameters=[
                ToolParameter(name="title", type="string", description="Note title", required=True),
                ToolParameter(name="content", type="string", description="Note content", required=True),
            ],
            function=create_note_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(create_note_tool)
        count += 1
        
        def search_notes_handler(query: str) -> str:
            try:
                results = assistant.note_taking.search_notes(query)
                if results:
                    titles = [note["title"] for note in results[:5]]
                    return f"Found {len(results)} notes matching '{query}':\n" + "\n".join(titles)
                return f"No notes found matching '{query}'"
            except Exception as e:
                return f"Search error: {str(e)}"
        
        search_notes_tool = FunctionTool(
            name="search_notes",
            description="Search within notes",
            parameters=[
                ToolParameter(name="query", type="string", description="Search query", required=True),
            ],
            function=search_notes_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(search_notes_tool)
        count += 1
    
    # To-Do List tools
    if assistant.todo_list:
        def add_todo_handler(task: str, priority: str = "medium") -> str:
            try:
                priority = priority.lower()
                if priority not in ["low", "medium", "high"]:
                    priority = "medium"
                assistant.todo_list.add_todo(task, priority)
                return f"Added to-do: {task} [{priority}]"
            except Exception as e:
                return f"Error adding todo: {str(e)}"
        
        add_todo_tool = FunctionTool(
            name="add_todo",
            description="Add a new to-do item",
            parameters=[
                ToolParameter(name="task", type="string", description="Task description", required=True),
                ToolParameter(
                    name="priority", type="string", description="Priority (low/medium/high)", required=False, default="medium"
                ),
            ],
            function=add_todo_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(add_todo_tool)
        count += 1
        
        def list_todos_handler(show_completed: bool = False) -> str:
            try:
                todos = assistant.todo_list.list_todos(show_completed=show_completed)
                if todos:
                    lines = []
                    for todo in todos[:10]:
                        status = "done" if todo["completed"] else "pending"
                        lines.append(f"  [{status}] {todo['task']} (ID: {todo['id']})")
                    return f"You have {len(todos)} tasks:\n" + "\n".join(lines)
                return "Your to-do list is empty"
            except Exception as e:
                return f"Error listing todos: {str(e)}"
        
        list_todos_tool = FunctionTool(
            name="list_todos",
            description="List to-do items",
            parameters=[
                ToolParameter(name="show_completed", type="boolean", description="Show completed tasks", required=False, default=False),
            ],
            function=list_todos_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(list_todos_tool)
        count += 1
        
        def complete_todo_handler(task_id: int) -> str:
            try:
                if assistant.todo_list.complete_todo(task_id):
                    return f"Completed task {task_id}"
                return f"Task {task_id} not found"
            except Exception as e:
                return f"Error completing todo: {str(e)}"
        
        complete_todo_tool = FunctionTool(
            name="complete_todo",
            description="Mark a task as completed",
            parameters=[
                ToolParameter(name="task_id", type="integer", description="Task ID to complete", required=True),
            ],
            function=complete_todo_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(complete_todo_tool)
        count += 1
        
        def delete_todo_handler(task_id: int) -> str:
            try:
                if assistant.todo_list.remove_todo(task_id):
                    return f"Removed task {task_id}"
                return f"Task {task_id} not found"
            except Exception as e:
                return f"Error deleting todo: {str(e)}"
        
        delete_todo_tool = FunctionTool(
            name="delete_todo",
            description="Remove a to-do item",
            parameters=[
                ToolParameter(name="task_id", type="integer", description="Task ID to remove", required=True),
            ],
            function=delete_todo_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(delete_todo_tool)
        count += 1
    
    # Reminders tools
    if assistant.reminders:
        def add_reminder_handler(text: str, minutes: int = 30) -> str:
            try:
                from datetime import datetime, timedelta
                remind_at = datetime.now() + timedelta(minutes=minutes)
                assistant.reminders.add_reminder(text, remind_at)
                return f"Reminder set for {minutes} minutes from now: {text}"
            except Exception as e:
                return f"Error adding reminder: {str(e)}"
        
        add_reminder_tool = FunctionTool(
            name="create_reminder",
            description="Create a new reminder",
            parameters=[
                ToolParameter(name="text", type="string", description="Reminder text", required=True),
                ToolParameter(name="minutes", type="integer", description="Minutes from now", required=False, default=30),
            ],
            function=add_reminder_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(add_reminder_tool)
        count += 1
        
        def list_reminders_handler(include_triggered: bool = False) -> str:
            try:
                reminders = assistant.reminders.reminders
                if not include_triggered:
                    reminders = [r for r in reminders if not r.get("triggered", False)]
                if reminders:
                    lines = []
                    for r in reminders[:10]:
                        status = "triggered" if r.get("triggered", False) else "pending"
                        time_str = r.get("remind_at", "unknown")
                        if time_str != "unknown":
                            try:
                                dt = datetime.fromisoformat(time_str)
                                time_str = dt.strftime("%I:%M %p")
                            except:
                                pass
                        lines.append(f"  [{status}] {r['text']} at {time_str}")
                    return f"You have {len(reminders)} reminders:\n" + "\n".join(lines)
                return "No reminders found"
            except Exception as e:
                return f"Error listing reminders: {str(e)}"
        
        list_reminders_tool = FunctionTool(
            name="list_reminders",
            description="List reminders",
            parameters=[
                ToolParameter(name="include_triggered", type="boolean", description="Include triggered reminders", required=False, default=False),
            ],
            function=list_reminders_handler,
            safety_level=TOOL_SAFETY_SAFE,
        )
        registry.register(list_reminders_tool)
        count += 1
    
    logger.info("standard_tools_created", extra={"count": count})
    return count