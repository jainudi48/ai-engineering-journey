"""
tests/test_rings.py

Unit tests for tool implementations (no API key needed — tests the client-side
execution layer independently of Claude). Integration tests for the rings are
run with the full demo.py.
"""

import json
import pytest
from unittest.mock import patch
from tools.github_tools   import get_github_repo, execute_github_tool
from tools.code_executor  import execute_python, execute_code_tool
from tools.web_search_tool import web_search, execute_search_tool
from tools                import execute_tool, schemas_for, ALL_SCHEMAS


# ══════════════════════════════════════════════════════════════════════════════
#  Tool schema tests (no network)
# ══════════════════════════════════════════════════════════════════════════════

class TestToolSchemas:
    def test_all_schemas_have_required_keys(self):
        for name, schema in ALL_SCHEMAS.items():
            assert "name" in schema,         f"{name}: missing 'name'"
            assert "description" in schema,  f"{name}: missing 'description'"
            assert "input_schema" in schema, f"{name}: missing 'input_schema'"
            assert schema["input_schema"]["type"] == "object"

    def test_schemas_for_returns_subset(self):
        subset = schemas_for("get_github_repo", "web_search")
        assert len(subset) == 2
        names = {s["name"] for s in subset}
        assert names == {"get_github_repo", "web_search"}

    def test_schemas_for_ignores_unknown_names(self):
        result = schemas_for("get_github_repo", "nonexistent_tool")
        assert len(result) == 1


# ══════════════════════════════════════════════════════════════════════════════
#  Code executor tests (no network)
# ══════════════════════════════════════════════════════════════════════════════

class TestCodeExecutor:
    def test_simple_print(self):
        result = execute_python("print('hello tool use')")
        assert result["stdout"] == "hello tool use"
        assert result["returncode"] == 0

    def test_arithmetic(self):
        result = execute_python("print(2 ** 10)")
        assert result["stdout"] == "1024"

    def test_syntax_error_returns_stderr(self):
        result = execute_python("def broken(")
        assert result["returncode"] != 0
        assert result["stderr"]  # some error message

    def test_timeout_respected(self):
        result = execute_python("import time; time.sleep(60)", timeout=1)
        assert result["returncode"] == -1
        assert "timed out" in result["stderr"].lower()

    def test_dispatcher_is_error_on_failure(self):
        result_json, is_error = execute_code_tool(
            "execute_python", {"code": "raise RuntimeError('boom')"}
        )
        assert is_error is True
        data = json.loads(result_json)
        assert data["returncode"] != 0

    def test_dispatcher_ok_on_success(self):
        result_json, is_error = execute_code_tool(
            "execute_python", {"code": "print(42)"}
        )
        assert is_error is False
        data = json.loads(result_json)
        assert data["stdout"] == "42"

    def test_dispatcher_unknown_tool(self):
        result_json, is_error = execute_code_tool("not_a_tool", {})
        assert is_error is True


# ══════════════════════════════════════════════════════════════════════════════
#  GitHub tools tests (mocked network)
# ══════════════════════════════════════════════════════════════════════════════

MOCK_REPO_RESPONSE = {
    "full_name":        "anthropics/anthropic-sdk-python",
    "description":      "The official Python library for the Anthropic API",
    "stargazers_count": 5000,
    "forks_count":      400,
    "open_issues_count": 30,
    "language":         "Python",
    "pushed_at":        "2026-05-01T12:00:00Z",
    "html_url":         "https://github.com/anthropics/anthropic-sdk-python",
}


class TestGitHubTools:
    def test_get_github_repo_shapes_response(self):
        import requests
        with patch("tools.github_tools.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_REPO_RESPONSE
            mock_get.return_value.raise_for_status = lambda: None

            result = get_github_repo("anthropics", "anthropic-sdk-python")

        assert result["stars"] == 5000
        assert result["language"] == "Python"
        assert "full_name" in result

    def test_execute_github_tool_404_is_error(self):
        import requests
        with patch("tools.github_tools.requests.get") as mock_get:
            resp = mock_get.return_value
            resp.raise_for_status.side_effect = requests.HTTPError(
                response=type("R", (), {"status_code": 404})()
            )
            result_json, is_error = execute_github_tool(
                "get_github_repo", {"owner": "x", "repo": "private"}
            )

        assert is_error is True
        data = json.loads(result_json)
        assert "error" in data

    def test_execute_github_tool_unknown_name(self):
        result_json, is_error = execute_github_tool("nonexistent", {})
        assert is_error is True


# ══════════════════════════════════════════════════════════════════════════════
#  Unified dispatcher tests
# ══════════════════════════════════════════════════════════════════════════════

class TestUnifiedDispatcher:
    def test_routes_to_code_executor(self):
        result_json, is_error = execute_tool(
            "execute_python", {"code": "print('dispatched')"}
        )
        assert is_error is False
        assert "dispatched" in json.loads(result_json)["stdout"]

    def test_unknown_tool_returns_error(self):
        result_json, is_error = execute_tool("totally_unknown_tool", {})
        assert is_error is True
        data = json.loads(result_json)
        assert "error" in data


# ══════════════════════════════════════════════════════════════════════════════
#  ToolRunner unit tests (mocked client)
# ══════════════════════════════════════════════════════════════════════════════

class TestToolRunner:
    def test_runner_init_with_subset(self):
        from rings.ring5_beta_sdk import ToolRunner
        runner = ToolRunner(tool_names=["get_github_repo", "web_search"])
        names = {t["name"] for t in runner.tools}
        assert names == {"get_github_repo", "web_search"}

    def test_for_github_classmethod(self):
        from rings.ring5_beta_sdk import ToolRunner
        runner = ToolRunner.for_github()
        names = {t["name"] for t in runner.tools}
        assert "get_github_repo" in names
        assert "get_github_issues" in names

    def test_for_research_classmethod(self):
        from rings.ring5_beta_sdk import ToolRunner
        runner = ToolRunner.for_research()
        names = {t["name"] for t in runner.tools}
        assert "web_search" in names
        assert "execute_python" in names
