"""
tools/github_tools.py

Client-side GitHub tools for the Tool Use Rings demo.
Uses the GitHub REST API — no auth required for public repos (60 req/hr).

These are CLIENT-SIDE tools: the Anthropic SDK sends a tool_use block,
our Python code executes the HTTP call, and we return a tool_result.
Compare with MCP SERVER-SIDE tools where a remote process handles execution.
"""

import json
import requests
from typing import Any

# ── Tool Schemas ──────────────────────────────────────────────────────────────
# These are sent to Claude in every messages.create() call so it knows
# what tools exist and how to call them.

GET_GITHUB_REPO_SCHEMA = {
    "name": "get_github_repo",
    "description": (
        "Fetch metadata for a public GitHub repository: description, star count, "
        "fork count, open issue count, language, and last push timestamp."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "owner": {
                "type": "string",
                "description": "GitHub username or organisation (e.g. 'anthropics')"
            },
            "repo": {
                "type": "string",
                "description": "Repository name (e.g. 'anthropic-sdk-python')"
            }
        },
        "required": ["owner", "repo"]
    }
}

GET_GITHUB_ISSUES_SCHEMA = {
    "name": "get_github_issues",
    "description": (
        "Return the most recent open issues for a GitHub repository, including "
        "title, number, label names, and creation date."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "owner": {"type": "string", "description": "GitHub org/user"},
            "repo":  {"type": "string", "description": "Repository name"},
            "limit": {
                "type": "integer",
                "description": "Max issues to return (default 5, max 10)",
                "default": 5
            }
        },
        "required": ["owner", "repo"]
    }
}

GET_GITHUB_PRS_SCHEMA = {
    "name": "get_github_prs",
    "description": (
        "Return the most recent open pull requests for a GitHub repository, "
        "including title, number, author, and creation date."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "repo":  {"type": "string"},
            "limit": {"type": "integer", "default": 5}
        },
        "required": ["owner", "repo"]
    }
}

GET_GITHUB_CONTRIBUTORS_SCHEMA = {
    "name": "get_github_contributors",
    "description": "Return the top contributors of a repository by commit count.",
    "input_schema": {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "repo":  {"type": "string"},
            "limit": {"type": "integer", "default": 5}
        },
        "required": ["owner", "repo"]
    }
}

# Registry: name → schema (handy for building tool lists per ring)
ALL_GITHUB_SCHEMAS = {
    "get_github_repo":         GET_GITHUB_REPO_SCHEMA,
    "get_github_issues":       GET_GITHUB_ISSUES_SCHEMA,
    "get_github_prs":          GET_GITHUB_PRS_SCHEMA,
    "get_github_contributors": GET_GITHUB_CONTRIBUTORS_SCHEMA,
}

# ── Tool Implementations ──────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github.v3+json"}


def get_github_repo(owner: str, repo: str) -> dict[str, Any]:
    """Fetch repo metadata. Raises on non-200 status."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    return {
        "full_name":      data["full_name"],
        "description":    data.get("description", ""),
        "stars":          data["stargazers_count"],
        "forks":          data["forks_count"],
        "open_issues":    data["open_issues_count"],
        "language":       data.get("language", "unknown"),
        "last_pushed_at": data["pushed_at"],
        "html_url":       data["html_url"],
    }


def get_github_issues(owner: str, repo: str, limit: int = 5) -> list[dict]:
    limit = min(limit, 10)
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    r = requests.get(
        url,
        headers=HEADERS,
        params={"state": "open", "per_page": limit, "sort": "created", "direction": "desc"},
        timeout=10
    )
    r.raise_for_status()
    return [
        {
            "number":     i["number"],
            "title":      i["title"],
            "labels":     [lbl["name"] for lbl in i.get("labels", [])],
            "created_at": i["created_at"],
            "url":        i["html_url"],
        }
        for i in r.json()
        if "pull_request" not in i   # exclude PRs from issues endpoint
    ][:limit]


def get_github_prs(owner: str, repo: str, limit: int = 5) -> list[dict]:
    limit = min(limit, 10)
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    r = requests.get(
        url,
        headers=HEADERS,
        params={"state": "open", "per_page": limit, "sort": "created", "direction": "desc"},
        timeout=10
    )
    r.raise_for_status()
    return [
        {
            "number":     pr["number"],
            "title":      pr["title"],
            "author":     pr["user"]["login"],
            "created_at": pr["created_at"],
            "url":        pr["html_url"],
        }
        for pr in r.json()
    ][:limit]


def get_github_contributors(owner: str, repo: str, limit: int = 5) -> list[dict]:
    limit = min(limit, 10)
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contributors"
    r = requests.get(url, headers=HEADERS, params={"per_page": limit}, timeout=10)
    r.raise_for_status()
    return [
        {"login": c["login"], "contributions": c["contributions"]}
        for c in r.json()
    ][:limit]


# ── Dispatcher ────────────────────────────────────────────────────────────────

def execute_github_tool(tool_name: str, tool_input: dict) -> tuple[str, bool]:
    """
    Execute a GitHub tool by name.

    Returns (result_json_string, is_error).
    is_error=True signals to Claude that the tool failed — it will adapt.
    """
    dispatch = {
        "get_github_repo":         get_github_repo,
        "get_github_issues":       get_github_issues,
        "get_github_prs":          get_github_prs,
        "get_github_contributors": get_github_contributors,
    }
    fn = dispatch.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"}), True
    try:
        result = fn(**tool_input)
        return json.dumps(result, indent=2), False
    except requests.HTTPError as e:
        status = e.response.status_code if e.response else "unknown"
        msg = f"GitHub API error {status} for {tool_name}({tool_input})"
        return json.dumps({"error": msg, "status_code": status}), True
    except Exception as e:
        return json.dumps({"error": str(e)}), True
