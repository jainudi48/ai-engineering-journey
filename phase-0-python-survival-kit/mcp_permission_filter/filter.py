"""
MCP Permission Filter — Core Function
Phase 0: Python Survival Kit
"""

from __future__ import annotations

from .models import AuthorizedToolView, MCPServer, User


def filter_mcp_tools(
    user: User,
    servers: list[MCPServer],
) -> AuthorizedToolView:
    """
    Return the subset of MCP tools that *user* is authorized to call.

    Args:
        user:    The requesting user with their permission grants.
        servers: All MCP servers and their tool registries.

    Returns:
        AuthorizedToolView containing only tools the user may invoke,
        grouped by server. Servers with zero authorized tools are omitted.
    """
    authorized: dict[str, list] = {}

    for server in servers:
        allowed_tools = [
            tool
            for tool in server.tools
            if user.can_use_tool(server.server_id, tool)
        ]
        if allowed_tools:
            authorized[server.server_id] = allowed_tools

    return AuthorizedToolView(
        user_id=user.user_id,
        user_name=user.name,
        authorized_tools=authorized,
    )


def filter_mcp_tools_for_many(
    users: list[User],
    servers: list[MCPServer],
) -> dict[str, AuthorizedToolView]:
    """
    Batch version: compute authorized views for multiple users at once.

    Returns a dict keyed by user_id.
    """
    return {
        user.user_id: filter_mcp_tools(user, servers)
        for user in users
    }
