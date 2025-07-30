"""Fuzzy matching utilities for tool suggestions.

This module provides fuzzy string matching capabilities to suggest
similar tool names when a tool is not found.
"""

from typing import List, Tuple, Optional
import difflib


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        The minimum number of edits needed to transform s1 into s2
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def fuzzy_match_tools(
    query: str,
    available_tools: List[str],
    max_suggestions: int = 3,
    threshold: float = 0.6
) -> List[Tuple[str, float]]:
    """Find tools that are similar to the query.
    
    Args:
        query: The tool name being searched for
        available_tools: List of all available tool names
        max_suggestions: Maximum number of suggestions to return
        threshold: Minimum similarity score (0-1) to include
        
    Returns:
        List of (tool_name, similarity_score) tuples, sorted by score
    """
    # Normalize query for comparison
    query_lower = query.lower()
    
    # Use both difflib and Levenshtein for better matches
    suggestions = []
    
    for tool in available_tools:
        tool_lower = tool.lower()
        
        # Calculate similarity using difflib (0-1 score)
        ratio = difflib.SequenceMatcher(None, query_lower, tool_lower).ratio()
        
        # Also check if query is substring (boost score)
        if query_lower in tool_lower:
            ratio = max(ratio, 0.8)
        
        # Check if tool is substring of query
        if tool_lower in query_lower:
            ratio = max(ratio, 0.7)
        
        # Calculate normalized Levenshtein distance
        lev_dist = levenshtein_distance(query_lower, tool_lower)
        max_len = max(len(query_lower), len(tool_lower))
        lev_score = 1 - (lev_dist / max_len) if max_len > 0 else 0
        
        # Combine scores (weighted average)
        combined_score = (ratio * 0.7) + (lev_score * 0.3)
        
        if combined_score >= threshold:
            suggestions.append((tool, combined_score))
    
    # Sort by score (descending) and return top suggestions
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return suggestions[:max_suggestions]


def format_suggestions(suggestions: List[Tuple[str, float]]) -> str:
    """Format tool suggestions into a user-friendly message.
    
    Args:
        suggestions: List of (tool_name, score) tuples
        
    Returns:
        Formatted string with suggestions
    """
    if not suggestions:
        return ""
    
    if len(suggestions) == 1:
        return f"Did you mean: {suggestions[0][0]}"
    
    tool_names = [name for name, _ in suggestions]
    return f"Did you mean one of these: {', '.join(tool_names)}"


def find_similar_aliases(
    query: str,
    tool_aliases: dict[str, str],
    max_suggestions: int = 3
) -> List[str]:
    """Find tool aliases that match the query.
    
    Args:
        query: The natural language query
        tool_aliases: Dictionary mapping aliases to tool names
        max_suggestions: Maximum number of suggestions
        
    Returns:
        List of actual tool names that have matching aliases
    """
    query_lower = query.lower()
    matches = []
    
    for alias, tool_name in tool_aliases.items():
        if alias.lower() == query_lower:
            # Exact match - return immediately
            return [tool_name]
        
        # Check for partial matches
        if query_lower in alias.lower() or alias.lower() in query_lower:
            matches.append(tool_name)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for tool in matches:
        if tool not in seen:
            seen.add(tool)
            unique_matches.append(tool)
    
    return unique_matches[:max_suggestions]