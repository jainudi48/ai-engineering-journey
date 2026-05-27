"""
tools/__init__.py

Unified tool dispatcher — routes any tool_use block to the right implementation.
All rings import this so they never care which module owns which tool.
"""

import json
from .github_tools    import execute_github_tool, ALL_GITHUB_SCHEMAS
from .code_executor   import execute_code_tool,   EXECUTE_PYTHON_SCHEMA
from .web_search_tool import execute_search_tool, WEB_SEARCH_SCHEMA

# ── All available schemas ─────────────────────────────────────────────────────

ALL_SCHEMAS = {
    **ALL_GITHUB_SCHEMAS,
    "execute_python": EXECUTE_PYTHON_SCHEMA,
    "web_search":     WEB_SEARCH_SCHEMA,
}


def execute_tool(tool_name: str, tool_input: dict) -> tuple[str, bool]:
    """
    Unified dispatcher: given a tool name and its input dict,
    route to the correct implementation and return (result_json, is_error).

    This is the CLIENT-SIDE execution layer — what runs AFTER Claude
    emits a tool_use block with stop_reason="tool_use".
    """
    github_tools = set(ALL_GITHUB_SCHEMAS.keys())
    if tool_name in github_tools:
        return execute_github_tool(tool_name, tool_input)
    elif tool_name == "execute_python":
        return execute_code_tool(tool_name, tool_input)
    elif tool_name == "web_search":
        return execute_search_tool(tool_name, tool_input)
    else:
        return json.dumps({"error": f"No implementation for tool: {tool_name}"}), True


def schemas_for(*names: str) -> list[dict]:
    """Return tool schemas by name. Convenient for building per-ring tool lists."""
    return [ALL_SCHEMAS[n] for n in names if n in ALL_SCHEMAS]
