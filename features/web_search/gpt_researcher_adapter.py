"""
Enhanced GPT Researcher Adapter for Charlie AI.

Fully integrates the local GPT Researcher codebase (gpt-researcher-main/)
with Charlie AI, providing:

1. Autonomous deep research via GPTResearcher agent.
2. Quick web search fallback (DuckDuckGo + Wikipedia).
3. Optional LLM synthesis of search results via ModelManager or Colibri.
4. Support for both synchronous and async execution contexts.

GPT Researcher requires environment variables for external services
(OPENAI_API_KEY, TAVILY_API_KEY, etc.).  When those are absent or when
the library's heavy dependencies are not installed, the adapter
transparently falls back to its own live-web search engine so Charlie
always has a working search capability.
"""

import asyncio
import html
import json
import logging
import os
import re
import sys
import threading
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

# ── Path setup ──────────────────────────────────────────────────────────────
# Keep Charlie's own root first so our packages are never shadowed.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT_STR = str(_PROJECT_ROOT)
if _PROJECT_ROOT_STR in sys.path:
    sys.path.remove(_PROJECT_ROOT_STR)
sys.path.insert(0, _PROJECT_ROOT_STR)

_CANDIDATE_PATHS = [
    _PROJECT_ROOT / "gpt-researcher-main" / "gpt-researcher-main",
    _PROJECT_ROOT / "gpt-researcher-main",
]
for _p in _CANDIDATE_PATHS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.append(str(_p))

# ── HTML utilities ──────────────────────────────────────────────────────────

class _SimpleHTMLTextExtractor(HTMLParser):
    """Strips HTML tags and returns plain text."""

    def __init__(self):
        super().__init__()
        self.result: List[str] = []

    def handle_data(self, d: str) -> None:
        self.result.append(d)

    def get_text(self) -> str:
        return "".join(self.result).strip()


def _strip_html(html_str: str) -> str:
    if not html_str:
        return ""
    parser = _SimpleHTMLTextExtractor()
    try:
        parser.feed(html_str)
        text = parser.get_text()
    except Exception:
        text = re.sub(r"<[^>]+>", "", html_str)
    return html.unescape(text).strip()


# ════════════════════════════════════════════════════════════════════════════
class GPTResearcherAdapter:
    """
    Adapter that provides web search and autonomous research to Charlie AI.

    Priority order for each search call:
    1. GPTResearcher (deep / autonomous research) — when available & configured.
    2. DuckDuckGo Instant Answer API + Wikipedia OpenSearch (always available).
    3. Optional synthesis of the raw results through ModelManager.chat().
    """

    # Default request headers
    _HEADERS = {"User-Agent": "CharlieAI/2.0 (Windows NT 10.0; Win64; x64)"}

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "./charlie_data/research")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._gpt_researcher_cls = self._detect_gpt_researcher()

    # ------------------------------------------------------------------ init
    def _detect_gpt_researcher(self):
        """Attempt to import GPTResearcher from the local repository."""
        try:
            from gpt_researcher import GPTResearcher  # type: ignore
            logger.info("GPT Researcher detected and imported successfully.")
            return GPTResearcher
        except Exception as exc:
            logger.debug(
                "GPT Researcher import unavailable (%s). "
                "Fallback search engine will be used.",
                exc,
            )
            return None

    # ------------------------------------------------------------------ public
    def search(
        self,
        query: str,
        max_results: int = 5,
        model_manager: Any = None,
        deep: bool = False,
        report_type: str = "research_report",
    ) -> str:
        """
        Execute a web search or autonomous research query.

        Args:
            query:        The user's question or research topic.
            max_results:  How many web results to retrieve in fallback mode.
            model_manager: Optional ModelManager for LLM-based synthesis.
            deep:         Request a full multi-source research report
                          (slow, requires GPT Researcher + API keys).
            report_type:  GPT Researcher report type string (e.g.
                          "research_report", "outline_report", "custom_report").

        Returns:
            Formatted Markdown string with the answer and sources.
        """
        clean_query = query.strip()
        if not clean_query:
            return "Please provide a search query."

        # 1. Try GPT Researcher (autonomous deep research)
        if self._gpt_researcher_cls and (deep or os.getenv("OPENAI_API_KEY")):
            try:
                result = self._run_gpt_researcher(clean_query, report_type=report_type)
                if result and len(result.strip()) > 100:
                    return result
            except Exception as exc:
                logger.warning("GPT Researcher failed (%s); using fallback.", exc)

        # 2. Resilient live search (DuckDuckGo + Wikipedia)
        return self._run_web_search(clean_query, max_results=max_results, model_manager=model_manager)

    def deep_research(self, topic: str, model_manager: Any = None) -> str:
        """
        Convenience wrapper for a full multi-source research report.
        Falls back to enhanced web search when GPT Researcher is unavailable.
        """
        return self.search(topic, max_results=8, model_manager=model_manager, deep=True)

    # ------------------------------------------------------------------ GPT Researcher
    def _run_gpt_researcher(self, query: str, report_type: str = "research_report") -> Optional[str]:
        """Run GPTResearcher in a dedicated asyncio loop inside a thread."""

        async def _coro():
            researcher = self._gpt_researcher_cls(
                query=query,
                report_type=report_type,
                verbose=False,
            )
            # Prefer quick_search when available and not requesting deep report
            if hasattr(researcher, "quick_search") and report_type != "research_report":
                summary = await researcher.quick_search(query, aggregated_summary=True)
                if summary:
                    return str(summary)
            await researcher.conduct_research()
            report = await researcher.write_report()
            return report

        result = None
        exc_holder: List[Exception] = []

        def _run():
            nonlocal result
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(_coro())
                loop.close()
            except Exception as e:
                exc_holder.append(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=120)  # 2-minute cap for deep research

        if exc_holder:
            raise exc_holder[0]
        return result

    # ------------------------------------------------------------------ fallback search
    def _run_web_search(
        self,
        query: str,
        max_results: int = 5,
        model_manager: Any = None,
    ) -> str:
        """Fetch results from DuckDuckGo and Wikipedia, then optionally synthesise."""
        results = self._fetch_duckduckgo(query, max_results=max_results)

        # Supplement with Wikipedia when few results
        if len(results) < 2:
            results.extend(self._fetch_wikipedia(query, max_results=3))

        if not results:
            return (
                f"No web results found for: **{query}**.\n"
                "Please check your internet connection or try rephrasing."
            )

        # LLM synthesis when model_manager is available
        if model_manager and hasattr(model_manager, "chat"):
            synthesised = self._synthesise_with_llm(query, results, max_results, model_manager)
            if synthesised:
                return synthesised

        # Plain formatted output
        return self._format_results(query, results, max_results)

    # ------------------------------------------------------------------ DuckDuckGo
    def _fetch_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        try:
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json"
            resp = requests.get(url, headers=self._HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()

                abstract = _strip_html(data.get("AbstractText", ""))
                abstract_url = data.get("AbstractURL", "").strip()
                heading = data.get("Heading", "").strip() or query
                if abstract and abstract_url:
                    results.append({
                        "title": heading,
                        "url": abstract_url,
                        "snippet": abstract,
                    })

                for item in data.get("RelatedTopics", []):
                    if len(results) >= max_results:
                        break
                    sub_items = item.get("Topics") or [item]
                    for sub in sub_items:
                        if len(results) >= max_results:
                            break
                        text = sub.get("Text", "")
                        url_ = sub.get("FirstURL", "")
                        if text and url_:
                            parts = text.split(" - ", 1)
                            title = parts[0] if len(parts) > 1 else text[:60]
                            snippet = parts[1] if len(parts) > 1 else text
                            results.append({"title": title, "url": url_, "snippet": snippet})
        except Exception as exc:
            logger.debug("DuckDuckGo fetch error: %s", exc)
        return results

    # ------------------------------------------------------------------ Wikipedia
    def _fetch_wikipedia(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        try:
            api_url = (
                f"https://en.wikipedia.org/w/api.php"
                f"?action=opensearch&search={quote_plus(query)}"
                f"&limit={max_results}&namespace=0&format=json"
            )
            resp = requests.get(api_url, headers=self._HEADERS, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4:
                    for title, snippet, url in zip(data[1], data[2], data[3]):
                        if title and url:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet or f"Wikipedia article: {title}",
                            })
        except Exception as exc:
            logger.debug("Wikipedia fetch error: %s", exc)
        return results

    # ------------------------------------------------------------------ LLM synthesis
    def _synthesise_with_llm(
        self,
        query: str,
        results: List[Dict[str, str]],
        max_results: int,
        model_manager: Any,
    ) -> Optional[str]:
        """Use ModelManager.chat() to synthesise search results into a coherent answer."""
        try:
            context_lines = []
            for idx, r in enumerate(results[:max_results], 1):
                context_lines.append(
                    f"[{idx}] {r['title']}\nSnippet: {r['snippet']}\nURL: {r['url']}"
                )
            context_str = "\n\n".join(context_lines)
            prompt = (
                f"You are Charlie, an intelligent assistant. Based on the following live "
                f"web search results, provide a clear, accurate, and concise answer to the "
                f"question: '{query}'\n\n"
                f"Search Results:\n{context_str}\n\n"
                f"Answer:"
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Charlie, a helpful AI assistant. "
                        "Synthesise the provided search results into a clear answer."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            answer = model_manager.chat(messages).strip()
            if answer and len(answer) > 20 and "timed out" not in answer.lower():
                sources = "\n".join(
                    f"- [{r['title']}]({r['url']})" for r in results[:max_results]
                )
                return (
                    f"**Search Results for:** *{query}*\n\n"
                    f"{answer}\n\n"
                    f"**Sources:**\n{sources}"
                )
        except Exception as exc:
            logger.debug("LLM synthesis failed: %s", exc)
        return None

    # ------------------------------------------------------------------ formatting
    @staticmethod
    def _format_results(query: str, results: List[Dict[str, str]], max_results: int) -> str:
        lines = [f"**Web Search Results for:** *{query}*\n"]
        for i, item in enumerate(results[:max_results], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            snippet = item.get("snippet", "")
            lines.append(f"**{i}. [{title}]({url})**")
            if snippet:
                lines.append(f"> {snippet}\n")
        return "\n".join(lines)

    # ------------------------------------------------------------------ info
    @property
    def gpt_researcher_available(self) -> bool:
        return self._gpt_researcher_cls is not None

    def describe(self) -> str:
        gptr = "GPT Researcher (deep research)" if self.gpt_researcher_available else "fallback web search"
        return (
            f"Web Search powered by {gptr} + DuckDuckGo + Wikipedia.\n"
            "Set OPENAI_API_KEY (or TAVILY_API_KEY) environment variables to enable GPT Researcher."
        )
