"""
Connection management for MCP proxy.

This module provides connection abstractions for different transport types
(WebSocket, HTTP) used by the MCP proxy forwarder.

AI_CONTEXT:
    Separates connection management concerns from the main forwarder logic.
    Provides a unified interface for different transport types while handling
    their specific requirements (persistent WebSocket connections vs stateless HTTP).
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse

from agtos.utils import get_logger

logger = get_logger(__name__)


class MCPConnection(ABC):
    """
    Abstract base class for MCP connections.
    
    AI_CONTEXT:
        Defines the interface that all MCP transport implementations must follow.
        This abstraction allows the forwarder to work with different transport
        types without knowing their implementation details.
    """
    
    def __init__(self, url: str, server_id: str):
        self.url = url
        self.server_id = server_id
        self.session: Optional[ClientSession] = None
        self._connected = False
    
    @property
    def connected(self) -> bool:
        """Check if connection is established."""
        return self._connected
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the MCP server."""
        pass
    
    @abstractmethod
    async def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request and return the response."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class WebSocketConnection(MCPConnection):
    """
    WebSocket-based MCP connection.
    
    AI_CONTEXT:
        Manages persistent WebSocket connections for real-time bidirectional
        communication with MCP servers. Handles message correlation and
        connection lifecycle.
    """
    
    def __init__(self, url: str, server_id: str, heartbeat: int = 30):
        super().__init__(url, server_id)
        self.websocket: Optional[ClientWebSocketResponse] = None
        self.heartbeat = heartbeat
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        if self._connected:
            return
        
        logger.debug(f"Establishing WebSocket connection to {self.url}")
        
        if not self.session:
            self.session = ClientSession()
        
        try:
            self.websocket = await self.session.ws_connect(
                self.url,
                heartbeat=self.heartbeat,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            self._connected = True
            
            # Start message receiver task
            self._receive_task = asyncio.create_task(self._receive_messages())
            
            logger.info(f"WebSocket connected to {self.server_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket to {self.server_id}: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if not self._connected:
            return
        
        logger.debug(f"Closing WebSocket connection to {self.server_id}")
        
        # Cancel receiver task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Close session
        if self.session:
            await self.session.close()
            self.session = None
        
        self._connected = False
        self._response_futures.clear()
        
        logger.info(f"WebSocket disconnected from {self.server_id}")
    
    async def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request and wait for correlated response."""
        if not self._connected or not self.websocket:
            raise ConnectionError(f"WebSocket not connected to {self.server_id}")
        
        request_id = request.get("id")
        if not request_id:
            raise ValueError("Request must have an 'id' field")
        
        # Create future for response
        response_future = asyncio.Future()
        self._response_futures[request_id] = response_future
        
        try:
            # Send request
            await self.websocket.send_json(request)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=30)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request {request_id} timed out for {self.server_id}")
            raise
        finally:
            # Clean up future
            self._response_futures.pop(request_id, None)
    
    async def _receive_messages(self):
        """
        Background task to receive and route WebSocket messages.
        
        AI_CONTEXT:
            Continuously receives messages from the WebSocket and correlates
            responses with pending requests using the request ID.
        """
        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        
                        # Check if this is a response to a pending request
                        request_id = data.get("id")
                        if request_id and request_id in self._response_futures:
                            future = self._response_futures[request_id]
                            if not future.done():
                                future.set_result(data)
                        else:
                            # Handle notifications or other messages
                            logger.debug(f"Received unsolicited message from {self.server_id}: {data}")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON from {self.server_id}: {e}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error from {self.server_id}: {msg.data}")
                    # Set exception on all pending futures
                    error = ConnectionError(f"WebSocket error: {msg.data}")
                    for future in self._response_futures.values():
                        if not future.done():
                            future.set_exception(error)
                    break
                    
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning(f"WebSocket closed by {self.server_id}")
                    # Set exception on all pending futures
                    error = ConnectionError("WebSocket closed")
                    for future in self._response_futures.values():
                        if not future.done():
                            future.set_exception(error)
                    break
                    
        except Exception as e:
            logger.error(f"Error in WebSocket receiver for {self.server_id}: {e}")
            # Set exception on all pending futures
            for future in self._response_futures.values():
                if not future.done():
                    future.set_exception(e)
        finally:
            self._connected = False


class HTTPConnection(MCPConnection):
    """
    HTTP-based MCP connection.
    
    AI_CONTEXT:
        Manages stateless HTTP connections for request/response communication
        with MCP servers. Each request is a separate HTTP POST.
    """
    
    def __init__(self, url: str, server_id: str, timeout: int = 30):
        super().__init__(url, server_id)
        self.timeout = timeout
    
    async def connect(self) -> None:
        """Initialize HTTP session."""
        if self._connected:
            return
        
        logger.debug(f"Initializing HTTP connection to {self.url}")
        
        if not self.session:
            self.session = ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        self._connected = True
        logger.info(f"HTTP connection ready for {self.server_id}")
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if not self._connected:
            return
        
        logger.debug(f"Closing HTTP connection to {self.server_id}")
        
        if self.session:
            await self.session.close()
            self.session = None
        
        self._connected = False
        logger.info(f"HTTP connection closed for {self.server_id}")
    
    async def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send HTTP request and return response."""
        if not self._connected or not self.session:
            raise ConnectionError(f"HTTP session not initialized for {self.server_id}")
        
        try:
            async with self.session.post(self.url, json=request) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed for {self.server_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in HTTP request for {self.server_id}: {e}")
            raise


class StdioConnection(MCPConnection):
    """
    Stdio-based MCP connection for local servers.
    
    AI_CONTEXT:
        Manages MCP servers that communicate via stdin/stdout. The client
        launches the server as a subprocess and communicates using JSON-RPC
        over the process's standard I/O streams.
    """
    
    def __init__(self, command: list[str], server_id: str, env: Optional[Dict[str, str]] = None):
        super().__init__(url="stdio", server_id=server_id)
        self.command = command
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._write_lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Start the server subprocess and establish stdio connection."""
        if self._connected:
            return
        
        logger.debug(f"Starting stdio server for {self.server_id}: {' '.join(self.command)}")
        
        try:
            # Merge environment variables
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            # Start subprocess
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env
            )
            
            if not self.process.stdin or not self.process.stdout:
                raise ConnectionError("Failed to create subprocess pipes")
            
            self._connected = True
            
            # Start message receiver task
            self._receive_task = asyncio.create_task(self._receive_messages())
            
            # Also monitor stderr
            self._stderr_task = asyncio.create_task(self._monitor_stderr())
            
            logger.info(f"Stdio server started for {self.server_id} (PID: {self.process.pid})")
            
        except Exception as e:
            logger.error(f"Failed to start stdio server for {self.server_id}: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Terminate the server subprocess."""
        if not self._connected:
            return
        
        logger.debug(f"Stopping stdio server for {self.server_id}")
        
        # Cancel receiver task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Cancel stderr task
        if self._stderr_task:
            self._stderr_task.cancel()
            try:
                await self._stderr_task
            except asyncio.CancelledError:
                pass
        
        # Terminate process
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Process did not terminate, killing {self.server_id}")
                self.process.kill()
                await self.process.wait()
            
            self.process = None
        
        self._connected = False
        self._response_futures.clear()
        
        logger.info(f"Stdio server stopped for {self.server_id}")
    
    async def send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request via stdin and wait for response via stdout."""
        if not self._connected or not self.process or not self.process.stdin:
            raise ConnectionError(f"Stdio server not connected for {self.server_id}")
        
        request_id = request.get("id")
        if not request_id:
            raise ValueError("Request must have an 'id' field")
        
        # Create future for response
        response_future = asyncio.Future()
        self._response_futures[request_id] = response_future
        
        try:
            # Send request as JSON line
            request_json = json.dumps(request) + "\n"
            
            async with self._write_lock:
                self.process.stdin.write(request_json.encode())
                await self.process.stdin.drain()
            
            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=30)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request {request_id} timed out for {self.server_id}")
            raise
        finally:
            # Clean up future
            self._response_futures.pop(request_id, None)
    
    async def _receive_messages(self):
        """
        Read JSON-RPC messages from stdout.
        
        AI_CONTEXT:
            Reads lines from the subprocess stdout and parses them as JSON-RPC
            messages. Correlates responses with pending requests by ID.
        """
        if not self.process or not self.process.stdout:
            return
        
        try:
            while self._connected:
                line = await self.process.stdout.readline()
                if not line:
                    logger.warning(f"EOF from {self.server_id} stdout")
                    break
                
                try:
                    data = json.loads(line.decode().strip())
                    
                    # Check if this is a response to a pending request
                    request_id = data.get("id")
                    if request_id and request_id in self._response_futures:
                        future = self._response_futures[request_id]
                        if not future.done():
                            future.set_result(data)
                    else:
                        # Handle notifications or other messages
                        logger.debug(f"Received unsolicited message from {self.server_id}: {data}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {self.server_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing message from {self.server_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in stdio receiver for {self.server_id}: {e}")
            # Set exception on all pending futures
            for future in self._response_futures.values():
                if not future.done():
                    future.set_exception(e)
        finally:
            self._connected = False
    
    async def _monitor_stderr(self):
        """Monitor stderr for error messages."""
        if not self.process or not self.process.stderr:
            return
        
        try:
            while self._connected:
                line = await self.process.stderr.readline()
                if not line:
                    break
                
                error_msg = line.decode().strip()
                if error_msg:
                    logger.warning(f"[{self.server_id} stderr] {error_msg}")
        except Exception as e:
            logger.error(f"Error monitoring stderr for {self.server_id}: {e}")


class ConnectionFactory:
    """
    Factory for creating MCP connections based on transport type.
    
    AI_CONTEXT:
        Centralizes connection creation logic and allows for easy extension
        with new transport types in the future.
    """
    
    @staticmethod
    def create_connection(
        transport: str,
        url: str,
        server_id: str,
        **kwargs
    ) -> MCPConnection:
        """
        Create a connection instance based on transport type.
        
        Args:
            transport: Transport type ("websocket", "http", or "stdio")
            url: Server URL (ignored for stdio)
            server_id: Unique server identifier
            **kwargs: Additional transport-specific parameters
                - For stdio: command (list), env (dict)
        
        Returns:
            MCPConnection instance
        
        Raises:
            ValueError: If transport type is not supported
        """
        if transport.lower() == "websocket":
            return WebSocketConnection(
                url=url,
                server_id=server_id,
                heartbeat=kwargs.get("heartbeat", 30)
            )
        elif transport.lower() == "http":
            return HTTPConnection(
                url=url,
                server_id=server_id,
                timeout=kwargs.get("timeout", 30)
            )
        elif transport.lower() == "stdio":
            command = kwargs.get("command")
            if not command:
                raise ValueError("stdio transport requires 'command' parameter")
            return StdioConnection(
                command=command,
                server_id=server_id,
                env=kwargs.get("env")
            )
        else:
            raise ValueError(f"Unsupported transport type: {transport}")