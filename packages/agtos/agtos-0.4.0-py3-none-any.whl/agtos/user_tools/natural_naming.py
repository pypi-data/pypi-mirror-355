"""Natural language naming system for tools.

This module provides utilities to create tools with names that read like
natural language when displayed in Claude's interface.

AI_CONTEXT:
    This addresses the user's request for more natural tool displays by:
    - Converting intents to readable function names
    - Adding conversational prefixes
    - Using descriptive naming patterns
    - Creating ephemeral tools with exact user phrases
"""

import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class NaturalNamer:
    """Creates natural, readable names for tools."""
    
    # Conversational prefixes for different action types
    ACTION_PREFIXES = {
        "check": ["checking", "looking_at", "examining"],
        "get": ["fetching", "retrieving", "getting"],
        "create": ["creating", "making", "building"],
        "update": ["updating", "modifying", "changing"],
        "delete": ["removing", "deleting", "clearing"],
        "list": ["listing", "showing", "displaying"],
        "search": ["searching_for", "finding", "looking_for"],
        "analyze": ["analyzing", "examining", "studying"],
        "send": ["sending", "dispatching", "delivering"],
        "post": ["posting", "publishing", "sharing"]
    }
    
    # Conversational connectors
    CONNECTORS = ["the", "all", "your", "my", "current", "latest", "new"]
    
    # Temporal markers for immediate action feel
    TEMPORAL_MARKERS = ["now", "currently", "just", "quickly"]
    
    def __init__(self, style: str = "conversational"):
        """Initialize the natural namer.
        
        Args:
            style: Naming style - 'conversational', 'narrative', or 'action'
        """
        self.style = style
        
    def create_natural_name(
        self,
        user_intent: str,
        base_action: Optional[str] = None
    ) -> str:
        """Create a natural, readable tool name from user intent.
        
        Args:
            user_intent: What the user asked for
            base_action: Optional base action verb
            
        Returns:
            Natural tool name that reads like a sentence
        """
        # Clean and normalize the intent
        intent_lower = user_intent.lower().strip()
        
        # Special handling for known tool names that shouldn't be transformed  
        if intent_lower in ['tool_creator_create', 'ephemeral_create', 'tool_creator_list']:
            return intent_lower
            
        # Extract action verb if not provided
        if not base_action:
            base_action = self._extract_action(intent_lower)
        
        if self.style == "conversational":
            return self._create_conversational_name(intent_lower, base_action)
        elif self.style == "narrative":
            return self._create_narrative_name(intent_lower, base_action)
        elif self.style == "action":
            return self._create_action_name(intent_lower, base_action)
        else:
            # Default to simple underscore conversion
            return self._simple_conversion(intent_lower)
    
    def _extract_action(self, intent: str) -> str:
        """Extract the main action verb from intent."""
        # Common action patterns
        action_patterns = [
            r'^(check|get|create|update|delete|list|find|search|send|post|fetch)\b',
            r'^(show|display|retrieve|remove|modify|analyze|examine)\b',
            r'^(can you |please |i need to |i want to )?(.*?)(?:\s|$)'
        ]
        
        for pattern in action_patterns:
            match = re.match(pattern, intent)
            if match:
                if len(match.groups()) > 1:
                    return match.group(2)
                return match.group(1)
        
        # Default to 'process' if no clear action
        return "process"
    
    def _create_conversational_name(self, intent: str, action: str) -> str:
        """Create a conversational style name.
        
        Examples:
        - "checking_bitcoin_price_now"
        - "fetching_weather_data"
        - "posting_to_slack_channel"
        """
        # Get conversational form of action
        conv_action = self.ACTION_PREFIXES.get(action, [action])[0]
        
        # Clean intent of action verb
        cleaned_intent = re.sub(rf'^{action}\s+', '', intent)
        
        # Remove common phrases that make names awkward
        cleanup_patterns = [
            r'^(a |an |the )',  # Remove articles
            r'^(request to |request for )',  # Remove "request to/for"
            r'^(get |fetch |retrieve )',  # Remove redundant action verbs
            r'\s*\{[^}]+\}',  # Remove parameter placeholders like {pokemon_name}
        ]
        
        for pattern in cleanup_patterns:
            cleaned_intent = re.sub(pattern, '', cleaned_intent, flags=re.IGNORECASE)
        
        # Extract key subject from common patterns
        # Pattern: "api.domain.com/path" -> "domain"
        # Special handling for URLs and API paths
        if "pokeapi.co" in cleaned_intent:
            cleaned_intent = "pokemon stats"
        elif "api.coingecko.com" in cleaned_intent or "coingecko" in cleaned_intent:
            cleaned_intent = "cryptocurrency prices"
        else:
            api_match = re.search(r'(?:api\.|/)([a-zA-Z0-9]+)(?:\.|/)', cleaned_intent)
            if api_match:
                subject = api_match.group(1)
                cleaned_intent = f"{subject} api"
        
        # Pattern: "X from/at Y" -> "Y X"
        from_match = re.search(r'(.+?)\s+(?:from|at)\s+(.+)', cleaned_intent)
        if from_match:
            what = from_match.group(1).strip()
            where = from_match.group(2).strip()
            cleaned_intent = f"{where} {what}"
        
        # Build name parts
        parts = [conv_action]
        
        # Clean up the intent further
        cleaned_intent = cleaned_intent.strip()
        if cleaned_intent:
            parts.append(cleaned_intent)
        
        # Add temporal marker for immediacy only if name is short
        if len("_".join(parts)) < 30 and action in ['check', 'get', 'create']:
            parts.append('now')
        
        # Convert to valid function name
        name = "_".join(parts)
        return self._sanitize_name(name)
    
    def _create_narrative_name(self, intent: str, action: str) -> str:
        """Create a narrative style name.
        
        Examples:
        - "let_me_check_the_bitcoin_price"
        - "i_will_fetch_the_weather_data"
        - "going_to_post_this_to_slack"
        """
        # Narrative prefixes based on action
        narrative_prefixes = {
            "check": "let_me_check",
            "get": "i_will_get",
            "create": "going_to_create",
            "update": "about_to_update",
            "send": "preparing_to_send",
            "post": "ready_to_post"
        }
        
        prefix = narrative_prefixes.get(action, f"going_to_{action}")
        
        # Clean intent of action verb
        cleaned_intent = re.sub(rf'^{action}\s+', '', intent)
        
        # Build narrative name
        name = f"{prefix}_{cleaned_intent}"
        return self._sanitize_name(name)
    
    def _create_action_name(self, intent: str, action: str) -> str:
        """Create an action-focused name.
        
        Examples:
        - "bitcoin_price_check_in_progress"
        - "weather_data_retrieval_active"
        - "slack_message_being_sent"
        """
        # Clean intent of action verb
        cleaned_intent = re.sub(rf'^{action}\s+', '', intent)
        
        # Action suffixes
        action_suffixes = {
            "check": "check_in_progress",
            "get": "retrieval_active",
            "create": "creation_underway",
            "update": "update_processing",
            "send": "being_sent",
            "post": "posting_now"
        }
        
        suffix = action_suffixes.get(action, f"{action}_active")
        
        # Build action name
        name = f"{cleaned_intent}_{suffix}"
        return self._sanitize_name(name)
    
    def _simple_conversion(self, intent: str) -> str:
        """Simple underscore conversion as fallback."""
        return self._sanitize_name(intent)
    
    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid Python identifier."""
        # Replace common phrases for readability
        replacements = {
            " to ": "_to_",
            " for ": "_for_",
            " with ": "_with_",
            " from ": "_from_",
            " in ": "_in_",
            " on ": "_on_",
            " at ": "_at_",
            " and ": "_and_",
            " or ": "_or_"
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        # Replace remaining spaces and special chars
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        
        # Ensure it starts with a letter
        if name and not name[0].isalpha():
            name = 'tool_' + name
        
        return name.lower()
    
    def create_tool_with_natural_name(
        self,
        tool_spec: Dict[str, Any],
        user_intent: str,
        base_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a tool specification with natural naming.
        
        Args:
            tool_spec: The base tool specification
            user_intent: What the user asked for
            base_name: Optional base name to use
            
        Returns:
            Tool spec with natural name applied
        """
        # Generate natural name
        if base_name:
            natural_name = base_name
        else:
            natural_name = self.create_natural_name(user_intent)
        
        # Apply to tool spec
        tool_spec["name"] = natural_name
        
        # Store the original intent for reference
        tool_spec["metadata"] = tool_spec.get("metadata", {})
        tool_spec["metadata"]["user_intent"] = user_intent
        tool_spec["metadata"]["natural_name"] = natural_name
        
        return tool_spec


# Convenience functions
def convert_to_natural_name(
    intent: str,
    style: str = "conversational"
) -> str:
    """Convert user intent to a natural function name.
    
    Args:
        intent: The user's intent or description
        style: Naming style to use
        
    Returns:
        Natural function name
    """
    namer = NaturalNamer(style=style)
    return namer.create_natural_name(intent)


def apply_natural_naming(
    tool_spec: Dict[str, Any],
    user_intent: str,
    style: str = "conversational"
) -> Dict[str, Any]:
    """Apply natural naming to a tool specification.
    
    Args:
        tool_spec: The tool specification
        user_intent: What the user asked for
        style: Naming style to use
        
    Returns:
        Tool spec with natural naming applied
    """
    namer = NaturalNamer(style=style)
    return namer.create_tool_with_natural_name(tool_spec, user_intent)