"""
tools/web_search_tool.py

Client-side web search tool using DuckDuckGo's free Instant Answer API.
No API key required. Returns top abstract/results for a query.

IN A PRODUCTION SYSTEM this would be an MCP server tool:
  - A remote MCP server process exposes a "web_search" tool
  - Claude SDK connects to it via SSE or stdio transport
  - The server handles rate limiting, caching, auth
Here we keep it client-side to stay self-contained.
"""

import json
import requests
from typing import Any

# ── Tool Schema ───────────────────────────────────────────────────────────────

WEB_SEARCH_SCHEMA = {
    "name": "web_search",
    "description": (
        "Search the web for current information about a topic. "
        "Returns a short abstract and related topics. "
        "Use when you need facts that may not be in your training data, "
        "such as recent library releases, known bugs, or current documentation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (concise, keyword-style works best)"
            }
        },
        "required": ["query"]
    }
}

# ── Tool Implementation ───────────────────────────────────────────────────────

DDG_API = "https://api.duckduckgo.com/"


def web_search(query: str) -> dict[str, Any]:
    """
    Hit DuckDuckGo's Instant Answer API.
    Falls back gracefully if the API returns no abstract.
    """
    try:
        r = requests.get(
            DDG_API,
            params={
                "q":              query,
                "format":         "json",
                "no_html":        "1",
                "skip_disambig":  "1",
            },
            timeout=10,
            headers={"User-Agent": "tool-use-rings-demo/1.0"}
        )
        r.raise_for_status()
        data = r.json()

        abstract  = data.get("Abstract", "").strip()
        source    = data.get("AbstractSource", "")
        source_url= data.get("AbstractURL", "")
        related   = [
            {"text": t.get("Text", ""), "url": t.get("FirstURL", "")}
            for t in data.get("RelatedTopics", [])[:3]
            if isinstance(t, dict) and "Text" in t
        ]

        if not abstract and not related:
            return {
                "abstract": "No instant answer found. Try a more specific query.",
                "source":   "",
                "related":  [],
                "query":    query,
            }

        return {
            "abstract":   abstract or "No summary available.",
            "source":     source,
            "source_url": source_url,
            "related":    related,
            "query":      query,
        }

    except Exception as e:
        return {
            "abstract": f"Search failed: {e}",
            "source":   "",
            "related":  [],
            "query":    query,
        }


def execute_search_tool(tool_name: str, tool_input: dict) -> tuple[str, bool]:
    """Dispatcher matching the pattern used across all tools."""
    if tool_name != "web_search":
        return json.dumps({"error": f"Unknown tool: {tool_name}"}), True
    result = web_search(query=tool_input["query"])
    is_error = result["abstract"].startswith("Search failed")
    return json.dumps(result, indent=2), is_error
