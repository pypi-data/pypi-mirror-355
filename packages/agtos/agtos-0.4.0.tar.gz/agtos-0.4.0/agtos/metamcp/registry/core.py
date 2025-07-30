"""Core Service Registry implementation.

AI_CONTEXT:
    This module contains the core ServiceRegistry class and data models.
    It manages service registration, configuration, and high-level operations.
    Detailed implementation for discovery, health, connections, and execution
    are delegated to other modules in this package.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ...knowledge.acquisition import KnowledgeAcquisition
from ..types import ToolSpec, ServerCapabilities, ServiceHealth

# Make bridge imports conditional
try:
    from ..bridge.cli import CLIBridge
    BRIDGE_AVAILABLE = True
except ImportError:
    CLIBridge = None
    BRIDGE_AVAILABLE = False
    
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ServiceType(Enum):
    """Types of services that can be registered."""
    MCP = "mcp"          # Native MCP servers
    CLI = "cli"          # Command-line tools
    REST = "rest"        # REST APIs
    PLUGIN = "plugin"    # agentctl plugins


class ServiceStatus(Enum):
    """Status of a registered service."""
    PENDING = "pending"      # Not yet connected
    CONNECTING = "connecting"  # Connection in progress
    ERROR = "error"         # Connection failed
    READY = "ready"         # Connected and ready
    DISABLED = "disabled"   # Manually disabled


@dataclass
class ServiceConfig:
    """Configuration for a registered service."""
    name: str
    type: ServiceType
    enabled: bool = True
    
    # Connection details
    url: Optional[str] = None          # For MCP/REST
    command: Optional[List[str]] = None  # For MCP stdio
    binary: Optional[str] = None       # For CLI tools
    
    # Authentication
    auth_type: Optional[str] = None    # oauth2, api_key, basic, etc.
    auth_provider: Optional[str] = None  # keychain, 1password, env
    auth_config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    description: Optional[str] = None
    namespace: Optional[str] = None    # Tool name prefix
    tags: List[str] = field(default_factory=list)


@dataclass
class ServiceInfo:
    """Runtime information about a registered service."""
    config: ServiceConfig
    status: ServiceStatus = ServiceStatus.PENDING
    tools: List[ToolSpec] = field(default_factory=list)
    capabilities: Optional[ServerCapabilities] = None
    health: Optional[ServiceHealth] = None
    last_error: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.now)
    last_connected: Optional[datetime] = None


# ============================================================================
# Core Registry Class
# ============================================================================

class ServiceRegistry:
    """Central registry for all Meta-MCP services.
    
    AI_CONTEXT:
        The registry is the source of truth for all services available to
        the Meta-MCP server. It delegates complex operations to specialized
        modules:
        - discovery: Tool discovery for each service type
        - connection: MCP server connection management
        - health: Service health monitoring
        - execution: Tool execution across service types
    """
    
    def __init__(self, debug: bool = False):
        """Initialize the service registry.
        
        Args:
            debug: Enable debug mode for detailed error messages
        """
        self.services: Dict[str, ServiceInfo] = {}
        self.knowledge = KnowledgeAcquisition()
        
        # Only create CLI bridge if available
        if BRIDGE_AVAILABLE:
            self.cli_bridge = CLIBridge()
        else:
            self.cli_bridge = None
            logger.warning("CLI Bridge not available - CLI tools disabled")
            
        self._health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._connections: Dict[str, Any] = {}  # MCP server connections
        self.debug = debug
        self._plugin_tools: Dict[str, Dict[str, Any]] = {}  # Plugin tool storage
        
        # Initialize helper modules lazily
        self._discovery = None
        self._connection = None
        self._health = None
        self._execution = None
    
    # ========================================================================
    # Service Registration Methods
    # ========================================================================
    
    async def register_mcp_server(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> ServiceInfo:
        """Register a downstream MCP server.
        
        Args:
            name: Unique name for the service
            config: Service configuration including:
                - url: HTTP/WebSocket URL (optional)
                - command: Command to start stdio server (optional)
                - auth_type: Authentication method
                - namespace: Tool name prefix
        
        Returns:
            ServiceInfo object for the registered service
        """
        logger.info(f"Registering MCP server: {name}")
        
        service_config = ServiceConfig(
            name=name,
            type=ServiceType.MCP,
            url=config.get("url"),
            command=config.get("command"),
            auth_type=config.get("auth_type"),
            auth_provider=config.get("auth_provider", "env"),
            auth_config=config.get("auth_config", {}),
            namespace=config.get("namespace", name),
            description=config.get("description")
        )
        
        service_info = ServiceInfo(config=service_config)
        self.services[name] = service_info
        
        # Start connection process asynchronously
        from .connection import ConnectionManager
        if not self._connection:
            self._connection = ConnectionManager(self)
        
        asyncio.create_task(self._connection.connect_mcp_server(name))
        
        return service_info
    
    async def register_cli_tool(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> ServiceInfo:
        """Register a CLI tool for MCP bridging.
        
        Args:
            name: Unique name for the service
            config: Service configuration including:
                - binary: CLI binary name or path
                - knowledge_key: Key in knowledge base
                - namespace: Tool name prefix
        
        Returns:
            ServiceInfo object for the registered service
        """
        logger.info(f"Registering CLI tool: {name}")
        
        service_config = ServiceConfig(
            name=name,
            type=ServiceType.CLI,
            binary=config.get("binary", name),
            namespace=config.get("namespace", name),
            description=config.get("description")
        )
        
        service_info = ServiceInfo(config=service_config)
        
        # Discover CLI capabilities from knowledge base
        try:
            from .discovery import DiscoveryManager
            if not self._discovery:
                self._discovery = DiscoveryManager(self)
            
            tools = await self._discovery.discover_cli_tools(service_config)
            service_info.tools = tools
            service_info.status = ServiceStatus.READY
            service_info.capabilities = ServerCapabilities(
                tools=len(tools) > 0
            )
        except Exception as e:
            logger.error(f"Failed to discover CLI tools for {name}: {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.last_error = str(e)
        
        self.services[name] = service_info
        return service_info
    
    async def register_rest_api(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> ServiceInfo:
        """Register a REST API for MCP bridging.
        
        Args:
            name: Unique name for the service
            config: Service configuration including:
                - base_url: API base URL
                - openapi_url: OpenAPI spec URL (optional)
                - auth_type: Authentication method
                - namespace: Tool name prefix
        
        Returns:
            ServiceInfo object for the registered service
        """
        logger.info(f"Registering REST API: {name}")
        
        service_config = ServiceConfig(
            name=name,
            type=ServiceType.REST,
            url=config.get("base_url"),
            auth_type=config.get("auth_type"),
            auth_provider=config.get("auth_provider", "env"),
            auth_config=config.get("auth_config", {}),
            namespace=config.get("namespace", name),
            description=config.get("description")
        )
        
        service_info = ServiceInfo(config=service_config)
        
        # Discover REST API capabilities
        try:
            from .discovery import DiscoveryManager
            if not self._discovery:
                self._discovery = DiscoveryManager(self)
                
            tools = await self._discovery.discover_rest_tools(
                service_config,
                config.get("openapi_url")
            )
            service_info.tools = tools
            service_info.status = ServiceStatus.READY
            service_info.capabilities = ServerCapabilities(
                tools=len(tools) > 0
            )
        except Exception as e:
            logger.error(f"Failed to discover REST tools for {name}: {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.last_error = str(e)
        
        self.services[name] = service_info
        return service_info
    
    async def register_plugin(
        self,
        name: str,
        plugin_instance: Any
    ) -> ServiceInfo:
        """Register an agentctl plugin as a service.
        
        Args:
            name: Unique name for the service
            plugin_instance: Instance of the plugin
        
        Returns:
            ServiceInfo object for the registered service
        """
        logger.info(f"Registering plugin: {name}")
        
        service_config = ServiceConfig(
            name=name,
            type=ServiceType.PLUGIN,
            namespace=name,
            description=f"agtos plugin: {name}"
        )
        
        service_info = ServiceInfo(config=service_config)
        
        # Extract tools from plugin
        try:
            from .discovery import DiscoveryManager
            if not self._discovery:
                self._discovery = DiscoveryManager(self)
                
            tools = self._discovery.extract_plugin_tools(plugin_instance)
            service_info.tools = tools
            service_info.status = ServiceStatus.READY
            service_info.capabilities = ServerCapabilities(
                tools=len(tools) > 0
            )
        except Exception as e:
            logger.error(f"Failed to extract plugin tools for {name}: {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.last_error = str(e)
        
        self.services[name] = service_info
        return service_info
    
    async def register_plugin_service(
        self,
        name: str,
        config: Dict[str, Any]
    ) -> ServiceInfo:
        """Register a plugin service with pre-discovered tools.
        
        Args:
            name: Unique name for the service
            config: Service configuration including:
                - description: Service description
                - tools: Dictionary of tool_name -> tool_data
        
        Returns:
            ServiceInfo object for the registered service
        """
        logger.info(f"Registering plugin service: {name}")
        
        service_config = ServiceConfig(
            name=name,
            type=ServiceType.PLUGIN,
            namespace=name,
            description=config.get("description", f"Plugin service: {name}")
        )
        
        service_info = ServiceInfo(config=service_config)
        
        # Convert tools dictionary to ToolSpec objects
        tools_dict = config.get("tools", {})
        tools = []
        
        for tool_name, tool_data in tools_dict.items():
            # Create ToolSpec from plugin tool data
            tool_spec = ToolSpec(
                name=tool_name,
                description=tool_data.get("description", ""),
                inputSchema=tool_data.get("schema", {})
            )
            tools.append(tool_spec)
        
        service_info.tools = tools
        service_info.status = ServiceStatus.READY
        service_info.capabilities = ServerCapabilities(
            tools=len(tools) > 0
        )
        
        # Store the actual tool functions for execution
        self._plugin_tools[name] = tools_dict
        
        self.services[name] = service_info
        return service_info
    
    async def unregister_service(self, name: str):
        """Unregister a service."""
        if name in self.services:
            logger.info(f"Unregistering service: {name}")
            
            # Disconnect if it's an MCP server
            if self._connections and name in self._connections:
                try:
                    await self._connections[name].disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting from {name}: {e}")
                del self._connections[name]
            
            del self.services[name]
    
    # ========================================================================
    # Service Query Methods
    # ========================================================================
    
    async def get_service_tools(self, service_name: str) -> List[Dict[str, Any]]:
        """Get all tools from a specific service."""
        if service_name not in self.services:
            return []
        
        service = self.services[service_name]
        
        # Convert ToolSpec objects to dicts, ensuring only standard MCP fields
        tools = []
        for tool in service.tools:
            if hasattr(tool, "to_dict"):
                # Use the ToolSpec's to_dict method which filters fields
                tool_dict = tool.to_dict()
            else:
                # It's a dict - filter to only standard MCP fields
                tool_dict = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {})
                }
            tools.append(tool_dict)
        
        return tools
    
    async def get_service_capabilities(
        self,
        service_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get capabilities of a specific service."""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        if service.capabilities:
            return service.capabilities.to_dict()
        
        # Default capabilities based on service type
        if service.config.type == ServiceType.CLI:
            return {"tools": True}
        elif service.config.type == ServiceType.REST:
            return {"tools": True}
        elif service.config.type == ServiceType.PLUGIN:
            return {"tools": True}
        
        return None
    
    # ========================================================================
    # Health Monitoring
    # ========================================================================
    
    async def check_service_health(
        self,
        service_name: str
    ) -> ServiceHealth:
        """Check health of a specific service.
        
        AI_CONTEXT:
            Delegates to the health module which implements
            service-specific health check strategies.
        """
        from .health import HealthMonitor
        if not self._health:
            self._health = HealthMonitor(self)
        
        return await self._health.check_service_health(service_name)
    
    async def start_health_monitoring(self):
        """Start background health monitoring for all services."""
        from .health import HealthMonitor
        if not self._health:
            self._health = HealthMonitor(self)
        
        await self._health.start_monitoring()
    
    async def stop_health_monitoring(self):
        """Stop background health monitoring."""
        if self._health:
            await self._health.stop_monitoring()
    
    # ========================================================================
    # Tool Execution
    # ========================================================================
    
    async def execute_tool(
        self,
        service_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on a specific service.
        
        AI_CONTEXT:
            Delegates to the execution module which handles
            service-specific execution strategies.
        
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
        from .execution import ExecutionManager
        if not self._execution:
            self._execution = ExecutionManager(self)
        
        return await self._execution.execute_tool(
            service_name,
            tool_name,
            arguments
        )