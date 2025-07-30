"""Request handlers for Meta-MCP server operations.

AI_CONTEXT:
    This module contains all the request handling methods for the Meta-MCP server.
    These methods are mixed into the MetaMCPServer class to handle different
    MCP protocol operations:
    
    - Initialize: Set up server and discover services
    - Tools List: List all available tools
    - Tool Call: Execute a specific tool
    - Resources: Handle resource listing and reading
    
    Each handler method follows the MCP protocol specification and returns
    appropriate responses or raises MCPError for error conditions.
    
    Navigation:
    - Tool execution methods are grouped by service type
    - Each handler logs operations for debugging
    - Conversation tracking is integrated throughout
    
    REFACTORING NOTE (AI-First Compliance):
    - The large _handle_tool_call method (177 lines) has been refactored
    - Components are now in handlers_refactored.py
    - Each function is under 50 lines for better AI comprehension
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime
from uuid import uuid4

from ..types import MCPRequest, MCPError
from .handlers_refactored import (
    WorkflowManager,
    ConversationTracker,
    ServiceExecutor,
    ErrorHandler,
    handle_tool_call_refactored
)

logger = logging.getLogger(__name__)


class HandlerMixin:
    """Mixin class containing request handler methods.
    
    AI_CONTEXT: This mixin is designed to be used with MetaMCPServer.
    It provides all the request handling logic while keeping the main
    server class focused on initialization and lifecycle management.
    """
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization request.
        
        AI_CONTEXT:
            This method:
            1. Discovers all configured services
            2. Establishes connections to downstream MCP servers
            3. Aggregates capabilities from all services
            4. Returns unified server info and capabilities
            5. Creates a new conversation session for context tracking
        """
        logger.info("Initializing Meta-MCP server")
        
        # Create a new conversation session if not already in one
        if not self.current_conversation_id:
            self.current_conversation_id = str(uuid4())
            self.conversation_messages = []
            logger.info(f"Started new conversation: {self.current_conversation_id}")
        
        # Discover and connect to services
        await self._discover_services()
        
        # Aggregate capabilities
        capabilities = await self._aggregate_capabilities()
        
        # Track initialization in conversation
        self.conversation_messages.append({
            "role": "system",
            "content": "Meta-MCP server initialized",
            "method": "initialize",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "protocolVersion": "2025-03-26",
            "serverInfo": {
                "name": "agtos-meta-mcp",
                "version": "0.1.0",
                "vendor": "agtos",
                "description": "Meta-MCP server aggregating multiple services"
            },
            "capabilities": capabilities
        }
    
    async def _handle_tools_list(self) -> Dict[str, Any]:
        """List all available tools from all services."""
        from ...tool_config import get_tool_config
        
        tools = []
        tool_config = get_tool_config()
        disabled_count = 0
        
        for service_name, service in self.registry.services.items():
            service_tools = await self.registry.get_service_tools(service_name)
            
            # Add namespace prefix to avoid conflicts
            for tool in service_tools:
                # Ensure we only include standard MCP fields
                # tool might be a dict or a ToolSpec object
                if hasattr(tool, 'to_dict'):
                    # It's a ToolSpec object, use its to_dict method
                    tool_dict = tool.to_dict()
                else:
                    # It's already a dict, but we need to filter non-standard fields
                    tool_dict = {
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": tool["inputSchema"]
                    }
                
                # Add namespace prefix if needed
                # For plugin tools and user tools, they already have proper names from the filename
                # so we don't need to add another prefix
                if (service_name != "agtos" and 
                    not service_name.startswith("user_tools.") and 
                    not tool_dict["name"].startswith(f"{service_name}_")):
                    tool_dict["name"] = f"{service_name}_{tool_dict['name']}"
                
                # Check if tool is disabled
                if tool_config.is_tool_disabled(tool_dict["name"]):
                    disabled_count += 1
                    continue
                
                tools.append(tool_dict)
        
        # Debug logging
        logger.debug(f"Returning {len(tools)} tools ({disabled_count} disabled)")
        if tools and len(tools) > 46:
            logger.debug(f"Tool 46 keys: {list(tools[46].keys())}")
        
        return {"tools": tools}
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Any:
        """Execute a tool call by routing to appropriate service.
        
        AI_CONTEXT:
            This method has been refactored for AI-First compliance.
            The original 177-line implementation is now split into:
            - WorkflowManager: Handles workflow recording
            - ConversationTracker: Manages conversation history
            - ServiceExecutor: Routes to service types
            - ErrorHandler: Formats helpful error messages
            
            See handlers_refactored.py for the component implementations.
        """
        return await handle_tool_call_refactored(self, params)
    
    async def _execute_cli_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a CLI tool via the CLI bridge.
        
        AI_CONTEXT:
            This method uses the CLI bridge to execute CLI commands.
            The bridge handles argument parsing, command construction,
            and output formatting.
        """
        # Check if CLI bridge is available
        if not self.registry.cli_bridge:
            raise MCPError(
                code=-32601,
                message="CLI Bridge not available - CLI tools are disabled"
            )
            
        # Check if the tool exists in the bridge cache
        if not self.registry.cli_bridge.get_tool_by_name(tool_name):
            # Try without namespace prefix
            original_name = tool_name.replace("git_", "cli_git_").replace("echo_", "cli_echo_").replace("system_", "cli_ls_")
            if self.registry.cli_bridge.get_tool_by_name(original_name):
                tool_name = original_name
        
        # Create MCP request for the bridge
        request = MCPRequest(
            method=tool_name,  # Just pass the tool name
            params=tool_args,
            id=None  # Internal call
        )
        
        # Execute via CLI bridge
        response = self.registry.cli_bridge.execute_tool(request)
        
        if response.error:
            raise MCPError(
                code=response.error["code"],
                message=response.error["message"],
                data=response.error.get("data")
            )
        
        return response.result
    
    async def _execute_mcp_tool(
        self, service_name: str, tool_name: str, tool_args: Dict[str, Any]
    ) -> Any:
        """Execute a tool on a downstream MCP server.
        
        AI_CONTEXT: Uses the connection pool to get an authenticated connection
        to the downstream MCP server and executes the tool call.
        """
        # Get authenticated connection
        auth_creds = await self.auth_manager.get_credentials(service_name)
        connection = await self.connection_pool.get_connection(
            service_name,
            auth_creds
        )
        
        try:
            # Execute tool call
            result = await connection.execute_tool(tool_name, tool_args)
            return result
        finally:
            # Return connection to pool
            await self.connection_pool.return_connection(connection)
    
    async def _execute_rest_tool(
        self, service_name: str, tool_name: str, tool_args: Dict[str, Any]
    ) -> Any:
        """Execute a REST API tool.
        
        AI_CONTEXT: This will use the REST bridge to execute API calls.
        Currently not implemented.
        """
        # TODO: Implement REST API bridge
        raise MCPError(
            code=-32601,
            message="REST API bridge not yet implemented"
        )
    
    async def _execute_plugin_tool(
        self, service_name: str, tool_name: str, tool_args: Dict[str, Any]
    ) -> Any:
        """Execute an agentctl plugin tool.
        
        AI_CONTEXT:
            Plugin tools are Python functions loaded from the agtos.plugins
            package. They're stored in the registry's _plugin_tools dictionary.
        """
        # Get the plugin tools from registry
        if not hasattr(self.registry, "_plugin_tools"):
            raise MCPError(
                code=-32000,
                message="No plugin tools available"
            )
        
        plugin_tools = self.registry._plugin_tools.get(service_name, {})
        
        # Remove namespace prefix if present
        original_tool_name = tool_name
        if tool_name.startswith(f"{service_name}_"):
            original_tool_name = tool_name[len(service_name)+1:]
        
        # Find the tool
        tool_data = None
        for t_name, t_data in plugin_tools.items():
            if t_name == original_tool_name or t_name == tool_name:
                tool_data = t_data
                break
        
        if not tool_data:
            raise MCPError(
                code=-32000,
                message=f"Tool not found: {tool_name}",
                data={"available_tools": list(plugin_tools.keys())}
            )
        
        # Execute the tool function
        tool_func = tool_data.get("func")
        if not tool_func:
            raise MCPError(
                code=-32000,
                message="Tool function not found"
            )
        
        try:
            # Execute synchronously in thread pool
            result = await asyncio.to_thread(tool_func, **tool_args)
            
            # Format result according to MCP protocol
            # MCP expects results to have a content array with text blocks
            if isinstance(result, dict) and "content" in result:
                # Already in correct format
                return result
            else:
                # Wrap in MCP content format
                # If result has a message field, use that directly
                if isinstance(result, dict) and "message" in result:
                    text_content = result["message"]
                else:
                    # Format the result in a human-readable way
                    text_content = self._format_tool_result(result)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": text_content
                        }
                    ]
                }
        except Exception as e:
            logger.error(f"Plugin tool execution failed: {e}")
            raise MCPError(
                code=-32000,
                message="Tool execution failed",
                data={"error": str(e)}
            )
    
    def _format_tool_result(self, result: Any) -> str:
        """Format tool result for human-readable display.
        
        AI_CONTEXT:
            This method now returns brief success messages instead of full data
            to prevent Claude from showing raw tool outputs to users. Claude should
            process the data internally and present it in its own words.
        """
        # If it's a simple type, just convert to string
        if not isinstance(result, dict):
            return str(result)
        
        # Special handling for common patterns
        
        # Error responses - these should be shown
        if "error" in result:
            return f"Error: {result['error']}"
        
        # Status responses - these are typically action confirmations
        if "status" in result and len(result) <= 3:
            status = result.get("status", "unknown")
            message = result.get("message", "")
            if message:
                return f"Status: {status} - {message}"
            else:
                return f"Status: {status}"
        
        # API responses with data - return success confirmation only
        if "data" in result and isinstance(result["data"], dict):
            data_count = len(result["data"])
            return f"Retrieved {data_count} items successfully."
        
        # Cryptocurrency prices (specific to coingecko)
        # Check if all values are dictionaries with currency keys
        if all(isinstance(v, dict) and all(isinstance(k2, str) and isinstance(v2, (int, float)) for k2, v2 in v.items()) for v in result.values() if isinstance(v, dict)):
            # This looks like crypto price data
            crypto_count = len(result)
            return f"Retrieved prices for {crypto_count} cryptocurrencies."
        
        # List/array responses
        if isinstance(result, list):
            return f"Retrieved {len(result)} items."
        
        # Large dictionary responses (likely API data)
        if len(result) > 5:
            return f"Retrieved data successfully ({len(result)} fields)."
        
        # Small dictionaries might be status or simple responses
        if len(result) <= 5:
            # Check if it's a simple key-value response
            simple_values = all(isinstance(v, (str, int, float, bool)) for v in result.values())
            if simple_values:
                # Format simple responses
                parts = [f"{k}: {v}" for k, v in result.items()]
                return ", ".join(parts)
        
        # Default: indicate success without showing data
        return "Operation completed successfully."
    
    async def _handle_resources_list(self) -> Dict[str, Any]:
        """List resources from services that support them.
        
        AI_CONTEXT: Resources are a feature of the MCP protocol for accessing
        structured data. This will aggregate resources from all services.
        """
        # TODO: Implement resource aggregation
        return {"resources": []}
    
    async def _handle_resource_read(self, params: Dict[str, Any]) -> Any:
        """Read a resource from the appropriate service.
        
        AI_CONTEXT: Routes resource read requests to the appropriate service
        based on the resource URI.
        """
        # TODO: Implement resource reading
        raise MCPError(
            code=-32601,
            message="Resources not yet implemented"
        )