"""
Meta-MCP server implementation for agtos.

This package provides the core functionality for agentctl to act as a
Meta-MCP server that can aggregate and proxy multiple downstream MCP servers.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .proxy.forwarder import MCPForwarder
    from .server import MetaMCPServer
    from .aliases import (
        AliasRegistry,
        get_registry,
        find_tool_for_alias,
        suggest_aliases_for_tool,
        add_custom_alias
    )

__all__ = [
    "MCPForwarder",
    "MetaMCPServer",
    "AliasRegistry",
    "get_registry", 
    "find_tool_for_alias",
    "suggest_aliases_for_tool",
    "add_custom_alias"
]