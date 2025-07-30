"""Tool simplifier plugin for creating conversational wrappers.

This plugin allows users to create simplified, conversational versions
of existing tools with presets, smart defaults, and other patterns
to reduce verbosity in tool calls.

AI_CONTEXT:
    This plugin addresses the verbosity issue by allowing users to create
    wrapper tools that accept simple parameters like "top7" instead of
    listing all values explicitly.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from agtos.user_tools.conversational import ConversationalWrapper
from agtos.user_tools.inspector import ToolInspector
from agtos.user_tools.formatter import ToolCreationFormatter

logger = logging.getLogger(__name__)


def create_conversational_wrapper(
    tool_name: str,
    wrapper_type: str,
    wrapper_name: Optional[str] = None,
    description: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a conversational wrapper for an existing tool.
    
    Args:
        tool_name: Name of the tool to wrap
        wrapper_type: Type of wrapper (preset, smart_defaults, config_reference, abstraction)
        wrapper_name: Name for the wrapper (auto-generated if not provided)
        description: Description for the wrapper
        config: Configuration for the wrapper type
        
    Returns:
        Result with wrapper creation status
    """
    formatter = ToolCreationFormatter()
    wrapper = ConversationalWrapper()
    
    try:
        # Inspect the original tool
        inspector = ToolInspector()
        tool_info = inspector.inspect_tool(tool_name)
        
        if not tool_info.get("success"):
            return {
                "success": False,
                "message": f"❌ Tool '{tool_name}' not found. Use tool_creator_list_all to see available tools."
            }
        
        # Auto-generate wrapper name if not provided
        if not wrapper_name:
            wrapper_name = f"{tool_name}_{wrapper_type}"
        
        # Auto-generate description if not provided
        if not description:
            original_desc = tool_info.get("description", "")
            description = f"Simplified version of {tool_name}: {original_desc}"
        
        # Create wrapper based on type
        if wrapper_type == "preset":
            result = _create_preset_wrapper(tool_name, wrapper_name, description, config, wrapper)
        elif wrapper_type == "smart_defaults":
            result = _create_smart_defaults_wrapper(tool_name, wrapper_name, description, config, wrapper)
        elif wrapper_type == "config_reference":
            result = _create_config_reference_wrapper(tool_name, wrapper_name, description, config, wrapper)
        elif wrapper_type == "abstraction":
            result = _create_abstraction_wrapper(tool_name, wrapper_name, description, config, wrapper)
        else:
            return {
                "success": False,
                "message": f"❌ Unknown wrapper type '{wrapper_type}'. Available: preset, smart_defaults, config_reference, abstraction"
            }
        
        # Generate and save the wrapper code
        code = wrapper.generate_wrapper_code(tool_name, wrapper_type, result["config"])
        
        # Save wrapper as a user tool
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        user_tools_dir.mkdir(parents=True, exist_ok=True)
        
        wrapper_file = user_tools_dir / f"{wrapper_name}.py"
        wrapper_file.write_text(code)
        
        # Format success message
        success_msg = f"""✅ Created conversational wrapper: {wrapper_name}

🎯 Wrapper Type: {wrapper_type}
📝 Description: {description}

✨ The wrapper is now available for use!"""

        if wrapper_type == "preset" and result["config"].get("presets"):
            presets = result["config"]["presets"]
            success_msg += f"\n\n📋 Available Presets:"
            for name, params in presets.items():
                success_msg += f"\n  • {name}: {_summarize_params(params)}"
        
        return {
            "success": True,
            "message": success_msg,
            "wrapper_name": wrapper_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to create wrapper: {str(e)}"
        }


def create_crypto_preset_example() -> Dict[str, Any]:
    """Create an example preset wrapper for cryptocurrency tools.
    
    This demonstrates how to create a tool that accepts "top7" instead
    of listing all cryptocurrencies.
    
    Returns:
        Result of wrapper creation
    """
    config = {
        "presets": {
            "top7": {
                "ids": "bitcoin,ethereum,binance-coin,ripple,cardano,solana,polkadot"
            },
            "top10": {
                "ids": "bitcoin,ethereum,binance-coin,ripple,cardano,solana,polkadot,dogecoin,avalanche,chainlink"
            },
            "stablecoins": {
                "ids": "tether,usd-coin,binance-usd,dai,frax"
            },
            "defi": {
                "ids": "uniswap,aave,compound,maker,curve-dao,1inch"
            },
            "layer2": {
                "ids": "polygon,arbitrum,optimism,immutable-x,loopring"
            }
        },
        "default_preset": "top7"
    }
    
    return create_conversational_wrapper(
        tool_name="coingecko_prices",  # Assuming this tool exists
        wrapper_type="preset",
        wrapper_name="crypto_quick",
        description="Quick cryptocurrency price checks with preset lists",
        config=config
    )


def suggest_wrapper_for_tool(tool_name: str) -> Dict[str, Any]:
    """Analyze a tool and suggest the best wrapper type.
    
    Args:
        tool_name: Name of the tool to analyze
        
    Returns:
        Suggestion with wrapper type and configuration
    """
    formatter = ToolCreationFormatter()
    wrapper = ConversationalWrapper()
    
    try:
        # Inspect the tool
        inspector = ToolInspector()
        tool_info = inspector.inspect_tool(tool_name)
        
        if not tool_info.get("success"):
            return {
                "success": False,
                "message": f"❌ Tool '{tool_name}' not found."
            }
        
        # Get suggestion
        suggested_type = wrapper.suggest_wrapper_type(tool_info)
        
        # Generate example configuration based on type
        example_config = _generate_example_config(suggested_type, tool_info)
        
        message = f"""💡 Wrapper Suggestion for '{tool_name}'

📊 Analysis:
  • Parameters: {len(tool_info.get('parameters', []))} total
  • Required: {sum(1 for p in tool_info.get('parameters', []) if p.get('required'))}
  • Optional: {sum(1 for p in tool_info.get('parameters', []) if not p.get('required'))}

🎯 Recommended Wrapper Type: {suggested_type}

📝 Reasoning: {_get_suggestion_reasoning(suggested_type, tool_info)}

Example configuration:
```python
{json.dumps(example_config, indent=2)}
```

To create this wrapper, use:
tool_simplifier_create with wrapper_type="{suggested_type}" and the configuration above."""
        
        return {
            "success": True,
            "message": message,
            "suggested_type": suggested_type,
            "example_config": example_config
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to analyze tool: {str(e)}"
        }


def list_conversational_wrappers() -> Dict[str, Any]:
    """List all conversational wrappers that have been created.
    
    Returns:
        List of wrappers with their configurations
    """
    config_dir = Path.home() / ".agtos" / "tool_configs"
    
    if not config_dir.exists():
        return {
            "success": True,
            "message": "No conversational wrappers found yet.",
            "wrappers": []
        }
    
    wrappers = []
    
    # Check for preset wrappers
    for preset_file in config_dir.glob("*_presets.json"):
        data = json.loads(preset_file.read_text())
        wrapper_name = preset_file.stem.replace("_presets", "")
        wrappers.append({
            "name": wrapper_name,
            "type": "preset",
            "base_tool": data.get("base_tool"),
            "presets": list(data.get("presets", {}).keys()),
            "created": data.get("created_at")
        })
    
    # Check for config wrappers
    for config_file in config_dir.glob("*_config.json"):
        data = json.loads(config_file.read_text())
        wrapper_name = config_file.stem.replace("_config", "")
        wrappers.append({
            "name": wrapper_name,
            "type": "smart_defaults",
            "base_tool": data.get("base_tool"),
            "defaults_count": len(data.get("defaults", {})),
            "created": data.get("created_at")
        })
    
    message_parts = [f"🎭 Conversational Wrappers ({len(wrappers)} total)"]
    
    if wrappers:
        message_parts.append("")
        for wrapper in wrappers:
            message_parts.append(f"📦 {wrapper['name']} ({wrapper['type']})")
            message_parts.append(f"   Base tool: {wrapper['base_tool']}")
            if wrapper['type'] == 'preset':
                message_parts.append(f"   Presets: {', '.join(wrapper['presets'])}")
            message_parts.append("")
    
    return {
        "success": True,
        "message": "\n".join(message_parts),
        "wrappers": wrappers,
        "total": len(wrappers)
    }


# Helper functions

def _create_preset_wrapper(
    tool_name: str,
    wrapper_name: str,
    description: str,
    config: Optional[Dict[str, Any]],
    wrapper: ConversationalWrapper
) -> Dict[str, Any]:
    """Create a preset-based wrapper."""
    if not config or "presets" not in config:
        raise ValueError("Preset wrapper requires 'presets' in config")
    
    presets = config["presets"]
    default_preset = config.get("default_preset")
    
    result = wrapper.create_preset_tool(
        base_tool_name=tool_name,
        wrapper_name=wrapper_name,
        description=description,
        presets=presets,
        default_preset=default_preset
    )
    
    return result


def _create_smart_defaults_wrapper(
    tool_name: str,
    wrapper_name: str,
    description: str,
    config: Optional[Dict[str, Any]],
    wrapper: ConversationalWrapper
) -> Dict[str, Any]:
    """Create a smart defaults wrapper."""
    if not config or "defaults" not in config:
        raise ValueError("Smart defaults wrapper requires 'defaults' in config")
    
    defaults = config["defaults"]
    patterns = config.get("patterns")
    
    result = wrapper.create_smart_defaults_tool(
        base_tool_name=tool_name,
        wrapper_name=wrapper_name,
        description=description,
        defaults=defaults,
        common_patterns=patterns
    )
    
    return result


def _create_config_reference_wrapper(
    tool_name: str,
    wrapper_name: str,
    description: str,
    config: Optional[Dict[str, Any]],
    wrapper: ConversationalWrapper
) -> Dict[str, Any]:
    """Create a config reference wrapper."""
    if not config or "config_type" not in config:
        config = {"config_type": f"{tool_name}_configs"}
    
    result = wrapper.create_config_reference_tool(
        base_tool_name=tool_name,
        wrapper_name=wrapper_name,
        description=description,
        config_type=config["config_type"]
    )
    
    return result


def _create_abstraction_wrapper(
    tool_name: str,
    wrapper_name: str,
    description: str,
    config: Optional[Dict[str, Any]],
    wrapper: ConversationalWrapper
) -> Dict[str, Any]:
    """Create an abstraction wrapper."""
    if not config or "mappings" not in config:
        raise ValueError("Abstraction wrapper requires 'mappings' in config")
    
    mappings = config["mappings"]
    patterns = config.get("patterns", {})
    
    result = wrapper.create_abstraction_tool(
        tool_mappings=mappings,
        wrapper_name=wrapper_name,
        description=description,
        intent_patterns=patterns
    )
    
    return result


def _summarize_params(params: Dict[str, Any]) -> str:
    """Create a short summary of parameters."""
    if not params:
        return "no parameters"
    
    # For long values, show abbreviated version
    summary_parts = []
    for key, value in params.items():
        if isinstance(value, str) and len(value) > 50:
            # Count items if comma-separated
            if ',' in value:
                count = len(value.split(','))
                summary_parts.append(f"{key}={count} items")
            else:
                summary_parts.append(f"{key}=...")
        else:
            summary_parts.append(f"{key}={value}")
    
    return ", ".join(summary_parts[:3])  # Show first 3


def _generate_example_config(wrapper_type: str, tool_info: Dict[str, Any]) -> Dict[str, Any]:
    """Generate example configuration for a wrapper type."""
    if wrapper_type == "preset":
        # Look for array/list parameters
        list_params = [
            p for p in tool_info.get("parameters", [])
            if p.get("type") == "array" or "list" in str(p.get("description", "")).lower()
        ]
        
        if list_params:
            param_name = list_params[0]["name"]
            return {
                "presets": {
                    "common": {param_name: "value1,value2,value3"},
                    "extended": {param_name: "value1,value2,value3,value4,value5"},
                    "minimal": {param_name: "value1"}
                },
                "default_preset": "common"
            }
    
    elif wrapper_type == "smart_defaults":
        # Get all optional parameters
        optional_params = [
            p for p in tool_info.get("parameters", [])
            if not p.get("required", False)
        ]
        
        defaults = {}
        for param in optional_params[:3]:  # First 3 optional params
            param_type = param.get("type", "string")
            if param_type == "boolean":
                defaults[param["name"]] = True
            elif param_type == "number":
                defaults[param["name"]] = 100
            else:
                defaults[param["name"]] = "default_value"
        
        return {
            "defaults": defaults,
            "patterns": {
                "quick": {"limit": 10},
                "full": {"limit": 100, "detailed": True}
            }
        }
    
    elif wrapper_type == "config_reference":
        return {
            "config_type": f"{tool_info.get('tool_name', 'tool')}_configs"
        }
    
    else:  # abstraction
        return {
            "mappings": {
                "check": tool_info.get("tool_name", "tool"),
                "update": f"{tool_info.get('tool_name', 'tool')}_update",
                "list": f"{tool_info.get('tool_name', 'tool')}_list"
            },
            "patterns": {
                "check": ["status", "get", "fetch"],
                "update": ["modify", "change", "set"],
                "list": ["all", "show", "display"]
            }
        }
    
    return {}


def _get_suggestion_reasoning(wrapper_type: str, tool_info: Dict[str, Any]) -> str:
    """Get reasoning for wrapper type suggestion."""
    if wrapper_type == "preset":
        return "This tool has parameters that accept lists or multiple values. Presets will allow using simple names like 'top10' instead of listing all values."
    
    elif wrapper_type == "smart_defaults":
        return "This tool has many optional parameters. Smart defaults will provide sensible values automatically, making the tool easier to use."
    
    elif wrapper_type == "config_reference":
        return "This tool has complex nested parameters. Config references allow saving and reusing complete configurations by name."
    
    else:  # abstraction
        return "This tool could benefit from a higher-level interface that simplifies common operations into simple intents."


# Plugin registration
def get_tool_simplifier_tools() -> Dict[str, Dict[str, Any]]:
    """Get tool simplifier tools for the plugin system."""
    return {
        "tool_simplifier_create": {
            "description": "Create a conversational wrapper for an existing tool to reduce verbosity",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to wrap"
                    },
                    "wrapper_type": {
                        "type": "string",
                        "description": "Type of wrapper to create",
                        "enum": ["preset", "smart_defaults", "config_reference", "abstraction"]
                    },
                    "wrapper_name": {
                        "type": "string",
                        "description": "Name for the wrapper (auto-generated if not provided)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description for the wrapper"
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration specific to the wrapper type"
                    }
                },
                "required": ["tool_name", "wrapper_type"]
            },
            "func": create_conversational_wrapper
        },
        "tool_simplifier_suggest": {
            "description": "Analyze a tool and suggest the best wrapper type to reduce verbosity",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to analyze"
                    }
                },
                "required": ["tool_name"]
            },
            "func": suggest_wrapper_for_tool
        },
        "tool_simplifier_list": {
            "description": "List all conversational wrappers that have been created",
            "schema": {
                "type": "object",
                "properties": {}
            },
            "func": list_conversational_wrappers
        },
        "tool_simplifier_crypto_example": {
            "description": "Create an example cryptocurrency preset wrapper demonstrating the 'top7' pattern",
            "schema": {
                "type": "object",
                "properties": {}
            },
            "func": create_crypto_preset_example
        }
    }