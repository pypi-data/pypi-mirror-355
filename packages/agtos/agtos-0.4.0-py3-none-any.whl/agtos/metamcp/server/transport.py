"""Transport implementations for Meta-MCP server.

AI_CONTEXT:
    This module contains transport-specific code for the Meta-MCP server,
    supporting both HTTP (via FastAPI) and stdio transports. The transport
    layer is responsible for:
    
    - Receiving requests in the appropriate format
    - Parsing JSON-RPC messages
    - Routing to handler methods
    - Formatting and sending responses
    
    The module provides:
    - HTTP route setup for FastAPI
    - Stdio mode for Claude Code compatibility
    - WebSocket support for future real-time features
    - Common JSON-RPC processing logic
    
    Navigation:
    - setup_routes: Configures FastAPI routes
    - start_stdio: Main stdio transport implementation
    - _process_json_rpc_request: Common request processing
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import Request, WebSocket
from fastapi.responses import JSONResponse

from ..types import MCPRequest, MCPResponse, MCPError

logger = logging.getLogger(__name__)


def setup_routes(server):
    """Configure FastAPI routes for the Meta-MCP server.
    
    AI_CONTEXT: This function sets up HTTP routes on the server's FastAPI app.
    It's called from the server's initialization to configure all endpoints.
    
    Args:
        server: The MetaMCPServer instance to configure routes for
    """
    app = server.app
    
    # Register route handlers
    _register_main_mcp_route(app, server)
    _register_websocket_route(app, server)
    _register_health_routes(app, server)
    _register_internal_routes(app, server)


def _register_main_mcp_route(app, server):
    """Register the main MCP JSON-RPC endpoint."""
    @app.post("/")
    async def handle_mcp_request(request: Request) -> JSONResponse:
        """Handle MCP JSON-RPC requests over HTTP.
        
        AI_CONTEXT: Main HTTP endpoint for MCP protocol. Receives JSON-RPC
        requests, processes them, and returns JSON-RPC responses.
        """
        try:
            # Parse JSON-RPC request
            body = await request.json()
            
            # Process the request using common handler
            response_dict = await server._process_json_rpc_request(body)
            
            # Debug check for tools/list
            if body.get("method") == "tools/list" and "result" in response_dict:
                if "tools" in response_dict["result"] and response_dict["result"]["tools"]:
                    first_tool = response_dict["result"]["tools"][0]
                    logger.debug(f"[DEBUG HTTP] First tool keys before JSONResponse: {list(first_tool.keys())}")
            
            return JSONResponse(content=response_dict)
            
        except Exception as e:
            return _build_error_response(e)


def _register_websocket_route(app, server):
    """Register WebSocket endpoint for real-time features."""
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Handle WebSocket connections for real-time features.
        
        AI_CONTEXT: WebSocket support for future features like:
        - Real-time log streaming
        - Progress updates for long-running operations
        - Bidirectional communication with clients
        """
        await websocket.accept()
        try:
            await _handle_websocket_messages(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close()


def _register_health_routes(app, server):
    """Register health and statistics endpoints."""
    @app.get("/health")
    async def health_check():
        """Health check endpoint.
        
        AI_CONTEXT: Provides server health status including service health,
        uptime, and statistics. Used for monitoring and debugging.
        """
        return await _build_health_response(server)
    
    @app.get("/stats")
    async def get_stats():
        """Get server statistics.
        
        AI_CONTEXT: Detailed statistics endpoint for monitoring request counts,
        cache performance, and service usage.
        """
        return _build_stats_response(server)


def _register_internal_routes(app, server):
    """Register internal management endpoints."""
    @app.post("/internal/reload-tool")
    async def reload_tool(request: Request):
        """Internal endpoint to trigger hot-reload of a specific tool.
        
        AI_CONTEXT: This endpoint is called by tool_creator when a new tool
        is created, triggering immediate reload without server restart.
        """
        try:
            return await _handle_tool_reload(request, server)
        except Exception as e:
            logger.exception("Error in tool reload endpoint")
            return JSONResponse(content={"error": str(e)}, status_code=500)


def _build_error_response(exception: Exception) -> JSONResponse:
    """Build standard JSON-RPC error response."""
    logger.exception("Unexpected error handling HTTP request")
    error_response = {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": -32603,
            "message": "Internal error",
            "data": {"error": str(exception)}
        }
    }
    return JSONResponse(content=error_response)


async def _handle_websocket_messages(websocket: WebSocket):
    """Handle incoming WebSocket messages."""
    while True:
        # Handle WebSocket messages (future: streaming, logs)
        data = await websocket.receive_text()
        # Echo for now - will implement real features later
        await websocket.send_text(f"Echo: {data}")


async def _build_health_response(server) -> dict:
    """Build health check response data."""
    services_health = await server._check_services_health()
    uptime = (datetime.now() - server.stats["start_time"]).total_seconds()
    
    return {
        "status": "healthy" if all(s["healthy"] for s in services_health.values()) else "degraded",
        "uptime_seconds": uptime,
        "services": services_health,
        "stats": server.stats
    }


def _build_stats_response(server) -> dict:
    """Build statistics response data."""
    cache_hits = server.stats["cache_hits"]
    cache_misses = server.stats["cache_misses"]
    hit_rate = cache_hits / max(1, cache_hits + cache_misses)
    
    return {
        "server": server.stats,
        "session": server._get_session_summary() if hasattr(server, '_get_session_summary') else {},
        "cache": {
            "size": server.cache.size(),
            "hit_rate": hit_rate
        }
    }


async def _handle_tool_reload(request: Request, server) -> JSONResponse:
    """Handle tool reload request."""
    body = await request.json()
    tool_name = body.get("tool_name")
    
    if not tool_name:
        return JSONResponse(
            content={"error": "tool_name is required"},
            status_code=400
        )
    
    # Trigger reload
    success = await server.hot_reloader.reload_specific_tool(tool_name)
    
    if success:
        # Rebuild routes after reload
        server.router.build_routes_from_registry()
        return JSONResponse(
            content={"status": "success", "message": f"Tool {tool_name} reloaded successfully"}
        )
    else:
        return JSONResponse(
            content={"status": "error", "message": f"Failed to reload tool {tool_name}"},
            status_code=500
        )


class TransportMixin:
    """Mixin class containing transport-specific methods.
    
    AI_CONTEXT: This mixin provides stdio transport and common JSON-RPC
    processing logic. It's designed to be used with MetaMCPServer.
    """
    
    async def start_stdio(self):
        """Start the Meta-MCP server in stdio mode.
        
        AI_CONTEXT:
            In stdio mode, the server reads JSON-RPC messages from stdin
            and writes responses to stdout. This is compatible with Claude Code
            and other MCP clients that expect stdio communication.
            
            Key aspects:
            - All logging goes to stderr to avoid protocol interference
            - Each message is a single line of JSON
            - EOF on stdin triggers graceful shutdown
            - Errors are returned as JSON-RPC error responses
        """
        logger.info("Starting Meta-MCP server in stdio mode")
        
        # Configure logging for stdio
        self._configure_logging_for_stdio()
        
        # Discover services on startup
        await self._discover_services()
        
        # Setup stdio reader
        reader = await self._setup_stdio_reader()
        
        # Main stdio loop
        while True:
            should_continue = await self._read_and_process_stdio_line(reader)
            if not should_continue:
                break
        
        # Cleanup on exit
        await self.stop()
    
    def _configure_logging_for_stdio(self):
        """Configure logging to use stderr for stdio mode."""
        for handler in logging.root.handlers:
            if hasattr(handler, 'stream') and handler.stream == sys.stdout:
                handler.stream = sys.stderr
    
    async def _setup_stdio_reader(self) -> asyncio.StreamReader:
        """Setup async reader for stdin.
        
        Returns:
            StreamReader for stdin
        """
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        return reader
    
    async def _read_and_process_stdio_line(self, reader: asyncio.StreamReader) -> bool:
        """Read and process a single line from stdio.
        
        Args:
            reader: StreamReader for stdin
            
        Returns:
            True to continue loop, False to exit
        """
        try:
            # Read a line from stdin
            line = await reader.readline()
            if not line:
                # EOF reached
                logger.info("EOF received on stdin, shutting down")
                return False
            
            # Parse and process request
            request_data = self._parse_stdio_request(line)
            if request_data:
                response = await self._process_json_rpc_request(request_data)
                self._send_stdio_response(response)
            
            return True
            
        except asyncio.CancelledError:
            logger.info("Stdio server cancelled")
            return False
        except Exception as e:
            logger.exception(f"Error in stdio loop: {e}")
            self._send_stdio_error(e)
            return True
    
    def _parse_stdio_request(self, line: bytes) -> Optional[dict]:
        """Parse JSON request from stdio line.
        
        Args:
            line: Raw bytes from stdin
            
        Returns:
            Parsed request dict or None if parse error
        """
        try:
            return json.loads(line.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            # Send parse error response
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                }
            }
            self._send_stdio_response(error_response)
            return None
    
    def _send_stdio_response(self, response: dict):
        """Send response to stdout.
        
        Args:
            response: Response dictionary to send
        """
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    
    def _send_stdio_error(self, exception: Exception):
        """Send error response to stdout.
        
        Args:
            exception: Exception that occurred
        """
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(exception)
            }
        }
        try:
            self._send_stdio_response(error_response)
        except:
            # If we can't even send the error, just log it
            pass
    
    async def _process_json_rpc_request(self, body: dict) -> dict:
        """Process a JSON-RPC request and return the response.
        
        AI_CONTEXT:
            This method contains the core JSON-RPC processing logic that's
            shared between HTTP and stdio transports. It handles request parsing,
            routing, execution, and response building.
            
            The method:
            1. Parses the JSON-RPC request
            2. Routes to appropriate handler based on method
            3. Executes the handler
            4. Builds and returns JSON-RPC response
            5. Handles errors according to JSON-RPC spec
        
        Args:
            body: The JSON-RPC request as a dictionary
            
        Returns:
            The JSON-RPC response as a dictionary
        """
        try:
            # Log request if enabled
            self._log_request_if_enabled(body)
            
            mcp_request = MCPRequest.from_dict(body)
            
            # Update statistics
            self.stats["requests_total"] += 1
            
            # Route to appropriate handler
            result = await self._route_to_handler(mcp_request)
            
            # Build and return success response
            return self._build_success_response(mcp_request.id, result)
            
        except MCPError as e:
            return self._handle_mcp_error(e, mcp_request.id if "mcp_request" in locals() else None)
            
        except Exception as e:
            return self._handle_unexpected_error(e, mcp_request.id if "mcp_request" in locals() else None)
    
    def _log_request_if_enabled(self, body: dict):
        """Log request if logging is enabled.
        
        Args:
            body: Request body to log
        """
        if self.log_requests:
            logger.info(f"MCP Request: {json.dumps(body, indent=2)}")
    
    async def _route_to_handler(self, mcp_request: MCPRequest) -> Any:
        """Route request to appropriate handler based on method.
        
        Args:
            mcp_request: The MCP request
            
        Returns:
            Handler result
            
        Raises:
            MCPError: If method not found
        """
        if mcp_request.method == "initialize":
            return await self._handle_initialize(mcp_request.params or {})
        elif mcp_request.method == "tools/list":
            return await self._handle_tools_list()
        elif mcp_request.method == "tools/call":
            return await self._handle_tool_call(mcp_request.params)
        elif mcp_request.method == "resources/list":
            return await self._handle_resources_list()
        elif mcp_request.method == "resources/read":
            return await self._handle_resource_read(mcp_request.params)
        else:
            raise MCPError(
                code=-32601,
                message=f"Method not found: {mcp_request.method}"
            )
    
    def _build_success_response(self, request_id: Any, result: Any) -> dict:
        """Build successful JSON-RPC response.
        
        Args:
            request_id: Request ID
            result: Handler result
            
        Returns:
            Response dictionary
        """
        # Special handling for tools/list to ensure no non-standard fields
        if isinstance(result, dict) and "tools" in result:
            filtered_tools = []
            for tool in result["tools"]:
                # Ensure only standard MCP fields are included
                if isinstance(tool, dict):
                    filtered_tool = {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {})
                    }
                    filtered_tools.append(filtered_tool)
                else:
                    filtered_tools.append(tool)
            result = {"tools": filtered_tools}
        
        response = MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            result=result
        )
        
        self.stats["requests_success"] += 1
        
        # Log response if enabled
        if self.log_requests:
            logger.info(f"MCP Response: {json.dumps(response.to_dict(), indent=2)}")
        
        return response.to_dict()
    
    def _handle_mcp_error(self, error: MCPError, request_id: Any) -> dict:
        """Handle MCP-specific errors.
        
        Args:
            error: MCP error
            request_id: Request ID
            
        Returns:
            Error response dictionary
        """
        self.stats["requests_error"] += 1
        error_response = MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            error=error.to_dict()
        )
        
        # Log error response if enabled
        if self.log_requests:
            logger.error(f"MCP Error Response: {json.dumps(error_response.to_dict(), indent=2)}")
        
        return error_response.to_dict()
    
    def _handle_unexpected_error(self, exception: Exception, request_id: Any) -> dict:
        """Handle unexpected errors.
        
        Args:
            exception: The exception
            request_id: Request ID
            
        Returns:
            Error response dictionary
        """
        logger.exception("Unexpected error processing JSON-RPC request")
        self.stats["requests_error"] += 1
        
        error = MCPError(
            code=-32603,
            message="Internal error",
            data={"error": str(exception)}
        )
        
        error_response = MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            error=error.to_dict()
        )
        
        return error_response.to_dict()