"""Connection pooling for Meta-MCP Server.

AI_CONTEXT:
    This module manages persistent connections to downstream services.
    It provides:
    - Connection pooling with configurable limits
    - Automatic reconnection on failure
    - Connection health monitoring
    - Load distribution across connections
    - Resource cleanup on shutdown
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ..types import (
    ConnectionState,
    ConnectionInfo,
    Credential,
    ConnectionError
)

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for connection pools."""
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0  # 5 minutes
    health_check_interval: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PoolStats:
    """Statistics for a connection pool."""
    created_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "created": self.created_connections,
            "active": self.active_connections,
            "idle": self.idle_connections,
            "failed": self.failed_connections,
            "requests": self.total_requests
        }


class Connection(ABC):
    """Abstract base class for service connections.
    
    AI_CONTEXT:
        This is the base class for all connection types (MCP, CLI, REST).
        Each connection maintains its own state and handles protocol-specific
        communication with the downstream service.
    """
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        """Initialize connection.
        
        Args:
            service_name: Name of the service
            config: Connection configuration
        """
        self.service_name = service_name
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self.info = ConnectionInfo(
            service_name=service_name,
            state=self.state
        )
        self.credential: Optional[Credential] = None
    
    @abstractmethod
    async def connect(self, credential: Optional[Credential] = None):
        """Establish connection to the service."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close the connection."""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool on this connection."""
        pass
    
    def update_state(self, state: ConnectionState):
        """Update connection state."""
        self.state = state
        self.info.state = state
        if state == ConnectionState.CONNECTED:
            self.info.connected_at = datetime.now()


class ServicePool:
    """Connection pool for a specific service.
    
    AI_CONTEXT:
        Each service gets its own pool to manage connections independently.
        The pool handles:
        - Creating connections up to max_connections
        - Reusing idle connections
        - Health checking and removing unhealthy connections
        - Fair distribution of requests across connections
    """
    
    def __init__(
        self,
        service_name: str,
        connection_factory,
        config: PoolConfig
    ):
        """Initialize service pool.
        
        Args:
            service_name: Name of the service
            connection_factory: Factory function to create connections
            config: Pool configuration
        """
        self.service_name = service_name
        self.connection_factory = connection_factory
        self.config = config
        
        # Connection management
        self.connections: List[Connection] = []
        self.available: asyncio.Queue[Connection] = asyncio.Queue()
        self.stats = PoolStats()
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the pool with minimum connections."""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            logger.info(
                f"Initializing pool for {self.service_name} "
                f"with min={self.config.min_connections} connections"
            )
            
            # Create minimum connections
            for _ in range(self.config.min_connections):
                try:
                    conn = await self._create_connection()
                    if conn:
                        self.connections.append(conn)
                        await self.available.put(conn)
                except Exception as e:
                    logger.error(
                        f"Failed to create initial connection for "
                        f"{self.service_name}: {e}"
                    )
            
            # Start health check task
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )
            
            self._initialized = True
    
    async def acquire(self, timeout: Optional[float] = None) -> Connection:
        """Acquire a connection from the pool.
        
        Args:
            timeout: Maximum time to wait for a connection
            
        Returns:
            Available connection
            
        Raises:
            ConnectionError: If no connection can be acquired
        """
        if not self._initialized:
            await self.initialize()
        
        timeout = timeout or self.config.connection_timeout
        deadline = asyncio.get_event_loop().time() + timeout
        
        while asyncio.get_event_loop().time() < deadline:
            # Try to get an available connection
            try:
                remaining = deadline - asyncio.get_event_loop().time()
                conn = await asyncio.wait_for(
                    self.available.get(),
                    timeout=min(remaining, 0.1)
                )
                
                # Check if connection is healthy
                if await conn.is_healthy():
                    self.stats.total_requests += 1
                    self.stats.active_connections += 1
                    self.stats.idle_connections = self.available.qsize()
                    conn.info.last_used = datetime.now()
                    return conn
                else:
                    # Remove unhealthy connection
                    await self._remove_connection(conn)
                    
            except asyncio.TimeoutError:
                pass
            
            # Try to create a new connection if under limit
            if len(self.connections) < self.config.max_connections:
                try:
                    conn = await self._create_connection()
                    if conn:
                        self.connections.append(conn)
                        self.stats.total_requests += 1
                        self.stats.active_connections += 1
                        conn.info.last_used = datetime.now()
                        return conn
                except Exception as e:
                    logger.error(
                        f"Failed to create new connection for "
                        f"{self.service_name}: {e}"
                    )
        
        raise ConnectionError(
            f"Failed to acquire connection for {self.service_name} "
            f"within {timeout} seconds"
        )
    
    async def release(self, connection: Connection):
        """Return a connection to the pool.
        
        Args:
            connection: Connection to release
        """
        if connection not in self.connections:
            logger.warning(
                f"Attempted to release unknown connection for {self.service_name}"
            )
            return
        
        self.stats.active_connections -= 1
        
        # Check if connection is still healthy
        if await connection.is_healthy():
            await self.available.put(connection)
            self.stats.idle_connections = self.available.qsize()
        else:
            # Remove unhealthy connection
            await self._remove_connection(connection)
    
    async def close_all(self):
        """Close all connections and cleanup."""
        logger.info(f"Closing all connections for {self.service_name}")
        
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for conn in self.connections:
            try:
                await conn.disconnect()
            except Exception as e:
                logger.error(
                    f"Error closing connection for {self.service_name}: {e}"
                )
        
        self.connections.clear()
        # Clear the queue
        while not self.available.empty():
            try:
                self.available.get_nowait()
            except asyncio.QueueEmpty:
                break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "service": self.service_name,
            "stats": self.stats.to_dict(),
            "connections": len(self.connections),
            "healthy": sum(
                1 for c in self.connections
                if c.state == ConnectionState.CONNECTED
            )
        }
    
    async def _create_connection(self) -> Connection:
        """Create a new connection."""
        logger.debug(f"Creating new connection for {self.service_name}")
        
        for attempt in range(self.config.retry_attempts):
            try:
                conn = self.connection_factory(self.service_name)
                await conn.connect()
                
                self.stats.created_connections += 1
                logger.info(
                    f"Created connection for {self.service_name} "
                    f"(total: {len(self.connections) + 1})"
                )
                return conn
                
            except Exception as e:
                self.stats.failed_connections += 1
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(
                        f"Connection attempt {attempt + 1} failed for "
                        f"{self.service_name}: {e}. Retrying..."
                    )
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    logger.error(
                        f"Failed to create connection for {self.service_name} "
                        f"after {self.config.retry_attempts} attempts: {e}"
                    )
                    raise
    
    async def _remove_connection(self, connection: Connection):
        """Remove a connection from the pool."""
        logger.info(f"Removing connection for {self.service_name}")
        
        try:
            await connection.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting connection: {e}")
        
        if connection in self.connections:
            self.connections.remove(connection)
    
    async def _health_check_loop(self):
        """Background task to check connection health."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Check each idle connection
                idle_connections = []
                for _ in range(self.available.qsize()):
                    try:
                        conn = self.available.get_nowait()
                        idle_connections.append(conn)
                    except asyncio.QueueEmpty:
                        break
                
                # Test and re-queue healthy connections
                for conn in idle_connections:
                    if await conn.is_healthy():
                        await self.available.put(conn)
                    else:
                        logger.warning(
                            f"Removing unhealthy connection for {self.service_name}"
                        )
                        await self._remove_connection(conn)
                
                # Ensure minimum connections
                while len(self.connections) < self.config.min_connections:
                    try:
                        conn = await self._create_connection()
                        if conn:
                            self.connections.append(conn)
                            await self.available.put(conn)
                    except Exception as e:
                        logger.error(
                            f"Failed to maintain minimum connections for "
                            f"{self.service_name}: {e}"
                        )
                        break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {self.service_name}: {e}")


class ConnectionPool:
    """Global connection pool manager.
    
    AI_CONTEXT:
        This is the main connection pool that manages individual service pools.
        It provides a unified interface for acquiring connections to any service
        and handles credential injection from the AuthManager.
    """
    
    def __init__(self, config: Optional[PoolConfig] = None):
        """Initialize connection pool manager.
        
        Args:
            config: Default pool configuration
        """
        self.config = config or PoolConfig()
        self.pools: Dict[str, ServicePool] = {}
        self.connection_factories: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    def register_connection_factory(self, service_type: str, factory):
        """Register a connection factory for a service type.
        
        Args:
            service_type: Type of service ("mcp", "cli", "rest")
            factory: Factory function to create connections
        """
        self.connection_factories[service_type] = factory
    
    async def get_connection(
        self,
        service_name: str,
        credential: Optional[Credential] = None,
        service_type: str = "mcp"
    ) -> Connection:
        """Get a connection to a service.
        
        Args:
            service_name: Name of the service
            credential: Optional credential for authentication
            service_type: Type of service
            
        Returns:
            Connection to the service
        """
        # Ensure pool exists
        if service_name not in self.pools:
            await self._create_pool(service_name, service_type)
        
        # Get connection from pool
        pool = self.pools[service_name]
        conn = await pool.acquire()
        
        # Set credential if provided
        if credential:
            conn.credential = credential
        
        return conn
    
    async def return_connection(self, connection: Connection):
        """Return a connection to its pool.
        
        Args:
            connection: Connection to return
        """
        service_name = connection.service_name
        if service_name in self.pools:
            await self.pools[service_name].release(connection)
        else:
            logger.warning(
                f"No pool found for service {service_name}, "
                "closing connection"
            )
            await connection.disconnect()
    
    async def close_all(self):
        """Close all connection pools."""
        logger.info("Closing all connection pools")
        
        tasks = []
        for pool in self.pools.values():
            tasks.append(pool.close_all())
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self.pools.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all pools."""
        return {
            "pools": [
                pool.get_stats()
                for pool in self.pools.values()
            ]
        }
    
    async def _create_pool(
        self,
        service_name: str,
        service_type: str
    ):
        """Create a new service pool."""
        async with self._lock:
            if service_name in self.pools:
                return
            
            if service_type not in self.connection_factories:
                raise ValueError(
                    f"No connection factory registered for type: {service_type}"
                )
            
            logger.info(f"Creating connection pool for {service_name}")
            
            factory = self.connection_factories[service_type]
            pool = ServicePool(
                service_name=service_name,
                connection_factory=factory,
                config=self.config
            )
            
            self.pools[service_name] = pool