"""Tool discovery for different service types.

AI_CONTEXT:
    This module handles discovering tools from various service types:
    - CLI tools from knowledge base
    - REST APIs from OpenAPI specs
    - Plugin tools from Python objects
    
    It generates proper tool specifications with schemas and metadata
    for each service type.
"""

import json
import logging
from typing import Dict, List, Optional, Any
import inspect

from ..types import ToolSpec
from .core import ServiceConfig

logger = logging.getLogger(__name__)


class DiscoveryManager:
    """Manages tool discovery for all service types.
    
    AI_CONTEXT:
        This class contains methods to discover and generate tool
        specifications from different sources. It handles:
        - CLI tool discovery using knowledge base
        - REST API endpoint discovery from OpenAPI specs
        - Plugin method introspection
        - Tool naming and aliasing
    """
    
    def __init__(self, registry):
        """Initialize discovery manager with registry reference."""
        self.registry = registry
    
    # ========================================================================
    # CLI Tool Discovery
    # ========================================================================
    
    async def discover_cli_tools(
        self,
        config: ServiceConfig
    ) -> List[ToolSpec]:
        """Discover CLI tools from knowledge base using CLI bridge.
        
        AI_CONTEXT:
            This method uses the CLI bridge to discover and convert CLI tools
            into MCP-compatible tool specifications. The bridge handles:
            - Loading CLI knowledge from the knowledge store
            - Parsing help text and examples
            - Generating JSON schemas
            - Creating proper tool specs with namespacing
        """
        # Check if CLI bridge is available
        if not self.registry.cli_bridge:
            logger.warning(f"CLI Bridge not available - cannot discover tools for {config.binary}")
            return []
            
        # Use CLI bridge to discover tools
        tools = self.registry.cli_bridge.discover_cli_tools([config.binary])
        
        # Apply namespace to avoid conflicts
        namespaced_tools = []
        for tool in tools:
            # Update tool name with namespace if needed
            if not tool.name.startswith(f"{config.namespace}_"):
                tool.name = tool.name.replace(f"cli_{config.binary}", config.namespace)
            namespaced_tools.append(tool)
        
        # If no tools discovered, provide a fallback
        if not namespaced_tools:
            logger.warning(f"No tools discovered for CLI {config.binary}, using fallback")
            return [
                ToolSpec(
                    name=f"{config.namespace}_execute",
                    description=f"Execute {config.binary} command",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "args": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["command"]
                    }
                )
            ]
        
        return namespaced_tools
    
    # ========================================================================
    # REST API Discovery
    # ========================================================================
    
    async def discover_rest_tools(
        self,
        config: ServiceConfig,
        openapi_url: Optional[str]
    ) -> List[ToolSpec]:
        """Discover REST API tools from OpenAPI spec or knowledge base.
        
        AI_CONTEXT: This method discovers REST API tools by:
        
        1. Using the REST bridge to generate tools from knowledge store
        2. Optionally fetching and parsing OpenAPI specs
        3. Converting tool definitions to ToolSpec objects
        4. Applying proper namespacing
        
        The REST bridge handles the heavy lifting of parsing API
        definitions and generating proper tool schemas.
        """
        tools = []
        
        try:
            # Try to import REST bridge
            try:
                from ..bridge.rest import RESTBridge
                bridge = RESTBridge()
            except ImportError:
                logger.warning(f"REST Bridge not available - cannot discover tools for {config.name}")
                return []
            
            if openapi_url:
                # Fetch and store OpenAPI spec in knowledge base
                await self._fetch_and_store_openapi(config, openapi_url)
            
            # Generate tools using REST bridge
            tool_defs = bridge.generate_tools_for_api(config.name)
            
            # Convert to ToolSpec objects
            for tool_name, tool_def in tool_defs.items():
                # Apply namespace if not already present
                if not tool_name.startswith(f"{config.namespace}_"):
                    tool_name = f"{config.namespace}_{tool_name}"
                
                # Generate display name and aliases for REST tools
                display_name = self._generate_rest_display_name(tool_name)
                aliases = self._generate_rest_aliases(tool_name, config.namespace)
                
                tool = ToolSpec(
                    name=tool_name,
                    description=tool_def.get("description", ""),
                    inputSchema=tool_def.get("schema", {}),
                    displayName=display_name,
                    aliases=aliases
                )
                tools.append(tool)
            
            logger.info(f"Discovered {len(tools)} REST tools for {config.name}")
            
        except Exception as e:
            logger.error(f"Failed to discover REST tools for {config.name}: {e}")
        
        return tools
    
    async def _fetch_and_store_openapi(
        self, 
        config: ServiceConfig, 
        openapi_url: str
    ):
        """Fetch OpenAPI spec and store in knowledge base."""
        import aiohttp
        import yaml
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(openapi_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse as JSON or YAML
                        try:
                            spec = json.loads(content)
                        except json.JSONDecodeError:
                            spec = yaml.safe_load(content)
                        
                        # Store in knowledge base
                        from ...knowledge_store import get_knowledge_store
                        store = get_knowledge_store()
                        
                        # Extract endpoints from OpenAPI spec
                        endpoints = []
                        paths = spec.get("paths", {})
                        
                        for path, path_item in paths.items():
                            for method, operation in path_item.items():
                                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                    endpoint = {
                                        "path": path,
                                        "method": method.upper(),
                                        "operation_id": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                                        "summary": operation.get("summary", ""),
                                        "description": operation.get("description", ""),
                                        "parameters": operation.get("parameters", []),
                                        "request_body": operation.get("requestBody", {})
                                    }
                                    endpoints.append(endpoint)
                        
                        # Store API knowledge
                        api_data = {
                            "name": config.name,
                            "base_url": config.url or spec.get("servers", [{}])[0].get("url", ""),
                            "endpoints": endpoints,
                            "auth_methods": self._extract_openapi_auth(spec),
                            "openapi_spec": spec
                        }
                        
                        store.store(
                            type="api",
                            name=config.name,
                            data=api_data,
                            source=f"openapi:{openapi_url}"
                        )
                        
                        logger.info(f"Stored OpenAPI spec for {config.name} with {len(endpoints)} endpoints")
                        
        except Exception as e:
            logger.error(f"Failed to fetch OpenAPI spec from {openapi_url}: {e}")
    
    def _extract_openapi_auth(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract authentication methods from OpenAPI spec."""
        auth_methods = []
        
        # Check components.securitySchemes (OpenAPI 3.0)
        security_schemes = spec.get("components", {}).get("securitySchemes", {})
        
        for scheme_name, scheme in security_schemes.items():
            auth_type = scheme.get("type", "")
            
            if auth_type == "http":
                auth_methods.append({
                    "type": "http",
                    "scheme": scheme.get("scheme", "bearer"),
                    "name": scheme_name
                })
            elif auth_type == "apiKey":
                auth_methods.append({
                    "type": "api_key",
                    "in": scheme.get("in", "header"),
                    "key_name": scheme.get("name", "X-API-Key"),
                    "name": scheme_name
                })
            elif auth_type == "oauth2":
                auth_methods.append({
                    "type": "oauth2",
                    "flows": scheme.get("flows", {}),
                    "name": scheme_name
                })
        
        return auth_methods
    
    # ========================================================================
    # Plugin Tool Discovery
    # ========================================================================
    
    def extract_plugin_tools(self, plugin_instance: Any) -> List[ToolSpec]:
        """Extract tool specifications from an agentctl plugin."""
        tools = []
        
        # Get all methods that should be exposed as tools
        for method_name in dir(plugin_instance):
            if method_name.startswith("_"):
                continue
                
            method = getattr(plugin_instance, method_name)
            if callable(method) and hasattr(method, "__doc__"):
                # Extract tool info from docstring or annotations
                tool_name = f"{plugin_instance.__class__.__name__.lower()}_{method_name}"
                display_name = self._generate_plugin_display_name(tool_name)
                aliases = self._generate_plugin_aliases(tool_name, plugin_instance.__class__.__name__.lower())
                
                tool = ToolSpec(
                    name=tool_name,
                    description=method.__doc__ or f"Execute {method_name}",
                    inputSchema=self._extract_method_schema(method),
                    displayName=display_name,
                    aliases=aliases
                )
                tools.append(tool)
        
        return tools
    
    def _extract_method_schema(self, method: Any) -> Dict[str, Any]:
        """Extract parameter schema from method signature."""
        sig = inspect.signature(method)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            param_type = "string"  # Default
            if param.annotation != inspect.Parameter.empty:
                # Simple type mapping
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
            
            properties[param_name] = {"type": param_type}
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    # ========================================================================
    # Tool Naming and Aliasing
    # ========================================================================
    
    def _generate_rest_display_name(self, tool_name: str) -> str:
        """Generate a user-friendly display name for a REST tool.
        
        Examples:
            github_list_repos -> GitHub List Repos
            stripe_create_customer -> Stripe Create Customer
        """
        # Remove common prefixes and convert to title case
        parts = tool_name.split('_')
        
        # Capitalize known API names properly
        if parts[0] in ['github', 'stripe', 'openai', 'slack']:
            parts[0] = parts[0].title()
            if parts[0] == 'Github':
                parts[0] = 'GitHub'
            elif parts[0] == 'Openai':
                parts[0] = 'OpenAI'
        
        # Convert remaining parts to title case
        display_parts = [parts[0]]
        for part in parts[1:]:
            display_parts.append(part.capitalize())
            
        return ' '.join(display_parts)
    
    def _generate_rest_aliases(self, tool_name: str, namespace: str) -> List[str]:
        """Generate natural language aliases for a REST tool.
        
        Examples:
            github_list_repos -> ["list github repos", "github repos", "show repos"]
            stripe_create_customer -> ["create stripe customer", "new customer", "add customer"]
        """
        aliases = []
        
        # Remove namespace prefix if present
        if tool_name.startswith(f"{namespace}_"):
            base_name = tool_name[len(namespace)+1:]
        else:
            base_name = tool_name
            
        # Split into parts
        parts = base_name.split('_')
        
        # Basic alias without namespace
        if namespace not in base_name:
            aliases.append(f"{namespace} {base_name.replace('_', ' ')}")
        
        # Natural language variations
        if len(parts) >= 2:
            verb = parts[0]
            resource = '_'.join(parts[1:])
            
            # Standard format
            aliases.append(f"{verb} {resource.replace('_', ' ')}")
            
            # With namespace
            aliases.append(f"{verb} {namespace} {resource.replace('_', ' ')}")
            
            # Common verb substitutions
            if verb == "list":
                aliases.extend([
                    f"show {resource.replace('_', ' ')}",
                    f"get {resource.replace('_', ' ')}"
                ])
            elif verb == "create":
                aliases.extend([
                    f"new {resource.replace('_', ' ')}",
                    f"add {resource.replace('_', ' ')}"
                ])
            elif verb == "delete":
                aliases.append(f"remove {resource.replace('_', ' ')}")
            elif verb == "update":
                aliases.append(f"modify {resource.replace('_', ' ')}")
                
        # Remove duplicates while preserving order
        seen = set()
        unique_aliases = []
        for alias in aliases:
            if alias not in seen and alias != tool_name:
                seen.add(alias)
                unique_aliases.append(alias)
                
        return unique_aliases
    
    def _generate_plugin_display_name(self, tool_name: str) -> str:
        """Generate a user-friendly display name for a plugin tool.
        
        Examples:
            gitplugin_create_add -> Git Create Add
            cloudflare_update_dns -> Cloudflare Update DNS
        """
        parts = tool_name.split('_')
        
        # First part is plugin name, capitalize appropriately
        if parts[0].endswith('plugin'):
            parts[0] = parts[0][:-6]  # Remove 'plugin' suffix
            
        # Capitalize each part
        display_parts = []
        for part in parts:
            if part.lower() in ['dns', 'api', 'cdn', 'url']:
                display_parts.append(part.upper())
            else:
                display_parts.append(part.capitalize())
                
        return ' '.join(display_parts)
    
    def _generate_plugin_aliases(self, tool_name: str, plugin_name: str) -> List[str]:
        """Generate natural language aliases for a plugin tool.
        
        Examples:
            git_create_init -> ["git init", "initialize repo"]
            cloudflare_update_dns -> ["update dns", "change dns record"]
        """
        aliases = []
        
        # Remove plugin name prefix if present
        if tool_name.startswith(f"{plugin_name}_"):
            base_name = tool_name[len(plugin_name)+1:]
        else:
            base_name = tool_name
            
        # Split into parts
        parts = base_name.split('_')
        
        # Basic alias
        aliases.append(base_name.replace('_', ' '))
        
        # Plugin-specific aliases
        if plugin_name == "git":
            # Git commands are often used directly
            if base_name in ["init", "add", "commit", "push", "pull", "status"]:
                aliases.append(f"git {base_name}")
                
        elif plugin_name == "cloudflare":
            if "dns" in base_name:
                aliases.append(base_name.replace('_', ' ').replace('dns', 'DNS'))
                
        # Remove duplicates
        seen = set()
        unique_aliases = []
        for alias in aliases:
            if alias not in seen and alias != tool_name:
                seen.add(alias)
                unique_aliases.append(alias)
                
        return unique_aliases