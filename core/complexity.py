"""Deterministic routing for the local chat-model tier.

TinyLlama remains the conversational front door. Only requests that are long,
explicitly multi-step, or clearly analytical are sent to a configured stronger
local model. Tool commands are routed before this module runs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ComplexityDecision:
    """The selected model-routing task and an auditable reason."""

    task: str
    level: str
    reason: str


class ComplexityRouter:
    """Classify free-form chat without spending another model call."""

    _COMPLEX_MARKERS = re.compile(
        r"\b(?:analyse|analyze|compare|contrast|evaluate|critique|debug|"
        r"architect|design|implement|refactor|research|derive|prove|"
        r"trade[- ]?offs?|step[- ]by[- ]step|detailed plan|comprehensive)\b",
        re.IGNORECASE,
    )

    def __init__(self, config: Optional[Mapping[str, Any]] = None) -> None:
        config = config or {}
        self.long_request_chars = max(1, int(config.get("long_request_chars", 700)))
        self.multi_step_threshold = max(1, int(config.get("multi_step_threshold", 2)))

    def classify(self, text: str) -> ComplexityDecision:
        cleaned = " ".join(str(text).split())
        if len(cleaned) >= self.long_request_chars:
            return ComplexityDecision("complex", "complex", "long request")
        if self._has_code_or_structured_payload(str(text)):
            return ComplexityDecision("complex", "complex", "code or structured payload")
        if self._step_count(cleaned) >= self.multi_step_threshold:
            return ComplexityDecision("complex", "complex", "multi-step request")
        if self._COMPLEX_MARKERS.search(cleaned):
            return ComplexityDecision("complex", "complex", "analytical request")
        return ComplexityDecision("simple", "simple", "conversational request")

    @staticmethod
    def _has_code_or_structured_payload(text: str) -> bool:
        return "```" in text or ("{" in text and "}" in text) or ("\n" in text and ":" in text)

    @staticmethod
    def _step_count(text: str) -> int:
        numbered = len(re.findall(r"(?:^|\s)\d+[.)]", text))
        clauses = len(re.findall(r"\b(?:then|after that|next|finally)\b", text, re.IGNORECASE))
        return numbered + clauses
