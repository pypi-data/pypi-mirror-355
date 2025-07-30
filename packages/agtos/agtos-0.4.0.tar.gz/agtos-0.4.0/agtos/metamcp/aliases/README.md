# Alias System Package

This package implements the natural language alias system for agtos, allowing tools to be accessed through human-friendly names and commands.

## Purpose

The alias system bridges the gap between technical tool names (e.g., `cli__git__status`) and natural language (e.g., "git status" or "show changes"). It includes learning capabilities to improve suggestions based on usage patterns.

## Module Breakdown

- **`core.py`** (~400 lines) - Core alias registry and pattern matching
  - `AliasRegistry` class for managing all aliases
  - Pattern matching logic for tool resolution
  - Integration with the service registry

- **`learning.py`** (~250 lines) - Usage-based learning and adaptation
  - `AliasLearner` class for tracking usage patterns
  - Weight adjustment algorithms
  - Success/failure recording for continuous improvement

- **`custom.py`** (~350 lines) - Custom alias management
  - Loading built-in aliases from JSON
  - User-defined custom aliases
  - Persistence to disk
  - Pattern handlers for dynamic commands

## Key Classes and Functions

### AliasRegistry (core.py)
```python
registry = AliasRegistry()
registry.register_alias("git status", "cli__git__status")
tool_name = registry.resolve_alias("show git status")  # Returns "cli__git__status"
```

### AliasLearner (learning.py)
```python
learner = AliasLearner()
learner.record_usage("git status", "cli__git__status", success=True)
suggestions = learner.get_suggestions("git st")  # Returns learned patterns
```

### Custom Alias Management (custom.py)
```python
registry.add_custom_alias("deploy", "cli__kubectl__apply")
registry.save_custom_aliases()  # Persists to ~/.agtos/custom_aliases.json
```

## How Modules Work Together

1. **Initialization**: `custom.py` loads built-in and custom aliases into the registry
2. **Resolution**: `core.py` handles pattern matching when resolving aliases
3. **Learning**: `learning.py` tracks usage and adjusts weights for better suggestions
4. **Persistence**: `custom.py` saves user customizations and learned patterns

The alias system integrates with the Meta-MCP server through the router, intercepting tool calls and resolving natural language requests to actual tool names before execution.