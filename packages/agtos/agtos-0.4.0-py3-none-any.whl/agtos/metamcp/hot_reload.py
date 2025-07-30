"""Hot-reload functionality for dynamically created tools.

AI_CONTEXT:
    This module provides hot-reload capabilities for user-created tools in agtos.
    When a new tool is created via tool_creator.create, it can be immediately
    loaded into the Meta-MCP registry without restarting the server.
    
    Key features:
    - Monitor ~/.agtos/user_tools/ for changes
    - Dynamically load single tools or tool modules
    - Thread-safe updates to the registry
    - Integration with tool creation workflow
    
    Architecture:
    1. FileWatcher monitors user_tools directory
    2. ToolLoader dynamically imports and validates tools
    3. HotReloader coordinates updates to the registry
    4. Thread safety via asyncio locks
"""

import asyncio
import importlib
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Set, Callable
from datetime import datetime
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy classes to avoid import errors
    FileSystemEventHandler = object
    FileCreatedEvent = object
    FileModifiedEvent = object
    Observer = None

from agtos.metamcp.types import ToolSpec
from agtos.metamcp.registry import ServiceRegistry

logger = logging.getLogger(__name__)


class ToolFileHandler(FileSystemEventHandler):
    """Handles file system events for tool hot-reload.
    
    AI_CONTEXT:
        This handler watches for new or modified Python files in the user_tools
        directory and triggers reload when changes are detected.
    """
    
    def __init__(self, callback: Callable[[Path], None]):
        """Initialize with callback for tool changes.
        
        Args:
            callback: Function to call with path when a tool file changes
        """
        self.callback = callback
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._debounce_delay = 0.5  # seconds
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self._debounced_callback(Path(event.src_path))
    
    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self._debounced_callback(Path(event.src_path))
    
    def _debounced_callback(self, path: Path) -> None:
        """Debounce rapid file changes to avoid multiple reloads.
        
        AI_CONTEXT:
            File saves often trigger multiple events. This debouncer ensures
            we only reload once after changes have settled.
        """
        # Cancel existing timer for this file
        if str(path) in self._debounce_timers:
            self._debounce_timers[str(path)].cancel()
        
        # Start new timer
        timer = threading.Timer(
            self._debounce_delay,
            lambda: self.callback(path)
        )
        self._debounce_timers[str(path)] = timer
        timer.start()


class ToolLoader:
    """Dynamically loads and validates user-created tools.
    
    AI_CONTEXT:
        This class handles the actual loading of Python modules from the
        user_tools directory. It validates tool structure and converts
        them to the format expected by the Meta-MCP registry.
    """
    
    def __init__(self):
        """Initialize the tool loader."""
        self._loaded_modules: Dict[str, Any] = {}
    
    def load_tool_file(self, tool_path: Path) -> Optional[Dict[str, Any]]:
        """Load a tool from a Python file.
        
        Args:
            tool_path: Path to the tool Python file
            
        Returns:
            Dictionary of tool_name -> tool_data or None if loading fails
        """
        try:
            # Get module name from file (use just the stem, not the full path)
            tool_stem = tool_path.stem
            module_name = f"agtos.user_tools.{tool_stem}"
            
            # Create module spec
            spec = self._create_module_spec(module_name, tool_path)
            if not spec:
                return None
            
            # Load or reload module
            module = self._load_or_reload_module(module_name, spec)
            
            # Store reference
            self._loaded_modules[str(tool_path)] = module
            
            # Extract tools from module
            tools = self._extract_tools_from_module(module, tool_stem)
            
            # Load metadata and check for MCP schema
            metadata = self._load_metadata_file(tool_path)
            if metadata and "mcp_schema" in metadata and "tools" in metadata["mcp_schema"]:
                # Use MCP schema to create properly named tools
                tools = self._reconcile_with_mcp_schema(tools, metadata["mcp_schema"]["tools"], metadata)
            else:
                # Apply metadata to auto-generated tools
                self._apply_metadata_to_tools(tools, metadata)
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to load tool from {tool_path}: {e}")
            return None
    
    def _create_module_spec(self, module_name: str, tool_path: Path) -> Optional[importlib.machinery.ModuleSpec]:
        """Create module spec for the tool file."""
        spec = importlib.util.spec_from_file_location(module_name, tool_path)
        if not spec or not spec.loader:
            logger.error(f"Failed to create spec for {tool_path}")
            return None
        return spec
    
    def _load_or_reload_module(self, module_name: str, spec: importlib.machinery.ModuleSpec) -> Any:
        """Load a new module or reload if already loaded."""
        if module_name in sys.modules:
            # Reload existing module
            module = importlib.reload(sys.modules[module_name])
            logger.info(f"Reloaded tool module: {module_name}")
        else:
            # Load new module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.info(f"Loaded new tool module: {module_name}")
        
        return module
    
    def _extract_tools_from_module(self, module: Any, module_name: str) -> Dict[str, Any]:
        """Extract tools from a module.
        
        For user-created tools, we expect a single class with methods that
        become the tool functions. We prioritize MCP schema names when available.
        """
        tools = {}
        
        # Look for the tool class (e.g., JsonplaceholderClient)
        tool_class = None
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
                
            attr = getattr(module, attr_name)
            # Check if it's a class and not a built-in type
            if isinstance(attr, type) and attr.__module__ == module.__name__:
                tool_class = attr
                break
        
        if not tool_class:
            return tools
        
        # Create an instance
        try:
            instance = tool_class()
            
            # Collect all available methods first
            available_methods = {}
            for method_name in dir(instance):
                if method_name.startswith("_"):
                    continue
                    
                method = getattr(instance, method_name)
                if callable(method) and hasattr(method, "__self__"):
                    available_methods[method_name] = method
            
            # Now create tools with auto-generated names
            # These will be overridden by MCP schema names if available
            for method_name, method in available_methods.items():
                # The tool name will be module_name + method_name
                tool_name = f"{module_name}_{method_name}"
                
                # Try to get schema from method or use a default
                schema = self._extract_schema_from_method(method)
                
                tools[tool_name] = {
                    "func": method,
                    "schema": schema,
                    "description": method.__doc__ or f"Execute {method_name}",
                    "version": "1.0",
                    "_method_name": method_name  # Store for MCP schema matching
                }
        except Exception as e:
            logger.warning(f"Failed to instantiate class {tool_class.__name__}: {e}")
        
        return tools
    
    def _extract_schema_from_method(self, method: Any) -> Dict[str, Any]:
        """Extract or generate schema for a method."""
        # Check if method has schema attached
        if hasattr(method, "_mcp_schema"):
            return method._mcp_schema
            
        # Try to extract from function signature
        import inspect
        try:
            sig = inspect.signature(method)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                    
                # Basic type mapping
                param_type = "string"  # default
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            return {
                "type": "object",
                "properties": properties,
                "required": required
            }
        except:
            # Fallback schema
            return {
                "type": "object",
                "properties": {},
                "additionalProperties": True
            }
    
    def _load_metadata_file(self, tool_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata from JSON file."""
        # For versioned tools, metadata is in metadata.json
        if "versions" in str(tool_path):
            metadata_path = tool_path.parent / "metadata.json"
        else:
            # For regular tools, metadata is alongside the .py file
            metadata_path = tool_path.with_suffix(".json")
            
        if not metadata_path.exists():
            return None
            
        try:
            return json.loads(metadata_path.read_text())
        except Exception as e:
            logger.warning(f"Failed to load metadata for {tool_path}: {e}")
            return None
    
    def _reconcile_with_mcp_schema(
        self, 
        discovered_tools: Dict[str, Any], 
        mcp_tools: list,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconcile discovered tools with MCP schema definitions.
        
        This ensures tools are named exactly as defined in the MCP schema,
        which is what Claude expects when calling the tools.
        """
        reconciled_tools = {}
        
        # Map method names to tool data for easier lookup
        method_map = {}
        for tool_name, tool_data in discovered_tools.items():
            method_name = tool_data.get("_method_name")
            if method_name:
                method_map[method_name] = tool_data
        
        # Create tools based on MCP schema
        for mcp_tool in mcp_tools:
            mcp_tool_name = mcp_tool.get("name", "")
            if not mcp_tool_name:
                continue
            
            # Try to find matching method
            # MCP tool names are usually in format: modulename_methodname
            parts = mcp_tool_name.split("_", 1)
            if len(parts) > 1:
                method_suffix = parts[1]
                
                # Look for exact match first
                if method_suffix in method_map:
                    tool_data = method_map[method_suffix].copy()
                    tool_data["schema"] = mcp_tool.get("inputSchema", {})
                    tool_data["description"] = mcp_tool.get("description", tool_data["description"])
                    tool_data["metadata"] = metadata
                    reconciled_tools[mcp_tool_name] = tool_data
                else:
                    # Try to find a method that ends with the suffix
                    for method_name, tool_data in method_map.items():
                        if method_name.endswith(method_suffix) or method_suffix.endswith(method_name):
                            reconciled_tool = tool_data.copy()
                            reconciled_tool["schema"] = mcp_tool.get("inputSchema", {})
                            reconciled_tool["description"] = mcp_tool.get("description", reconciled_tool["description"])
                            reconciled_tool["metadata"] = metadata
                            reconciled_tools[mcp_tool_name] = reconciled_tool
                            break
        
        # If no tools were reconciled, fall back to discovered tools
        if not reconciled_tools:
            logger.warning(f"Could not reconcile any tools with MCP schema, using discovered tools")
            self._apply_metadata_to_tools(discovered_tools, metadata)
            return discovered_tools
        
        return reconciled_tools
    
    def _apply_metadata_to_tools(self, tools: Dict[str, Any], metadata: Optional[Dict[str, Any]]) -> None:
        """Apply metadata to tools."""
        if not metadata:
            return
            
        for tool_name in tools:
            if "metadata" not in tools[tool_name]:
                tools[tool_name]["metadata"] = metadata
            
            # Update description if available
            if "description" in metadata:
                tools[tool_name]["description"] = metadata["description"]
    
    def validate_tool(self, tool_name: str, tool_data: Dict[str, Any]) -> bool:
        """Validate tool structure and requirements."""
        required_fields = ["func", "schema", "description"]
        
        for field in required_fields:
            if field not in tool_data:
                logger.error(f"Tool '{tool_name}' missing required field: {field}")
                return False
        
        # Check that func is callable
        if not callable(tool_data["func"]):
            logger.error(f"Tool '{tool_name}' func is not callable")
            return False
        
        # Check schema structure
        schema = tool_data["schema"]
        if not isinstance(schema, dict) or "type" not in schema:
            logger.error(f"Tool '{tool_name}' has invalid schema")
            return False
        
        return True


class HotReloader:
    """Manages hot-reload functionality for user-created tools.
    
    AI_CONTEXT:
        This is the main class that coordinates hot-reload functionality.
        It watches the user_tools directory, loads new/modified tools,
        and updates the Meta-MCP registry dynamically.
    """
    
    def __init__(self, registry: ServiceRegistry):
        """Initialize hot reloader with registry reference."""
        self.registry = registry
        self.loader = ToolLoader()
        self.observer: Optional[Observer] = None
        self._reload_lock = asyncio.Lock()
        self._loaded_tools: Set[str] = set()
        self.user_tools_dir = Path.home() / ".agtos" / "user_tools"
        
        # Ensure user tools directory exists
        self.user_tools_dir.mkdir(parents=True, exist_ok=True)
    
    async def start_watching(self) -> None:
        """Start watching the user_tools directory for changes."""
        # Load existing tools first
        await self.load_all_user_tools()
        
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available. Hot-reload will not monitor file changes automatically.")
            logger.info("Install watchdog with: pip install watchdog")
            return
        
        if self.observer and self.observer.is_alive():
            logger.warning("File watcher already running")
            return
        
        # Setup file watcher
        event_handler = ToolFileHandler(
            callback=lambda path: asyncio.create_task(self.reload_tool(path))
        )
        
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            str(self.user_tools_dir),
            recursive=False
        )
        
        self.observer.start()
        logger.info(f"Started watching {self.user_tools_dir} for tool changes")
    
    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped file watcher")
    
    async def load_all_user_tools(self) -> None:
        """Load all existing user tools from the directory."""
        logger.info("Loading existing user tools...")
        
        tool_count = 0
        
        # Check active directory first (for versioned tools)
        active_dir = self.user_tools_dir / "active"
        if active_dir.exists():
            for tool_file in active_dir.glob("*.py"):
                if not tool_file.name.startswith("_"):
                    # Resolve symlink to actual file
                    actual_file = tool_file.resolve()
                    if actual_file.exists():
                        success = await self.reload_tool(actual_file)
                        if success:
                            tool_count += 1
        
        # Then check root directory (for non-versioned tools)
        for tool_file in self.user_tools_dir.glob("*.py"):
            if not tool_file.name.startswith("_"):
                success = await self.reload_tool(tool_file)
                if success:
                    tool_count += 1
        
        if tool_count > 0:
            logger.info(f"Loaded {tool_count} user tools")
    
    async def reload_tool(self, tool_path: Path) -> bool:
        """Reload a specific tool file."""
        async with self._reload_lock:
            try:
                logger.info(f"Reloading tool: {tool_path.name}")
                
                # Load the tool file
                tools = self.loader.load_tool_file(tool_path)
                if not tools:
                    logger.error(f"No tools found in {tool_path}")
                    return False
                
                # Validate all tools
                valid_tools = {}
                for tool_name, tool_data in tools.items():
                    if self.loader.validate_tool(tool_name, tool_data):
                        valid_tools[tool_name] = tool_data
                    else:
                        logger.warning(f"Skipping invalid tool: {tool_name}")
                
                if not valid_tools:
                    logger.error(f"No valid tools in {tool_path}")
                    return False
                
                # Update registry (use just the stem name)
                tool_stem = tool_path.stem
                await self._update_registry(tool_stem, valid_tools)
                
                # Track loaded tools
                self._loaded_tools.add(tool_stem)
                
                logger.info(f"Successfully loaded {len(valid_tools)} tools from {tool_path.name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to reload tool {tool_path}: {e}")
                return False
    
    async def _update_registry(self, service_name: str, tools: Dict[str, Any]) -> None:
        """Update the service registry with new/updated tools."""
        # Instead of creating a separate service, we need to update the main agtos service
        # This ensures tools are accessible as mcp__agtos__toolname in Claude
        
        # Get the existing agtos service
        agtos_service = self.registry.services.get("agtos")
        
        if agtos_service:
            # Get the current plugin tools from the registry's storage
            current_tools = self.registry._plugin_tools.get("agtos", {}).copy()
            
            # Update with new/modified tools
            current_tools.update(tools)
            
            # Update the plugin tools storage
            self.registry._plugin_tools["agtos"] = current_tools
            
            # Update the service's tools list with new ToolSpec objects
            for tool_name, tool_data in tools.items():
                # Create ToolSpec for the new/updated tool
                from agtos.metamcp.types import ToolSpec
                tool_spec = ToolSpec(
                    name=tool_name,
                    description=tool_data.get("description", ""),
                    inputSchema=tool_data.get("schema", {})
                )
                
                # Remove old version if exists
                agtos_service.tools = [t for t in agtos_service.tools if t.name != tool_name]
                
                # Add new version
                agtos_service.tools.append(tool_spec)
            
            logger.info(f"Updated agtos service with user tool: {service_name} (total tools: {len(agtos_service.tools)})")
        else:
            # Fallback: If agtos service doesn't exist, create a user_tools service
            # This shouldn't happen in normal operation
            logger.warning("agtos service not found, creating separate user_tools service")
            full_service_name = f"user_tools.{service_name}"
            
            # Check if service already exists
            if full_service_name in self.registry.services:
                await self.registry.unregister_service(full_service_name)
            
            # Register as plugin service
            await self.registry.register_plugin_service(
                full_service_name,
                {
                    "description": f"User-created tool: {service_name}",
                    "tools": tools
                }
            )
    
    async def reload_specific_tool(self, tool_name: str) -> bool:
        """Reload a specific tool by name."""
        tool_path = self.user_tools_dir / f"{tool_name}.py"
        
        if not tool_path.exists():
            logger.error(f"Tool file not found: {tool_path}")
            return False
        
        return await self.reload_tool(tool_path)
    
    def get_loaded_tools(self) -> Set[str]:
        """Get set of currently loaded user tool names."""
        return self._loaded_tools.copy()


# Singleton instance
_hot_reloader: Optional[HotReloader] = None


def get_hot_reloader(registry: ServiceRegistry) -> HotReloader:
    """Get or create the hot reloader instance."""
    global _hot_reloader
    
    if _hot_reloader is None:
        _hot_reloader = HotReloader(registry)
    
    return _hot_reloader


async def reload_user_tool(tool_name: str, registry: ServiceRegistry) -> bool:
    """Convenience function to reload a specific user tool."""
    reloader = get_hot_reloader(registry)
    return await reloader.reload_specific_tool(tool_name)