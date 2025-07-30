"""
Enhanced MCP proxy forwarder with modular architecture.

This is an improved version of the forwarder that uses the connection,
health, and registry modules for better separation of concerns.

AI_CONTEXT:
    This version demonstrates how the forwarder can be refactored to use
    the modular components we've created. It maintains the same functionality
    but with cleaner architecture and better maintainability.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .connection import ConnectionFactory, MCPConnection
from .health import HealthMonitor, HealthStatus
from ..registry import ServiceRegistry
from agtos.utils import get_logger

logger = get_logger(__name__)


@dataclass
class ServerConfig:
    """Configuration for a downstream MCP server."""
    id: str
    url: str
    transport: str
    namespace: str
    metadata: Dict[str, Any] = None


class EnhancedMCPForwarder:
    """
    Enhanced MCP forwarder using modular components.
    
    AI_CONTEXT:
        This implementation delegates responsibilities to specialized modules:
        - ConnectionFactory/MCPConnection: Handles transport-specific logic
        - HealthMonitor: Manages health checks and circuit breaking
        - ToolRegistry: Handles tool namespacing and conflict resolution
        
        This separation makes the forwarder easier to maintain and extend.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced forwarder."""
        self.config = config or {}
        
        # Core components
        self.connections: Dict[str, MCPConnection] = {}
        self.tool_registry = ToolRegistry()
        self.health_monitor = HealthMonitor(
            check_interval=self.config.get("health_check_interval", 30.0),
            timeout=self.config.get("health_check_timeout", 10.0)
        )
        
        # Request tracking
        self.request_mappings: Dict[str, Dict[str, Any]] = {}
        
        # Server configurations
        self.server_configs: Dict[str, ServerConfig] = {}
        
        # State
        self._running = False
        self._initialized_servers: set = set()
        
        # Configure servers from config
        self._configure_servers()
        
        # Set up health monitor callbacks
        self.health_monitor.add_status_callback(self._on_health_status_change)
    
    def _configure_servers(self):
        """Load server configurations."""
        servers_config = self.config.get("servers", [])
        
        for server_data in servers_config:
            server_config = ServerConfig(
                id=server_data["id"],
                url=server_data["url"],
                transport=server_data.get("transport", "websocket"),
                namespace=server_data.get("namespace", server_data["id"]),
                metadata=server_data.get("metadata", {})
            )
            
            self.server_configs[server_config.id] = server_config
            
            # Register namespace in tool registry
            self.tool_registry.register_server_namespace(
                server_config.id,
                server_config.namespace
            )
    
    async def start(self):
        """Start the forwarder."""
        if self._running:
            return
        
        self._running = True
        
        # Start health monitor
        await self.health_monitor.start()
        
        # Connect to all configured servers
        await self._connect_all_servers()
        
        logger.info("Enhanced MCP forwarder started")
    
    async def stop(self):
        """Stop the forwarder."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop health monitor
        await self.health_monitor.stop()
        
        # Disconnect all servers
        await self._disconnect_all_servers()
        
        logger.info("Enhanced MCP forwarder stopped")
    
    async def _connect_all_servers(self):
        """Connect to all configured servers."""
        tasks = []
        
        for server_id, server_config in self.server_configs.items():
            if server_id not in self.connections:
                task = asyncio.create_task(self._connect_server(server_id))
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for server_id, result in zip(self.server_configs.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to connect to {server_id}: {result}")
    
    async def _connect_server(self, server_id: str) -> bool:
        """Connect to a single server."""
        server_config = self.server_configs.get(server_id)
        if not server_config:
            return False
        
        try:
            # Determine transport and create connection
            transport_kwargs = {}
            
            if server_config.transport == "stdio":
                # Parse command from URL or metadata
                command = server_config.metadata.get("command", [])
                if not command and server_config.url.startswith("stdio:"):
                    # Parse command from URL like "stdio:python server.py"
                    command_str = server_config.url[6:].strip()
                    command = command_str.split()
                
                if not command:
                    raise ValueError(f"No command specified for stdio server {server_id}")
                
                transport_kwargs["command"] = command
                transport_kwargs["env"] = server_config.metadata.get("env", {})
            
            # Create connection
            connection = ConnectionFactory.create_connection(
                transport=server_config.transport,
                url=server_config.url,
                server_id=server_id,
                **transport_kwargs
            )
            
            # Connect
            await connection.connect()
            self.connections[server_id] = connection
            
            # Register with health monitor
            self.health_monitor.register_server(
                server_id=server_id,
                server_info=server_config,
                health_check_handler=lambda: self._health_check_server(server_id)
            )
            
            # Initialize MCP session
            await self._initialize_server(server_id)
            
            logger.info(f"Connected to server {server_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {server_id}: {e}")
            return False
    
    async def _initialize_server(self, server_id: str):
        """Initialize MCP session with server."""
        connection = self.connections.get(server_id)
        if not connection:
            return
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "clientInfo": {
                    "name": "agtos-metamcp",
                    "version": "0.3.0"
                }
            },
            "id": str(uuid.uuid4())
        }
        
        try:
            response = await connection.send_request(init_request)
            
            if response and "result" in response:
                # Store capabilities
                capabilities = response["result"].get("capabilities", {})
                
                # Mark as initialized
                self._initialized_servers.add(server_id)
                
                # Fetch tools
                await self._refresh_server_tools(server_id)
                
                logger.info(f"Initialized MCP session with {server_id}")
                
        except Exception as e:
            logger.error(f"Failed to initialize {server_id}: {e}")
            raise
    
    async def _refresh_server_tools(self, server_id: str):
        """Refresh tool list from server."""
        connection = self.connections.get(server_id)
        if not connection or server_id not in self._initialized_servers:
            return
        
        list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": str(uuid.uuid4())
        }
        
        try:
            response = await connection.send_request(list_request)
            
            if response and "result" in response:
                tools = response["result"].get("tools", [])
                
                # Clear existing tools for this server
                self.tool_registry.unregister_server_tools(server_id)
                
                # Register new tools
                for tool in tools:
                    self.tool_registry.register_tool(
                        server_id=server_id,
                        tool_name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {}),
                        metadata=tool.get("metadata", {})
                    )
                
                logger.info(f"Registered {len(tools)} tools from {server_id}")
                
        except Exception as e:
            logger.error(f"Failed to refresh tools from {server_id}: {e}")
            raise
    
    async def _disconnect_server(self, server_id: str):
        """Disconnect from a server."""
        # Unregister from health monitor
        self.health_monitor.unregister_server(server_id)
        
        # Remove tools
        self.tool_registry.unregister_server_tools(server_id)
        
        # Close connection
        connection = self.connections.pop(server_id, None)
        if connection:
            try:
                await connection.disconnect()
                logger.info(f"Disconnected from {server_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from {server_id}: {e}")
        
        # Remove from initialized set
        self._initialized_servers.discard(server_id)
    
    async def _disconnect_all_servers(self):
        """Disconnect from all servers."""
        server_ids = list(self.connections.keys())
        tasks = []
        
        for server_id in server_ids:
            task = asyncio.create_task(self._disconnect_server(server_id))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _health_check_server(self, server_id: str):
        """Perform health check on a server."""
        connection = self.connections.get(server_id)
        if not connection or not connection.connected:
            raise ConnectionError(f"Server {server_id} not connected")
        
        # Simple health check using list_tools
        health_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": str(uuid.uuid4())
        }
        
        response = await connection.send_request(health_request)
        if not response or "error" in response:
            raise Exception(f"Health check failed: {response}")
    
    async def _on_health_status_change(self, server_id: str, status: HealthStatus):
        """Handle health status changes."""
        logger.info(f"Server {server_id} health status changed to {status.value}")
        
        if status == HealthStatus.UNHEALTHY:
            # Attempt reconnection
            connection = self.connections.get(server_id)
            if connection:
                await self._disconnect_server(server_id)
                # Reconnection will be handled by health monitor retry logic
    
    async def forward_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to appropriate server(s)."""
        method = request.get("method", "")
        request_id = request.get("id", str(uuid.uuid4()))
        
        try:
            if method == "tools/list":
                return self._handle_list_tools(request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(request)
            else:
                return await self._broadcast_request(request)
                
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return self._error_response(request_id, str(e))
    
    def _handle_list_tools(self, request_id: str) -> Dict[str, Any]:
        """Return aggregated tool list."""
        tools = self.tool_registry.export_tool_list()
        
        return {
            "jsonrpc": "2.0",
            "result": {"tools": tools},
            "id": request_id
        }
    
    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool call to appropriate server."""
        request_id = request.get("id")
        params = request.get("params", {})
        tool_name = params.get("name", "")
        
        # Resolve tool name
        namespaced_name = self.tool_registry.resolve_tool_name(tool_name)
        if not namespaced_name:
            return self._error_response(request_id, f"Unknown tool: {tool_name}")
        
        # Get server for tool
        tool_info = self.tool_registry.get_tool(namespaced_name)
        if not tool_info:
            return self._error_response(request_id, f"Tool not found: {namespaced_name}")
        
        server_id = tool_info.server_id
        
        # Check server health
        server_status = self.health_monitor.get_server_status(server_id)
        if server_status == HealthStatus.UNHEALTHY:
            return self._error_response(request_id, f"Server {server_id} is unhealthy")
        
        # Get connection
        connection = self.connections.get(server_id)
        if not connection or not connection.connected:
            return self._error_response(request_id, f"Server {server_id} not connected")
        
        # Create downstream request
        downstream_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                **params,
                "name": tool_info.original_name  # Use original name
            },
            "id": str(uuid.uuid4())
        }
        
        # Track mapping
        self.request_mappings[downstream_request["id"]] = {
            "upstream_id": request_id,
            "server_id": server_id,
            "timestamp": time.time()
        }
        
        try:
            # Send request
            response = await connection.send_request(downstream_request)
            
            if response:
                # Map response ID back
                response["id"] = request_id
                return response
            else:
                return self._error_response(request_id, "No response from server")
                
        except Exception as e:
            return self._error_response(request_id, str(e))
        finally:
            # Clean up mapping
            self.request_mappings.pop(downstream_request["id"], None)
    
    async def _broadcast_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast request to all healthy servers."""
        request_id = request.get("id")
        errors = []
        
        for server_id, connection in self.connections.items():
            # Skip unhealthy servers
            if self.health_monitor.get_server_status(server_id) == HealthStatus.UNHEALTHY:
                continue
            
            if not connection.connected:
                continue
            
            try:
                response = await connection.send_request(request)
                if response and "result" in response:
                    response["id"] = request_id
                    return response
            except Exception as e:
                errors.append(f"{server_id}: {str(e)}")
        
        error_msg = "All servers failed: " + "; ".join(errors) if errors else "No healthy servers"
        return self._error_response(request_id, error_msg)
    
    def _error_response(self, request_id: str, message: str, code: int = -32603) -> Dict[str, Any]:
        """Create JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get forwarder status."""
        return {
            "running": self._running,
            "connections": {
                server_id: {
                    "connected": conn.connected,
                    "transport": self.server_configs[server_id].transport,
                    "namespace": self.server_configs[server_id].namespace
                }
                for server_id, conn in self.connections.items()
            },
            "health": self.health_monitor.get_all_statuses(),
            "registry": self.tool_registry.get_statistics()
        }