"""
features.web_search — Web search and autonomous research feature for Charlie.

Powered by GPT Researcher with automatic resilient fallback.
Registers commands:
  - 'web.search' → search the web for information
"""

from typing import Any, Dict, List, Optional

from core.base import BaseFeature, Command, CommandResult, FeatureConfig
from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter


class WebSearchFeature(BaseFeature):
    """Feature that provides web search and research functionality."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides web search and research functionality via GPT Researcher"

    def initialize(self) -> None:
        """Register commands and emit feature ready event."""
        self.register_command(
            Command(
                name="web.search",
                handler=self._search_web,
                description="Search the web for up-to-date information",
                aliases=["web.search", "search.web"],
            )
        )
        from core.events import Events, get_event_bus
        bus = get_event_bus()
        bus.emit(Events.FEATURE_READY, feature=self.name)

    def shutdown(self) -> None:
        """Clean up resources."""
        pass

    def _search_web(self) -> CommandResult:
        """Handler for web.search command."""
        import typer

        query = typer.prompt("Search query").strip()
        if not query:
            return CommandResult.fail("Search query cannot be empty")

        adapter = GPTResearcherAdapter()
        result = adapter.search(query)
        return CommandResult.ok(result)


__all__ = ["WebSearchFeature", "GPTResearcherAdapter"]
