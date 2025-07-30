"""
Health monitoring for MCP proxy connections.

This module provides health checking and automatic recovery capabilities
for downstream MCP server connections.

AI_CONTEXT:
    Implements a sophisticated health monitoring system that:
    - Periodically checks server connectivity and responsiveness
    - Implements circuit breaker pattern to prevent cascading failures
    - Manages automatic reconnection with exponential backoff
    - Provides health metrics for monitoring and alerting
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from agtos.utils import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status of a monitored connection."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class HealthMetrics:
    """
    Health metrics for a server connection.
    
    AI_CONTEXT:
        Tracks various health indicators that help determine when to
        mark a server as unhealthy and trigger recovery procedures.
    """
    last_check_time: float = 0
    last_success_time: float = 0
    consecutive_failures: int = 0
    total_checks: int = 0
    total_failures: int = 0
    average_response_time: float = 0
    response_times: List[float] = field(default_factory=list)
    
    def add_response_time(self, response_time: float):
        """Add a response time measurement."""
        self.response_times.append(response_time)
        # Keep only last 100 measurements
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        self.average_response_time = sum(self.response_times) / len(self.response_times)
    
    def record_success(self, response_time: float):
        """Record a successful health check."""
        self.last_success_time = time.time()
        self.consecutive_failures = 0
        self.total_checks += 1
        self.add_response_time(response_time)
    
    def record_failure(self):
        """Record a failed health check."""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.total_checks += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_checks == 0:
            return 0.0
        return ((self.total_checks - self.total_failures) / self.total_checks) * 100
    
    @property
    def time_since_last_success(self) -> float:
        """Time in seconds since last successful check."""
        if self.last_success_time == 0:
            return float('inf')
        return time.time() - self.last_success_time


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for connection failure management.
    
    AI_CONTEXT:
        Implements the circuit breaker pattern to prevent repeated
        attempts to use a failing connection. This protects both
        the client and server from cascading failures.
    """
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_requests: int = 3
    
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    last_failure_time: float = 0
    half_open_successes: int = 0
    
    def record_success(self):
        """Record a successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self.close()
        elif self.state == CircuitState.CLOSED:
            self.failures = 0
    
    def record_failure(self):
        """Record a failed operation."""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            if self.failures >= self.failure_threshold:
                self.trip()
        elif self.state == CircuitState.HALF_OPEN:
            self.trip()
    
    def trip(self):
        """Trip the circuit breaker to OPEN state."""
        self.state = CircuitState.OPEN
        logger.warning(f"Circuit breaker tripped after {self.failures} failures")
    
    def close(self):
        """Close the circuit breaker (normal operation)."""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.half_open_successes = 0
        logger.info("Circuit breaker closed, resuming normal operation")
    
    def attempt_reset(self):
        """Attempt to reset the circuit breaker to HALF_OPEN."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_successes = 0
                logger.info("Circuit breaker entering half-open state")
    
    @property
    def is_available(self) -> bool:
        """Check if requests should be allowed."""
        self.attempt_reset()  # Check if we should transition to HALF_OPEN
        return self.state != CircuitState.OPEN


class HealthMonitor:
    """
    Monitors health of MCP server connections.
    
    AI_CONTEXT:
        Central health monitoring system that tracks multiple server
        connections, performs periodic health checks, and manages
        automatic recovery. Integrates with the forwarder to enable/disable
        servers based on their health status.
    """
    
    def __init__(
        self,
        check_interval: float = 30.0,
        timeout: float = 10.0,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0
    ):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Seconds between health checks
            timeout: Timeout for health check operations
            failure_threshold: Failures before marking unhealthy
            recovery_timeout: Seconds before retrying failed server
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.servers: Dict[str, Any] = {}  # server_id -> server_info
        self.metrics: Dict[str, HealthMetrics] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_check_handlers: Dict[str, Callable] = {}
        
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._status_callbacks: List[Callable] = []
    
    def register_server(
        self,
        server_id: str,
        server_info: Any,
        health_check_handler: Callable
    ):
        """
        Register a server for health monitoring.
        
        Args:
            server_id: Unique server identifier
            server_info: Server configuration/state object
            health_check_handler: Async function to check server health
        """
        self.servers[server_id] = server_info
        self.metrics[server_id] = HealthMetrics()
        self.circuit_breakers[server_id] = CircuitBreaker(
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout
        )
        self.health_check_handlers[server_id] = health_check_handler
        
        logger.info(f"Registered server {server_id} for health monitoring")
    
    def unregister_server(self, server_id: str):
        """Remove a server from health monitoring."""
        self.servers.pop(server_id, None)
        self.metrics.pop(server_id, None)
        self.circuit_breakers.pop(server_id, None)
        self.health_check_handlers.pop(server_id, None)
        
        logger.info(f"Unregistered server {server_id} from health monitoring")
    
    def add_status_callback(self, callback: Callable):
        """Add a callback to be notified of status changes."""
        self._status_callbacks.append(callback)
    
    async def start(self):
        """Start health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started")
    
    async def stop(self):
        """Stop health monitoring."""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Check all servers
                await self._check_all_servers()
                
                # Wait for next check interval
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _check_all_servers(self):
        """Perform health checks on all registered servers."""
        tasks = []
        
        for server_id in list(self.servers.keys()):
            circuit_breaker = self.circuit_breakers.get(server_id)
            
            # Skip if circuit breaker is open
            if circuit_breaker and not circuit_breaker.is_available:
                continue
            
            task = asyncio.create_task(self._check_server(server_id))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_server(self, server_id: str):
        """
        Perform health check on a single server.
        
        AI_CONTEXT:
            Executes the registered health check handler and updates
            metrics and circuit breaker state based on the result.
        """
        metrics = self.metrics.get(server_id)
        circuit_breaker = self.circuit_breakers.get(server_id)
        handler = self.health_check_handlers.get(server_id)
        
        if not all([metrics, circuit_breaker, handler]):
            return
        
        metrics.last_check_time = time.time()
        start_time = time.time()
        
        try:
            # Execute health check with timeout
            await asyncio.wait_for(handler(), timeout=self.timeout)
            
            # Record success
            response_time = time.time() - start_time
            metrics.record_success(response_time)
            circuit_breaker.record_success()
            
            # Update status if changed
            await self._update_server_status(server_id, HealthStatus.HEALTHY)
            
            logger.debug(f"Health check succeeded for {server_id} in {response_time:.2f}s")
            
        except asyncio.TimeoutError:
            logger.warning(f"Health check timed out for {server_id}")
            metrics.record_failure()
            circuit_breaker.record_failure()
            await self._update_server_status(server_id, HealthStatus.UNHEALTHY)
            
        except Exception as e:
            logger.error(f"Health check failed for {server_id}: {e}")
            metrics.record_failure()
            circuit_breaker.record_failure()
            await self._update_server_status(server_id, HealthStatus.UNHEALTHY)
    
    async def _update_server_status(self, server_id: str, status: HealthStatus):
        """Update server status and notify callbacks."""
        # Notify callbacks of status change
        for callback in self._status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(server_id, status)
                else:
                    callback(server_id, status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def get_server_status(self, server_id: str) -> HealthStatus:
        """
        Get current health status of a server.
        
        AI_CONTEXT:
            Determines health status based on metrics and circuit breaker state.
            Uses multiple factors including consecutive failures, response times,
            and time since last success.
        """
        metrics = self.metrics.get(server_id)
        circuit_breaker = self.circuit_breakers.get(server_id)
        
        if not metrics:
            return HealthStatus.UNKNOWN
        
        # Check circuit breaker first
        if circuit_breaker and circuit_breaker.state == CircuitState.OPEN:
            return HealthStatus.UNHEALTHY
        
        # Check consecutive failures
        if metrics.consecutive_failures >= self.failure_threshold:
            return HealthStatus.UNHEALTHY
        
        # Check time since last success
        if metrics.time_since_last_success > self.recovery_timeout * 2:
            return HealthStatus.UNHEALTHY
        
        # Check if degraded
        if metrics.consecutive_failures > 0 or metrics.success_rate < 95:
            return HealthStatus.DEGRADED
        
        # Check response times (degraded if slow)
        if metrics.average_response_time > self.timeout * 0.8:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all monitored servers."""
        statuses = {}
        
        for server_id in self.servers:
            metrics = self.metrics.get(server_id, HealthMetrics())
            circuit_breaker = self.circuit_breakers.get(server_id)
            
            statuses[server_id] = {
                "status": self.get_server_status(server_id).value,
                "last_check": datetime.fromtimestamp(metrics.last_check_time).isoformat() if metrics.last_check_time else None,
                "consecutive_failures": metrics.consecutive_failures,
                "success_rate": f"{metrics.success_rate:.1f}%",
                "average_response_time": f"{metrics.average_response_time:.3f}s",
                "circuit_breaker": circuit_breaker.state.value if circuit_breaker else None
            }
        
        return statuses
    
    async def force_check(self, server_id: str) -> HealthStatus:
        """Force an immediate health check for a specific server."""
        if server_id not in self.servers:
            raise ValueError(f"Unknown server: {server_id}")
        
        await self._check_server(server_id)
        return self.get_server_status(server_id)