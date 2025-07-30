"""Tool inspection system for agtOS.

This module provides detailed information about any tool in the system,
including plugins, user-created tools, and built-in tools.

AI_CONTEXT:
    The inspector is designed to help users understand what tools are available
    and how to use them without exposing implementation details. It provides:
    - Tool discovery across all sources
    - Parameter documentation
    - Usage statistics and examples
    - Different detail levels (summary, full, debug)
"""

import json
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

from agtos.user_tools.models import ToolSpecification
from agtos.versioning.version_manager import VersionManager
from agtos.utils import get_logger

logger = get_logger(__name__)


class ToolSource(Enum):
    """Source of a tool."""
    USER = "user"
    PLUGIN = "plugin"
    BUILTIN = "builtin"
    MCP = "mcp"
    UNKNOWN = "unknown"


class DetailLevel(Enum):
    """Level of detail for tool information."""
    SUMMARY = "summary"
    FULL = "full"
    DEBUG = "debug"


class ToolInspector:
    """Inspector for examining tools from any source.
    
    AI_CONTEXT:
        This class provides comprehensive tool inspection capabilities.
        It can examine tools from:
        - User-created tools (via tool_creator)
        - Plugins (built-in and custom)
        - MCP servers
        - Built-in system tools
        
        The inspector provides different levels of detail based on needs,
        from simple summaries to full debug information.
    """
    
    def __init__(self):
        self._plugin_manager = None  # Lazy load to avoid circular imports
        self.user_tools_dir = Path.home() / ".agtos" / "user_tools"
        self.version_manager = VersionManager(self.user_tools_dir)
        self._usage_cache = {}
    
    @property
    def plugin_manager(self):
        """Lazy load plugin manager to avoid circular imports."""
        if self._plugin_manager is None:
            from agtos.plugins.manager import PluginManager
            self._plugin_manager = PluginManager()
        return self._plugin_manager
        
    def inspect_tool(
        self, 
        tool_name: str, 
        detail_level: DetailLevel = DetailLevel.FULL
    ) -> Dict[str, Any]:
        """Inspect any tool by name.
        
        Args:
            tool_name: Name of the tool to inspect
            detail_level: Level of detail to return
            
        Returns:
            Tool information dict
        """
        # Determine tool source
        source, tool_data = self._find_tool(tool_name)
        
        if source == ToolSource.UNKNOWN:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "suggestions": self._get_similar_tools(tool_name)
            }
        
        # Build inspection result based on source
        if source == ToolSource.USER:
            return self._inspect_user_tool(tool_name, tool_data, detail_level)
        elif source == ToolSource.PLUGIN:
            return self._inspect_plugin_tool(tool_name, tool_data, detail_level)
        elif source == ToolSource.BUILTIN:
            return self._inspect_builtin_tool(tool_name, tool_data, detail_level)
        elif source == ToolSource.MCP:
            return self._inspect_mcp_tool(tool_name, tool_data, detail_level)
        
        return {
            "success": False,
            "error": f"Unknown tool source: {source}"
        }
    
    def list_all_tools(
        self, 
        source_filter: Optional[ToolSource] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all available tools.
        
        Args:
            source_filter: Filter by tool source
            pattern: Name pattern to match
            
        Returns:
            Dict with categorized tool lists
        """
        tools = {
            "user": [],
            "plugin": [],
            "builtin": [],
            "mcp": [],
            "total": 0
        }
        
        # Get user tools
        if not source_filter or source_filter == ToolSource.USER:
            tools["user"] = self._list_user_tools(pattern)
        
        # Get plugin tools
        if not source_filter or source_filter == ToolSource.PLUGIN:
            tools["plugin"] = self._list_plugin_tools(pattern)
        
        # Get builtin tools
        if not source_filter or source_filter == ToolSource.BUILTIN:
            tools["builtin"] = self._list_builtin_tools(pattern)
        
        # Get MCP tools (if connected)
        if not source_filter or source_filter == ToolSource.MCP:
            tools["mcp"] = self._list_mcp_tools(pattern)
        
        # Calculate total
        tools["total"] = sum(len(tools[cat]) for cat in ["user", "plugin", "builtin", "mcp"])
        
        return tools
    
    def get_usage_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get usage statistics for a tool.
        
        Returns:
            Usage statistics including call count, last used, errors, etc.
        """
        # Check cache first
        if tool_name in self._usage_cache:
            return self._usage_cache[tool_name]
        
        # Try to load from usage log
        usage_file = Path.home() / ".agtos" / "usage" / f"{tool_name}.json"
        if usage_file.exists():
            try:
                stats = json.loads(usage_file.read_text())
                self._usage_cache[tool_name] = stats
                return stats
            except Exception as e:
                logger.error(f"Failed to load usage stats for {tool_name}: {e}")
        
        # Return default stats
        return {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_used": None,
            "average_duration_ms": 0,
            "error_rate": 0.0
        }
    
    def _find_tool(self, tool_name: str) -> Tuple[ToolSource, Any]:
        """Find a tool and determine its source.
        
        Returns (source, tool_data) tuple.
        """
        # Check user tools first (highest priority)
        if self._is_user_tool(tool_name):
            return ToolSource.USER, self._load_user_tool_data(tool_name)
        
        # Check plugins
        plugin_tool = self._find_plugin_tool(tool_name)
        if plugin_tool:
            return ToolSource.PLUGIN, plugin_tool
        
        # Check builtin tools
        builtin_tool = self._find_builtin_tool(tool_name)
        if builtin_tool:
            return ToolSource.BUILTIN, builtin_tool
        
        # Check MCP tools
        mcp_tool = self._find_mcp_tool(tool_name)
        if mcp_tool:
            return ToolSource.MCP, mcp_tool
        
        return ToolSource.UNKNOWN, None
    
    def _is_user_tool(self, tool_name: str) -> bool:
        """Check if a tool is a user-created tool."""
        # Check if tool exists in version manager
        versions = self.version_manager.get_available_versions(tool_name)
        return bool(versions)
    
    def _load_user_tool_data(self, tool_name: str) -> Dict[str, Any]:
        """Load data for a user-created tool."""
        active_version = self.version_manager.get_active_version(tool_name)
        if not active_version:
            return None
        
        metadata = self.version_manager.get_version_metadata(tool_name, active_version)
        return {
            "metadata": metadata,
            "version": active_version,
            "versions": self.version_manager.get_available_versions(tool_name)
        }
    
    def _find_plugin_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Find a tool in plugins."""
        # Get all plugins
        plugins = self.plugin_manager.list_plugins()
        
        for plugin in plugins:
            if plugin.get("status") == "active":
                plugin_name = plugin["name"]
                # Check if tool belongs to this plugin
                if tool_name.startswith(f"{plugin_name}_"):
                    return {
                        "plugin": plugin_name,
                        "tool": tool_name,
                        "config": plugin.get("config", {})
                    }
        
        return None
    
    def _find_builtin_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Find a builtin system tool."""
        # Check tool_creator tools
        if tool_name.startswith("tool_creator_"):
            try:
                from agtos.plugins.tool_creator import get_tool_creator_tools
                tools = get_tool_creator_tools()
                if tool_name in tools:
                    return tools[tool_name]
            except ImportError:
                # Avoid circular import
                pass
        
        # Check other builtin tools
        # TODO: Add more builtin tool sources
        
        return None
    
    def _find_mcp_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Find a tool from MCP servers."""
        # TODO: Query connected MCP servers
        return None
    
    def _inspect_user_tool(
        self, 
        tool_name: str, 
        tool_data: Dict[str, Any], 
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """Inspect a user-created tool."""
        metadata = tool_data["metadata"]
        spec = metadata.get("specification", {})
        
        result = {
            "success": True,
            "tool_name": tool_name,
            "source": "user",
            "version": tool_data["version"],
            "description": metadata.get("description", ""),
            "created_at": metadata.get("created_at"),
            "endpoints": []
        }
        
        # Add endpoint information
        for ep in spec.get("endpoints", []):
            endpoint_info = {
                "url": ep.get("url", ""),
                "method": ep.get("method", "GET"),
                "parameters": []
            }
            
            # Add parameters
            for param in ep.get("parameters", []):
                param_info = {
                    "name": param.get("name"),
                    "type": param.get("type", "string"),
                    "required": param.get("required", False),
                    "location": param.get("location", "query")
                }
                
                if detail_level in [DetailLevel.FULL, DetailLevel.DEBUG]:
                    param_info["description"] = param.get("description", "")
                
                endpoint_info["parameters"].append(param_info)
            
            # Add auth info if present
            if auth := ep.get("authentication"):
                endpoint_info["authentication"] = {
                    "type": auth.get("type"),
                    "location": auth.get("location", "header")
                }
            
            result["endpoints"].append(endpoint_info)
        
        # Add version information
        if detail_level in [DetailLevel.FULL, DetailLevel.DEBUG]:
            result["versions"] = {
                "active": tool_data["version"],
                "available": tool_data["versions"],
                "total": len(tool_data["versions"])
            }
        
        # Add usage stats
        if detail_level == DetailLevel.FULL:
            result["usage"] = self.get_usage_stats(tool_name)
        
        # Add debug information
        if detail_level == DetailLevel.DEBUG:
            result["debug"] = {
                "metadata_keys": list(metadata.keys()),
                "mcp_schema": metadata.get("mcp_schema"),
                "file_path": str(self.user_tools_dir / f"{tool_name}.py")
            }
        
        return result
    
    def _inspect_plugin_tool(
        self, 
        tool_name: str, 
        tool_data: Dict[str, Any], 
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """Inspect a plugin tool."""
        plugin_name = tool_data["plugin"]
        
        result = {
            "success": True,
            "tool_name": tool_name,
            "source": "plugin",
            "plugin": plugin_name,
            "description": f"Tool from {plugin_name} plugin"
        }
        
        # Try to get more info from plugin
        try:
            plugin_module = importlib.import_module(f"agtos.plugins.{plugin_name}")
            
            # Look for tool function
            tool_func_name = tool_name.replace(f"{plugin_name}_", "")
            if hasattr(plugin_module, tool_func_name):
                func = getattr(plugin_module, tool_func_name)
                
                # Get function info
                result["description"] = inspect.getdoc(func) or result["description"]
                
                # Get parameters
                sig = inspect.signature(func)
                result["parameters"] = []
                
                for param_name, param in sig.parameters.items():
                    param_info = {
                        "name": param_name,
                        "required": param.default == inspect.Parameter.empty
                    }
                    
                    # Try to infer type from annotation
                    if param.annotation != inspect.Parameter.empty:
                        param_info["type"] = str(param.annotation)
                    
                    result["parameters"].append(param_info)
        
        except Exception as e:
            logger.error(f"Failed to inspect plugin tool {tool_name}: {e}")
        
        # Add usage stats if requested
        if detail_level in [DetailLevel.FULL, DetailLevel.DEBUG]:
            result["usage"] = self.get_usage_stats(tool_name)
        
        return result
    
    def _inspect_builtin_tool(
        self, 
        tool_name: str, 
        tool_data: Dict[str, Any], 
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """Inspect a builtin tool."""
        result = {
            "success": True,
            "tool_name": tool_name,
            "source": "builtin",
            "description": tool_data.get("description", ""),
            "schema": tool_data.get("schema", {})
        }
        
        # Extract parameters from schema
        if "properties" in tool_data.get("schema", {}):
            result["parameters"] = []
            properties = tool_data["schema"]["properties"]
            required = tool_data["schema"].get("required", [])
            
            for param_name, param_schema in properties.items():
                param_info = {
                    "name": param_name,
                    "type": param_schema.get("type", "string"),
                    "required": param_name in required,
                    "description": param_schema.get("description", "")
                }
                result["parameters"].append(param_info)
        
        # Add usage stats if requested
        if detail_level in [DetailLevel.FULL, DetailLevel.DEBUG]:
            result["usage"] = self.get_usage_stats(tool_name)
        
        # Add debug info
        if detail_level == DetailLevel.DEBUG:
            result["debug"] = {
                "function": str(tool_data.get("func")),
                "schema": tool_data.get("schema")
            }
        
        return result
    
    def _inspect_mcp_tool(
        self, 
        tool_name: str, 
        tool_data: Dict[str, Any], 
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """Inspect an MCP tool."""
        # TODO: Implement MCP tool inspection
        return {
            "success": True,
            "tool_name": tool_name,
            "source": "mcp",
            "description": "MCP tool (details not available)"
        }
    
    def _list_user_tools(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List user-created tools."""
        tools = []
        all_tools = self.version_manager.list_all_tools()
        
        for tool_name, active_version, total_versions in all_tools:
            if pattern and pattern.lower() not in tool_name.lower():
                continue
            
            metadata = self.version_manager.get_version_metadata(tool_name, active_version)
            if metadata:
                tools.append({
                    "name": tool_name,
                    "description": metadata.get("description", ""),
                    "version": active_version,
                    "versions": total_versions
                })
        
        return tools
    
    def _list_plugin_tools(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List plugin tools."""
        tools = []
        plugins = self.plugin_manager.list_plugins()
        
        for plugin in plugins:
            if plugin.get("status") == "active":
                plugin_name = plugin["name"]
                
                # Skip specific system plugins that are listed as builtin
                if plugin_name in ["tool_creator", "tool_simplifier", "ephemeral_creator"]:
                    continue
                
                # Get tools from plugin
                try:
                    plugin_tools = self.plugin_manager.get_plugin_tools(plugin_name)
                    for tool_name, tool_data in plugin_tools.items():
                        # Skip if it doesn't match pattern
                        if pattern and pattern.lower() not in tool_name.lower():
                            continue
                        
                        tools.append({
                            "name": tool_name,
                            "description": tool_data.get("description", "")
                        })
                except Exception as e:
                    logger.error(f"Failed to get tools from plugin {plugin_name}: {e}")
        
        return tools
    
    def _list_builtin_tools(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List builtin tools."""
        tools = []
        
        # List tool_creator tools
        try:
            from agtos.plugins.tool_creator import get_tool_creator_tools
            for tool_name, tool_config in get_tool_creator_tools().items():
                if pattern and pattern.lower() not in tool_name.lower():
                    continue
                
                tools.append({
                    "name": tool_name,
                    "description": tool_config.get("description", "")
                })
        except ImportError:
            # Avoid circular import
            pass
        
        # List tool_simplifier tools
        try:
            from agtos.plugins.tool_simplifier import get_tool_simplifier_tools
            for tool_name, tool_config in get_tool_simplifier_tools().items():
                if pattern and pattern.lower() not in tool_name.lower():
                    continue
                
                tools.append({
                    "name": tool_name,
                    "description": tool_config.get("description", "")
                })
        except ImportError:
            pass
        
        # List ephemeral_creator tools
        try:
            from agtos.plugins.ephemeral_creator import get_ephemeral_creator_tools
            for tool_name, tool_config in get_ephemeral_creator_tools().items():
                if pattern and pattern.lower() not in tool_name.lower():
                    continue
                
                tools.append({
                    "name": tool_name,
                    "description": tool_config.get("description", "")
                })
        except ImportError:
            pass
        
        return tools
    
    def _list_mcp_tools(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List MCP tools."""
        # TODO: Query connected MCP servers
        return []
    
    def _get_similar_tools(self, tool_name: str) -> List[str]:
        """Get similar tool names for suggestions."""
        all_tools = self.list_all_tools()
        similar = []
        
        tool_name_lower = tool_name.lower()
        
        # Check all categories
        for category in ["user", "plugin", "builtin", "mcp"]:
            for tool in all_tools.get(category, []):
                name = tool.get("name", "")
                if (tool_name_lower in name.lower() or 
                    name.lower() in tool_name_lower or
                    self._calculate_similarity(tool_name_lower, name.lower()) > 0.6):
                    similar.append(name)
        
        # Remove duplicates and limit
        return list(set(similar))[:5]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple implementation)."""
        # Simple character overlap ratio
        common = sum(1 for c in str1 if c in str2)
        return common / max(len(str1), len(str2)) if str1 and str2 else 0.0