"""MCP (Model Context Protocol) export functionality.

This package provides tools for exporting agentctl plugins as standalone MCP tools
that can be used in the wider MCP ecosystem.

AI_CONTEXT:
    This package was refactored from a single 735-line file to improve AI-friendliness.
    Each module is focused on a specific aspect of MCP export functionality.
    The main entry points are export_plugin() and create_tool_bundle() functions.
"""

# Public API exports
from .exporter import MCPExporter
from .api import export_plugin, create_tool_bundle

__all__ = [
    "MCPExporter",
    "export_plugin", 
    "create_tool_bundle"
]