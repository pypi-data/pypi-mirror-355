"""MCP server connection management.

AI_CONTEXT:
    This module handles establishing and maintaining connections to
    downstream MCP servers. It manages:
    - Different transport types (stdio, HTTP, WebSocket)
    - Connection lifecycle (connect, initialize, disconnect)
    - Tool discovery after connection
    - Connection pooling and reuse
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..types import ToolSpec, ServerCapabilities
from .core import ServiceInfo, ServiceStatus

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages connections to MCP servers.
    
    AI_CONTEXT:
        This class handles the complexity of connecting to MCP servers
        across different transport types. It maintains connection state,
        performs initialization handshakes, and discovers available tools.
    """
    
    def __init__(self, registry):
        """Initialize connection manager with registry reference."""
        self.registry = registry
    
    async def connect_mcp_server(self, name: str):
        """Connect to an MCP server and discover tools.
        
        AI_CONTEXT:
            This method orchestrates the complete connection process:
            1. Determine transport type from configuration
            2. Create appropriate connection instance
            3. Establish connection
            4. Send initialization request
            5. Discover available tools
            6. Update service status
        """
        service = self.registry.services[name]
        service.status = ServiceStatus.CONNECTING
        
        try:
            # Create and establish connection
            connection = await self._create_connection(service, name)
            await connection.connect()
            
            # Initialize the server
            init_response = await self._initialize_server(connection, name)
            
            # Store connection
            self._store_connection(name, connection)
            
            # Discover tools
            await self._discover_mcp_tools(service, connection)
            
            # Update service with capabilities
            self._update_service_capabilities(service, init_response)
            
            # Mark as ready
            service.status = ServiceStatus.READY
            service.last_connected = datetime.now()
            logger.info(f"Connected to MCP server: {name}")
            
        except Exception as e:
            await self._handle_connection_error(service, name, e)
    
    async def _discover_mcp_tools(self, service: ServiceInfo, connection: Any):
        """Discover tools from connected MCP server.
        
        AI_CONTEXT:
            Sends tools/list request to discover available tools.
            Applies namespace prefixing to avoid tool name conflicts.
        """
        list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": f"list-{service.config.name}"
        }
        
        list_response = await connection.send_request(list_request)
        
        if list_response and "result" in list_response:
            tools = list_response["result"].get("tools", [])
            service.tools = []
            
            for tool_data in tools:
                # Apply namespace to tool name
                tool_name = tool_data.get("name", "")
                if not tool_name.startswith(f"{service.config.namespace}_"):
                    tool_name = f"{service.config.namespace}_{tool_name}"
                
                tool = ToolSpec(
                    name=tool_name,
                    description=tool_data.get("description", ""),
                    inputSchema=tool_data.get("inputSchema", {})
                )
                service.tools.append(tool)
            
            logger.info(f"Discovered {len(service.tools)} tools from {service.config.name}")
    
    async def disconnect_server(self, name: str):
        """Disconnect from an MCP server.
        
        AI_CONTEXT:
            Cleanly disconnects from a server and removes the connection
            from the registry's connection pool.
        """
        if hasattr(self.registry, "_connections") and name in self.registry._connections:
            try:
                connection = self.registry._connections[name]
                await connection.disconnect()
                logger.info(f"Disconnected from MCP server: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")
            finally:
                del self.registry._connections[name]
    
    async def reconnect_server(self, name: str):
        """Reconnect to an MCP server.
        
        AI_CONTEXT:
            Disconnects if already connected, then establishes a fresh
            connection. Useful for recovering from connection errors.
        """
        # Disconnect first if connected
        await self.disconnect_server(name)
        
        # Reconnect
        await self.connect_mcp_server(name)
    
    def get_connection(self, name: str) -> Optional[Any]:
        """Get active connection for a server.
        
        Args:
            name: Server name
            
        Returns:
            Connection instance or None if not connected
        """
        if hasattr(self.registry, "_connections"):
            return self.registry._connections.get(name)
        return None
    
    async def check_connection(self, name: str) -> bool:
        """Check if server is connected.
        
        AI_CONTEXT:
            Quick check to see if we have an active connection.
            Does not perform actual health check.
        
        Args:
            name: Server name
            
        Returns:
            True if connected, False otherwise
        """
        connection = self.get_connection(name)
        return connection is not None
    
    # ========================================================================
    # Helper Methods for connect_mcp_server
    # ========================================================================
    
    async def _create_connection(self, service: ServiceInfo, name: str):
        """Create appropriate connection based on service configuration.
        
        Args:
            service: Service information
            name: Service name
            
        Returns:
            Connection instance
            
        Raises:
            ValueError: If no connection method specified
        """
        from ..proxy.connection import ConnectionFactory
        
        if service.config.command:
            # Stdio transport
            return ConnectionFactory.create_connection(
                transport="stdio",
                url="stdio",
                server_id=name,
                command=service.config.command,
                env=service.config.auth_config.get("env", {})
            )
        elif service.config.url:
            # HTTP or WebSocket transport
            return self._create_url_connection(service, name)
        else:
            raise ValueError(f"No connection method specified for {name}")
    
    def _create_url_connection(self, service: ServiceInfo, name: str):
        """Create HTTP or WebSocket connection based on URL.
        
        Args:
            service: Service information
            name: Service name
            
        Returns:
            Connection instance
        """
        from ..proxy.connection import ConnectionFactory
        
        if service.config.url.startswith("ws://") or service.config.url.startswith("wss://"):
            return ConnectionFactory.create_connection(
                transport="websocket",
                url=service.config.url,
                server_id=name
            )
        else:
            return ConnectionFactory.create_connection(
                transport="http",
                url=service.config.url,
                server_id=name
            )
    
    async def _initialize_server(self, connection: Any, name: str) -> dict:
        """Send initialization request to server.
        
        Args:
            connection: Active connection
            name: Service name
            
        Returns:
            Initialize response
            
        Raises:
            ConnectionError: If initialization fails
        """
        init_request = self._build_init_request(name)
        init_response = await connection.send_request(init_request)
        
        if not init_response or "error" in init_response:
            error_msg = self._extract_init_error(init_response)
            raise ConnectionError(f"Failed to initialize: {error_msg}")
        
        return init_response
    
    def _build_init_request(self, name: str) -> dict:
        """Build initialization request.
        
        Args:
            name: Service name
            
        Returns:
            Request dictionary
        """
        return {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "clientInfo": {
                    "name": "agtos-metamcp",
                    "version": "0.3.0"
                },
                "capabilities": {
                    "tools": {},
                    "prompts": {},
                    "resources": {},
                    "logging": {}
                }
            },
            "id": f"init-{name}"
        }
    
    def _extract_init_error(self, response: Optional[dict]) -> str:
        """Extract error message from initialization response.
        
        Args:
            response: Response dictionary or None
            
        Returns:
            Error message string
        """
        if not response:
            return "No response"
        return response.get("error", {}).get("message", "Unknown error")
    
    def _store_connection(self, name: str, connection: Any):
        """Store connection in registry.
        
        Args:
            name: Service name
            connection: Connection instance
        """
        if not hasattr(self.registry, "_connections"):
            self.registry._connections = {}
        self.registry._connections[name] = connection
    
    def _update_service_capabilities(self, service: ServiceInfo, init_response: dict):
        """Update service with capabilities from initialization response.
        
        Args:
            service: Service to update
            init_response: Initialize response
        """
        if "result" not in init_response:
            return
            
        capabilities = init_response["result"].get("capabilities", {})
        service.capabilities = ServerCapabilities(
            tools=capabilities.get("tools", False),
            prompts=capabilities.get("prompts", False),
            resources=capabilities.get("resources", False),
            logging=capabilities.get("logging", False),
            experimental=capabilities.get("experimental", {})
        )
    
    async def _handle_connection_error(
        self,
        service: ServiceInfo,
        name: str,
        error: Exception
    ):
        """Handle connection error and cleanup.
        
        Args:
            service: Service that failed
            name: Service name
            error: Exception that occurred
        """
        logger.error(f"Failed to connect to MCP server {name}: {error}")
        service.status = ServiceStatus.ERROR
        service.last_error = str(error)
        
        # Clean up connection on error
        await self._cleanup_connection(name)
    
    async def _cleanup_connection(self, name: str):
        """Clean up connection after error.
        
        Args:
            name: Service name
        """
        if hasattr(self.registry, "_connections") and name in self.registry._connections:
            try:
                await self.registry._connections[name].disconnect()
            except:
                pass
            del self.registry._connections[name]