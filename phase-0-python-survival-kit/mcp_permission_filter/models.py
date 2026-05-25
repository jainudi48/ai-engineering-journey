"""
MCP Permission Filter — Pydantic Models
Phase 0: Python Survival Kit

Real-world scenario: A system connected to multiple MCP servers (GitHub, Slack,
Notion, Jira). Each server exposes tools. Users have different permission levels
per server. We only show a user the tools they are actually authorized to call.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Permission primitives
# ---------------------------------------------------------------------------

class Permission(str, Enum):
    """Granular permissions a user can hold on an MCP server."""
    READ = "read"        # Can call read-only / list / get tools
    WRITE = "write"      # Can call mutation tools (create, update)
    ADMIN = "admin"      # Can call privileged / destructive tools


# Permission hierarchy: admin ⊇ write ⊇ read
PERMISSION_HIERARCHY: dict[Permission, set[Permission]] = {
    Permission.READ:  {Permission.READ},
    Permission.WRITE: {Permission.READ, Permission.WRITE},
    Permission.ADMIN: {Permission.READ, Permission.WRITE, Permission.ADMIN},
}


def satisfies(user_permission: Permission, required: Permission) -> bool:
    """Return True if *user_permission* grants access to a *required* level."""
    return required in PERMISSION_HIERARCHY[user_permission]


# ---------------------------------------------------------------------------
# MCP Server / Tool models
# ---------------------------------------------------------------------------

class MCPTool(BaseModel):
    """A single callable tool exposed by an MCP server."""
    name: str = Field(..., description="Unique tool identifier within its server")
    description: str = Field(..., description="Human-readable description of what the tool does")
    required_permission: Permission = Field(
        ..., description="Minimum permission level needed to invoke this tool"
    )

    model_config = {"frozen": True}  # tools are immutable value objects


class MCPServer(BaseModel):
    """An MCP server that exposes a collection of tools."""
    server_id: str = Field(..., description="Unique identifier, e.g. 'github', 'slack'")
    display_name: str = Field(..., description="Human-friendly name")
    tools: list[MCPTool] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_unique_tool_names(self) -> MCPServer:
        names = [t.name for t in self.tools]
        if (len(names) != len(set(names))):
            raise ValueError(f"Duplicate tool names in server '{self.server_id}'")
        return self

    def get_tool(self, name: str) -> Optional[MCPTool]:
        return next((t for t in self.tools if t.name == name), None)


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class User(BaseModel):
    """A user in the system with per-server permission grants."""
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="Display name")
    # Maps server_id -> the highest permission level the user holds on that server
    server_permissions: dict[str, Permission] = Field(
        default_factory=dict,
        description="Keyed by server_id. Absence means no access.",
    )

    def permission_for(self, server_id: str) -> Optional[Permission]:
        """Return the user's permission on a server, or None if not granted."""
        return self.server_permissions.get(server_id)

    def can_use_tool(self, server_id: str, tool: MCPTool) -> bool:
        """Return True if this user may invoke *tool* on *server_id*."""
        perm = self.permission_for(server_id)
        if perm is None:
            return False
        return satisfies(perm, tool.required_permission)


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class AuthorizedToolView(BaseModel):
    """The filtered MCP view returned to a specific user."""
    user_id: str
    user_name: str
    # Maps server_id -> list of tools the user is allowed to see/call
    authorized_tools: dict[str, list[MCPTool]] = Field(default_factory=dict)

    @property
    def total_tools(self) -> int:
        return sum(len(tools) for tools in self.authorized_tools.values())

    def summary(self) -> str:
        lines = [f"User: {self.user_name} ({self.user_id})"]
        if not self.authorized_tools:
            lines.append("  No authorized tools.")
            return "\n".join(lines)
        for server_id, tools in self.authorized_tools.items():
            lines.append(f"\n  [{server_id}]")
            for tool in tools:
                lines.append(f"    • {tool.name} [{tool.required_permission.value}] — {tool.description}")
        lines.append(f"\n  Total: {self.total_tools} tool(s) authorized")
        return "\n".join(lines)
