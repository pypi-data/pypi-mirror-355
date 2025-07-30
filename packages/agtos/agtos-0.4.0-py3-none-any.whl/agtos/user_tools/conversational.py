"""Conversational tool wrappers for cleaner interactions.

This module provides utilities to create simplified, conversational versions
of tools that accept presets and have smart defaults, reducing verbosity
in Claude's tool calls.

AI_CONTEXT:
    This solves the problem of verbose tool parameters by:
    - Creating preset-based wrappers (e.g., "top7" instead of listing coins)
    - Providing smart defaults for common use cases
    - Storing complex configurations that can be referenced by name
    - Creating higher-level abstraction tools
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationalWrapper:
    """Creates simplified, conversational versions of tools."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the conversational wrapper system.
        
        Args:
            config_dir: Directory to store presets and configs
        """
        self.config_dir = config_dir or Path.home() / ".agtos" / "tool_configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded presets
        self._presets_cache = {}
        self._configs_cache = {}
    
    def create_preset_tool(
        self,
        base_tool_name: str,
        wrapper_name: str,
        description: str,
        presets: Dict[str, Dict[str, Any]],
        default_preset: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a preset-based wrapper for an existing tool.
        
        Args:
            base_tool_name: Name of the tool to wrap
            wrapper_name: Name for the new wrapper tool
            description: User-friendly description
            presets: Dictionary of preset names to parameter configs
            default_preset: Default preset to use if none specified
            
        Returns:
            Tool configuration for the wrapper
        """
        # Save presets configuration
        preset_file = self.config_dir / f"{wrapper_name}_presets.json"
        preset_data = {
            "base_tool": base_tool_name,
            "presets": presets,
            "default": default_preset,
            "created_at": datetime.now().isoformat()
        }
        preset_file.write_text(json.dumps(preset_data, indent=2))
        
        # Generate wrapper function
        def preset_wrapper(preset: Optional[str] = None, **overrides) -> Dict[str, Any]:
            """Execute tool with preset configuration."""
            # Load presets
            if not preset and default_preset:
                preset = default_preset
            
            if preset:
                if preset not in presets:
                    available = ", ".join(presets.keys())
                    raise ValueError(f"Unknown preset '{preset}'. Available: {available}")
                
                # Get preset parameters
                params = presets[preset].copy()
            else:
                params = {}
            
            # Apply any overrides
            params.update(overrides)
            
            # Note: In real implementation, this would call the actual tool
            # For now, return the configuration that would be used
            return {
                "tool": base_tool_name,
                "parameters": params,
                "preset_used": preset
            }
        
        # Create tool schema for the wrapper
        schema = {
            "name": wrapper_name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "preset": {
                        "type": "string",
                        "description": f"Preset configuration to use: {', '.join(presets.keys())}",
                        "enum": list(presets.keys())
                    }
                },
                "required": []
            }
        }
        
        # Cache the preset configuration
        self._presets_cache[wrapper_name] = preset_data
        
        return {
            "schema": schema,
            "function": preset_wrapper,
            "config": preset_data
        }
    
    def create_smart_defaults_tool(
        self,
        base_tool_name: str,
        wrapper_name: str,
        description: str,
        defaults: Dict[str, Any],
        common_patterns: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a tool with smart defaults and common usage patterns.
        
        Args:
            base_tool_name: Name of the tool to wrap
            wrapper_name: Name for the new wrapper tool
            description: User-friendly description
            defaults: Default parameter values
            common_patterns: Named patterns for common use cases
            
        Returns:
            Tool configuration for the wrapper
        """
        # Save configuration
        config_file = self.config_dir / f"{wrapper_name}_config.json"
        config_data = {
            "base_tool": base_tool_name,
            "defaults": defaults,
            "patterns": common_patterns or {},
            "created_at": datetime.now().isoformat()
        }
        config_file.write_text(json.dumps(config_data, indent=2))
        
        # Generate wrapper function
        def smart_wrapper(pattern: Optional[str] = None, **params) -> Dict[str, Any]:
            """Execute tool with smart defaults."""
            # Start with defaults
            final_params = defaults.copy()
            
            # Apply pattern if specified
            if pattern and common_patterns and pattern in common_patterns:
                final_params.update(common_patterns[pattern])
            elif pattern:
                raise ValueError(f"Unknown pattern '{pattern}'")
            
            # Apply explicit parameters (override defaults and patterns)
            final_params.update(params)
            
            return {
                "tool": base_tool_name,
                "parameters": final_params,
                "pattern_used": pattern
            }
        
        # Create minimal schema
        schema = {
            "name": wrapper_name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Add pattern parameter if patterns exist
        if common_patterns:
            schema["inputSchema"]["properties"]["pattern"] = {
                "type": "string",
                "description": f"Common usage pattern: {', '.join(common_patterns.keys())}",
                "enum": list(common_patterns.keys())
            }
        
        return {
            "schema": schema,
            "function": smart_wrapper,
            "config": config_data
        }
    
    def create_config_reference_tool(
        self,
        base_tool_name: str,
        wrapper_name: str,
        description: str,
        config_type: str
    ) -> Dict[str, Any]:
        """Create a tool that references stored configurations.
        
        Args:
            base_tool_name: Name of the tool to wrap
            wrapper_name: Name for the new wrapper tool
            description: User-friendly description
            config_type: Type of configuration (e.g., 'api_list', 'watchlist')
            
        Returns:
            Tool configuration for the wrapper
        """
        # Create config storage directory
        config_type_dir = self.config_dir / config_type
        config_type_dir.mkdir(exist_ok=True)
        
        def config_wrapper(config_name: str, action: str = "use", **params) -> Dict[str, Any]:
            """Execute tool with named configuration."""
            config_file = config_type_dir / f"{config_name}.json"
            
            if action == "save":
                # Save a new configuration
                config_file.write_text(json.dumps(params, indent=2))
                return {
                    "status": "saved",
                    "config_name": config_name,
                    "config_type": config_type
                }
            
            elif action == "use":
                # Load and use configuration
                if not config_file.exists():
                    available = [f.stem for f in config_type_dir.glob("*.json")]
                    raise ValueError(f"Config '{config_name}' not found. Available: {', '.join(available)}")
                
                config_params = json.loads(config_file.read_text())
                config_params.update(params)  # Allow overrides
                
                return {
                    "tool": base_tool_name,
                    "parameters": config_params,
                    "config_used": config_name
                }
            
            elif action == "list":
                # List available configurations
                configs = [f.stem for f in config_type_dir.glob("*.json")]
                return {
                    "config_type": config_type,
                    "available_configs": configs
                }
            
            else:
                raise ValueError(f"Unknown action '{action}'. Use: save, use, or list")
        
        # Create schema
        schema = {
            "name": wrapper_name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "config_name": {
                        "type": "string",
                        "description": f"Name of the {config_type} configuration"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["use", "save", "list"],
                        "default": "use"
                    }
                },
                "required": ["config_name"]
            }
        }
        
        return {
            "schema": schema,
            "function": config_wrapper,
            "config_type": config_type
        }
    
    def create_abstraction_tool(
        self,
        tool_mappings: Dict[str, str],
        wrapper_name: str,
        description: str,
        intent_patterns: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Create a high-level abstraction tool that routes to specific tools.
        
        Args:
            tool_mappings: Map of intents to tool names
            wrapper_name: Name for the abstraction tool
            description: User-friendly description
            intent_patterns: Keywords/patterns for each intent
            
        Returns:
            Tool configuration for the abstraction
        """
        def abstraction_wrapper(intent: str, **params) -> Dict[str, Any]:
            """Route to appropriate tool based on intent."""
            # Find matching tool
            tool_name = tool_mappings.get(intent)
            
            if not tool_name:
                # Try pattern matching
                intent_lower = intent.lower()
                for mapped_intent, patterns in intent_patterns.items():
                    if any(pattern in intent_lower for pattern in patterns):
                        tool_name = tool_mappings.get(mapped_intent)
                        intent = mapped_intent
                        break
                
                if not tool_name:
                    available = ", ".join(tool_mappings.keys())
                    raise ValueError(f"Unknown intent '{intent}'. Available: {available}")
            
            return {
                "routed_to": tool_name,
                "intent": intent,
                "parameters": params
            }
        
        # Create schema
        schema = {
            "name": wrapper_name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": f"What you want to do: {', '.join(tool_mappings.keys())}"
                    }
                },
                "required": ["intent"]
            }
        }
        
        return {
            "schema": schema,
            "function": abstraction_wrapper,
            "mappings": tool_mappings,
            "patterns": intent_patterns
        }
    
    def suggest_wrapper_type(self, tool_info: Dict[str, Any]) -> str:
        """Suggest the best wrapper type for a tool based on its characteristics.
        
        Args:
            tool_info: Information about the tool
            
        Returns:
            Suggested wrapper type
        """
        params = tool_info.get("parameters", [])
        
        # Check for list/array parameters that could benefit from presets
        has_list_params = any(
            p.get("type") == "array" or "list" in p.get("description", "").lower()
            for p in params
        )
        
        # Check for many optional parameters that could use defaults
        optional_count = sum(1 for p in params if not p.get("required", False))
        
        # Check for complex nested parameters
        has_complex_params = any(p.get("type") == "object" for p in params)
        
        if has_list_params or "ids" in str(params).lower():
            return "preset"
        elif optional_count >= 3:
            return "smart_defaults"
        elif has_complex_params:
            return "config_reference"
        else:
            return "abstraction"
    
    def generate_wrapper_code(
        self,
        tool_name: str,
        wrapper_type: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate Python code for a conversational wrapper.
        
        Args:
            tool_name: Original tool name
            wrapper_type: Type of wrapper (preset, smart_defaults, etc.)
            config: Wrapper configuration
            
        Returns:
            Generated Python code
        """
        if wrapper_type == "preset":
            return self._generate_preset_wrapper_code(tool_name, config)
        elif wrapper_type == "smart_defaults":
            return self._generate_smart_defaults_code(tool_name, config)
        elif wrapper_type == "config_reference":
            return self._generate_config_reference_code(tool_name, config)
        elif wrapper_type == "abstraction":
            return self._generate_abstraction_code(tool_name, config)
        else:
            raise ValueError(f"Unknown wrapper type: {wrapper_type}")
    
    def _generate_preset_wrapper_code(self, tool_name: str, config: Dict[str, Any]) -> str:
        """Generate code for preset wrapper."""
        wrapper_name = config.get("wrapper_name", f"{tool_name}_simple")
        presets = config.get("presets", {})
        
        code = f'''"""Conversational wrapper for {tool_name}."""
from typing import Dict, Any, Optional
from agtos.user_tools.conversational import load_preset

def {wrapper_name}(preset: Optional[str] = None, **overrides) -> Dict[str, Any]:
    """Simplified {tool_name} with preset configurations.
    
    Presets available: {', '.join(presets.keys())}
    """
    params = load_preset("{wrapper_name}", preset)
    params.update(overrides)
    
    # Call the original tool
    from {tool_name} import execute as original_tool
    return original_tool(**params)

# Presets configuration
PRESETS = {json.dumps(presets, indent=4)}
'''
        return code
    
    def _generate_smart_defaults_code(self, tool_name: str, config: Dict[str, Any]) -> str:
        """Generate code for smart defaults wrapper."""
        wrapper_name = config.get("wrapper_name", f"{tool_name}_easy")
        defaults = config.get("defaults", {})
        
        code = f'''"""Smart defaults wrapper for {tool_name}."""
from typing import Dict, Any, Optional

# Default values for common use
DEFAULTS = {json.dumps(defaults, indent=4)}

def {wrapper_name}(**params) -> Dict[str, Any]:
    """Simplified {tool_name} with smart defaults.
    
    All parameters are optional - sensible defaults are provided.
    """
    # Start with defaults
    final_params = DEFAULTS.copy()
    
    # Apply user parameters
    final_params.update(params)
    
    # Call the original tool
    from {tool_name} import execute as original_tool
    return original_tool(**final_params)
'''
        return code
    
    def _generate_config_reference_code(self, tool_name: str, config: Dict[str, Any]) -> str:
        """Generate code for config reference wrapper."""
        wrapper_name = config.get("wrapper_name", f"{tool_name}_config")
        config_type = config.get("config_type", "config")
        
        code = f'''"""Configuration-based wrapper for {tool_name}."""
from typing import Dict, Any
from agtos.user_tools.conversational import load_config, save_config

def {wrapper_name}(config_name: str, action: str = "use", **params) -> Dict[str, Any]:
    """Use {tool_name} with saved configurations.
    
    Actions:
    - use: Load and use a saved configuration
    - save: Save current parameters as a configuration
    - list: List available configurations
    """
    if action == "save":
        return save_config("{config_type}", config_name, params)
    elif action == "list":
        return list_configs("{config_type}")
    else:  # use
        config_params = load_config("{config_type}", config_name)
        config_params.update(params)
        
        # Call the original tool
        from {tool_name} import execute as original_tool
        return original_tool(**config_params)
'''
        return code
    
    def _generate_abstraction_code(self, tool_name: str, config: Dict[str, Any]) -> str:
        """Generate code for abstraction wrapper."""
        wrapper_name = config.get("wrapper_name", f"{tool_name}_helper")
        mappings = config.get("mappings", {})
        
        code = f'''"""High-level abstraction for multiple tools."""
from typing import Dict, Any

# Intent to tool mappings
TOOL_MAPPINGS = {json.dumps(mappings, indent=4)}

def {wrapper_name}(intent: str, **params) -> Dict[str, Any]:
    """High-level interface for common tasks.
    
    Intents: {', '.join(mappings.keys())}
    """
    tool_name = TOOL_MAPPINGS.get(intent)
    if not tool_name:
        raise ValueError(f"Unknown intent '{{intent}}'. Available: {{', '.join(TOOL_MAPPINGS.keys())}}")
    
    # Import and call the appropriate tool
    tool_module = __import__(tool_name, fromlist=['execute'])
    return tool_module.execute(**params)
'''
        return code


# Helper functions for generated code
def load_preset(wrapper_name: str, preset: Optional[str] = None) -> Dict[str, Any]:
    """Load preset configuration for a wrapper."""
    config_dir = Path.home() / ".agtos" / "tool_configs"
    preset_file = config_dir / f"{wrapper_name}_presets.json"
    
    if not preset_file.exists():
        raise ValueError(f"No presets found for {wrapper_name}")
    
    data = json.loads(preset_file.read_text())
    presets = data.get("presets", {})
    
    if not preset:
        preset = data.get("default")
    
    if preset and preset in presets:
        return presets[preset].copy()
    elif preset:
        raise ValueError(f"Unknown preset '{preset}'")
    else:
        return {}


def load_config(config_type: str, config_name: str) -> Dict[str, Any]:
    """Load a saved configuration."""
    config_dir = Path.home() / ".agtos" / "tool_configs" / config_type
    config_file = config_dir / f"{config_name}.json"
    
    if not config_file.exists():
        raise ValueError(f"Config '{config_name}' not found")
    
    return json.loads(config_file.read_text())


def save_config(config_type: str, config_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Save a configuration."""
    config_dir = Path.home() / ".agtos" / "tool_configs" / config_type
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / f"{config_name}.json"
    config_file.write_text(json.dumps(params, indent=2))
    
    return {
        "status": "saved",
        "config_type": config_type,
        "config_name": config_name
    }


def list_configs(config_type: str) -> Dict[str, Any]:
    """List available configurations."""
    config_dir = Path.home() / ".agtos" / "tool_configs" / config_type
    
    if not config_dir.exists():
        return {"configs": [], "config_type": config_type}
    
    configs = [f.stem for f in config_dir.glob("*.json")]
    return {
        "configs": configs,
        "config_type": config_type,
        "total": len(configs)
    }