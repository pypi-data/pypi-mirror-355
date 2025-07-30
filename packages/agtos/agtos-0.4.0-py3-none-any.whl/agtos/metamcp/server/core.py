"""Core Meta-MCP Server implementation.

AI_CONTEXT:
    This module contains the core MetaMCPServer class responsible for:
    - Server initialization and configuration
    - Component setup (registry, router, auth, cache, etc.)
    - Service discovery and auto-discovery
    - Statistics tracking
    - Graceful shutdown handling
    
    Request handling logic is delegated to handlers.py
    Session management is in session.py
    Transport-specific code is in transport.py
    
    Navigation:
    - See handlers.py for request processing methods
    - See session.py for context persistence
    - See transport.py for HTTP/stdio implementations
"""

import asyncio
import logging
import signal
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI

from ..registry import ServiceRegistry
from ..router import Router
from ..auth import AuthManager
from ..proxy.pool import ConnectionPool
from ..cache import CacheManager
from ..types import ServerCapabilities
# Make hot reload import conditional
try:
    from ..hot_reload import get_hot_reloader
    HOT_RELOAD_AVAILABLE = True
except ImportError:
    get_hot_reloader = None
    HOT_RELOAD_AVAILABLE = False
from ...context import ContextManager
from ...workflows.recorder import WorkflowRecorder

logger = logging.getLogger(__name__)


class MetaMCPServer:
    """Core Meta-MCP server implementation.
    
    AI_CONTEXT:
        The server acts as a single MCP endpoint that aggregates multiple
        downstream services. This class handles initialization, component setup,
        and service discovery. Request handling is delegated to handler methods.
        
        Key components:
        - Registry: Manages service registrations
        - Router: Routes requests to appropriate services
        - AuthManager: Handles authentication
        - ConnectionPool: Manages connections to downstream services
        - CacheManager: Provides intelligent caching
        - ContextManager: Persists conversation context
        
        The server supports both HTTP and stdio transports.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Meta-MCP server.
        
        Args:
            config: Server configuration including:
                - host: Server host (default: "localhost")
                - port: Server port (default: 3000)
                - services: List of services to register
                - cache: Cache configuration
                - auth: Authentication configuration
                - project_name: Project name for context isolation
                - debug: Enable debug logging
                - log_requests: Log all requests/responses
        """
        # Store config and extract debug settings
        self.config = config or {}
        self.debug = self.config.get("debug", False)
        self.log_requests = self.config.get("log_requests", False)
        
        # Initialize all components
        self._initialize_core_components()
        self._initialize_server_app()
        self._initialize_runtime_stats()
        self._initialize_conversation_tracking()
        
        # Complete setup
        self._complete_initialization()
    
    def _initialize_core_components(self) -> None:
        """Initialize core server components."""
        # Initialize context manager with project name
        project_name = self.config.get("project_name", "meta-mcp")
        self.context_manager = ContextManager(project_name)
        
        # Core components
        self.registry = ServiceRegistry(debug=self.debug)
        self.router = Router(self.registry)
        self.auth_manager = AuthManager(context_manager=self.context_manager)
        self.connection_pool = ConnectionPool()
        self.cache = CacheManager()
        
        # Hot reloader for user tools (if available)
        if HOT_RELOAD_AVAILABLE:
            self.hot_reloader = get_hot_reloader(self.registry)
        else:
            self.hot_reloader = None
        
        # Workflow recorder (initialized on demand)
        self._workflow_recorder: Optional[WorkflowRecorder] = None
    
    def _initialize_server_app(self) -> None:
        """Initialize FastAPI application."""
        self.app = FastAPI(
            title="Meta-MCP Server",
            description="Unified MCP orchestration platform",
            version="0.1.0"
        )
    
    def _initialize_runtime_stats(self) -> None:
        """Initialize runtime statistics tracking."""
        self.stats = {
            "start_time": datetime.now(),
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def _initialize_conversation_tracking(self) -> None:
        """Initialize conversation state tracking."""
        self.current_conversation_id = None
        self.conversation_messages = []
        # Flag to track if services have been discovered
        self._services_discovered = False
    
    def _complete_initialization(self) -> None:
        """Complete server initialization with final setup steps."""
        # Import handler methods after initialization
        self._setup_handlers()
        
        # Setup routes after handlers are available
        self._setup_routes()
        
        # Restore previous session context if available
        self._restore_session_context()
        
        # Setup graceful shutdown
        self._setup_shutdown_handlers()
    
    def _setup_handlers(self):
        """Import and bind handler methods.
        
        AI_CONTEXT: This method imports handler methods from the handlers module
        and binds them to this instance. This allows us to keep the handler logic
        in a separate file while maintaining the same API.
        """
        from .handlers import HandlerMixin
        from .session import SessionMixin
        from .transport import TransportMixin
        
        # Bind all handler methods to this instance
        for mixin_cls in [HandlerMixin, SessionMixin, TransportMixin]:
            for attr_name in dir(mixin_cls):
                # Skip magic methods
                if attr_name.startswith('__'):
                    continue
                attr = getattr(mixin_cls, attr_name)
                if callable(attr):
                    # Bind the method to this instance
                    bound_method = attr.__get__(self, self.__class__)
                    setattr(self, attr_name, bound_method)
    
    def _setup_routes(self):
        """Configure FastAPI routes for MCP protocol.
        
        AI_CONTEXT: Routes are defined here but delegate to transport-specific
        handlers in transport.py. This keeps HTTP-specific code separate.
        """
        # Import route setup from transport module
        from .transport import setup_routes
        setup_routes(self)
    
    def _setup_shutdown_handlers(self) -> None:
        """Setup graceful shutdown handlers to save context.
        
        AI_CONTEXT: Registers signal handlers for SIGINT and SIGTERM to ensure
        context is saved when the server is stopped. This prevents data loss
        on unexpected shutdowns. Only sets up handlers if running in the main thread.
        """
        import threading
        
        # Only set up signal handlers if we're in the main thread
        # This prevents ValueError when running in background threads
        if threading.current_thread() is threading.main_thread():
            def handle_shutdown(signum, frame):
                logger.info(f"Received signal {signum}, saving context...")
                self._save_session_context()
                # Note: In async context, we might need asyncio handling here
                
            # Register signal handlers
            signal.signal(signal.SIGINT, handle_shutdown)
            signal.signal(signal.SIGTERM, handle_shutdown)
        else:
            logger.debug("Running in background thread, skipping signal handler setup")
    
    async def _discover_services(self):
        """Discover and register all configured services.
        
        AI_CONTEXT: This method loads services from configuration and
        auto-discovers plugins and CLI tools. It's called during initialization
        to set up all available services. It ensures services are only discovered
        once to prevent duplicate registrations.
        """
        # Check if services have already been discovered
        if self._services_discovered:
            if self.debug:
                logger.debug("Services already discovered, skipping...")
            return
        
        # Check if tools are disabled
        if self.config.get("no_tools", False):
            logger.info("Tool loading disabled (--no-tools flag)")
            self._services_discovered = True
            return
            
        if self.debug:
            logger.debug("Starting service discovery...")
        
        # Load from configuration
        services_config = self.config.get("services", [])
        
        for service_config in services_config:
            service_type = service_config["type"]
            service_name = service_config["name"]
            
            if service_type == "mcp":
                await self.registry.register_mcp_server(
                    service_name,
                    service_config
                )
            elif service_type == "cli":
                await self.registry.register_cli_tool(
                    service_name,
                    service_config
                )
            elif service_type == "rest":
                await self.registry.register_rest_api(
                    service_name,
                    service_config
                )
            else:
                logger.warning(f"Unknown service type: {service_type}")
        
        # Auto-discover agentctl plugins and CLI tools
        await self._auto_discover_plugins()
        await self._auto_discover_cli_tools()
        
        # Start hot-reload watcher for user tools (if available)
        if self.hot_reloader:
            await self.hot_reloader.start_watching()
        
        if self.debug:
            logger.debug(f"Registered {len(self.registry.services)} services")
        
        # Build routes from registry after all services are registered
        self.router.build_routes_from_registry()
        
        # Mark services as discovered to prevent duplicate registration
        self._services_discovered = True
        logger.info(f"Service discovery complete: {len(self.registry.services)} services registered")
    
    async def _aggregate_capabilities(self) -> Dict[str, Any]:
        """Aggregate capabilities from all services.
        
        AI_CONTEXT: Combines capabilities from all registered services
        to present a unified set of capabilities to the client.
        """
        # Start with base capabilities
        capabilities = ServerCapabilities(
            tools=False,
            resources=False,
            prompts=False,
            logging=False
        )
        
        # Aggregate from all services
        for service_name in self.registry.services:
            service_caps = await self.registry.get_service_capabilities(service_name)
            if service_caps:
                # Check if capabilities are enabled (can be True or {} in MCP spec)
                if service_caps.get("tools") is not None:
                    capabilities.tools = True
                if service_caps.get("resources") is not None:
                    capabilities.resources = True
                if service_caps.get("prompts") is not None:
                    capabilities.prompts = True
                if service_caps.get("logging") is not None:
                    capabilities.logging = True
        
        return capabilities.to_dict()
    
    async def _check_services_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered services."""
        health_status = {}
        
        for service_name in self.registry.services:
            try:
                status = await self.registry.check_service_health(service_name)
                health_status[service_name] = {
                    "healthy": status.healthy,
                    "status": status.status,
                    "last_check": status.last_check.isoformat(),
                    "response_time_ms": status.response_time_ms
                }
            except Exception as e:
                health_status[service_name] = {
                    "healthy": False,
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    async def _auto_discover_plugins(self):
        """Auto-discover and register agentctl plugins.
        
        AI_CONTEXT:
            This method discovers plugins in the agtos.plugins package
            and registers them as services. Each plugin can provide multiple
            tools that will be exposed through the Meta-MCP server.
        """
        logger.info("Auto-discovering agentctl plugins...")
        
        try:
            from ...plugins import get_all_tools
            
            # Get all plugin tools
            all_tools = get_all_tools()
            
            if all_tools:
                # Register as a single "agtos" plugin service that provides all tools
                await self.registry.register_plugin_service(
                    "agtos",
                    {
                        "description": "Built-in agentctl plugin tools",
                        "tools": all_tools
                    }
                )
                logger.info(f"Registered agentctl plugin service with {len(all_tools)} tools")
        except ImportError:
            logger.warning("Plugins not available - plugin tools disabled")
        except Exception as e:
            logger.error(f"Failed to auto-discover plugins: {e}")
    
    async def _auto_discover_cli_tools(self):
        """Auto-discover common CLI tools.
        
        AI_CONTEXT:
            This method looks for commonly available CLI tools like git,
            docker, kubectl, etc. and registers them automatically.
            Tools are only registered if they're available on the system.
        """
        # Try to import tool config
        try:
            from ...tool_config import get_tool_config
            tool_config = get_tool_config()
        except ImportError:
            tool_config = None
            
        logger.info("Auto-discovering CLI tools...")
        
        # List of common CLI tools to try
        common_tools = [
            {
                "name": "git",
                "binary": "git",
                "description": "Git version control system",
                "discover_subcommands": True
            },
            {
                "name": "docker",
                "binary": "docker",
                "description": "Docker container platform",
                "discover_subcommands": True
            },
            {
                "name": "kubectl",
                "binary": "kubectl",
                "description": "Kubernetes command-line tool",
                "discover_subcommands": True
            },
            {
                "name": "npm",
                "binary": "npm",
                "description": "Node.js package manager",
                "discover_subcommands": True
            },
            {
                "name": "python",
                "binary": "python3",
                "description": "Python interpreter",
                "discover_subcommands": False
            }
        ]
        
        for tool_info in common_tools:
            try:
                # Check if tool is disabled (if tool_config available)
                if tool_config:
                    tool_name = f"cli__{tool_info['name']}"
                    if tool_config.is_tool_disabled(tool_name):
                        logger.debug(f"Skipping disabled CLI tool: {tool_info['name']}")
                        continue
                
                # Check if tool is available
                import shutil
                if shutil.which(tool_info["binary"]):
                    await self.registry.register_cli_tool(
                        tool_info["name"],
                        tool_info
                    )
                    logger.info(f"Auto-registered CLI tool: {tool_info['name']}")
            except Exception as e:
                logger.debug(f"Could not register {tool_info['name']}: {e}")
    
    def _get_debug_context(self) -> Dict[str, Any]:
        """Get debug context for error messages.
        
        Returns:
            Dictionary with helpful debug information
        """
        return {
            "available_services": list(self.registry.services.keys()),
            "total_tools": sum(len(s.tools) for s in self.registry.services.values()),
            "cache_stats": {
                "hits": self.stats.get("cache_hits", 0),
                "misses": self.stats.get("cache_misses", 0)
            },
            "uptime_seconds": int((datetime.now() - self.stats["start_time"]).total_seconds())
        }
    
    async def start(self, host: str = "localhost", port: int = 3000):
        """Start the Meta-MCP server in HTTP mode.
        
        AI_CONTEXT: This method starts the server using uvicorn for HTTP transport.
        For stdio transport, use start_stdio() instead.
        """
        import uvicorn
        
        logger.info(f"Starting Meta-MCP server on {host}:{port}")
        await uvicorn.Server(
            uvicorn.Config(
                self.app,
                host=host,
                port=port,
                log_level="info"
            )
        ).serve()
    
    async def stop(self):
        """Stop the Meta-MCP server and cleanup resources."""
        logger.info("Stopping Meta-MCP server")
        
        # Save current conversation context
        self._save_session_context()
        
        # Stop hot-reload watcher (if available)
        if self.hot_reloader:
            self.hot_reloader.stop_watching()
        
        # Close all connections
        await self.connection_pool.close_all()
        
        # Flush cache
        await self.cache.flush()
        
        logger.info("Meta-MCP server stopped")