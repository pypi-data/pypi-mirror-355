"""Natural language tool creator plugin.

This enhanced version of the tool creator automatically generates tools
with natural, readable names based on user intent.
"""

from typing import Dict, Any, Optional
from agtos.plugins.tool_creator import create_tool_from_description
from agtos.user_tools.natural_naming import NaturalNamer
from agtos.user_tools.ephemeral import create_natural_tool, get_ephemeral_manager
import logging

logger = logging.getLogger(__name__)


def create_natural_tool_from_description(
    description: str,
    naming_style: str = "conversational",
    ephemeral: bool = False,
    ttl_seconds: int = 300,
    **kwargs
) -> Dict[str, Any]:
    """Create a tool with natural naming from description.
    
    This is an enhanced version of create_tool_from_description that
    automatically generates natural, readable tool names.
    
    Args:
        description: Natural language description of the tool
        naming_style: Style for naming - "conversational", "narrative", or "action"
        ephemeral: If True, create an ephemeral tool that auto-expires
        ttl_seconds: Time to live for ephemeral tools
        **kwargs: Additional arguments passed to create_tool_from_description
        
    Returns:
        Tool creation result with natural naming
    """
    # Extract intent and create natural name
    namer = NaturalNamer(naming_style)
    
    # First create the tool normally
    result = create_tool_from_description(description, **kwargs)
    
    if result.get("success", False):
        # Extract the generated tool name and enhance it
        original_name = result.get("tool_name", "")
        tool_spec = result.get("tool_spec", {})
        
        # Create natural name based on description
        natural_name = namer.create_natural_name(description)
        
        if ephemeral:
            # Create as ephemeral tool
            manager = get_ephemeral_manager()
            ephemeral_name = create_natural_tool(
                user_intent=description,
                base_tool=original_name,
                parameters={},  # Default params, can be overridden
                ttl_seconds=ttl_seconds
            )
            
            result["tool_name"] = ephemeral_name
            result["ephemeral"] = True
            result["expires_in"] = ttl_seconds
            result["message"] = f"✅ Created ephemeral tool: {ephemeral_name}"
        else:
            # Update the tool spec with natural name
            result["tool_name"] = natural_name
            result["natural_name"] = natural_name
            result["original_name"] = original_name
            
            # Update the generated code to use natural name
            if "code" in result:
                result["code"] = result["code"].replace(
                    f"def {original_name}",
                    f"def {natural_name}"
                ).replace(
                    f'"name": "{original_name}"',
                    f'"name": "{natural_name}"'
                )
            
            result["message"] = f"✅ Created tool with natural name: {natural_name}"
    
    return result


def suggest_tool_names(
    description: str,
    count: int = 5
) -> Dict[str, Any]:
    """Suggest multiple natural names for a tool based on description.
    
    Args:
        description: Natural language description
        count: Number of suggestions to generate
        
    Returns:
        Dictionary with name suggestions in different styles
    """
    styles = ["conversational", "narrative", "action"]
    suggestions = {}
    
    for style in styles:
        namer = NaturalNamer(style)
        name = namer.create_natural_name(description)
        suggestions[style] = name
    
    # Also create some variations
    namer = NaturalNamer()
    base_name = namer.create_natural_name(description)
    variations = namer.suggest_natural_variations(base_name)
    
    suggestions["variations"] = variations[:count]
    
    return {
        "description": description,
        "suggestions": suggestions,
        "recommended": suggestions.get("conversational", base_name),
        "message": "💡 Here are some natural name suggestions for your tool"
    }


def convert_existing_tool_name(
    tool_name: str,
    user_intent: Optional[str] = None,
    style: str = "conversational"
) -> Dict[str, Any]:
    """Convert an existing tool name to a more natural format.
    
    Args:
        tool_name: Existing tool name (e.g., "check_btc_price")
        user_intent: Optional user intent for better conversion
        style: Naming style to use
        
    Returns:
        Natural name conversion result
    """
    namer = NaturalNamer(style)
    
    # If no intent provided, try to reconstruct from name
    if not user_intent:
        # Convert underscores to spaces and clean up
        user_intent = tool_name.replace("_", " ").replace("-", " ")
        # Expand common abbreviations
        abbreviations = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "msg": "message",
            "temp": "temperature",
            "info": "information",
            "config": "configuration",
            "repo": "repository"
        }
        for abbr, full in abbreviations.items():
            user_intent = user_intent.replace(abbr, full)
    
    natural_name = namer.create_natural_name(user_intent)
    variations = namer.suggest_natural_variations(tool_name)
    
    return {
        "original": tool_name,
        "natural": natural_name,
        "style": style,
        "variations": variations,
        "message": f"✨ Converted '{tool_name}' to '{natural_name}'"
    }


# Export functions for MCP
__all__ = [
    "create_natural_tool_from_description",
    "suggest_tool_names",
    "convert_existing_tool_name"
]