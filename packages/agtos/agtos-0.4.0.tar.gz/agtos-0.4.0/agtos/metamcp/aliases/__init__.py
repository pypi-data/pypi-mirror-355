"""Natural Language Alias System for Meta-MCP.

This package provides a comprehensive alias registry for mapping natural language
commands to MCP tools. It supports weighted mappings, context-aware aliases,
user-definable custom aliases, and learning from usage patterns.

AI_CONTEXT:
    The alias system is split into three focused modules:
    
    1. core.py: Core alias mapping and registry functionality
       - AliasMapping and UsageStats data structures
       - Basic registration and lookup methods
       - Pattern matching infrastructure
       
    2. learning.py: Usage learning and pattern recognition
       - Track usage statistics
       - Adjust weights based on success/failure
       - Learn from user patterns
       
    3. custom.py: Custom alias management
       - Load builtin aliases
       - Manage user-defined custom aliases
       - Pattern handlers for dynamic commands
       - Persistence to disk
       
    The system is designed to be extensible and AI-friendly, making it easy
    for AI assistants to understand and suggest better aliases.
"""

# Import core functionality for backward compatibility
from .core import (
    AliasMapping,
    UsageStats,
    AliasRegistry,
    get_registry,
    find_tool_for_alias,
    suggest_aliases_for_tool,
    add_custom_alias,
)

# Re-export all public APIs
__all__ = [
    'AliasMapping',
    'UsageStats',
    'AliasRegistry',
    'get_registry',
    'find_tool_for_alias',
    'suggest_aliases_for_tool',
    'add_custom_alias',
]