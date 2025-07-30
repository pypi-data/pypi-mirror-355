"""
MCP proxy components for forwarding requests to downstream servers.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .forwarder import MCPForwarder

__all__ = ["MCPForwarder"]