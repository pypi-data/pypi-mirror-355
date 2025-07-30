"""Health monitoring for registered services.

AI_CONTEXT:
    This module implements health checking strategies for different
    service types. It monitors:
    - MCP server connectivity and response times
    - CLI tool availability
    - REST API reachability
    - Plugin status
    
    Health checks can be run on-demand or continuously in the background.
"""

import asyncio
import aiohttp
import subprocess
import logging
from typing import Dict, Optional
from datetime import datetime

from ..types import ServiceHealth
from .core import ServiceInfo, ServiceStatus, ServiceType

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors health of all registered services.
    
    AI_CONTEXT:
        This class implements service-specific health check strategies
        and manages background health monitoring tasks. Each service type
        has its own health check implementation.
    """
    
    def __init__(self, registry):
        """Initialize health monitor with registry reference."""
        self.registry = registry
        self._health_check_task: Optional[asyncio.Task] = None
    
    # ========================================================================
    # Public Health Check Interface
    # ========================================================================
    
    async def check_service_health(
        self,
        service_name: str
    ) -> ServiceHealth:
        """Check health of a specific service.
        
        AI_CONTEXT:
            Dispatches to the appropriate health check method based on
            service type. Returns standardized health information.
        """
        if service_name not in self.registry.services:
            return ServiceHealth(
                service=service_name,
                healthy=False,
                status="not_found"
            )
        
        service = self.registry.services[service_name]
        
        # Different health check strategies by type
        if service.config.type == ServiceType.MCP:
            return await self._check_mcp_health(service)
        elif service.config.type == ServiceType.CLI:
            return await self._check_cli_health(service)
        elif service.config.type == ServiceType.REST:
            return await self._check_rest_health(service)
        elif service.config.type == ServiceType.PLUGIN:
            # Plugins are always healthy if loaded
            return ServiceHealth(
                service=service_name,
                healthy=service.status == ServiceStatus.READY,
                status=service.status.value,
                last_check=datetime.now()
            )
        
        return ServiceHealth(
            service=service_name,
            healthy=False,
            status="unknown_type"
        )
    
    # ========================================================================
    # Background Monitoring
    # ========================================================================
    
    async def start_monitoring(self):
        """Start background health monitoring for all services."""
        if self._health_check_task:
            return
        
        self._health_check_task = asyncio.create_task(
            self._health_monitor_loop()
        )
    
    async def stop_monitoring(self):
        """Stop background health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
    
    async def _health_monitor_loop(self):
        """Background task to monitor service health.
        
        AI_CONTEXT:
            Runs periodic health checks on all services and updates
            their health status in the registry.
        """
        while True:
            try:
                for service_name in list(self.registry.services.keys()):
                    try:
                        health = await self.check_service_health(service_name)
                        self.registry.services[service_name].health = health
                    except Exception as e:
                        logger.error(
                            f"Health check failed for {service_name}: {e}"
                        )
                
                await asyncio.sleep(self.registry._health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)  # Brief pause on error
    
    # ========================================================================
    # Service-Specific Health Checks
    # ========================================================================
    
    async def _check_mcp_health(self, service: ServiceInfo) -> ServiceHealth:
        """Check health of an MCP server.
        
        AI_CONTEXT:
            Sends a lightweight tools/list request to verify the server
            is responsive. Measures response time for monitoring.
        """
        start_time = datetime.now()
        
        try:
            # Check if we have a connection
            if not hasattr(self.registry, "_connections") or service.config.name not in self.registry._connections:
                return ServiceHealth(
                    service=service.config.name,
                    healthy=False,
                    status="disconnected",
                    last_check=datetime.now(),
                    error="No active connection"
                )
            
            connection = self.registry._connections[service.config.name]
            
            # Send a simple health check request (tools/list is lightweight)
            health_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": f"health-{service.config.name}-{start_time.timestamp()}"
            }
            
            # Use a shorter timeout for health checks
            response = await asyncio.wait_for(
                connection.send_request(health_request),
                timeout=5.0
            )
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response and "result" in response:
                return ServiceHealth(
                    service=service.config.name,
                    healthy=True,
                    status="healthy",
                    last_check=datetime.now(),
                    response_time_ms=int(response_time)
                )
            else:
                error_msg = response.get("error", {}).get("message", "Invalid response") if response else "No response"
                return ServiceHealth(
                    service=service.config.name,
                    healthy=False,
                    status="unhealthy",
                    last_check=datetime.now(),
                    response_time_ms=int(response_time),
                    error=error_msg
                )
                
        except asyncio.TimeoutError:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="timeout",
                last_check=datetime.now(),
                error="Health check timed out"
            )
        except Exception as e:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="error",
                last_check=datetime.now(),
                error=str(e)
            )
    
    async def _check_cli_health(self, service: ServiceInfo) -> ServiceHealth:
        """Check health of a CLI tool.
        
        AI_CONTEXT:
            Verifies the CLI binary exists and is executable by running
            a simple version command.
        """
        try:
            # Check if binary exists and is executable
            start_time = datetime.now()
            result = subprocess.run(
                [service.config.binary, "--version"],
                capture_output=True,
                timeout=5
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ServiceHealth(
                service=service.config.name,
                healthy=result.returncode == 0,
                status="healthy" if result.returncode == 0 else "unhealthy",
                last_check=datetime.now(),
                response_time_ms=int(response_time)
            )
        except subprocess.TimeoutExpired:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="timeout",
                last_check=datetime.now(),
                error="Version check timed out"
            )
        except FileNotFoundError:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="not_found",
                last_check=datetime.now(),
                error=f"Binary '{service.config.binary}' not found"
            )
        except Exception as e:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="error",
                last_check=datetime.now(),
                error=str(e)
            )
    
    async def _check_rest_health(self, service: ServiceInfo) -> ServiceHealth:
        """Check health of a REST API.
        
        AI_CONTEXT: This method performs a simple HTTP health check on the
        REST API. It tries to:
        
        1. Make a HEAD request to the base URL (lightweight)
        2. Fall back to GET if HEAD is not supported
        3. Accept any 2xx or 3xx status as healthy
        4. Measure response time for monitoring
        
        This is a basic health check that verifies the API is reachable.
        More sophisticated checks could use dedicated health endpoints.
        """
        start_time = datetime.now()
        
        try:
            # Get base URL from service config
            base_url = service.config.url
            if not base_url:
                return ServiceHealth(
                    service=service.config.name,
                    healthy=False,
                    status="no_url",
                    last_check=datetime.now(),
                    error="No base URL configured"
                )
            
            # Create timeout for health check
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try HEAD request first (lightweight)
                try:
                    async with session.head(base_url) as response:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        # Any 2xx or 3xx status is considered healthy
                        healthy = 200 <= response.status < 400
                        
                        return ServiceHealth(
                            service=service.config.name,
                            healthy=healthy,
                            status="healthy" if healthy else "unhealthy",
                            last_check=datetime.now(),
                            response_time_ms=int(response_time),
                            metadata={
                                "status_code": response.status,
                                "method": "HEAD"
                            }
                        )
                except aiohttp.ClientError:
                    # HEAD might not be supported, try GET
                    async with session.get(base_url) as response:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        # Any 2xx or 3xx status is considered healthy
                        healthy = 200 <= response.status < 400
                        
                        return ServiceHealth(
                            service=service.config.name,
                            healthy=healthy,
                            status="healthy" if healthy else "unhealthy",
                            last_check=datetime.now(),
                            response_time_ms=int(response_time),
                            metadata={
                                "status_code": response.status,
                                "method": "GET"
                            }
                        )
                        
        except asyncio.TimeoutError:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="timeout",
                last_check=datetime.now(),
                error="Health check timed out after 10 seconds"
            )
        except aiohttp.ClientError as e:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="connection_error",
                last_check=datetime.now(),
                error=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return ServiceHealth(
                service=service.config.name,
                healthy=False,
                status="error",
                last_check=datetime.now(),
                error=f"Unexpected error: {str(e)}"
            )