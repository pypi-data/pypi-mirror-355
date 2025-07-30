"""Ephemeral tool creator plugin for natural, on-the-fly tool generation.

This plugin allows Claude to create temporary tools with natural names that:
- Match exactly what the user asked for
- Don't accumulate in the file system
- Auto-expire after use or time
- Can be persisted if the user likes them

AI_CONTEXT:
    This plugin revolutionizes tool creation by making it ephemeral and natural:
    - User: "Check the top 7 cryptocurrencies"
    - Claude creates: check_top_7_cryptocurrencies() 
    - Tool exists only as long as needed
    - No permanent storage unless requested
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from agtos.user_tools.ephemeral import (
    get_ephemeral_manager,
    create_natural_tool,
    execute_natural_tool
)
from agtos.user_tools.inspector import ToolInspector
from agtos.user_tools.formatter import ToolCreationFormatter

logger = logging.getLogger(__name__)


def create_ephemeral_tool_from_intent(
    intent: str,
    base_tool: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    ttl_seconds: int = 300,
    single_use: bool = False
) -> Dict[str, Any]:
    """Create an ephemeral tool based on natural language intent.
    
    This is the main function Claude uses to create tools on-the-fly
    with names that match exactly what the user asked for.
    
    Args:
        intent: What the user wants (e.g., "check top 7 cryptocurrencies")
        base_tool: The underlying tool to use (auto-detected if not provided)
        parameters: Parameters to bind (auto-extracted if not provided)
        ttl_seconds: How long the tool lives (default 5 minutes)
        single_use: If True, tool expires after one use
        
    Returns:
        Result with the natural tool name and how to use it
    """
    formatter = ToolCreationFormatter()
    
    try:
        # Auto-detect base tool if not provided
        if not base_tool:
            base_tool = _detect_base_tool(intent)
            if not base_tool:
                return {
                    "success": False,
                    "message": "❌ Could not determine which tool to use. Please specify the base_tool."
                }
        
        # Auto-extract parameters if not provided
        if parameters is None:
            parameters = _extract_parameters_from_intent(intent, base_tool)
        
        # Create natural tool name from intent
        natural_name = _intent_to_natural_name(intent)
        
        # Create the ephemeral tool
        tool_id = create_natural_tool(
            user_intent=intent,
            base_tool=base_tool,
            parameters=parameters,
            ttl_seconds=ttl_seconds,
            single_use=single_use
        )
        
        # Generate usage example
        usage_example = f"{natural_name}()"
        if single_use:
            usage_example += "  # Single use only!"
        
        message = f"""✨ Created ephemeral tool: {natural_name}

🎯 Intent: "{intent}"
🔧 Base Tool: {base_tool}
📦 Bound Parameters: {_format_parameters(parameters)}
⏱️  Expires: {ttl_seconds}s after creation{' or after 1 use' if single_use else ''}

Usage:
```python
{usage_example}
```

This tool will automatically clean up when expired.
To keep it permanently, use: ephemeral_persist("{natural_name}")"""
        
        return {
            "success": True,
            "message": message,
            "tool_name": natural_name,
            "ephemeral": True,
            "ttl": ttl_seconds
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to create ephemeral tool: {str(e)}"
        }


def create_ephemeral_preset(
    preset_name: str,
    base_tool: str,
    preset_config: Dict[str, Any],
    ttl_seconds: int = 300
) -> Dict[str, Any]:
    """Create an ephemeral preset tool with a natural name.
    
    This creates tools like:
    - get_top_7_cryptos()
    - check_stablecoins()
    - analyze_defi_tokens()
    
    Args:
        preset_name: Natural name for the preset (e.g., "top 7 cryptos")
        base_tool: The underlying tool
        preset_config: Configuration to bind
        ttl_seconds: Lifetime of the tool
        
    Returns:
        Result with the ephemeral tool info
    """
    # Convert to natural function name
    natural_name = _preset_to_natural_name(preset_name, base_tool)
    
    try:
        tool_id = create_natural_tool(
            user_intent=natural_name,
            base_tool=base_tool,
            parameters=preset_config,
            ttl_seconds=ttl_seconds,
            single_use=False
        )
        
        message = f"""✨ Created ephemeral preset: {natural_name}

🎯 Preset: "{preset_name}"
🔧 Base Tool: {base_tool}
⏱️  Expires: {ttl_seconds}s after creation

Usage:
```python
{natural_name}()
```"""
        
        return {
            "success": True,
            "message": message,
            "tool_name": natural_name,
            "preset": preset_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to create preset: {str(e)}"
        }


def execute_ephemeral(
    tool_name: str,
    **kwargs
) -> Dict[str, Any]:
    """Execute an ephemeral tool by its natural name.
    
    Args:
        tool_name: Natural name of the tool
        **kwargs: Additional parameters to pass
        
    Returns:
        Execution result
    """
    try:
        result = execute_natural_tool(tool_name, **kwargs)
        
        # Check if tool expired after use
        if result.get("expired"):
            logger.info(f"Ephemeral tool '{tool_name}' expired after use")
        
        return {
            "success": True,
            "result": result,
            "tool": tool_name
        }
        
    except ValueError as e:
        return {
            "success": False,
            "message": f"❌ {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Execution failed: {str(e)}"
        }


def list_ephemeral_tools() -> Dict[str, Any]:
    """List all active ephemeral tools.
    
    Returns:
        List of active ephemeral tools with their status
    """
    manager = get_ephemeral_manager()
    active_tools = manager.list_active_tools()
    
    if not active_tools:
        return {
            "success": True,
            "message": "No active ephemeral tools.",
            "tools": []
        }
    
    message_parts = [f"🌟 Active Ephemeral Tools ({len(active_tools)} total)", ""]
    
    for name, info in active_tools.items():
        message_parts.append(f"📦 {name}")
        message_parts.append(f"   Base: {info['base_tool']}")
        message_parts.append(f"   Expires in: {info['expires_in']}s")
        message_parts.append(f"   Usage: {info['usage']}")
        message_parts.append("")
    
    return {
        "success": True,
        "message": "\n".join(message_parts),
        "tools": active_tools
    }


def persist_ephemeral_tool(
    ephemeral_name: str,
    permanent_name: Optional[str] = None
) -> Dict[str, Any]:
    """Convert an ephemeral tool to a permanent tool.
    
    Args:
        ephemeral_name: Name of the ephemeral tool
        permanent_name: New name for permanent version (optional)
        
    Returns:
        Result with permanent tool location
    """
    manager = get_ephemeral_manager()
    
    try:
        permanent_file = manager.persist_ephemeral_tool(ephemeral_name, permanent_name)
        final_name = permanent_name or ephemeral_name
        
        message = f"""✅ Persisted ephemeral tool as permanent tool!

🌟 Ephemeral: {ephemeral_name}
💾 Permanent: {final_name}
📁 Location: {permanent_file}

The tool is now permanently available and won't expire."""
        
        return {
            "success": True,
            "message": message,
            "permanent_name": final_name,
            "file_path": str(permanent_file)
        }
        
    except ValueError as e:
        return {
            "success": False,
            "message": f"❌ {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to persist tool: {str(e)}"
        }


def cleanup_ephemeral_tools() -> Dict[str, Any]:
    """Manually trigger cleanup of expired ephemeral tools.
    
    Returns:
        Number of tools cleaned up
    """
    manager = get_ephemeral_manager()
    cleaned = manager.cleanup_expired()
    
    return {
        "success": True,
        "message": f"🧹 Cleaned up {cleaned} expired ephemeral tools.",
        "cleaned_count": cleaned
    }


# Helper functions

def _detect_base_tool(intent: str) -> Optional[str]:
    """Auto-detect the base tool from user intent."""
    intent_lower = intent.lower()
    
    # Common patterns
    patterns = {
        "crypto": ["coingecko", "crypto", "coin"],
        "weather": ["weather", "temperature", "forecast"],
        "github": ["github", "repo", "repository", "pr", "issue"],
        "file": ["file", "read", "write", "create"],
        "web": ["web", "url", "website", "fetch"],
    }
    
    # Check patterns
    for tool_category, keywords in patterns.items():
        if any(keyword in intent_lower for keyword in keywords):
            # Try to find matching tool
            inspector = ToolInspector()
            all_tools = inspector.list_all_tools()
            
            for tool_name in all_tools.get("tools", []):
                if tool_category in tool_name.lower():
                    return tool_name
    
    return None


def _extract_parameters_from_intent(intent: str, base_tool: str) -> Dict[str, Any]:
    """Extract parameters from natural language intent."""
    # This is a simplified version - in production would use NLP
    params = {}
    
    # Extract numbers
    import re
    numbers = re.findall(r'\d+', intent)
    
    # Common parameter patterns
    if "top" in intent.lower() and numbers:
        params["limit"] = int(numbers[0])
    
    if "crypto" in intent.lower():
        # Extract specific coins mentioned
        coins = ["bitcoin", "ethereum", "cardano", "solana", "dogecoin"]
        mentioned = [coin for coin in coins if coin in intent.lower()]
        if mentioned:
            params["ids"] = ",".join(mentioned)
        elif "top" in intent.lower() and numbers:
            # Default top N coins
            n = int(numbers[0])
            default_coins = ["bitcoin", "ethereum", "binance-coin", "ripple", 
                           "cardano", "solana", "polkadot", "dogecoin", 
                           "avalanche", "chainlink"]
            params["ids"] = ",".join(default_coins[:n])
    
    return params


def _intent_to_natural_name(intent: str) -> str:
    """Convert user intent to a natural function name."""
    # Clean and convert to snake_case
    # "Check the top 7 cryptocurrencies" -> "check_the_top_7_cryptocurrencies"
    name = intent.lower()
    
    # Remove common words that don't add value
    skip_words = ["the", "a", "an", "please", "can", "you"]
    words = name.split()
    words = [w for w in words if w not in skip_words]
    
    # Join with underscores
    name = "_".join(words)
    
    # Clean up
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    
    return name


def _preset_to_natural_name(preset_name: str, base_tool: str) -> str:
    """Convert preset name to natural function name."""
    # "top 7 cryptos" -> "get_top_7_cryptos"
    
    # Determine action verb based on tool
    if "price" in base_tool.lower() or "crypto" in base_tool.lower():
        verb = "get"
    elif "weather" in base_tool.lower():
        verb = "check"
    elif "file" in base_tool.lower():
        verb = "read"
    else:
        verb = "execute"
    
    # Clean preset name
    cleaned = preset_name.lower().replace(" ", "_")
    
    return f"{verb}_{cleaned}"


def _format_parameters(params: Dict[str, Any]) -> str:
    """Format parameters for display."""
    if not params:
        return "none"
    
    parts = []
    for key, value in params.items():
        if isinstance(value, str) and len(value) > 50:
            if ',' in value:
                count = len(value.split(','))
                parts.append(f"{key}={count} items")
            else:
                parts.append(f"{key}=<truncated>")
        else:
            parts.append(f"{key}={value}")
    
    return ", ".join(parts)


# Plugin registration
def get_ephemeral_creator_tools() -> Dict[str, Dict[str, Any]]:
    """Get ephemeral creator tools for the plugin system."""
    return {
        "ephemeral_create": {
            "description": "Create an ephemeral tool with natural naming from user intent",
            "schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "What the user wants (e.g., 'check top 7 cryptocurrencies')"
                    },
                    "base_tool": {
                        "type": "string",
                        "description": "The underlying tool to use (auto-detected if not provided)"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters to bind to the tool"
                    },
                    "ttl_seconds": {
                        "type": "integer",
                        "description": "How long the tool should live in seconds",
                        "default": 300
                    },
                    "single_use": {
                        "type": "boolean",
                        "description": "If true, tool expires after one use",
                        "default": False
                    }
                },
                "required": ["intent"]
            },
            "func": create_ephemeral_tool_from_intent
        },
        "ephemeral_preset": {
            "description": "Create an ephemeral preset tool with natural naming",
            "schema": {
                "type": "object",
                "properties": {
                    "preset_name": {
                        "type": "string",
                        "description": "Natural name for the preset (e.g., 'top 7 cryptos')"
                    },
                    "base_tool": {
                        "type": "string",
                        "description": "The underlying tool to wrap"
                    },
                    "preset_config": {
                        "type": "object",
                        "description": "Configuration to bind to the preset"
                    },
                    "ttl_seconds": {
                        "type": "integer",
                        "description": "Lifetime of the tool in seconds",
                        "default": 300
                    }
                },
                "required": ["preset_name", "base_tool", "preset_config"]
            },
            "func": create_ephemeral_preset
        },
        "ephemeral_execute": {
            "description": "Execute an ephemeral tool by its natural name",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Natural name of the ephemeral tool"
                    }
                },
                "required": ["tool_name"],
                "additionalProperties": True
            },
            "func": execute_ephemeral
        },
        "ephemeral_list": {
            "description": "List all active ephemeral tools",
            "schema": {
                "type": "object",
                "properties": {}
            },
            "func": list_ephemeral_tools
        },
        "ephemeral_persist": {
            "description": "Convert an ephemeral tool to a permanent tool",
            "schema": {
                "type": "object",
                "properties": {
                    "ephemeral_name": {
                        "type": "string",
                        "description": "Name of the ephemeral tool to persist"
                    },
                    "permanent_name": {
                        "type": "string",
                        "description": "New name for the permanent tool (optional)"
                    }
                },
                "required": ["ephemeral_name"]
            },
            "func": persist_ephemeral_tool
        },
        "ephemeral_cleanup": {
            "description": "Manually cleanup expired ephemeral tools",
            "schema": {
                "type": "object",
                "properties": {}
            },
            "func": cleanup_ephemeral_tools
        }
    }