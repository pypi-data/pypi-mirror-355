"""
Tool registry for MCP proxy.

This module manages tool registration, namespacing, and conflict resolution
for tools from multiple downstream MCP servers.

AI_CONTEXT:
    The tool registry is crucial for the Meta-MCP server functionality.
    It ensures that tools from different servers don't conflict by applying
    namespaces, and provides efficient lookup and routing capabilities.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from agtos.utils import get_logger

logger = get_logger(__name__)


@dataclass
class ToolInfo:
    """
    Information about a registered tool.
    
    AI_CONTEXT:
        Stores complete tool metadata including the server it belongs to,
        its original and namespaced names, and the full tool definition
        from the MCP server.
    """
    server_id: str
    original_name: str
    namespaced_name: str
    description: str
    input_schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def namespace(self) -> str:
        """Extract namespace from namespaced name."""
        parts = self.namespaced_name.split(".", 1)
        return parts[0] if len(parts) > 1 else ""


class ToolRegistry:
    """
    Registry for managing tools from multiple MCP servers.
    
    AI_CONTEXT:
        Central registry that tracks all available tools across downstream
        servers. Handles:
        - Tool registration with automatic namespacing
        - Conflict detection and resolution
        - Efficient tool lookup by name or pattern
        - Server-to-tool mapping for routing
    """
    
    def __init__(self, namespace_separator: str = "."):
        """
        Initialize tool registry.
        
        Args:
            namespace_separator: Character(s) to separate namespace from tool name
        """
        self.namespace_separator = namespace_separator
        
        # Primary storage: namespaced_name -> ToolInfo
        self.tools: Dict[str, ToolInfo] = {}
        
        # Index for fast lookups
        self.server_tools: Dict[str, Set[str]] = defaultdict(set)  # server_id -> tool names
        self.original_names: Dict[str, List[str]] = defaultdict(list)  # original_name -> namespaced names
        self.namespaces: Dict[str, str] = {}  # server_id -> namespace
        
        # Conflict tracking
        self.conflicts: Dict[str, List[str]] = defaultdict(list)  # original_name -> [server_ids]
    
    def register_server_namespace(self, server_id: str, namespace: str):
        """
        Register a namespace for a server.
        
        AI_CONTEXT:
            Namespaces prevent tool name conflicts between servers.
            Each server gets a unique namespace prefix for its tools.
        """
        if server_id in self.namespaces and self.namespaces[server_id] != namespace:
            logger.warning(f"Changing namespace for {server_id} from {self.namespaces[server_id]} to {namespace}")
        
        self.namespaces[server_id] = namespace
        logger.info(f"Registered namespace '{namespace}' for server {server_id}")
    
    def register_tool(
        self,
        server_id: str,
        tool_name: str,
        description: str,
        input_schema: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a tool from a server.
        
        Args:
            server_id: ID of the server providing the tool
            tool_name: Original tool name from the server
            description: Tool description
            input_schema: JSON schema for tool input
            metadata: Additional tool metadata
        
        Returns:
            Namespaced tool name
        
        AI_CONTEXT:
            Automatically applies namespace to prevent conflicts.
            Tracks which servers provide tools with the same original name.
        """
        namespace = self.namespaces.get(server_id, server_id)
        namespaced_name = f"{namespace}{self.namespace_separator}{tool_name}"
        
        # Check for existing registration
        if namespaced_name in self.tools:
            existing = self.tools[namespaced_name]
            if existing.server_id != server_id:
                logger.warning(f"Tool {namespaced_name} already registered by {existing.server_id}")
                return namespaced_name
        
        # Create tool info
        tool_info = ToolInfo(
            server_id=server_id,
            original_name=tool_name,
            namespaced_name=namespaced_name,
            description=description,
            input_schema=input_schema,
            metadata=metadata or {}
        )
        
        # Register tool
        self.tools[namespaced_name] = tool_info
        self.server_tools[server_id].add(namespaced_name)
        self.original_names[tool_name].append(namespaced_name)
        
        # Track potential conflicts
        servers_with_tool = {self.tools[name].server_id for name in self.original_names[tool_name]}
        if len(servers_with_tool) > 1:
            self.conflicts[tool_name] = list(servers_with_tool)
            logger.info(f"Tool '{tool_name}' is provided by multiple servers: {servers_with_tool}")
        
        logger.debug(f"Registered tool {namespaced_name} from {server_id}")
        return namespaced_name
    
    def unregister_server_tools(self, server_id: str):
        """
        Remove all tools from a specific server.
        
        AI_CONTEXT:
            Called when a server disconnects or is removed from the
            proxy configuration. Cleans up all associated data.
        """
        tool_names = list(self.server_tools.get(server_id, []))
        
        for tool_name in tool_names:
            if tool_name in self.tools:
                tool_info = self.tools[tool_name]
                
                # Remove from main registry
                del self.tools[tool_name]
                
                # Remove from original names index
                self.original_names[tool_info.original_name].remove(tool_name)
                if not self.original_names[tool_info.original_name]:
                    del self.original_names[tool_info.original_name]
                
                # Update conflicts
                if tool_info.original_name in self.conflicts:
                    remaining_servers = {
                        self.tools[name].server_id 
                        for name in self.original_names.get(tool_info.original_name, [])
                    }
                    if len(remaining_servers) <= 1:
                        del self.conflicts[tool_info.original_name]
        
        # Clear server tools
        self.server_tools.pop(server_id, None)
        
        logger.info(f"Unregistered {len(tool_names)} tools from {server_id}")
    
    def get_tool(self, namespaced_name: str) -> Optional[ToolInfo]:
        """Get tool information by namespaced name."""
        return self.tools.get(namespaced_name)
    
    def get_server_for_tool(self, namespaced_name: str) -> Optional[str]:
        """Get the server ID that provides a specific tool."""
        tool_info = self.tools.get(namespaced_name)
        return tool_info.server_id if tool_info else None
    
    def list_tools(
        self,
        server_id: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> List[ToolInfo]:
        """
        List registered tools with optional filtering.
        
        Args:
            server_id: Filter by specific server
            pattern: Regex pattern to match tool names
        
        Returns:
            List of matching tools
        
        AI_CONTEXT:
            Supports flexible tool discovery for clients.
            Pattern matching allows wildcards and regex.
        """
        tools = []
        
        # Get base set of tools
        if server_id:
            tool_names = self.server_tools.get(server_id, set())
            tools = [self.tools[name] for name in tool_names if name in self.tools]
        else:
            tools = list(self.tools.values())
        
        # Apply pattern filter if provided
        if pattern:
            try:
                regex = re.compile(pattern)
                tools = [
                    tool for tool in tools
                    if regex.search(tool.namespaced_name) or regex.search(tool.original_name)
                ]
            except re.error as e:
                logger.error(f"Invalid regex pattern: {pattern} - {e}")
        
        return tools
    
    def resolve_tool_name(self, name: str) -> Optional[str]:
        """
        Resolve a tool name to its namespaced version.
        
        Args:
            name: Tool name (with or without namespace)
        
        Returns:
            Fully namespaced tool name or None if not found
        
        AI_CONTEXT:
            Handles various name formats:
            - Full namespaced name: "server.tool" -> "server.tool"
            - Original name: "tool" -> "server.tool" (if unique)
            - Partial namespace: "serv.tool" -> "server.tool" (if unique match)
        """
        # If already namespaced and exists, return as-is
        if name in self.tools:
            return name
        
        # Check if it's an original name
        if name in self.original_names:
            namespaced_names = self.original_names[name]
            if len(namespaced_names) == 1:
                # Unique match
                return namespaced_names[0]
            else:
                # Ambiguous - would need user to specify namespace
                logger.warning(f"Tool '{name}' is ambiguous. Available: {namespaced_names}")
                return None
        
        # Try fuzzy matching for partial namespaces
        matches = []
        for tool_name in self.tools:
            if tool_name.endswith(f"{self.namespace_separator}{name}"):
                matches.append(tool_name)
        
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            logger.warning(f"Multiple matches for '{name}': {matches}")
        
        return None
    
    def get_conflicts(self) -> Dict[str, List[str]]:
        """Get all tool name conflicts between servers."""
        return dict(self.conflicts)
    
    def suggest_namespace(self, server_id: str) -> str:
        """
        Suggest a namespace for a new server.
        
        AI_CONTEXT:
            Generates unique namespace suggestions based on server ID
            to avoid conflicts with existing namespaces.
        """
        base_namespace = server_id.lower().replace("-", "_").replace(" ", "_")
        
        # Check if base namespace is available
        if base_namespace not in self.namespaces.values():
            return base_namespace
        
        # Try numbered variants
        for i in range(1, 100):
            candidate = f"{base_namespace}{i}"
            if candidate not in self.namespaces.values():
                return candidate
        
        # Fallback to server ID
        return server_id
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self.tools),
            "total_servers": len(self.server_tools),
            "servers": {
                server_id: len(tools)
                for server_id, tools in self.server_tools.items()
            },
            "conflicts": len(self.conflicts),
            "namespaces": dict(self.namespaces)
        }
    
    def export_tool_list(self) -> List[Dict[str, Any]]:
        """
        Export tool list in MCP format.
        
        AI_CONTEXT:
            Formats tools for the tools/list response that will be
            sent to MCP clients (like Claude).
        """
        tool_list = []
        
        for tool in self.tools.values():
            tool_entry = {
                "name": tool.namespaced_name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            
            # Add metadata if present
            if tool.metadata:
                tool_entry["metadata"] = tool.metadata
            
            tool_list.append(tool_entry)
        
        # Sort by name for consistent ordering
        tool_list.sort(key=lambda t: t["name"])
        
        return tool_list