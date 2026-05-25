"""
Tests for MCP Permission Filter
Phase 0: Python Survival Kit
"""

import pytest
from mcp_permission_filter import (
    MCPServer,
    MCPTool,
    Permission,
    User,
    filter_mcp_tools,
    filter_mcp_tools_for_many,
)
from mcp_permission_filter.models import satisfies


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def github_server() -> MCPServer:
    return MCPServer(
        server_id="github",
        display_name="GitHub MCP",
        tools=[
            MCPTool(name="list_repos",   description="List repos",      required_permission=Permission.READ),
            MCPTool(name="create_issue", description="Create issue",    required_permission=Permission.WRITE),
            MCPTool(name="delete_repo",  description="Delete repo",     required_permission=Permission.ADMIN),
        ],
    )


@pytest.fixture
def slack_server() -> MCPServer:
    return MCPServer(
        server_id="slack",
        display_name="Slack MCP",
        tools=[
            MCPTool(name="list_channels", description="List channels",  required_permission=Permission.READ),
            MCPTool(name="post_message",  description="Post message",   required_permission=Permission.WRITE),
        ],
    )


@pytest.fixture
def admin_user() -> User:
    return User(
        user_id="alice",
        name="Alice",
        server_permissions={"github": Permission.ADMIN, "slack": Permission.ADMIN},
    )


@pytest.fixture
def write_user() -> User:
    return User(
        user_id="bob",
        name="Bob",
        server_permissions={"github": Permission.WRITE},
    )


@pytest.fixture
def read_user() -> User:
    return User(
        user_id="carol",
        name="Carol",
        server_permissions={"github": Permission.READ, "slack": Permission.READ},
    )


@pytest.fixture
def no_access_user() -> User:
    return User(user_id="dave", name="Dave", server_permissions={})


# ---------------------------------------------------------------------------
# Permission hierarchy tests
# ---------------------------------------------------------------------------

class TestPermissionHierarchy:
    def test_read_satisfies_read(self):
        assert satisfies(Permission.READ, Permission.READ) is True

    def test_read_does_not_satisfy_write(self):
        assert satisfies(Permission.READ, Permission.WRITE) is False

    def test_read_does_not_satisfy_admin(self):
        assert satisfies(Permission.READ, Permission.ADMIN) is False

    def test_write_satisfies_read(self):
        assert satisfies(Permission.WRITE, Permission.READ) is True

    def test_write_satisfies_write(self):
        assert satisfies(Permission.WRITE, Permission.WRITE) is True

    def test_write_does_not_satisfy_admin(self):
        assert satisfies(Permission.WRITE, Permission.ADMIN) is False

    def test_admin_satisfies_all(self):
        for perm in Permission:
            assert satisfies(Permission.ADMIN, perm) is True


# ---------------------------------------------------------------------------
# User.can_use_tool tests
# ---------------------------------------------------------------------------

class TestUserCanUseTool:
    def test_admin_can_use_admin_tool(self, admin_user, github_server):
        delete_tool = github_server.get_tool("delete_repo")
        assert admin_user.can_use_tool("github", delete_tool) is True

    def test_write_user_cannot_use_admin_tool(self, write_user, github_server):
        delete_tool = github_server.get_tool("delete_repo")
        assert write_user.can_use_tool("github", delete_tool) is False

    def test_write_user_can_use_write_tool(self, write_user, github_server):
        create_tool = github_server.get_tool("create_issue")
        assert write_user.can_use_tool("github", create_tool) is True

    def test_write_user_can_use_read_tool(self, write_user, github_server):
        list_tool = github_server.get_tool("list_repos")
        assert write_user.can_use_tool("github", list_tool) is True

    def test_no_access_user_cannot_use_any_tool(self, no_access_user, github_server):
        for tool in github_server.tools:
            assert no_access_user.can_use_tool("github", tool) is False

    def test_user_without_server_permission_denied(self, write_user, slack_server):
        # Bob has no slack permissions
        list_tool = slack_server.get_tool("list_channels")
        assert write_user.can_use_tool("slack", list_tool) is False


# ---------------------------------------------------------------------------
# filter_mcp_tools tests
# ---------------------------------------------------------------------------

class TestFilterMCPTools:
    def test_admin_sees_all_tools(self, admin_user, github_server, slack_server):
        view = filter_mcp_tools(admin_user, [github_server, slack_server])
        assert len(view.authorized_tools["github"]) == 3
        assert len(view.authorized_tools["slack"]) == 2
        assert view.total_tools == 5

    def test_write_user_sees_read_and_write_tools_only(self, write_user, github_server):
        view = filter_mcp_tools(write_user, [github_server])
        tool_names = {t.name for t in view.authorized_tools["github"]}
        assert "list_repos" in tool_names      # read tool ✓
        assert "create_issue" in tool_names    # write tool ✓
        assert "delete_repo" not in tool_names # admin tool ✗

    def test_read_user_sees_only_read_tools(self, read_user, github_server):
        view = filter_mcp_tools(read_user, [github_server])
        tool_names = {t.name for t in view.authorized_tools["github"]}
        assert tool_names == {"list_repos"}

    def test_no_access_user_gets_empty_view(self, no_access_user, github_server, slack_server):
        view = filter_mcp_tools(no_access_user, [github_server, slack_server])
        assert view.authorized_tools == {}
        assert view.total_tools == 0

    def test_server_without_permission_omitted_from_view(self, write_user, github_server, slack_server):
        # Bob has github write but no slack access
        view = filter_mcp_tools(write_user, [github_server, slack_server])
        assert "github" in view.authorized_tools
        assert "slack" not in view.authorized_tools

    def test_user_id_and_name_preserved(self, read_user, github_server):
        view = filter_mcp_tools(read_user, [github_server])
        assert view.user_id == "carol"
        assert view.user_name == "Carol"

    def test_empty_server_list_returns_empty_view(self, admin_user):
        view = filter_mcp_tools(admin_user, [])
        assert view.authorized_tools == {}


# ---------------------------------------------------------------------------
# filter_mcp_tools_for_many tests
# ---------------------------------------------------------------------------

class TestBatchFilter:
    def test_returns_entry_for_every_user(self, admin_user, write_user, read_user, github_server):
        users = [admin_user, write_user, read_user]
        result = filter_mcp_tools_for_many(users, [github_server])
        assert set(result.keys()) == {"alice", "bob", "carol"}

    def test_each_entry_is_correct(self, admin_user, write_user, github_server):
        result = filter_mcp_tools_for_many([admin_user, write_user], [github_server])
        alice_tools = {t.name for t in result["alice"].authorized_tools.get("github", [])}
        bob_tools   = {t.name for t in result["bob"].authorized_tools.get("github", [])}
        assert "delete_repo" in alice_tools
        assert "delete_repo" not in bob_tools


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------

class TestModelValidation:
    def test_duplicate_tool_names_raise_error(self):
        with pytest.raises(ValueError, match="Duplicate tool names"):
            MCPServer(
                server_id="bad",
                display_name="Bad Server",
                tools=[
                    MCPTool(name="dup", description="first",  required_permission=Permission.READ),
                    MCPTool(name="dup", description="second", required_permission=Permission.WRITE),
                ],
            )

    def test_invalid_permission_value_raises_error(self):
        with pytest.raises(Exception):
            MCPTool(name="x", description="y", required_permission="superuser")  # type: ignore

    def test_get_tool_returns_none_for_unknown(self, github_server):
        assert github_server.get_tool("nonexistent") is None
