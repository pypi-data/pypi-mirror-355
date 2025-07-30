"""
Auto-completion engine for agentctl tools.

AI_CONTEXT:
    This module provides intelligent auto-completion for tool names and parameters.
    It integrates with the existing fuzzy matching and alias systems to provide:
    
    1. Tool name completion with fuzzy matching
    2. Parameter completion with type hints
    3. Context-aware suggestions based on recent usage
    4. Natural language alias suggestions
    
    The engine is designed to work across different shells and interfaces,
    providing a consistent completion experience.
"""

import json
import logging
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import difflib

from ..metamcp.registry import ServiceRegistry
from ..metamcp.fuzzy_match import fuzzy_match_tools
from ..metamcp.aliases import get_registry as get_alias_registry

logger = logging.getLogger(__name__)


@dataclass
class CompletionCandidate:
    """A single completion candidate.
    
    Attributes:
        value: The completion value (tool name or parameter value)
        display: Display string for the completion
        description: Short description of what this completion does
        score: Relevance score (0-1) for sorting
        type: Type of completion ('tool', 'parameter', 'alias')
        metadata: Additional metadata (e.g., parameter type info)
    """
    value: str
    display: str
    description: str = ""
    score: float = 1.0
    type: str = "tool"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionContext:
    """Context for completion suggestions.
    
    Attributes:
        partial_input: The partial input to complete
        cursor_position: Position of cursor in the input
        full_command: The full command line so far
        recent_tools: Recently used tools for prioritization
        project_type: Current project type for context
        active_service: Currently active service/namespace
    """
    partial_input: str
    cursor_position: int = 0
    full_command: str = ""
    recent_tools: List[str] = field(default_factory=list)
    project_type: Optional[str] = None
    active_service: Optional[str] = None


class AutoCompleteEngine:
    """Main auto-completion engine for agentctl tools.
    
    AI_CONTEXT:
        This engine provides intelligent completions by:
        
        1. Loading all available tools from the service registry
        2. Using fuzzy matching for partial inputs
        3. Leveraging the alias system for natural language
        4. Tracking usage patterns for better suggestions
        5. Providing parameter hints based on tool schemas
        
        The engine maintains a cache of tool information and usage
        statistics to provide fast, context-aware completions.
    """
    
    def __init__(self, registry: Optional[ServiceRegistry] = None, 
                 config_dir: Optional[Path] = None):
        """Initialize the auto-complete engine.
        
        Args:
            registry: Service registry to get tools from
            config_dir: Directory for storing usage history
        """
        self.registry = registry
        self.config_dir = config_dir or Path.home() / ".agtos"
        self.history_file = self.config_dir / "completion_history.json"
        
        # Caches
        self.tool_cache: Dict[str, Dict[str, Any]] = {}
        self.usage_history: Dict[str, int] = defaultdict(int)
        self.parameter_history: Dict[str, Dict[str, int]] = defaultdict(dict)
        
        # Load history
        self._load_history()
        
        # Get alias registry
        self.alias_registry = get_alias_registry()
        
    def complete(self, context: CompletionContext) -> List[CompletionCandidate]:
        """Get completion candidates for the given context.
        
        Args:
            context: Completion context with partial input
            
        Returns:
            List of completion candidates sorted by relevance
        """
        # Parse the command to determine what we're completing
        parts = context.full_command.split()
        
        if not parts:
            # Empty command, complete tool names
            return self._complete_tool_name(context)
        
        # Check if we're completing the first word (tool name)
        first_space = context.full_command.find(' ')
        if first_space == -1 or context.cursor_position <= first_space:
            # Still on the tool name
            return self._complete_tool_name(context)
        else:
            # Completing parameters
            tool_name = parts[0]
            return self._complete_parameters(tool_name, context)
    
    def _complete_tool_name(self, context: CompletionContext) -> List[CompletionCandidate]:
        """Complete tool names based on partial input.
        
        AI_CONTEXT:
            This method provides tool name completions by:
            
            1. Getting all available tools from the registry
            2. Matching against partial input using multiple strategies:
               - Exact prefix matching (highest priority)
               - Fuzzy matching for typos
               - Alias matching for natural language
            3. Scoring based on:
               - Match quality
               - Usage frequency
               - Recency of use
            4. Returning sorted candidates with descriptions
        """
        candidates = []
        partial = context.partial_input.lower()
        
        # Get all available tools
        all_tools = self._get_available_tools()
        
        # Apply different matching strategies
        candidates.extend(self._find_exact_prefix_matches(partial, all_tools, context))
        candidates.extend(self._find_fuzzy_matches(partial, all_tools, candidates))
        candidates.extend(self._find_alias_matches(partial, context, candidates))
        
        # Sort by score (descending) and limit results
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:20]
    
    def _complete_parameters(self, tool_name: str, context: CompletionContext) -> List[CompletionCandidate]:
        """Complete parameters for a specific tool.
        
        AI_CONTEXT:
            This method provides parameter completions by:
            
            1. Loading the tool's schema to understand parameters
            2. Parsing the current command to see what's been provided
            3. Suggesting parameter names and values based on:
               - Required vs optional parameters
               - Parameter types and constraints
               - Previously used values
            4. Providing inline help for each parameter
        """
        candidates = []
        
        # Get tool schema
        schema = self._get_tool_schema(tool_name)
        if not schema:
            return candidates
        
        # Parse current parameters
        parts = context.full_command.split()
        current_params = self._parse_parameters(parts[1:])
        
        # Get parameter being completed
        partial = context.partial_input
        
        # If starting with -- or -, complete parameter names
        if partial.startswith('-'):
            return self._complete_parameter_names(schema, current_params, partial)
        
        # Otherwise, complete parameter values
        # Find the last parameter name
        last_param = None
        for i in range(len(parts) - 1, 0, -1):
            if parts[i].startswith('-'):
                last_param = parts[i].lstrip('-')
                break
        
        if last_param:
            return self._complete_parameter_values(tool_name, last_param, partial, schema)
        
        return candidates
    
    def _complete_parameter_names(self, schema: Dict[str, Any], 
                                 current_params: Dict[str, str], 
                                 partial: str) -> List[CompletionCandidate]:
        """Complete parameter names based on schema."""
        candidates = []
        
        properties = schema.get("inputSchema", {}).get("properties", {})
        required = schema.get("inputSchema", {}).get("required", [])
        
        # Remove leading dashes from partial
        partial_clean = partial.lstrip('-')
        
        for param_name, param_schema in properties.items():
            # Skip if already provided
            if param_name in current_params:
                continue
            
            # Check if matches partial
            if param_name.startswith(partial_clean):
                # Format with appropriate dashes
                if len(param_name) == 1:
                    display = f"-{param_name}"
                else:
                    display = f"--{param_name}"
                
                # Score based on requirement and match quality
                score = 1.0 if param_name in required else 0.8
                
                # Exact match gets boost
                if param_name == partial_clean:
                    score += 0.2
                
                description = param_schema.get("description", "")
                param_type = param_schema.get("type", "string")
                
                if param_name in required:
                    description = f"[REQUIRED] {description}"
                
                candidates.append(CompletionCandidate(
                    value=display,
                    display=f"{display} <{param_type}>",
                    description=description,
                    score=score,
                    type="parameter",
                    metadata={"required": param_name in required, "param_type": param_type}
                ))
        
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates
    
    def _complete_parameter_values(self, tool_name: str, param_name: str, 
                                  partial: str, schema: Dict[str, Any]) -> List[CompletionCandidate]:
        """Complete parameter values based on type and history."""
        candidates = []
        
        properties = schema.get("inputSchema", {}).get("properties", {})
        param_schema = properties.get(param_name, {})
        
        if not param_schema:
            return candidates
        
        param_type = param_schema.get("type", "string")
        
        # Handle enums
        if "enum" in param_schema:
            for value in param_schema["enum"]:
                if str(value).startswith(partial):
                    candidates.append(CompletionCandidate(
                        value=str(value),
                        display=str(value),
                        description=f"Allowed value for {param_name}",
                        score=1.0,
                        type="value"
                    ))
        
        # Handle booleans
        elif param_type == "boolean":
            for value in ["true", "false"]:
                if value.startswith(partial.lower()):
                    candidates.append(CompletionCandidate(
                        value=value,
                        display=value,
                        description=f"Boolean value for {param_name}",
                        score=1.0,
                        type="value"
                    ))
        
        # Handle file paths
        elif param_name in ["path", "file", "directory", "file_path", "dir_path"]:
            candidates.extend(self._complete_file_path(partial))
        
        # Use history for other types
        else:
            # Get historical values for this parameter
            param_history = self.parameter_history.get(f"{tool_name}.{param_name}", {})
            
            for value, count in sorted(param_history.items(), key=lambda x: x[1], reverse=True):
                if value.startswith(partial):
                    score = min(1.0, 0.5 + (count / 10.0))
                    candidates.append(CompletionCandidate(
                        value=value,
                        display=value,
                        description=f"Previously used ({count} times)",
                        score=score,
                        type="value",
                        metadata={"source": "history"}
                    ))
        
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:10]
    
    def _complete_file_path(self, partial: str) -> List[CompletionCandidate]:
        """Complete file paths."""
        candidates = []
        
        try:
            path = Path(partial)
            parent = path.parent if partial.endswith('/') else path.parent if path.name else path
            prefix = path.name if not partial.endswith('/') else ""
            
            if parent.exists() and parent.is_dir():
                for item in parent.iterdir():
                    if item.name.startswith(prefix):
                        value = str(item)
                        if item.is_dir():
                            value += "/"
                            
                        candidates.append(CompletionCandidate(
                            value=value,
                            display=value,
                            description="Directory" if item.is_dir() else "File",
                            score=1.0 if item.is_dir() else 0.9,  # Prefer directories
                            type="path"
                        ))
        except Exception as e:
            logger.debug(f"Error completing file path: {e}")
        
        return candidates
    
    def _get_all_tools(self) -> List[str]:
        """Get all available tools from the registry."""
        tools = []
        
        if not self.registry:
            # If no registry, return cached tools
            return list(self.tool_cache.keys())
        
        for service_name, service in self.registry.services.items():
            for tool in service.tools:
                tools.append(tool.name)
        
        # Update cache
        for tool in tools:
            if tool not in self.tool_cache:
                self.tool_cache[tool] = {}
        
        return tools
    
    def _get_tool_description(self, tool_name: str) -> str:
        """Get description for a tool."""
        if self.registry:
            for service in self.registry.services.values():
                for tool in service.tools:
                    if tool.name == tool_name:
                        return tool.description or f"Tool from {service.config.name}"
        
        # Check cache
        if tool_name in self.tool_cache:
            return self.tool_cache[tool_name].get("description", "")
        
        # Generate from name
        parts = tool_name.split('__')
        if len(parts) >= 2:
            return f"{parts[0]} command: {' '.join(parts[1:])}"
        
        return ""
    
    def _get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a tool."""
        if self.registry:
            for service in self.registry.services.values():
                for tool in service.tools:
                    if tool.name == tool_name:
                        return {"inputSchema": tool.inputSchema}
        
        return None
    
    def _format_tool_display(self, tool_name: str) -> str:
        """Format tool name for display."""
        # Check if it has a display name
        if self.registry:
            for service in self.registry.services.values():
                for tool in service.tools:
                    if tool.name == tool_name and hasattr(tool, 'displayName'):
                        return f"{tool_name} ({tool.displayName})"
        
        # Default formatting
        parts = tool_name.split('__')
        if len(parts) == 2:
            return f"{parts[0]}::{parts[1]}"
        elif len(parts) > 2:
            return f"{parts[0]}::{'.'.join(parts[1:])}"
        
        return tool_name
    
    def _parse_parameters(self, parts: List[str]) -> Dict[str, str]:
        """Parse parameters from command parts."""
        params = {}
        i = 0
        
        while i < len(parts):
            if parts[i].startswith('-'):
                param_name = parts[i].lstrip('-')
                
                # Check if next part is the value
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    params[param_name] = parts[i + 1]
                    i += 2
                else:
                    params[param_name] = ""
                    i += 1
            else:
                i += 1
        
        return params
    
    def record_usage(self, tool_name: str, parameters: Optional[Dict[str, Any]] = None):
        """Record tool usage for better future suggestions.
        
        Args:
            tool_name: The tool that was used
            parameters: Parameters that were provided
        """
        # Update usage count
        self.usage_history[tool_name] += 1
        
        # Update parameter history
        if parameters:
            for param_name, param_value in parameters.items():
                key = f"{tool_name}.{param_name}"
                value_str = str(param_value)
                
                if key not in self.parameter_history:
                    self.parameter_history[key] = {}
                
                self.parameter_history[key][value_str] = \
                    self.parameter_history[key].get(value_str, 0) + 1
        
        # Save history periodically
        if sum(self.usage_history.values()) % 10 == 0:
            self._save_history()
    
    def _load_history(self):
        """Load usage history from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.usage_history = defaultdict(int, data.get("usage", {}))
                    
                    # Convert parameter history back to nested defaultdict
                    param_data = data.get("parameters", {})
                    for key, values in param_data.items():
                        self.parameter_history[key] = dict(values)
                        
            except Exception as e:
                logger.error(f"Failed to load completion history: {e}")
    
    def _save_history(self):
        """Save usage history to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                "usage": dict(self.usage_history),
                "parameters": dict(self.parameter_history),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save completion history: {e}")
    
    def get_suggestions_for_error(self, error_msg: str, tool_name: str) -> List[str]:
        """Get suggestions based on an error message.
        
        AI_CONTEXT:
            This method analyzes error messages to provide helpful suggestions:
            
            1. For "tool not found" errors, suggests similar tools
            2. For parameter errors, suggests correct parameter names/values
            3. For permission errors, suggests fixes
            
            This helps users recover from errors quickly.
        """
        suggestions = []
        
        # Tool not found errors
        if "not found" in error_msg.lower() or "unknown tool" in error_msg.lower():
            # Get all tools and find similar ones
            all_tools = self._get_all_tools()
            similar = fuzzy_match_tools(tool_name, all_tools, max_suggestions=3)
            
            for tool, score in similar:
                suggestions.append(f"Did you mean: {tool}")
            
            # Also check aliases
            alias_matches = self.alias_registry.find_all_matches(tool_name)
            for tool, confidence in alias_matches[:2]:
                if confidence > 0.6:
                    aliases = self.alias_registry.suggest_aliases(tool)
                    if aliases:
                        suggestions.append(f"Try: {tool} (alias: '{aliases[0]}')")
        
        # Parameter errors
        elif "parameter" in error_msg.lower() or "argument" in error_msg.lower():
            schema = self._get_tool_schema(tool_name)
            if schema:
                required = schema.get("inputSchema", {}).get("required", [])
                if required:
                    suggestions.append(f"Required parameters: {', '.join(required)}")
                
                # Extract parameter name from error if possible
                import re
                param_match = re.search(r"parameter[: ]+['\"]?(\w+)['\"]?", error_msg, re.IGNORECASE)
                if param_match:
                    param = param_match.group(1)
                    properties = schema.get("inputSchema", {}).get("properties", {})
                    
                    # Find similar parameter names
                    similar_params = difflib.get_close_matches(param, properties.keys(), n=2)
                    if similar_params:
                        suggestions.append(f"Did you mean: --{similar_params[0]}")
        
        return suggestions
    
    # ========================================================================
    # Helper Methods for _complete_tool_name
    # ========================================================================
    
    def _get_available_tools(self) -> List[str]:
        """Get all available tools from registry or cache.
        
        Returns:
            List of tool names
        """
        if self.registry:
            return self._get_all_tools()
        else:
            # Fallback: use cached tools
            return list(self.tool_cache.keys())
    
    def _find_exact_prefix_matches(
        self,
        partial: str,
        all_tools: List[str],
        context: CompletionContext
    ) -> List[CompletionCandidate]:
        """Find tools that start with the partial input.
        
        Args:
            partial: Lowercase partial input
            all_tools: List of all available tools
            context: Completion context
            
        Returns:
            List of completion candidates
        """
        candidates = []
        
        for tool in all_tools:
            if tool.lower().startswith(partial):
                score = self._calculate_tool_score(tool, context, base_score=1.0)
                
                candidates.append(CompletionCandidate(
                    value=tool,
                    display=self._format_tool_display(tool),
                    description=self._get_tool_description(tool),
                    score=score,
                    type="tool"
                ))
        
        return candidates
    
    def _find_fuzzy_matches(
        self,
        partial: str,
        all_tools: List[str],
        existing_candidates: List[CompletionCandidate]
    ) -> List[CompletionCandidate]:
        """Find tools using fuzzy matching for typos.
        
        Args:
            partial: Lowercase partial input
            all_tools: List of all available tools
            existing_candidates: Already found candidates to skip
            
        Returns:
            List of completion candidates
        """
        candidates = []
        
        # Only fuzzy match if we have at least 2 chars
        if len(partial) < 2:
            return candidates
            
        fuzzy_matches = fuzzy_match_tools(partial, all_tools, max_suggestions=10, threshold=0.5)
        
        for tool, match_score in fuzzy_matches:
            # Skip if already added as exact match
            if any(c.value == tool for c in existing_candidates):
                continue
                
            # Lower base score for fuzzy matches
            score = match_score * 0.8
            
            # Still apply usage boost
            usage_boost = min(0.2, self.usage_history.get(tool, 0) / 100.0)
            score += usage_boost
            
            candidates.append(CompletionCandidate(
                value=tool,
                display=self._format_tool_display(tool),
                description=self._get_tool_description(tool),
                score=score,
                type="tool",
                metadata={"match_type": "fuzzy"}
            ))
        
        return candidates
    
    def _find_alias_matches(
        self,
        partial: str,
        context: CompletionContext,
        existing_candidates: List[CompletionCandidate]
    ) -> List[CompletionCandidate]:
        """Find tools using natural language aliases.
        
        Args:
            partial: Lowercase partial input
            context: Completion context
            existing_candidates: Already found candidates to skip
            
        Returns:
            List of completion candidates
        """
        candidates = []
        
        # Build alias context
        alias_context = {
            "project_type": context.project_type,
            "active_tools": context.recent_tools[:5] if context.recent_tools else []
        }
        
        # Try to find matching aliases
        alias_matches = self.alias_registry.find_all_matches(context.partial_input, alias_context)
        
        for tool, confidence in alias_matches:
            # Skip if already added
            if any(c.value == tool for c in existing_candidates):
                continue
                
            # Get the matching alias for display
            matching_aliases = self._find_matching_aliases(tool, partial)
            
            if matching_aliases:
                candidates.append(CompletionCandidate(
                    value=tool,
                    display=f"{tool} ({matching_aliases[0]})",
                    description=self._get_tool_description(tool),
                    score=confidence * 0.9,  # Slightly lower than exact matches
                    type="alias",
                    metadata={"aliases": matching_aliases}
                ))
        
        return candidates
    
    def _calculate_tool_score(
        self,
        tool: str,
        context: CompletionContext,
        base_score: float = 1.0
    ) -> float:
        """Calculate completion score for a tool.
        
        Args:
            tool: Tool name
            context: Completion context
            base_score: Starting score
            
        Returns:
            Calculated score
        """
        score = base_score
        
        # Boost score based on usage
        usage_boost = min(0.3, self.usage_history.get(tool, 0) / 100.0)
        score += usage_boost
        
        # Extra boost for recent tools
        if tool in context.recent_tools:
            recency_boost = 0.2 * (1 - context.recent_tools.index(tool) / len(context.recent_tools))
            score += recency_boost
        
        return score
    
    def _find_matching_aliases(self, tool: str, partial: str) -> List[str]:
        """Find aliases that contain the partial input.
        
        Args:
            tool: Tool name
            partial: Lowercase partial input
            
        Returns:
            List of matching aliases
        """
        matching_aliases = []
        for alias in self.alias_registry.suggest_aliases(tool):
            if partial in alias.lower():
                matching_aliases.append(alias)
        return matching_aliases