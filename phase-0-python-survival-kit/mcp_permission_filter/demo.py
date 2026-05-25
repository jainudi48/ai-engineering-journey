"""
MCP Permission Filter — Demo
Phase 0: Python Survival Kit

Scenario
--------
Your AI platform is connected to 4 MCP servers:
  • github  — code operations
  • slack   — messaging
  • notion  — knowledge base
  • jira    — issue tracker

You have 4 users with varying permission levels. Run this script to see
exactly which tools each user is allowed to call.
"""

from __future__ import annotations

from mcp_permission_filter import (
    MCPServer,
    MCPTool,
    Permission,
    User,
    filter_mcp_tools,
    filter_mcp_tools_for_many,
)


# ---------------------------------------------------------------------------
# 1. Define MCP servers and their tools
# ---------------------------------------------------------------------------

SERVERS: list[MCPServer] = [
    MCPServer(
        server_id="github",
        display_name="GitHub MCP",
        tools=[
            MCPTool(name="list_repos",    description="List repositories",              required_permission=Permission.READ),
            MCPTool(name="get_issue",     description="Fetch a single issue",           required_permission=Permission.READ),
            MCPTool(name="create_issue",  description="Open a new issue",               required_permission=Permission.WRITE),
            MCPTool(name="merge_pr",      description="Merge a pull request",           required_permission=Permission.WRITE),
            MCPTool(name="delete_repo",   description="Permanently delete a repository",required_permission=Permission.ADMIN),
            MCPTool(name="add_collaborator", description="Add a repo collaborator",     required_permission=Permission.ADMIN),
        ],
    ),
    MCPServer(
        server_id="slack",
        display_name="Slack MCP",
        tools=[
            MCPTool(name="list_channels",  description="List public channels",           required_permission=Permission.READ),
            MCPTool(name="read_messages",  description="Read messages in a channel",     required_permission=Permission.READ),
            MCPTool(name="post_message",   description="Post a message to a channel",    required_permission=Permission.WRITE),
            MCPTool(name="delete_message", description="Delete any message (mod power)", required_permission=Permission.ADMIN),
        ],
    ),
    MCPServer(
        server_id="notion",
        display_name="Notion MCP",
        tools=[
            MCPTool(name="search_pages",  description="Search across workspace",         required_permission=Permission.READ),
            MCPTool(name="read_page",     description="Read a page's content",           required_permission=Permission.READ),
            MCPTool(name="create_page",   description="Create a new page",               required_permission=Permission.WRITE),
            MCPTool(name="update_page",   description="Edit an existing page",           required_permission=Permission.WRITE),
            MCPTool(name="delete_page",   description="Permanently delete a page",       required_permission=Permission.ADMIN),
        ],
    ),
    MCPServer(
        server_id="jira",
        display_name="Jira MCP",
        tools=[
            MCPTool(name="list_issues",   description="List issues in a project",        required_permission=Permission.READ),
            MCPTool(name="get_issue",     description="Get issue details",               required_permission=Permission.READ),
            MCPTool(name="create_issue",  description="Create a new ticket",             required_permission=Permission.WRITE),
            MCPTool(name="transition_issue", description="Move issue through workflow",  required_permission=Permission.WRITE),
            MCPTool(name="delete_project", description="Delete an entire Jira project",  required_permission=Permission.ADMIN),
        ],
    ),
]


# ---------------------------------------------------------------------------
# 2. Define users with their permission grants
# ---------------------------------------------------------------------------

USERS: list[User] = [
    User(
        user_id="alice",
        name="Alice (Platform Admin)",
        server_permissions={
            "github": Permission.ADMIN,
            "slack":  Permission.ADMIN,
            "notion": Permission.ADMIN,
            "jira":   Permission.ADMIN,
        },
    ),
    User(
        user_id="bob",
        name="Bob (Developer)",
        server_permissions={
            "github": Permission.WRITE,   # can open PRs, issues — not delete repos
            "slack":  Permission.WRITE,   # can post messages
            "notion": Permission.READ,    # read-only on Notion
            # jira: no access
        },
    ),
    User(
        user_id="carol",
        name="Carol (Analyst / Read-only)",
        server_permissions={
            "github": Permission.READ,
            "slack":  Permission.READ,
            "notion": Permission.READ,
            "jira":   Permission.READ,
        },
    ),
    User(
        user_id="dave",
        name="Dave (External Contractor)",
        server_permissions={
            "jira": Permission.WRITE,     # can create & transition tickets only
            # no access to github, slack, notion
        },
    ),
]


# ---------------------------------------------------------------------------
# 3. Run the filter and print results
# ---------------------------------------------------------------------------

def main() -> None:
    separator = "=" * 60

    print(separator)
    print("  MCP PERMISSION FILTER — DEMO")
    print(separator)

    # --- Single user example ---
    print("\n[Single user] Filtering for Bob...\n")
    bob_view = filter_mcp_tools(USERS[1], SERVERS)
    print(bob_view.summary())

    # --- Batch example ---
    print(f"\n{separator}")
    print("  BATCH FILTER — All Users")
    print(separator)

    all_views = filter_mcp_tools_for_many(USERS, SERVERS)

    for user_id, view in all_views.items():
        print(f"\n{view.summary()}")
        print("-" * 40)

    # --- Quick access check ---
    print("\n[Access checks]")
    alice = USERS[0]
    carol = USERS[2]
    dave  = USERS[3]
    github = SERVERS[0]

    delete_repo_tool = github.get_tool("delete_repo")
    print(f"  Alice can delete_repo?  {alice.can_use_tool('github', delete_repo_tool)}")   # True
    print(f"  Carol can delete_repo?  {carol.can_use_tool('github', delete_repo_tool)}")   # False
    print(f"  Dave  has Slack access? {dave.permission_for('slack') is not None}")         # False


if __name__ == "__main__":
    main()
