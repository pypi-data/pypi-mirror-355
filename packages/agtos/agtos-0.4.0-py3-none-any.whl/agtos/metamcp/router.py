"""Request routing engine for Meta-MCP Server.

AI_CONTEXT:
    This module implements intelligent routing of MCP requests to appropriate
    downstream services. It handles:
    - Tool name to service mapping
    - Namespace-based routing (e.g., github_* -> github service)
    - Pattern-based routing rules
    - Load balancing for replicated services
    - Fallback and error handling
"""

import re
import logging
from typing import Dict, List, Optional, Pattern, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .registry import ServiceRegistry, ServiceStatus
from .fuzzy_match import fuzzy_match_tools, format_suggestions, find_similar_aliases
from .aliases import get_registry as get_alias_registry, find_tool_for_alias
from .categories import CategoryManager

logger = logging.getLogger(__name__)


@dataclass
class RoutingRule:
    """A routing rule for pattern-based routing."""
    pattern: Pattern[str]
    service_name: str
    priority: int = 0
    description: Optional[str] = None
    
    def matches(self, tool_name: str) -> bool:
        """Check if this rule matches a tool name."""
        return bool(self.pattern.match(tool_name))


@dataclass
class RouteDecision:
    """Result of a routing decision."""
    tool_name: str
    service_name: str
    original_tool_name: str  # Tool name without namespace
    routing_method: str  # "direct", "namespace", "pattern", "default"
    confidence: float  # 0.0 to 1.0
    

class Router:
    """Intelligent request router for Meta-MCP.
    
    AI_CONTEXT:
        The router determines which downstream service should handle
        each incoming tool request. It uses multiple strategies:
        
        1. Direct mapping: Exact tool_name -> service mapping
        2. Namespace routing: Extract namespace prefix (e.g., "github_")
        3. Pattern rules: Regex-based routing for flexibility
        4. Service capabilities: Route based on what services can do
        5. Load balancing: Distribute load across equivalent services
        
        The router maintains a cache of routing decisions and tracks
        performance metrics for optimization.
    """
    
    def __init__(self, registry: ServiceRegistry):
        """Initialize router with service registry.
        
        Args:
            registry: Service registry containing all available services
        """
        self.registry = registry
        
        # Routing tables
        self.direct_routes: Dict[str, str] = {}  # tool -> service
        self.namespace_routes: Dict[str, str] = {}  # namespace -> service
        self.pattern_rules: List[RoutingRule] = []
        self.alias_routes: Dict[str, str] = {}  # alias -> actual tool name
        
        # Performance tracking
        self.route_cache: Dict[str, RouteDecision] = {}
        self.route_stats: Dict[str, Dict[str, int]] = {}  # service -> {success, error}
        
        # Configuration
        self.enable_cache = True
        self.cache_ttl = 300  # 5 minutes
        self.default_service: Optional[str] = None
        
        # Category manager for tool organization
        self.category_manager = CategoryManager()
        
    def route_tool(self, tool_name: str) -> str:
        """Route a tool to the appropriate service.
        
        Args:
            tool_name: Name of the tool to route
            
        Returns:
            Name of the service that should handle this tool
            
        Raises:
            RoutingError: If no service can handle the tool
        """
        # Check cache first
        if self.enable_cache and tool_name in self.route_cache:
            decision = self.route_cache[tool_name]
            logger.debug(
                f"Cache hit: {tool_name} -> {decision.service_name}"
            )
            return decision.service_name
        
        # Make routing decision
        decision = self._make_routing_decision(tool_name)
        
        # Cache the decision
        if self.enable_cache:
            self.route_cache[tool_name] = decision
        
        # Track statistics
        self._track_route(decision.service_name)
        
        logger.info(
            f"Routed {tool_name} to {decision.service_name} "
            f"(method: {decision.routing_method}, confidence: {decision.confidence})"
        )
        
        return decision.service_name
    
    def add_direct_route(self, tool_name: str, service_name: str):
        """Add a direct tool -> service mapping.
        
        Args:
            tool_name: Name of the tool
            service_name: Name of the service to handle it
        """
        logger.debug(f"Adding direct route: {tool_name} -> {service_name}")
        self.direct_routes[tool_name] = service_name
        
        # Invalidate cache for this tool
        if tool_name in self.route_cache:
            del self.route_cache[tool_name]
    
    def add_namespace_route(self, namespace: str, service_name: str):
        """Route all tools with a namespace prefix to a service.
        
        Args:
            namespace: Namespace prefix (e.g., "github")
            service_name: Name of the service to handle this namespace
        """
        logger.debug(f"Adding namespace route: {namespace}_* -> {service_name}")
        self.namespace_routes[namespace] = service_name
        
        # Invalidate cache for tools with this namespace
        self._invalidate_namespace_cache(namespace)
    
    def add_pattern_route(
        self,
        pattern: str,
        service_name: str,
        priority: int = 0,
        description: Optional[str] = None
    ):
        """Add a regex-based routing rule.
        
        Args:
            pattern: Regular expression pattern
            service_name: Name of the service to handle matches
            priority: Higher priority rules are checked first
            description: Human-readable description of the rule
        """
        logger.debug(f"Adding pattern route: {pattern} -> {service_name}")
        
        rule = RoutingRule(
            pattern=re.compile(pattern),
            service_name=service_name,
            priority=priority,
            description=description
        )
        
        # Insert in priority order
        self.pattern_rules.append(rule)
        self.pattern_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Clear cache as patterns might affect existing routes
        self.route_cache.clear()
    
    def set_default_service(self, service_name: str):
        """Set a default service for unmatched tools.
        
        Args:
            service_name: Name of the default service
        """
        logger.info(f"Setting default service: {service_name}")
        self.default_service = service_name
    
    def build_routes_from_registry(self):
        """Build routing tables from registered services.
        
        This method examines all registered services and their tools
        to automatically build routing tables based on:
        - Tool names and their source services
        - Service namespaces
        - Service capabilities
        """
        logger.info("Building routes from service registry")
        
        for service_name, service_info in self.registry.services.items():
            # Skip disabled or errored services
            if not service_info.config.enabled:
                continue
            if service_info.status == ServiceStatus.ERROR:
                continue
            
            # Add namespace route
            if namespace := service_info.config.namespace:
                self.add_namespace_route(namespace, service_name)
            
            # Add direct routes for all tools
            for tool in service_info.tools:
                tool_name = tool.name if hasattr(tool, "name") else tool.get("name")
                if tool_name:
                    self.add_direct_route(tool_name, service_name)
                    
                    # Categorize the tool
                    self.category_manager.categorize_tool(tool)
                    
                    # Add alias routes if available
                    if hasattr(tool, "aliases"):
                        for alias in tool.aliases:
                            self.alias_routes[alias.lower()] = tool_name
                    elif isinstance(tool, dict) and "aliases" in tool:
                        for alias in tool.get("aliases", []):
                            self.alias_routes[alias.lower()] = tool_name
        
        logger.info(
            f"Built routes: {len(self.direct_routes)} direct, "
            f"{len(self.namespace_routes)} namespace, "
            f"{len(self.pattern_rules)} pattern rules, "
            f"{len(self.alias_routes)} aliases"
        )
    
    def get_service_for_capability(self, capability: str) -> Optional[str]:
        """Find a service that provides a specific capability.
        
        Args:
            capability: Capability name (e.g., "resources", "prompts")
            
        Returns:
            Name of a service providing this capability, or None
        """
        for service_name, service_info in self.registry.services.items():
            if service_info.status != ServiceStatus.READY:
                continue
                
            caps = service_info.capabilities
            if caps and getattr(caps, capability, False):
                return service_name
        
        return None
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics.
        
        Returns:
            Dictionary of routing metrics
        """
        total_routes = sum(stats.get("success", 0) for stats in self.route_stats.values())
        total_errors = sum(stats.get("error", 0) for stats in self.route_stats.values())
        
        return {
            "total_routes": total_routes,
            "total_errors": total_errors,
            "error_rate": total_errors / max(total_routes, 1),
            "cache_size": len(self.route_cache),
            "direct_routes": len(self.direct_routes),
            "namespace_routes": len(self.namespace_routes),
            "pattern_rules": len(self.pattern_rules),
            "service_stats": self.route_stats
        }
    
    def clear_cache(self):
        """Clear the routing cache."""
        self.route_cache.clear()
        logger.debug("Routing cache cleared")
    
    def get_tools_by_category(self, category: Union[str, Any]) -> List[Dict[str, Any]]:
        """Get all tools in a specific category.
        
        Args:
            category: Category name or enum
            
        Returns:
            List of tool information dictionaries
        """
        tool_names = self.category_manager.get_tools_by_category(category)
        tools = []
        
        for tool_name in tool_names:
            if tool_name in self.direct_routes:
                service_name = self.direct_routes[tool_name]
                service_info = self.registry.services.get(service_name)
                
                if service_info:
                    # Find the tool in the service
                    for tool in service_info.tools:
                        if (hasattr(tool, "name") and tool.name == tool_name) or \
                           (isinstance(tool, dict) and tool.get("name") == tool_name):
                            tool_dict = tool.to_dict() if hasattr(tool, "to_dict") else dict(tool)
                            tool_dict["service"] = service_name
                            tools.append(tool_dict)
                            break
        
        return tools
    
    def get_category_stats(self) -> Dict[str, Any]:
        """Get statistics about tool categories.
        
        Returns:
            Dictionary of category statistics
        """
        return self.category_manager.get_category_stats()
    
    def search_tools_by_category(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for tools with category filtering.
        
        Args:
            query: Search query
            categories: Optional list of categories to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            List of matching tool information
        """
        matching_tool_names = self.category_manager.search_tools(query, categories, tags)
        tools = []
        
        for tool_name in matching_tool_names:
            if tool_name in self.direct_routes:
                service_name = self.direct_routes[tool_name]
                service_info = self.registry.services.get(service_name)
                
                if service_info:
                    for tool in service_info.tools:
                        if (hasattr(tool, "name") and tool.name == tool_name) or \
                           (isinstance(tool, dict) and tool.get("name") == tool_name):
                            tool_dict = tool.to_dict() if hasattr(tool, "to_dict") else dict(tool)
                            tool_dict["service"] = service_name
                            tool_dict["categories"] = list(self.category_manager.get_tool_categories(tool_name))
                            tools.append(tool_dict)
                            break
        
        return tools
    
    def _make_routing_decision(self, tool_name: str) -> RouteDecision:
        """Make a routing decision for a tool.
        
        Tries multiple strategies in order:
        1. Comprehensive alias lookup (using alias registry)
        2. Direct mapping
        3. Namespace extraction
        4. Pattern matching
        5. Default service
        
        AI_CONTEXT:
            This method coordinates the routing strategies by delegating
            to focused helper methods. Each strategy is isolated for
            better testability and maintainability.
        """
        # Try alias resolution first
        resolved_tool_name = self._resolve_alias(tool_name)
        
        # Try each routing strategy in order
        strategies = [
            (self._try_direct_route, resolved_tool_name),
            (self._try_namespace_route, resolved_tool_name),
            (self._try_pattern_route, resolved_tool_name),
            (self._try_discovery_route, resolved_tool_name),
            (self._try_default_route, resolved_tool_name)
        ]
        
        for strategy_func, tool in strategies:
            if decision := strategy_func(tool):
                return decision
        
        # No route found - provide helpful error message
        raise self._create_routing_error(resolved_tool_name)
    
    def _resolve_alias(self, tool_name: str) -> str:
        """Resolve tool name aliases using local and global registries.
        
        Args:
            tool_name: The tool name or alias to resolve
            
        Returns:
            The resolved tool name (may be the same as input)
        """
        # Check local alias routes (case-insensitive)
        tool_name_lower = tool_name.lower()
        if tool_name_lower in self.alias_routes:
            return self.alias_routes[tool_name_lower]
        
        # Try the global alias registry
        alias_result = find_tool_for_alias(tool_name)
        if alias_result:
            actual_tool_name, confidence = alias_result
            logger.debug(
                f"Alias registry matched '{tool_name}' to '{actual_tool_name}' "
                f"with confidence {confidence}"
            )
            return actual_tool_name
        
        return tool_name
    
    def _try_direct_route(self, tool_name: str) -> Optional[RouteDecision]:
        """Try to route using direct tool-to-service mapping.
        
        Args:
            tool_name: The tool name to route
            
        Returns:
            RouteDecision if found, None otherwise
        """
        if tool_name in self.direct_routes:
            service = self.direct_routes[tool_name]
            return RouteDecision(
                tool_name=tool_name,
                service_name=service,
                original_tool_name=self._remove_namespace(tool_name),
                routing_method="direct",
                confidence=1.0
            )
        return None
    
    def _try_namespace_route(self, tool_name: str) -> Optional[RouteDecision]:
        """Try to route using namespace prefix matching.
        
        Args:
            tool_name: The tool name to route
            
        Returns:
            RouteDecision if found, None otherwise
        """
        if namespace := self._extract_namespace(tool_name):
            if namespace in self.namespace_routes:
                service = self.namespace_routes[namespace]
                return RouteDecision(
                    tool_name=tool_name,
                    service_name=service,
                    original_tool_name=tool_name[len(namespace) + 1:],
                    routing_method="namespace",
                    confidence=0.9
                )
        return None
    
    def _try_pattern_route(self, tool_name: str) -> Optional[RouteDecision]:
        """Try to route using regex pattern matching.
        
        Args:
            tool_name: The tool name to route
            
        Returns:
            RouteDecision if found, None otherwise
        """
        for rule in self.pattern_rules:
            if rule.matches(tool_name):
                return RouteDecision(
                    tool_name=tool_name,
                    service_name=rule.service_name,
                    original_tool_name=self._remove_namespace(tool_name),
                    routing_method="pattern",
                    confidence=0.8
                )
        return None
    
    def _try_discovery_route(self, tool_name: str) -> Optional[RouteDecision]:
        """Try to discover route by scanning service tools.
        
        Args:
            tool_name: The tool name to route
            
        Returns:
            RouteDecision if found, None otherwise
        """
        if service := self._find_service_by_tool(tool_name):
            # Add to direct routes for faster future lookups
            self.add_direct_route(tool_name, service)
            return RouteDecision(
                tool_name=tool_name,
                service_name=service,
                original_tool_name=self._remove_namespace(tool_name),
                routing_method="discovery",
                confidence=0.7
            )
        return None
    
    def _try_default_route(self, tool_name: str) -> Optional[RouteDecision]:
        """Try to route using default service if configured.
        
        Args:
            tool_name: The tool name to route
            
        Returns:
            RouteDecision if default service exists, None otherwise
        """
        if self.default_service:
            return RouteDecision(
                tool_name=tool_name,
                service_name=self.default_service,
                original_tool_name=tool_name,
                routing_method="default",
                confidence=0.5
            )
        return None
    
    def _create_routing_error(self, tool_name: str) -> "RoutingError":
        """Create a helpful routing error with suggestions.
        
        Args:
            tool_name: The tool name that couldn't be routed
            
        Returns:
            RoutingError with helpful suggestions
        """
        error_msg = f"No service found for tool: {tool_name}"
        
        # Collect all available tools
        all_tools = list(self.direct_routes.keys())
        
        # Add suggestions based on fuzzy matching
        suggestions = fuzzy_match_tools(tool_name, all_tools)
        if suggestions:
            suggestion_msg = format_suggestions(suggestions)
            error_msg += f"\n\n{suggestion_msg}"
        
        # Check for similar aliases
        natural_form = tool_name.replace('_', ' ')
        if natural_form in self.alias_routes:
            actual_tool = self.alias_routes[natural_form]
            error_msg += f"\n\nTip: Try using the natural language form: '{natural_form}'"
        
        return RoutingError(error_msg)
    
    def _extract_namespace(self, tool_name: str) -> Optional[str]:
        """Extract namespace from tool name.
        
        Assumes namespace format: namespace_toolname
        """
        parts = tool_name.split("_", 1)
        if len(parts) > 1:
            return parts[0]
        return None
    
    def _remove_namespace(self, tool_name: str) -> str:
        """Remove namespace prefix from tool name."""
        parts = tool_name.split("_", 1)
        if len(parts) > 1:
            # Check if first part is a known namespace
            if parts[0] in self.namespace_routes:
                return parts[1]
        return tool_name
    
    def _find_service_by_tool(self, tool_name: str) -> Optional[str]:
        """Find a service that provides a specific tool.
        
        This is a fallback method that scans all services.
        """
        for service_name, service_info in self.registry.services.items():
            if service_info.status != ServiceStatus.READY:
                continue
                
            for tool in service_info.tools:
                if hasattr(tool, "name"):
                    if tool.name == tool_name:
                        return service_name
                elif isinstance(tool, dict) and tool.get("name") == tool_name:
                    return service_name
        
        return None
    
    def _invalidate_namespace_cache(self, namespace: str):
        """Invalidate cache entries for a namespace."""
        prefix = f"{namespace}_"
        keys_to_remove = [
            key for key in self.route_cache
            if key.startswith(prefix)
        ]
        for key in keys_to_remove:
            del self.route_cache[key]
    
    def _track_route(self, service_name: str):
        """Track routing statistics."""
        if service_name not in self.route_stats:
            self.route_stats[service_name] = {
                "success": 0,
                "error": 0
            }
        self.route_stats[service_name]["success"] += 1


class RoutingError(Exception):
    """Error raised when routing fails."""
    pass


class LoadBalancer:
    """Load balancer for distributing requests across equivalent services.
    
    AI_CONTEXT:
        This class implements various load balancing strategies:
        - Round-robin: Rotate through services
        - Least-connections: Route to service with fewest active connections
        - Response-time: Route to fastest responding service
        - Weighted: Route based on configured weights
        
        Used when multiple services can handle the same tool.
    """
    
    def __init__(self, strategy: str = "round-robin"):
        """Initialize load balancer.
        
        Args:
            strategy: Load balancing strategy to use
        """
        self.strategy = strategy
        self.service_indices: Dict[str, int] = {}  # For round-robin
        self.service_weights: Dict[str, float] = {}  # For weighted
        self.service_metrics: Dict[str, Dict[str, float]] = {}  # For metrics-based
    
    def select_service(
        self,
        services: List[str],
        tool_name: Optional[str] = None
    ) -> str:
        """Select a service from available options.
        
        Args:
            services: List of service names that can handle the request
            tool_name: Optional tool name for context
            
        Returns:
            Selected service name
        """
        if not services:
            raise ValueError("No services available")
        
        if len(services) == 1:
            return services[0]
        
        if self.strategy == "round-robin":
            return self._round_robin_select(services)
        elif self.strategy == "least-connections":
            return self._least_connections_select(services)
        elif self.strategy == "response-time":
            return self._response_time_select(services)
        elif self.strategy == "weighted":
            return self._weighted_select(services)
        else:
            # Default to round-robin
            return self._round_robin_select(services)
    
    def _round_robin_select(self, services: List[str]) -> str:
        """Select service using round-robin."""
        key = ",".join(sorted(services))
        
        if key not in self.service_indices:
            self.service_indices[key] = 0
        
        index = self.service_indices[key]
        selected = services[index % len(services)]
        self.service_indices[key] = index + 1
        
        return selected
    
    def _least_connections_select(self, services: List[str]) -> str:
        """Select service with least active connections."""
        # TODO: Implement connection tracking
        return self._round_robin_select(services)
    
    def _response_time_select(self, services: List[str]) -> str:
        """Select service with best response time."""
        # TODO: Implement response time tracking
        return self._round_robin_select(services)
    
    def _weighted_select(self, services: List[str]) -> str:
        """Select service based on weights."""
        # TODO: Implement weighted selection
        return self._round_robin_select(services)