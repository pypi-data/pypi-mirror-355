"""
MCP proxy forwarder for routing requests to downstream MCP servers.

This module implements the core proxy functionality that enables agentctl to act
as a Meta-MCP server, aggregating and forwarding requests to multiple downstream
MCP servers while handling protocol lifecycle, connection management, and tool
namespacing.

AI_CONTEXT:
    This is a critical component of the Meta-MCP architecture. The forwarder:
    1. Maintains persistent connections to downstream MCP servers
    2. Routes JSON-RPC requests with proper request ID mapping
    3. Handles MCP protocol lifecycle (initialize, list_tools, call_tool)
    4. Manages tool namespacing to avoid conflicts between servers
    5. Implements connection pooling and health monitoring
    
    Key design decisions:
    - Uses asyncio for concurrent connection management
    - Implements exponential backoff for connection retries
    - Caches tool capabilities to reduce downstream requests
    - Translates and aggregates errors from multiple servers
    - Supports both WebSocket and HTTP transports
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse

from agtos.utils import get_logger

logger = get_logger(__name__)


class ConnectionState(Enum):
    """State of a downstream MCP server connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


class TransportType(Enum):
    """Type of transport for MCP communication."""
    WEBSOCKET = "websocket"
    HTTP = "http"


@dataclass
class MCPServer:
    """
    Configuration and state for a downstream MCP server.
    
    AI_CONTEXT:
        Represents a single downstream MCP server that the forwarder connects to.
        Tracks connection state, capabilities, and health metrics.
    """
    id: str
    url: str
    transport: TransportType
    namespace: str  # Prefix for tool names from this server
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    websocket: Optional[ClientWebSocketResponse] = None
    session: Optional[ClientSession] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    tool_cache: Dict[str, Any] = field(default_factory=dict)
    last_health_check: float = 0
    consecutive_failures: int = 0
    backoff_until: float = 0
    
    def should_retry(self) -> bool:
        """Check if we should retry connecting to this server."""
        return time.time() >= self.backoff_until
    
    def calculate_backoff(self):
        """Calculate exponential backoff time after a failure."""
        # Exponential backoff: 1s, 2s, 4s, 8s, ..., max 60s
        delay = min(60, 2 ** self.consecutive_failures)
        self.backoff_until = time.time() + delay
        return delay


@dataclass
class RequestMapping:
    """Maps upstream request IDs to downstream request IDs."""
    upstream_id: str
    downstream_id: str
    server_id: str
    timestamp: float


class MCPForwarder:
    """
    Forwards MCP requests to downstream servers with intelligent routing.
    
    AI_CONTEXT:
        This is the core proxy component that makes agentctl a Meta-MCP server.
        It manages connections to multiple downstream MCP servers and routes
        requests appropriately. Key responsibilities:
        
        1. Connection lifecycle management
        2. Request routing and ID mapping
        3. Tool namespacing and conflict resolution
        4. Error aggregation and translation
        5. Health monitoring and failover
        
        The forwarder uses asyncio for concurrent operations and maintains
        persistent connections when possible for better performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MCP forwarder.
        
        Args:
            config: Configuration dictionary with server definitions
        """
        self.servers: Dict[str, MCPServer] = {}
        self.request_mappings: Dict[str, RequestMapping] = {}
        self.tool_to_server: Dict[str, str] = {}  # tool_name -> server_id
        self.config = config or {}
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Configure from config
        self._configure_servers()
    
    def _configure_servers(self):
        """Configure downstream servers from configuration."""
        servers_config = self.config.get("servers", [])
        for server_config in servers_config:
            server = MCPServer(
                id=server_config["id"],
                url=server_config["url"],
                transport=TransportType(server_config.get("transport", "websocket")),
                namespace=server_config.get("namespace", server_config["id"])
            )
            self.servers[server.id] = server
    
    async def start(self):
        """Start the forwarder and establish connections."""
        if self._running:
            return
        
        self._running = True
        
        # Start health check and cleanup tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Attempt to connect to all servers
        await self._connect_all_servers()
    
    async def stop(self):
        """Stop the forwarder and close all connections."""
        self._running = False
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all connections
        await self._disconnect_all_servers()
    
    async def _connect_all_servers(self):
        """Attempt to connect to all configured servers."""
        tasks = []
        for server in self.servers.values():
            if server.should_retry():
                tasks.append(self._connect_server(server))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _connect_server(self, server: MCPServer) -> bool:
        """
        Connect to a single MCP server.
        
        AI_CONTEXT:
            Establishes connection based on transport type and performs
            MCP initialization handshake. Caches server capabilities.
        """
        if server.connection_state == ConnectionState.CONNECTED:
            return True
        
        server.connection_state = ConnectionState.CONNECTING
        logger.info(f"Connecting to MCP server {server.id} at {server.url}")
        
        try:
            if server.transport == TransportType.WEBSOCKET:
                await self._connect_websocket(server)
            else:
                await self._connect_http(server)
            
            # Perform MCP initialization
            await self._initialize_server(server)
            
            server.connection_state = ConnectionState.CONNECTED
            server.consecutive_failures = 0
            logger.info(f"Successfully connected to {server.id}")
            return True
            
        except Exception as e:
            server.connection_state = ConnectionState.FAILED
            server.consecutive_failures += 1
            backoff = server.calculate_backoff()
            logger.error(f"Failed to connect to {server.id}: {e}. "
                        f"Retrying in {backoff}s")
            return False
    
    async def _connect_websocket(self, server: MCPServer):
        """Establish WebSocket connection to MCP server."""
        if not server.session:
            server.session = ClientSession()
        
        server.websocket = await server.session.ws_connect(
            server.url,
            heartbeat=30
        )
    
    async def _connect_http(self, server: MCPServer):
        """Establish HTTP session for MCP server."""
        if not server.session:
            server.session = ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def _initialize_server(self, server: MCPServer):
        """
        Perform MCP initialization handshake.
        
        AI_CONTEXT:
            Sends initialize request to establish protocol version and
            discover server capabilities. Also fetches initial tool list.
        """
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
        
        response = await self._send_to_server(server, init_request)
        if response and "result" in response:
            server.capabilities = response["result"].get("capabilities", {})
            
            # Fetch tool list
            await self._refresh_server_tools(server)
    
    async def _refresh_server_tools(self, server: MCPServer):
        """Fetch and cache tool list from server."""
        list_tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": str(uuid.uuid4())
        }
        
        response = await self._send_to_server(server, list_tools_request)
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            server.tool_cache.clear()
            
            # Cache tools with namespaced names
            for tool in tools:
                original_name = tool["name"]
                namespaced_name = f"{server.namespace}.{original_name}"
                server.tool_cache[namespaced_name] = tool
                self.tool_to_server[namespaced_name] = server.id
                
                logger.debug(f"Registered tool {namespaced_name} from {server.id}")
    
    async def _send_to_server(self, server: MCPServer, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send request to downstream server and wait for response.
        
        AI_CONTEXT:
            Handles both WebSocket and HTTP transports. For WebSocket,
            correlates responses by request ID. For HTTP, uses standard
            request/response pattern.
        """
        if server.connection_state != ConnectionState.CONNECTED:
            raise ConnectionError(f"Server {server.id} is not connected")
        
        try:
            if server.transport == TransportType.WEBSOCKET:
                return await self._send_websocket(server, request)
            else:
                return await self._send_http(server, request)
        except Exception as e:
            logger.error(f"Error sending to {server.id}: {e}")
            # Mark server as failed for reconnection
            server.connection_state = ConnectionState.FAILED
            raise
    
    async def _send_websocket(self, server: MCPServer, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request over WebSocket and wait for response."""
        if not server.websocket:
            raise ConnectionError(f"WebSocket not connected for {server.id}")
        
        request_id = request.get("id")
        
        # Send request
        await server.websocket.send_json(request)
        
        # Wait for response with matching ID
        # In production, this would use a proper correlation mechanism
        async for msg in server.websocket:
            if msg.type == aiohttp.WSMsgType.TEXT:
                response = json.loads(msg.data)
                if response.get("id") == request_id:
                    return response
            elif msg.type == aiohttp.WSMsgType.ERROR:
                raise ConnectionError(f"WebSocket error: {msg.data}")
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                raise ConnectionError("WebSocket closed")
        
        return None
    
    async def _send_http(self, server: MCPServer, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request over HTTP and return response."""
        if not server.session:
            raise ConnectionError(f"HTTP session not established for {server.id}")
        
        async with server.session.post(server.url, json=request) as response:
            response.raise_for_status()
            return await response.json()
    
    async def forward_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward an incoming request to the appropriate downstream server.
        
        AI_CONTEXT:
            Main entry point for request forwarding. Routes based on method:
            - tools/list: Aggregates from all servers
            - tools/call: Routes to specific server based on tool namespace
            - Other methods: Broadcasts or routes based on configuration
        """
        method = request.get("method", "")
        request_id = request.get("id", str(uuid.uuid4()))
        
        try:
            if method == "tools/list":
                return await self._handle_list_tools(request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(request)
            else:
                # For other methods, broadcast to all servers
                return await self._broadcast_request(request)
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return self._error_response(request_id, str(e))
    
    async def _handle_list_tools(self, request_id: str) -> Dict[str, Any]:
        """
        Aggregate tool lists from all connected servers.
        
        AI_CONTEXT:
            Combines tool lists from all servers, applying namespace
            prefixes to avoid conflicts. Returns unified tool list.
        """
        all_tools = []
        
        for server in self.servers.values():
            if server.connection_state == ConnectionState.CONNECTED:
                for namespaced_name, tool in server.tool_cache.items():
                    # Create tool entry with namespaced name
                    tool_entry = {
                        "name": namespaced_name,
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {})
                    }
                    all_tools.append(tool_entry)
        
        return {
            "jsonrpc": "2.0",
            "result": {"tools": all_tools},
            "id": request_id
        }
    
    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route tool call to the appropriate downstream server.
        
        AI_CONTEXT:
            Extracts namespace from tool name and routes to correct server.
            Translates request/response IDs for correlation.
        """
        request_id = request.get("id")
        params = request.get("params", {})
        tool_name = params.get("name", "")
        
        # Find server for this tool
        server_id = self.tool_to_server.get(tool_name)
        if not server_id:
            return self._error_response(request_id, f"Unknown tool: {tool_name}")
        
        server = self.servers.get(server_id)
        if not server or server.connection_state != ConnectionState.CONNECTED:
            return self._error_response(request_id, f"Server {server_id} not available")
        
        # Strip namespace from tool name for downstream request
        original_tool_name = tool_name.split(".", 1)[1] if "." in tool_name else tool_name
        
        # Create downstream request
        downstream_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                **params,
                "name": original_tool_name
            },
            "id": str(uuid.uuid4())
        }
        
        # Track request mapping
        self.request_mappings[downstream_request["id"]] = RequestMapping(
            upstream_id=request_id,
            downstream_id=downstream_request["id"],
            server_id=server_id,
            timestamp=time.time()
        )
        
        try:
            # Send to downstream server
            response = await self._send_to_server(server, downstream_request)
            
            if response:
                # Translate response ID back to upstream
                response["id"] = request_id
                return response
            else:
                return self._error_response(request_id, "No response from server")
                
        except Exception as e:
            return self._error_response(request_id, str(e))
    
    async def _broadcast_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Broadcast request to all connected servers.
        
        AI_CONTEXT:
            Used for methods that need to reach all servers.
            Aggregates responses and returns first successful one.
        """
        request_id = request.get("id")
        errors = []
        
        for server in self.servers.values():
            if server.connection_state == ConnectionState.CONNECTED:
                try:
                    response = await self._send_to_server(server, request)
                    if response and "result" in response:
                        response["id"] = request_id
                        return response
                except Exception as e:
                    errors.append(f"{server.id}: {str(e)}")
        
        # If no successful responses, return aggregated error
        error_msg = "All servers failed: " + "; ".join(errors) if errors else "No connected servers"
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
    
    async def _health_check_loop(self):
        """
        Background task to monitor server health.
        
        AI_CONTEXT:
            Periodically checks connection health and attempts to
            reconnect failed servers. Also refreshes tool caches.
        """
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                for server in self.servers.values():
                    if server.connection_state == ConnectionState.CONNECTED:
                        # Perform health check
                        try:
                            # Simple ping using list_tools
                            await self._refresh_server_tools(server)
                            server.last_health_check = time.time()
                        except Exception as e:
                            logger.warning(f"Health check failed for {server.id}: {e}")
                            server.connection_state = ConnectionState.FAILED
                    
                    elif server.connection_state == ConnectionState.FAILED and server.should_retry():
                        # Attempt reconnection
                        asyncio.create_task(self._connect_server(server))
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def _cleanup_loop(self):
        """
        Background task to clean up old request mappings.
        
        AI_CONTEXT:
            Prevents memory leak by removing old request mappings
            that are no longer needed for correlation.
        """
        while self._running:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                
                current_time = time.time()
                expired_ids = []
                
                for mapping_id, mapping in self.request_mappings.items():
                    # Remove mappings older than 5 minutes
                    if current_time - mapping.timestamp > 300:
                        expired_ids.append(mapping_id)
                
                for mapping_id in expired_ids:
                    del self.request_mappings[mapping_id]
                
                if expired_ids:
                    logger.debug(f"Cleaned up {len(expired_ids)} expired request mappings")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _disconnect_all_servers(self):
        """Disconnect from all servers."""
        tasks = []
        for server in self.servers.values():
            tasks.append(self._disconnect_server(server))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _disconnect_server(self, server: MCPServer):
        """Disconnect from a single server."""
        try:
            if server.websocket:
                await server.websocket.close()
                server.websocket = None
            
            if server.session:
                await server.session.close()
                server.session = None
            
            server.connection_state = ConnectionState.DISCONNECTED
            logger.info(f"Disconnected from {server.id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {server.id}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all connections and statistics.
        
        AI_CONTEXT:
            Provides health monitoring data for the Meta-MCP server,
            including connection states, tool counts, and metrics.
        """
        status = {
            "running": self._running,
            "servers": {},
            "total_tools": len(self.tool_to_server),
            "active_requests": len(self.request_mappings)
        }
        
        for server_id, server in self.servers.items():
            status["servers"][server_id] = {
                "state": server.connection_state.value,
                "url": server.url,
                "transport": server.transport.value,
                "tools": len(server.tool_cache),
                "consecutive_failures": server.consecutive_failures,
                "last_health_check": server.last_health_check
            }
        
        return status


# Example usage and testing
async def example_usage():
    """
    Example of how to use the MCP forwarder.
    
    AI_CONTEXT:
        This demonstrates the basic setup and usage pattern for the
        forwarder. In production, configuration would come from
        agtos's config system.
    """
    config = {
        "servers": [
            {
                "id": "filesystem",
                "url": "ws://localhost:3000",
                "transport": "websocket",
                "namespace": "fs"
            },
            {
                "id": "github",
                "url": "http://localhost:3001",
                "transport": "http",
                "namespace": "gh"
            }
        ]
    }
    
    forwarder = MCPForwarder(config)
    
    try:
        # Start the forwarder
        await forwarder.start()
        
        # Example: List all tools
        list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": "1"
        }
        
        response = await forwarder.forward_request(list_request)
        logger.debug(f"Available tools: {json.dumps(response, indent=2)}")
        
        # Example: Call a tool
        call_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fs.read_file",
                "arguments": {"path": "/tmp/test.txt"}
            },
            "id": "2"
        }
        
        response = await forwarder.forward_request(call_request)
        logger.debug(f"Tool response: {json.dumps(response, indent=2)}")
        
        # Get status
        status = forwarder.get_status()
        logger.debug(f"Forwarder status: {json.dumps(status, indent=2)}")
        
    finally:
        # Stop the forwarder
        await forwarder.stop()


if __name__ == "__main__":
    # For testing purposes
    asyncio.run(example_usage())