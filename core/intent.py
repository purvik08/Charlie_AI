import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class IntentResult:
    intent: str
    confidence: float
    slots: Dict[str, Any]
    requires_llm: bool = False


class IntentDetector:
    """Layered offline intent detector: rules, regex, lightweight heuristics."""

    _APP_PATTERNS = [
        (re.compile(r"^(open|launch|start)\s+(?P<app>chrome|calculator|calc|spotify|settings|vs code|vscode)$"), "open_application"),
        (re.compile(r"^open\s+(?P<folder>downloads|documents|desktop)$"), "open_folder"),
    ]

    def detect(self, text: str) -> IntentResult:
        command = text.strip()
        lowered = command.lower()

        if lowered in {"hello", "hi", "hey", "hello aria", "hi aria"}:
            return IntentResult("greeting", 1.0, {})
        if lowered in {"volume up", "increase volume"}:
            return IntentResult("volume_up", 0.98, {})
        if lowered in {"mute", "mute volume"}:
            return IntentResult("mute", 0.98, {})
        if lowered in {"take screenshot", "screenshot"}:
            return IntentResult("take_screenshot", 0.98, {})
        if lowered in {"lock pc", "lock computer", "lock windows"}:
            return IntentResult("lock_pc", 0.98, {})
        if lowered in {"shutdown", "shutdown pc", "restart", "restart pc"}:
            return IntentResult("system_power", 0.95, {"action": lowered.split()[0]})

        for pattern, intent in self._APP_PATTERNS:
            match = pattern.match(lowered)
            if match:
                return IntentResult(intent, 0.98, match.groupdict())

        task = self._match_task(lowered)
        if task is not None:
            return IntentResult("add_todo", 0.95, {"task": task})

        if "list todos" in lowered or "show tasks" in lowered:
            return IntentResult("list_todos", 0.98, {})
        if "list notes" in lowered or "show notes" in lowered or "list my notes" in lowered:
            return IntentResult("list_notes", 0.98, {})
        if "system info" in lowered or "computer info" in lowered:
            return IntentResult("system_info", 0.98, {})
        if "battery" in lowered:
            return IntentResult("battery", 0.98, {})

        return IntentResult("chat", 0.5, {}, requires_llm=True)

    @staticmethod
    def _match_task(lowered: str) -> Optional[str]:
        prefixes = (
            "add a todo", "add todo", "add a task", "add task",
            "create a task", "create task", "new task",
        )
        for prefix in prefixes:
            if lowered.startswith(prefix):
                task = lowered[len(prefix):].strip()
                for filler in ("to ", "for me to "):
                    if task.startswith(filler):
                        task = task[len(filler):].strip()
                return task or None
        return None

