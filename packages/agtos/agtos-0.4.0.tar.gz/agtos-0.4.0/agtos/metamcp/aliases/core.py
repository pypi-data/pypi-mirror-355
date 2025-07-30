"""Core alias mapping and registry functionality.

This module provides the fundamental data structures and registry class for
managing natural language aliases to MCP tools.

AI_CONTEXT:
    This is the core module that other alias modules build upon. It provides:
    
    1. Data structures:
       - AliasMapping: Represents a single alias to tool mapping
       - UsageStats: Tracks usage statistics for learning
       
    2. AliasRegistry: The central registry that manages all aliases
       - Registration of aliases and patterns
       - Finding tools for natural language commands
       - Context-aware matching with weighted scores
       
    3. Global registry management for singleton pattern
    
    The module focuses on core functionality, delegating learning and
    custom alias management to other modules in the package.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class AliasMapping:
    """Represents a mapping from an alias to a tool.
    
    Attributes:
        alias: The natural language alias
        tool_name: The actual MCP tool name
        weight: Confidence score (0-1) for this mapping
        context_hints: List of context clues that increase weight
        parameter_hints: Expected parameters for validation
        description: Human-readable description of what this does
    """
    alias: str
    tool_name: str
    weight: float = 1.0
    context_hints: List[str] = field(default_factory=list)
    parameter_hints: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    def matches_context(self, context: Dict[str, Any]) -> float:
        """Calculate context match score.
        
        Returns a score between 0 and 1 indicating how well this
        mapping matches the current context.
        
        AI_CONTEXT:
            This method uses a lenient scoring system:
            - If no context hints, returns 1.0 (always matches)
            - If context hints exist but no context provided, returns 0.5 (partial match)
            - If context provided, returns proportion of matching hints
            - Minimum score of 0.3 to allow aliases to work without perfect context
        """
        if not self.context_hints:
            return 1.0
        
        # If we have hints but no context, give partial credit
        if not context:
            return 0.5
        
        matches = 0
        for hint in self.context_hints:
            # Check project type
            if hint.startswith("project:"):
                project_type = hint[8:]
                if context.get("project_type") == project_type:
                    matches += 1
            # Check for active tools
            elif hint.startswith("tool:"):
                tool = hint[5:]
                if tool in context.get("active_tools", []):
                    matches += 1
            # Check recent commands
            elif hint.startswith("recent:"):
                cmd = hint[7:]
                if cmd in context.get("recent_commands", []):
                    matches += 1
        
        # Calculate score with minimum threshold
        raw_score = matches / len(self.context_hints) if self.context_hints else 1.0
        # Ensure minimum score of 0.3 so aliases can still work without perfect context
        return max(0.3, raw_score)


@dataclass
class UsageStats:
    """Track usage statistics for aliases."""
    total_uses: int = 0
    successful_uses: int = 0
    last_used: Optional[datetime] = None
    parameter_patterns: Dict[str, int] = field(default_factory=dict)


class AliasRegistry:
    """Central registry for natural language aliases.
    
    AI_CONTEXT:
        This class manages all alias mappings and provides methods for:
        1. Registering built-in and custom aliases
        2. Finding the best tool match for a natural language command
        3. Learning from usage patterns
        4. Persisting custom aliases and usage stats
        
        The registry uses a multi-stage matching process:
        - Exact match on alias
        - Fuzzy match using regex patterns
        - Contextual scoring to pick the best match
        - Parameter validation to ensure compatibility
        
        This core class focuses on registration and lookup. Learning
        and custom alias management are delegated to other modules.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the alias registry.
        
        Args:
            config_dir: Directory for storing custom aliases and stats
        """
        self.config_dir = config_dir or Path.home() / ".agtos"
        self.aliases_file = self.config_dir / "aliases.json"
        self.stats_file = self.config_dir / "alias_stats.json"
        
        # Core data structures
        self.mappings: List[AliasMapping] = []
        self.exact_map: Dict[str, List[AliasMapping]] = defaultdict(list)
        self.pattern_map: List[Tuple[re.Pattern, callable]] = []
        self.usage_stats: Dict[str, UsageStats] = defaultdict(UsageStats)
        
        # Initialize will be called by custom module
        self._initialized = False
    
    def register_alias(self, mapping: AliasMapping):
        """Register an alias mapping.
        
        Args:
            mapping: The alias mapping to register
        """
        self.mappings.append(mapping)
        
        # Add to exact match map
        key = mapping.alias.lower()
        self.exact_map[key].append(mapping)
    
    def register_pattern(self, pattern: str, handler: callable):
        """Register a regex pattern for fuzzy matching.
        
        Args:
            pattern: Regex pattern string
            handler: Function that takes match groups and returns mappings
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        self.pattern_map.append((compiled, handler))
    
    def find_tool(self, command: str, context: Optional[Dict[str, Any]] = None) -> Optional[Tuple[str, float]]:
        """Find the best matching tool for a natural language command.
        
        Args:
            command: The natural language command
            context: Optional context for disambiguation
            
        Returns:
            Tuple of (tool_name, confidence) or None if no match
            
        AI_CONTEXT:
            This method implements the core matching algorithm:
            
            1. First tries exact matching on the normalized command
            2. Then tries fuzzy matching with regex patterns
            3. Scores each candidate based on:
               - Base weight of the mapping
               - Context match score
               - Parameter compatibility
            4. Returns the highest scoring match above threshold
            
            The confidence score helps AI assistants decide whether
            to use the match or ask for clarification.
        """
        if not command:
            return None
        
        command_lower = command.lower().strip()
        context = context or {}
        candidates: List[Tuple[AliasMapping, float]] = []
        
        # Try exact match first
        if command_lower in self.exact_map:
            for mapping in self.exact_map[command_lower]:
                score = mapping.weight * mapping.matches_context(context)
                candidates.append((mapping, score))
        
        # Try pattern matching
        for pattern, handler in self.pattern_map:
            match = pattern.match(command)
            if match:
                pattern_mappings = handler(match)
                for mapping in pattern_mappings:
                    score = mapping.weight * mapping.matches_context(context)
                    candidates.append((mapping, score))
        
        # Find best candidate
        if not candidates:
            return None
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_mapping, best_score = candidates[0]
        
        # Require minimum confidence
        if best_score < 0.5:
            return None
        
        # Record usage (delegated to learning module)
        self._record_usage(command, best_mapping.tool_name, context)
        
        return (best_mapping.tool_name, best_score)
    
    def find_all_matches(self, command: str, context: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float]]:
        """Find all matching tools for a command, sorted by confidence.
        
        Returns:
            List of (tool_name, confidence) tuples
        """
        command_lower = command.lower().strip()
        context = context or {}
        candidates: List[Tuple[AliasMapping, float]] = []
        
        # Try exact match
        if command_lower in self.exact_map:
            for mapping in self.exact_map[command_lower]:
                score = mapping.weight * mapping.matches_context(context)
                candidates.append((mapping, score))
        
        # Try pattern matching
        for pattern, handler in self.pattern_map:
            match = pattern.match(command)
            if match:
                pattern_mappings = handler(match)
                for mapping in pattern_mappings:
                    score = mapping.weight * mapping.matches_context(context)
                    candidates.append((mapping, score))
        
        # Sort by score and filter low confidence
        candidates.sort(key=lambda x: x[1], reverse=True)
        results = []
        seen_tools = set()
        
        for mapping, score in candidates:
            if score >= 0.3 and mapping.tool_name not in seen_tools:
                results.append((mapping.tool_name, score))
                seen_tools.add(mapping.tool_name)
        
        return results
    
    def suggest_aliases(self, tool_name: str) -> List[str]:
        """Suggest natural language aliases for a tool.
        
        Args:
            tool_name: The MCP tool name
            
        Returns:
            List of suggested aliases
        """
        aliases = []
        
        for mapping in self.mappings:
            if mapping.tool_name == tool_name:
                aliases.append(mapping.alias)
        
        # Sort by weight
        alias_map = {m.alias: m.weight for m in self.mappings if m.tool_name == tool_name}
        aliases.sort(key=lambda a: alias_map.get(a, 0), reverse=True)
        
        return aliases
    
    def _record_usage(self, command: str, tool_name: str, context: Dict[str, Any]):
        """Record usage statistics for learning.
        
        AI_CONTEXT:
            This is a hook method that will be overridden or extended
            by the learning module to implement actual usage tracking.
        """
        # Basic implementation - extended by learning module
        stats = self.usage_stats[tool_name]
        stats.total_uses += 1
        stats.last_used = datetime.now()
        
        # Track parameter patterns
        if "parameters" in context:
            for param in context["parameters"]:
                stats.parameter_patterns[param] = stats.parameter_patterns.get(param, 0) + 1


# Global registry instance
_registry: Optional[AliasRegistry] = None


def get_registry() -> AliasRegistry:
    """Get the global alias registry instance."""
    global _registry
    if _registry is None:
        # Import here to avoid circular dependency
        from .custom import initialize_registry
        _registry = AliasRegistry()
        initialize_registry(_registry)
    return _registry


def find_tool_for_alias(command: str, context: Optional[Dict[str, Any]] = None) -> Optional[Tuple[str, float]]:
    """Find the best tool match for a natural language command.
    
    This is a convenience function that uses the global registry.
    
    Args:
        command: Natural language command
        context: Optional context for disambiguation
        
    Returns:
        Tuple of (tool_name, confidence) or None
    """
    return get_registry().find_tool(command, context)


def suggest_aliases_for_tool(tool_name: str) -> List[str]:
    """Suggest natural language aliases for a tool.
    
    Args:
        tool_name: The MCP tool name
        
    Returns:
        List of suggested aliases
    """
    return get_registry().suggest_aliases(tool_name)


def add_custom_alias(alias: str, tool_name: str, weight: float = 0.9):
    """Add a custom user-defined alias.
    
    Args:
        alias: Natural language alias
        tool_name: MCP tool name
        weight: Confidence weight (0-1)
    """
    # Import here to avoid circular dependency
    from .custom import add_custom_alias as _add_custom
    _add_custom(get_registry(), alias, tool_name, weight)