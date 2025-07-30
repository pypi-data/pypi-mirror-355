"""Simple tool configuration module for MCP server.

This module provides a minimal implementation to handle tool configuration
and disabling functionality.
"""

from typing import Set, Optional


class ToolConfig:
    """Manages tool configuration and disabled status."""
    
    def __init__(self):
        self.disabled_tools: Set[str] = set()
    
    def is_tool_disabled(self, tool_name: str) -> bool:
        """Check if a tool is disabled.
        
        Args:
            tool_name: The name of the tool to check
            
        Returns:
            True if the tool is disabled, False otherwise
        """
        return tool_name in self.disabled_tools
    
    def disable_tool(self, tool_name: str):
        """Disable a tool.
        
        Args:
            tool_name: The name of the tool to disable
        """
        self.disabled_tools.add(tool_name)
    
    def enable_tool(self, tool_name: str):
        """Enable a tool.
        
        Args:
            tool_name: The name of the tool to enable
        """
        self.disabled_tools.discard(tool_name)


# Global instance
_tool_config: Optional[ToolConfig] = None


def get_tool_config() -> ToolConfig:
    """Get the global tool configuration instance.
    
    Returns:
        The global ToolConfig instance
    """
    global _tool_config
    if _tool_config is None:
        _tool_config = ToolConfig()
    return _tool_config