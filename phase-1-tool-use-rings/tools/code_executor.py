"""
tools/code_executor.py

Client-side Python code execution tool.
Runs arbitrary Python snippets in a subprocess with a timeout.

WHY THIS MATTERS FOR TOOL USE:
Claude cannot execute code by itself — it generates code, then calls this tool.
The client (us) runs it in a sandboxed subprocess and returns stdout/stderr.
This is the same pattern behind Claude.ai's code execution feature, just local.
"""

import json
import subprocess
import sys
import textwrap

# ── Tool Schema ───────────────────────────────────────────────────────────────

EXECUTE_PYTHON_SCHEMA = {
    "name": "execute_python",
    "description": (
        "Execute a Python 3 code snippet and return its stdout and stderr. "
        "Use this to run calculations, parse data, or validate logic. "
        "The snippet runs in an isolated subprocess with a 10-second timeout."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Valid Python 3 code to execute. Use print() for output."
            },
            "timeout": {
                "type": "integer",
                "description": "Max execution time in seconds (default 10, max 30)",
                "default": 10
            }
        },
        "required": ["code"]
    }
}

# ── Tool Implementation ───────────────────────────────────────────────────────

def execute_python(code: str, timeout: int = 10) -> dict:
    """
    Run Python code in a subprocess. Returns {"stdout", "stderr", "returncode"}.

    Capped at 30s even if caller requests more — safety guardrail.
    """
    timeout = min(timeout, 30)
    # Dedent so Claude can write indented code blocks naturally
    code = textwrap.dedent(code)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout":     proc.stdout.strip(),
            "stderr":     proc.stderr.strip(),
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout":     "",
            "stderr":     f"Execution timed out after {timeout}s",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "stdout":     "",
            "stderr":     str(e),
            "returncode": -1,
        }


def execute_code_tool(tool_name: str, tool_input: dict) -> tuple[str, bool]:
    """Dispatcher matching the pattern used across all tools."""
    if tool_name != "execute_python":
        return json.dumps({"error": f"Unknown tool: {tool_name}"}), True
    result = execute_python(
        code=tool_input["code"],
        timeout=tool_input.get("timeout", 10)
    )
    is_error = result["returncode"] != 0
    return json.dumps(result, indent=2), is_error
