"""Tool execution across different service types.

AI_CONTEXT:
    This module handles executing tools on various service types:
    - MCP servers: Forward tool calls via JSON-RPC
    - CLI tools: Execute via CLI bridge
    - REST APIs: Execute via REST bridge
    - Plugins: Direct method invocation
    
    It provides a unified interface for tool execution while handling
    the specific requirements of each service type.
"""

import asyncio
import json
import logging
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from importlib import import_module

from ..types import MCPRequest, MCPMethod
from .core import ServiceInfo, ServiceStatus, ServiceType

logger = logging.getLogger(__name__)


class ExecutionManager:
    """Manages tool execution across all service types.
    
    AI_CONTEXT:
        This class provides a unified interface for executing tools
        regardless of the underlying service type. It handles:
        - Routing to appropriate execution method
        - Error handling and reporting
        - Result formatting
        - Debug information when enabled
    """
    
    def __init__(self, registry):
        """Initialize execution manager with registry reference."""
        self.registry = registry
    
    async def execute_tool(
        self,
        service_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on a specific service.
        
        Args:
            service_name: Name of the service
            tool_name: Name of the tool (with or without namespace)
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If service or tool not found
            ConnectionError: If service not connected
        """
        if service_name not in self.registry.services:
            raise ValueError(f"Service not found: {service_name}")
        
        service = self.registry.services[service_name]
        
        if service.status != ServiceStatus.READY:
            raise ConnectionError(f"Service {service_name} is not ready: {service.status.value}")
        
        # Handle different service types
        if service.config.type == ServiceType.MCP:
            return await self._execute_mcp_tool(service, tool_name, arguments)
        elif service.config.type == ServiceType.CLI:
            return await self._execute_cli_tool(service, tool_name, arguments)
        elif service.config.type == ServiceType.REST:
            return await self._execute_rest_tool(service, tool_name, arguments)
        elif service.config.type == ServiceType.PLUGIN:
            return await self._execute_plugin_tool(service, tool_name, arguments)
        else:
            raise ValueError(f"Unsupported service type: {service.config.type}")
    
    # ========================================================================
    # MCP Tool Execution
    # ========================================================================
    
    async def _execute_mcp_tool(
        self,
        service: ServiceInfo,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on an MCP server.
        
        AI_CONTEXT:
            Forwards the tool call to the MCP server via JSON-RPC.
            Handles namespace stripping and response formatting.
        """
        if service.config.name not in self.registry._connections:
            raise ConnectionError(f"No active connection to {service.config.name}")
        
        connection = self.registry._connections[service.config.name]
        
        # Remove namespace from tool name if present
        original_tool_name = tool_name
        if tool_name.startswith(f"{service.config.namespace}_"):
            original_tool_name = tool_name[len(service.config.namespace) + 1:]
        
        # Send tool call request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": original_tool_name,
                "arguments": arguments
            },
            "id": f"call-{service.config.name}-{datetime.now().timestamp()}"
        }
        
        try:
            response = await connection.send_request(request)
            
            if response and "result" in response:
                result = response["result"]
                # Ensure result is in MCP format
                if isinstance(result, dict) and "content" in result and isinstance(result["content"], list):
                    return result
                else:
                    # Wrap in MCP content format
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                            }
                        ]
                    }
            elif response and "error" in response:
                raise RuntimeError(f"Tool execution failed: {response['error'].get('message', 'Unknown error')}")
            else:
                raise RuntimeError("Invalid response from server")
                
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name} on {service.config.name}: {e}")
            raise
    
    # ========================================================================
    # CLI Tool Execution
    # ========================================================================
    
    async def _execute_cli_tool(
        self,
        service: ServiceInfo,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a CLI tool.
        
        AI_CONTEXT: This method integrates with the CLI bridge to execute
        command-line tools. The process:
        
        1. Creates a mock MCP request for the CLI bridge
        2. Uses the CLI bridge's execute_tool method
        3. Extracts and returns the result
        
        The CLI bridge handles all the command construction including:
        - Building proper command arguments
        - Managing subcommands and flags
        - Executing in subprocess with timeout
        - Capturing and parsing output
        - Error handling
        """
        try:
            # Create and execute CLI request
            request = self._create_cli_request(service, tool_name, arguments)
            response = self._execute_cli_bridge(request)
            
            # Process the response
            return self._process_cli_response(response)
                
        except Exception as e:
            logger.error(f"Failed to execute CLI tool {tool_name} on {service.config.name}: {e}", exc_info=True)
            return self._build_cli_error_response(e, tool_name, service)
    
    def _create_cli_request(self, service: ServiceInfo, tool_name: str, arguments: Dict[str, Any]) -> MCPRequest:
        """Create an MCP request for the CLI bridge.
        
        Args:
            service: Service information
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            MCP request object
        """
        request = MCPRequest(
            jsonrpc="2.0",
            method=MCPMethod.TOOLS_CALL,
            params={
                "name": tool_name,
                "arguments": arguments
            },
            id=f"cli-{service.config.name}-{datetime.now().timestamp()}"
        )
        
        # The CLI bridge expects the method to contain the tool name
        request.method = tool_name
        request.params = arguments
        
        return request
    
    def _execute_cli_bridge(self, request: MCPRequest) -> Any:
        """Execute request through CLI bridge.
        
        Args:
            request: MCP request
            
        Returns:
            Response from CLI bridge
        """
        return self.registry.cli_bridge.execute_tool(request)
    
    def _process_cli_response(self, response: Any) -> Dict[str, Any]:
        """Process response from CLI bridge.
        
        Args:
            response: Response from CLI bridge
            
        Returns:
            Processed result dictionary
        """
        # Extract result from MCP response
        if hasattr(response, "result") and response.result:
            result = response.result
            text_content = self._extract_text_content(result)
            
            # Return in MCP format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": text_content
                    }
                ]
            }
        elif hasattr(response, "error") and response.error:
            # Return error in MCP format
            error_msg = response.error.get("message", "Unknown error")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {error_msg}"
                    }
                ],
                "isError": True
            }
        else:
            # Return error in MCP format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: Invalid response from CLI bridge"
                    }
                ],
                "isError": True
            }
    
    def _extract_text_content(self, result: Any) -> str:
        """Extract text content from CLI result.
        
        Args:
            result: Result from CLI bridge
            
        Returns:
            Extracted text content
        """
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and content:
                return content[0].get("text", "")
            else:
                return str(content)
        else:
            return str(result)
    
    def _build_cli_error_response(self, error: Exception, tool_name: str, service: ServiceInfo) -> Dict[str, Any]:
        """Build detailed error response for CLI execution failure.
        
        Args:
            error: The exception that occurred
            tool_name: Name of the tool
            service: Service information
            
        Returns:
            Error response dictionary
        """
        error_msg = str(error)
        
        # Add helpful tips based on error type
        if "command not found" in error_msg.lower():
            error_msg += f"\n\nTip: The CLI command may not be installed. Check if '{tool_name.replace('cli__', '').split('__')[0]}' is available on your system."
        elif "permission denied" in error_msg.lower():
            error_msg += "\n\nTip: You may not have permission to run this command. Try with appropriate privileges."
        
        return {
            "success": False,
            "error": f"CLI Bridge Error: {error_msg}",
            "details": {
                "tool_name": tool_name,
                "service": service.config.name,
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc() if self.registry.debug else None,
                "suggestion": self._suggest_cli_alternatives(tool_name)
            }
        }
    
    # ========================================================================
    # REST API Execution
    # ========================================================================
    
    async def _execute_rest_tool(
        self,
        service: ServiceInfo,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a REST API tool.
        
        AI_CONTEXT: This method integrates with the REST bridge to execute
        API calls. The process:
        
        1. Creates a REST bridge instance
        2. Retrieves the tools for the specific API
        3. Finds the matching tool by name
        4. Executes the tool's handler function
        5. Returns the result
        
        The REST bridge handles all the HTTP details including:
        - URL construction with path/query parameters
        - Authentication headers
        - Request body formatting
        - Response parsing
        - Error handling
        """
        try:
            # Get tools from REST bridge
            tools = self._get_rest_bridge_tools(service)
            
            # Find the specific tool
            tool_def = self._find_rest_tool(tools, tool_name, service)
            
            # Execute the handler
            return self._execute_rest_handler(tool_def, tool_name, arguments)
            
        except ValueError as e:
            logger.error(f"REST tool not found or invalid: {e}")
            return self._build_rest_validation_error(e, tool_name, service, 
                                                   list(tools.keys()) if 'tools' in locals() else [])
        except Exception as e:
            logger.error(f"Failed to execute REST tool {tool_name} on {service.config.name}: {e}", exc_info=True)
            return self._build_rest_execution_error(e, tool_name, service, arguments)
    
    def _get_rest_bridge_tools(self, service: ServiceInfo) -> Dict[str, Any]:
        """Get tools from REST bridge for a service.
        
        Args:
            service: Service information
            
        Returns:
            Dictionary of tools
        """
        from ..bridge.rest import RESTBridge
        
        bridge = RESTBridge()
        return bridge.generate_tools_for_api(service.config.name)
    
    def _find_rest_tool(self, tools: Dict[str, Any], tool_name: str, service: ServiceInfo) -> Dict[str, Any]:
        """Find a specific REST tool by name.
        
        Args:
            tools: Dictionary of available tools
            tool_name: Name of the tool to find
            service: Service information
            
        Returns:
            Tool definition
            
        Raises:
            ValueError: If tool not found
        """
        if tool_name in tools:
            return tools[tool_name]
        
        # Try without namespace prefix
        original_tool_name = tool_name
        if tool_name.startswith(f"{service.config.namespace}_"):
            original_tool_name = tool_name[len(service.config.namespace) + 1:]
        
        # Look for tool with or without namespace
        for t_name, t_def in tools.items():
            if t_name == tool_name or t_name == original_tool_name or t_name.endswith(f"_{original_tool_name}"):
                return t_def
        
        raise ValueError(f"Tool '{tool_name}' not found in service '{service.config.name}'")
    
    def _execute_rest_handler(self, tool_def: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the REST handler function.
        
        Args:
            tool_def: Tool definition
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If handler not found
        """
        handler = tool_def.get("func")
        if not handler:
            raise ValueError(f"Tool '{tool_name}' has no handler function")
        
        # Execute the handler with the provided arguments
        # The handler is synchronous but we're in an async context
        result = handler(**arguments)
        
        # Format result according to MCP protocol
        if isinstance(result, dict) and "content" in result and isinstance(result["content"], list):
            # Already in MCP format
            return result
        else:
            # Wrap in MCP content format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                    }
                ]
            }
    
    def _build_rest_validation_error(self, error: ValueError, tool_name: str, 
                                   service: ServiceInfo, available_tools: List[str]) -> Dict[str, Any]:
        """Build validation error response for REST tool.
        
        Args:
            error: The validation error
            tool_name: Name of the tool
            service: Service information
            available_tools: List of available tool names
            
        Returns:
            Error response dictionary
        """
        return {
            "success": False,
            "error": f"REST Tool Error: {str(error)}",
            "details": {
                "tool_name": tool_name,
                "service": service.config.name,
                "available_tools": available_tools,
                "suggestion": "Check if the tool name is correct and the REST API is properly configured"
            }
        }
    
    def _build_rest_execution_error(self, error: Exception, tool_name: str, 
                                  service: ServiceInfo, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Build execution error response for REST tool.
        
        Args:
            error: The execution error
            tool_name: Name of the tool
            service: Service information
            arguments: Tool arguments
            
        Returns:
            Error response dictionary
        """
        return {
            "success": False,
            "error": f"REST Execution Error: {str(error)}",
            "details": {
                "tool_name": tool_name,
                "service": service.config.name,
                "arguments": arguments,
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc() if self.registry.debug else None
            }
        }
    
    # ========================================================================
    # Plugin Tool Execution
    # ========================================================================
    
    async def _execute_plugin_tool(
        self,
        service: ServiceInfo,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a plugin tool.
        
        AI_CONTEXT: This method executes tools from agtos plugins.
        Plugins are Python modules that expose methods as tools. The process:
        
        1. Check if tool is from pre-registered plugin service
        2. Otherwise, dynamically import the plugin module
        3. Find the method corresponding to the tool
        4. Call the method with the provided arguments
        5. Handle both sync and async methods
        6. Return the result in a standard format
        
        Plugin methods are expected to return dictionaries with
        success/error information.
        """
        try:
            # Try to get pre-registered tool first
            func = await self._get_preregistered_tool(service, tool_name)
            
            if func:
                return await self._execute_plugin_function(func, arguments)
            
            # Otherwise, try dynamic import and method lookup
            plugin_module = await self._import_plugin_module(service.config.name)
            method = await self._find_plugin_method(plugin_module, service.config.name, tool_name)
            
            if not callable(method):
                return {
                    "success": False,
                    "error": f"'{tool_name}' is not callable"
                }
            
            return await self._execute_plugin_function(method, arguments)
                
        except ImportError as e:
            return self._format_import_error(e, service.config.name)
        except AttributeError as e:
            return self._format_attribute_error(e, tool_name, service.config.name)
        except Exception as e:
            return self._format_execution_error(e, tool_name, service.config.name, arguments)
    
    async def _get_preregistered_tool(
        self,
        service: ServiceInfo,
        tool_name: str
    ) -> Optional[Callable]:
        """Get a pre-registered tool function if available.
        
        AI_CONTEXT:
            Checks if the service has pre-registered tools stored in the registry.
            This is more efficient than dynamic import as the functions are already loaded.
        """
        if service.config.name not in self.registry._plugin_tools:
            return None
            
        tools_dict = self.registry._plugin_tools[service.config.name]
        if tool_name not in tools_dict:
            return None
            
        tool_data = tools_dict[tool_name]
        if "func" in tool_data and callable(tool_data["func"]):
            return tool_data["func"]
        
        return None
    
    async def _import_plugin_module(self, plugin_name: str):
        """Import a plugin module dynamically.
        
        AI_CONTEXT:
            Tries to import from the agtos.plugins package first,
            then falls back to direct import if that fails.
        """
        try:
            # Try to import from plugins package
            return import_module(f"agtos.plugins.{plugin_name}")
        except ImportError:
            # Try direct import
            return import_module(plugin_name)
    
    async def _find_plugin_method(
        self,
        plugin_module,
        plugin_name: str,
        tool_name: str
    ) -> Callable:
        """Find a method in a plugin module.
        
        AI_CONTEXT:
            Looks for methods in three places:
            1. Direct module attribute with the method name
            2. Module attribute after stripping plugin prefix
            3. In the module's TOOLS dictionary
        """
        # Extract method name from tool name
        method_name = tool_name
        if method_name.startswith(f"{plugin_name}_"):
            method_name = method_name[len(plugin_name) + 1:]
        
        # Check direct module attribute
        if hasattr(plugin_module, method_name):
            return getattr(plugin_module, method_name)
        
        # Check TOOLS dictionary
        if hasattr(plugin_module, "TOOLS"):
            tools = plugin_module.TOOLS
            if tool_name in tools and "func" in tools[tool_name]:
                return tools[tool_name]["func"]
            raise AttributeError(f"Tool '{tool_name}' not found in plugin")
        
        raise AttributeError(f"Method '{method_name}' not found in plugin")
    
    async def _execute_plugin_function(
        self,
        func: Callable,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a plugin function and format the result.
        
        AI_CONTEXT:
            Handles both sync and async functions.
            Ensures the result is properly formatted as a dictionary
            with a success flag.
        """
        import inspect
        
        # Execute the function
        if inspect.iscoroutinefunction(func):
            result = await func(**arguments)
        else:
            result = func(**arguments)
        
        # Format the result according to MCP protocol
        # First ensure we have a proper dict with success flag
        if isinstance(result, dict):
            if "success" not in result:
                result["success"] = True
            formatted_result = result
        else:
            formatted_result = {
                "success": True,
                "result": result
            }
        
        # Now wrap in MCP content format if not already wrapped
        if "content" in formatted_result and isinstance(formatted_result["content"], list):
            # Already in MCP format
            return formatted_result
        else:
            # Wrap in MCP content format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(formatted_result, indent=2) if isinstance(formatted_result, dict) else str(formatted_result)
                    }
                ]
            }
    
    def _format_import_error(self, e: ImportError, plugin_name: str) -> Dict[str, Any]:
        """Format an import error response.
        
        AI_CONTEXT:
            Provides detailed error information for debugging import issues,
            including the attempted import paths and suggestions.
        """
        logger.error(f"Failed to import plugin {plugin_name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Plugin Import Error: Could not load plugin '{plugin_name}'",
            "details": {
                "plugin_name": plugin_name,
                "attempted_imports": [
                    f"agtos.plugins.{plugin_name}",
                    plugin_name
                ],
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc() if self.registry.debug else None,
                "suggestion": "Ensure the plugin is installed and accessible in the Python path"
            }
        }
    
    def _format_attribute_error(
        self,
        e: AttributeError,
        tool_name: str,
        plugin_name: str
    ) -> Dict[str, Any]:
        """Format an attribute error response.
        
        AI_CONTEXT:
            Provides helpful error messages when a tool or method
            cannot be found in a plugin.
        """
        logger.error(f"Tool or method not found in plugin: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Plugin Tool Error: {str(e)}",
            "details": {
                "tool_name": tool_name,
                "plugin_name": plugin_name,
                "error_type": "AttributeError",
                "suggestion": f"Check if tool '{tool_name}' exists in the plugin's TOOLS dictionary or as a module method"
            }
        }
    
    def _format_execution_error(
        self,
        e: Exception,
        tool_name: str,
        plugin_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format a general execution error response.
        
        AI_CONTEXT:
            Provides comprehensive error information for any unexpected
            errors during plugin execution.
        """
        logger.error(f"Failed to execute plugin tool {tool_name} on {plugin_name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Plugin Execution Error: {str(e)}",
            "details": {
                "tool_name": tool_name,
                "plugin_name": plugin_name,
                "arguments": arguments,
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc() if self.registry.debug else None
            }
        }
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _suggest_cli_alternatives(self, tool_name: str) -> Optional[str]:
        """Suggest alternative CLI tools when one fails.
        
        Args:
            tool_name: The CLI tool that failed
            
        Returns:
            Suggestion string or None
        """
        # Extract the CLI command name
        parts = tool_name.replace('cli__', '').split('__')
        cli_name = parts[0] if parts else ""
        
        # Common alternatives
        alternatives = {
            "git": "Make sure git is installed: brew install git",
            "docker": "Make sure Docker is installed and running",
            "npm": "Make sure Node.js and npm are installed",
            "python": "Make sure Python is in your PATH",
            "aws": "Install AWS CLI: brew install awscli",
            "gh": "Install GitHub CLI: brew install gh",
            "kubectl": "Install kubectl for Kubernetes",
        }
        
        if cli_name in alternatives:
            return alternatives[cli_name]
        
        # Generic suggestion
        return f"Make sure '{cli_name}' is installed and in your PATH"