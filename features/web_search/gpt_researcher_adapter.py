"""
GPT Researcher Adapter for Charlie AI.

Provides web search and autonomous research functionality using the integrated
GPT Researcher codebase, with an intelligent real-time fallback engine when
heavy dependencies or external API keys are unavailable.
"""

import asyncio
import html
import json
import logging
import re
import sys
import threading
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

logger = logging.getLogger(__name__)

# Ensure Charlie project root is first in sys.path so its packages (cli, core, etc.) are never shadowed
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_ROOT_STR = str(_PROJECT_ROOT)
if _PROJECT_ROOT_STR in sys.path:
    sys.path.remove(_PROJECT_ROOT_STR)
sys.path.insert(0, _PROJECT_ROOT_STR)

_CANDIDATE_PATHS = [
    _PROJECT_ROOT / "gpt-researcher-main" / "gpt-researcher-main",
    _PROJECT_ROOT / "gpt-researcher-main",
]
for p in _CANDIDATE_PATHS:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))


class _SimpleHTMLTextExtractor(HTMLParser):
    """Strips HTML tags and extracts plain text."""

    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def get_text(self) -> str:
        return "".join(self.result).strip()


def strip_html(html_str: str) -> str:
    """Strip tags and unescape HTML entities."""
    if not html_str:
        return ""
    parser = _SimpleHTMLTextExtractor()
    try:
        parser.feed(html_str)
        text = parser.get_text()
    except Exception:
        text = re.sub(r"<[^>]+>", "", html_str)
    return html.unescape(text).strip()


class GPTResearcherAdapter:
    """
    Adapter that leverages GPT Researcher for web search and research.
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "./offline_assistant_data")
        self._gpt_researcher_cls = self._detect_gpt_researcher()

    def _detect_gpt_researcher(self):
        """Try to import GPTResearcher from the local repository."""
        try:
            from gpt_researcher import GPTResearcher
            logger.info("GPT Researcher successfully detected and imported.")
            return GPTResearcher
        except Exception as e:
            logger.debug(f"GPT Researcher direct import unavailable: {e}. Fallback searcher will be used.")
            return None

    def search(
        self,
        query: str,
        max_results: int = 5,
        model_manager: Any = None,
        deep: bool = False,
    ) -> str:
        """
        Execute web search for the given query.

        Args:
            query: The search or research query.
            max_results: Maximum number of search results to retrieve.
            model_manager: Optional ModelManager instance to synthesize results.
            deep: If True and GPT Researcher is available, run full deep research.

        Returns:
            Formatted markdown response with research answer and sources.
        """
        clean_query = query.strip()
        if not clean_query:
            return "Please provide a query to search the web."

        # 1. Attempt using GPTResearcher if available and configured
        if self._gpt_researcher_cls:
            try:
                result = self._run_gpt_researcher(clean_query, deep=deep)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"GPT Researcher execution failed, falling back: {e}")

        # 2. Resilient live web search engine
        return self._run_web_search(clean_query, max_results=max_results, model_manager=model_manager)

    def _run_gpt_researcher(self, query: str, deep: bool = False) -> Optional[str]:
        """Execute autonomous research using GPTResearcher in an asyncio event loop."""
        async def _research_coro():
            report_type = "research_report" if deep else "quick"
            researcher = self._gpt_researcher_cls(
                query=query,
                report_type=report_type,
                verbose=False,
            )
            # Try quick search if available
            if hasattr(researcher, "quick_search") and not deep:
                summary = await researcher.quick_search(query, aggregated_summary=True)
                if summary:
                    return str(summary)
            await researcher.conduct_research()
            report = await researcher.write_report()
            return report

        try:
            # Run in a separate thread if an asyncio loop is already running
            result = None
            exception = None

            def _target():
                nonlocal result, exception
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(_research_coro())
                    loop.close()
                except Exception as ex:
                    exception = ex

            t = threading.Thread(target=_target)
            t.start()
            t.join(timeout=60)

            if exception:
                raise exception
            return result
        except Exception as e:
            logger.debug(f"_run_gpt_researcher failed: {e}")
            return None

    def _run_web_search(
        self,
        query: str,
        max_results: int = 5,
        model_manager: Any = None,
    ) -> str:
        """Fetch live search results from web providers and synthesize response."""
        results = self._fetch_duckduckgo_results(query, max_results=max_results)

        # If DuckDuckGo returned few or no results, supplement with Wikipedia
        if len(results) < 2:
            wiki_results = self._fetch_wikipedia_results(query, max_results=3)
            results.extend(wiki_results)

        if not results:
            return f"No web search results found for: **{query}**.\nPlease check your connection or refine the search query."

        # If model_manager is available, synthesize results with local LLM
        if model_manager and hasattr(model_manager, "chat"):
            try:
                context_lines = []
                for idx, r in enumerate(results[:max_results], 1):
                    context_lines.append(f"[{idx}] {r['title']}\nSnippet: {r['snippet']}\nURL: {r['url']}")
                context_str = "\n\n".join(context_lines)

                prompt = (
                    f"You are Charlie, an intelligent assistant. Based on these live web search results, "
                    f"provide a clear, concise, and accurate answer to the user's question: '{query}'.\n\n"
                    f"Web Search Results:\n{context_str}\n\n"
                    f"Answer clearly and concisely:"
                )

                messages = [
                    {"role": "system", "content": "You are Charlie, a helpful AI assistant. Answer using the provided search results."},
                    {"role": "user", "content": prompt},
                ]
                summary = model_manager.chat(messages).strip()
                if summary and len(summary) > 20 and "timed out" not in summary.lower():
                    sources_str = "\n".join(
                        [f"- [{r['title']}]({r['url']})" for r in results[:max_results]]
                    )
                    return f"**Search Results for:** *{query}*\n\n{summary}\n\n**Sources:**\n{sources_str}"
            except Exception as e:
                logger.debug(f"LLM synthesis failed: {e}")

        # Direct formatted output with rich snippets
        output = [f"**Web Search Results for:** *{query}*\n"]
        for i, item in enumerate(results[:max_results], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            snippet = item.get("snippet", "")
            output.append(f"**{i}. [{title}]({url})**")
            if snippet:
                output.append(f"> {snippet}\n")

        return "\n".join(output)

    def _fetch_duckduckgo_results(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fetch search results from DuckDuckGo Instant Answer API."""
        results = []
        try:
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json"
            headers = {"User-Agent": "CharlieAssistant/1.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code in (200, 202):
                data = resp.json()
                abstract = data.get("AbstractText", "").strip()
                abstract_url = data.get("AbstractURL", "").strip()
                heading = data.get("Heading", "").strip() or query

                if abstract and abstract_url:
                    results.append({
                        "title": heading,
                        "url": abstract_url,
                        "snippet": abstract,
                    })

                # Check RelatedTopics
                related = data.get("RelatedTopics", [])
                for item in related:
                    if len(results) >= max_results:
                        break
                    # If it's a category cluster
                    if "Topics" in item:
                        for sub in item["Topics"]:
                            if len(results) >= max_results:
                                break
                            text = sub.get("Text", "")
                            first_url = sub.get("FirstURL", "")
                            if text and first_url:
                                parts = text.split(" - ", 1)
                                t = parts[0] if len(parts) > 1 else text[:50]
                                s = parts[1] if len(parts) > 1 else text
                                results.append({"title": t, "url": first_url, "snippet": s})
                    else:
                        text = item.get("Text", "")
                        first_url = item.get("FirstURL", "")
                        if text and first_url:
                            parts = text.split(" - ", 1)
                            t = parts[0] if len(parts) > 1 else text[:50]
                            s = parts[1] if len(parts) > 1 else text
                            results.append({"title": t, "url": first_url, "snippet": s})
        except Exception as e:
            logger.debug(f"DuckDuckGo API exception: {e}")

        return results

    def _fetch_wikipedia_results(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Fetch encyclopedic results from Wikipedia OpenSearch API."""
        results = []
        try:
            api_url = (
                f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}"
                f"&limit={max_results}&namespace=0&format=json"
            )
            headers = {"User-Agent": "CharlieAssistant/1.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(api_url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4:
                    titles = data[1]
                    snippets = data[2]
                    urls = data[3]
                    for t, s, u in zip(titles, snippets, urls):
                        if t and u:
                            results.append({
                                "title": t,
                                "url": u,
                                "snippet": s or f"Wikipedia article regarding {t}",
                            })
        except Exception as e:
            logger.debug(f"Wikipedia search exception: {e}")
        return results
