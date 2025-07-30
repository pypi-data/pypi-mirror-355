"""Plugin manager for agtOS.

This module manages plugin discovery, loading, and configuration.
"""

from typing import Dict, Any, List
from pathlib import Path
import importlib
import json

from agtos.utils import get_logger

logger = get_logger(__name__)


class PluginManager:
    """Manages plugins for agtOS."""
    
    def __init__(self):
        self.plugins_dir = Path(__file__).parent
        self.loaded_plugins = {}
        self._discover_plugins()
    
    def _discover_plugins(self):
        """Discover available plugins."""
        # Find all Python files in plugins directory
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.stem.startswith("_") or plugin_file.stem == "manager":
                continue
            
            plugin_name = plugin_file.stem
            try:
                # Try to import the plugin
                module = importlib.import_module(f"agtos.plugins.{plugin_name}")
                self.loaded_plugins[plugin_name] = {
                    "name": plugin_name,
                    "module": module,
                    "status": "active",
                    "config": {}
                }
                logger.info(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all discovered plugins."""
        return [
            {
                "name": name,
                "status": info["status"],
                "config": info.get("config", {})
            }
            for name, info in self.loaded_plugins.items()
        ]
    
    def get_plugin(self, name: str) -> Any:
        """Get a specific plugin module."""
        if name in self.loaded_plugins:
            return self.loaded_plugins[name]["module"]
        return None
    
    def get_plugin_tools(self, plugin_name: str) -> Dict[str, Any]:
        """Get tools exported by a plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {}
        
        # Look for a get_tools function or similar
        if hasattr(plugin, f"get_{plugin_name}_tools"):
            return getattr(plugin, f"get_{plugin_name}_tools")()
        elif hasattr(plugin, "get_tools"):
            return plugin.get_tools()
        
        return {}