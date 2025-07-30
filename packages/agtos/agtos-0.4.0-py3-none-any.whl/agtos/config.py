"""Configuration management for agtos.

This module handles configuration loading, validation, and persistence.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import os


def get_config_dir() -> Path:
    """Get the agtos configuration directory.
    
    Returns:
        Path to the configuration directory (~/.agtos)
    
    AI_CONTEXT: Returns the standard agtos config directory, creating it
    if it doesn't exist. Used by various modules for storing persistent data.
    """
    config_dir = Path.home() / ".agtos"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

class Config:
    """Configuration manager for agtos."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to config file. Defaults to ~/.agtos/config.yml
        """
        self.config_path = config_path or (Path.home() / ".agtos" / "config.yml")
        self._config = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._get_defaults()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "mcp_server": {
                "host": "localhost",
                "port": 3000
            },
            "credential_provider": os.getenv("AGTOS_CRED_PROVIDER", "keychain"),
            "plugins": {
                "enabled": True,
                "auto_discover": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save()
    
    def _save(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)