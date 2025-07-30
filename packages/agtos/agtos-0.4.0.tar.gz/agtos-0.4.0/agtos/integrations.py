"""Integration management for agtos.

This module handles third-party service integrations and API connections.
"""
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import yaml
import os
import subprocess
import json
from .knowledge.acquisition import KnowledgeAcquisition
from .knowledge_store import get_knowledge_store

class IntegrationManager:
    """Manages third-party service integrations."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize integration manager.
        
        Args:
            config_path: Path to integrations config. Defaults to ~/.agtos/integrations.yml
        """
        self.config_path = config_path or (Path.home() / ".agtos" / "integrations.yml")
        self._integrations = self._load()
        self.knowledge = KnowledgeAcquisition()
        self.store = get_knowledge_store()
    
    def _load(self) -> Dict[str, Dict[str, Any]]:
        """Load integrations from config file."""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _save(self):
        """Save integrations to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self._integrations, f, default_flow_style=False)
    
    def add_integration(self, name: str, config: Dict[str, Any]):
        """Add or update an integration.
        
        Args:
            name: Integration name
            config: Integration configuration
        """
        self._integrations[name] = config
        self._save()
    
    def remove_integration(self, name: str):
        """Remove an integration.
        
        Args:
            name: Integration name
        """
        if name in self._integrations:
            del self._integrations[name]
            self._save()
    
    def get_integration(self, name: str) -> Optional[Dict[str, Any]]:
        """Get integration configuration.
        
        Args:
            name: Integration name
            
        Returns:
            Integration config or None if not found
        """
        return self._integrations.get(name)
    
    def list_integrations(self) -> List[str]:
        """List all configured integrations."""
        return list(self._integrations.keys())
    
    def validate_integration(self, name: str, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate integration configuration.
        
        Args:
            name: Integration name
            config: Integration configuration
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation - can be extended per integration type
        required_fields = {
            "cloudflare": ["api_token", "account_id"],
            "mailerlite": ["api_key"],
            "github": ["token"],
            "slack": ["webhook_url"],
        }
        
        if name in required_fields:
            for field in required_fields[name]:
                if field not in config:
                    return False, f"Missing required field: {field}"
        
        return True, None
    
    def acquire_knowledge(self, name: str, target_type: str = "auto") -> Dict[str, Any]:
        """Acquire comprehensive knowledge about a service.
        
        Args:
            name: Service/tool name
            target_type: Type (cli, api, package, auto)
            
        Returns:
            Acquired knowledge
        """
        return self.knowledge.acquire_comprehensive_knowledge(name, target_type)
    
    def generate_plugin(self, 
                       name: str, 
                       output_path: Optional[Path] = None,
                       force_acquire: bool = False) -> Tuple[Path, Dict[str, Any]]:
        """Generate a plugin with full knowledge.
        
        Args:
            name: Service name
            output_path: Where to save plugin
            force_acquire: Force re-acquisition of knowledge
            
        Returns:
            Tuple of (plugin_path, knowledge)
        """
        # Generate plugin with knowledge
        plugin_code, knowledge = self.knowledge.generate_plugin_with_knowledge(
            name, force_acquire
        )
        
        # Determine output path
        if not output_path:
            output_path = Path(__file__).parent / "plugins" / f"{name}.py"
        
        # Write plugin
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plugin_code)
        
        # Add integration config if API
        if knowledge.get("api") and knowledge["api"].get("discovered"):
            api_config = {
                "type": "api",
                "base_url": knowledge["api"].get("base_url", ""),
                "auth_required": bool(knowledge["api"].get("auth_methods")),
                "endpoints_count": len(knowledge["api"].get("endpoints", [])),
                "discovered_from": knowledge["api"].get("method", "unknown")
            }
            self.add_integration(name, api_config)
        
        return output_path, knowledge
    
    def install_package(self, package_name: str, package_type: str = "auto") -> bool:
        """Install a package and acquire its knowledge.
        
        Args:
            package_name: Package to install
            package_type: Type (python, node, auto)
            
        Returns:
            Success status
        """
        # First acquire knowledge to determine type
        pkg_knowledge = self.knowledge.package.discover_package_knowledge(
            package_name, package_type
        )
        
        if not pkg_knowledge.get("discovered"):
            return False
        
        actual_type = pkg_knowledge.get("type", "python")
        
        # Install based on type
        try:
            if actual_type == "python":
                subprocess.run(
                    ["pip", "install", package_name],
                    check=True,
                    capture_output=True
                )
            elif actual_type == "node":
                subprocess.run(
                    ["npm", "install", "-g", package_name],
                    check=True,
                    capture_output=True
                )
            else:
                return False
                
            # Store package knowledge
            self.add_integration(package_name, {
                "type": "package",
                "package_type": actual_type,
                "version": pkg_knowledge["info"].get("version", ""),
                "cli_tools": pkg_knowledge.get("cli_tools", [])
            })
            
            return True
            
        except subprocess.CalledProcessError:
            return False
    
    def export_knowledge(self, output_path: Path):
        """Export all acquired knowledge.
        
        Args:
            output_path: Path to export file
        """
        self.knowledge.export_knowledge_base(output_path)
    
    def import_knowledge(self, input_path: Path) -> int:
        """Import knowledge from file.
        
        Args:
            input_path: Path to import file
            
        Returns:
            Number of entries imported
        """
        return self.knowledge.import_knowledge_base(input_path)
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about stored knowledge.
        
        Returns:
            Knowledge statistics
        """
        return self.knowledge.get_knowledge_stats()

# Singleton instance
_manager = None

def get_integration_manager() -> IntegrationManager:
    """Get the singleton integration manager instance."""
    global _manager
    if _manager is None:
        _manager = IntegrationManager()
    return _manager