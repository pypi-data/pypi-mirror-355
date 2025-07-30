"""Custom alias management and builtin aliases.

This module handles loading builtin aliases, managing user-defined custom
aliases, and providing pattern handlers for dynamic command matching.

AI_CONTEXT:
    This module is responsible for:
    
    1. Loading the comprehensive set of builtin aliases that ship with agtos
    2. Managing user-defined custom aliases with persistence
    3. Providing pattern handlers for dynamic commands (create X, delete Y, etc)
    4. Saving and loading alias configurations from disk
    
    The builtin aliases cover common operations across:
    - File system operations
    - Git commands
    - Project management (build, test, deploy)
    - Docker operations
    - System administration
    
    Pattern handlers allow flexible matching of command patterns like
    "create file", "delete branch", "list containers" etc.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .core import AliasRegistry, AliasMapping, UsageStats
from .learning import enhance_registry_with_learning

logger = logging.getLogger(__name__)


def initialize_registry(registry: AliasRegistry):
    """Initialize a registry with builtin aliases and learning.
    
    Args:
        registry: The registry to initialize
        
    AI_CONTEXT:
        This is the main initialization function called when creating
        the global registry. It sets up all builtin aliases, loads
        custom aliases, and enables learning capabilities.
    """
    if registry._initialized:
        return
    
    # Load builtin aliases
    _load_builtin_aliases(registry)
    
    # Load custom aliases and stats
    _load_custom_aliases(registry)
    _load_usage_stats(registry)
    
    # Enable learning
    enhance_registry_with_learning(registry)
    
    registry._initialized = True


def _load_builtin_aliases(registry: AliasRegistry):
    """Load the built-in alias mappings.
    
    AI_CONTEXT:
        These are the core aliases that ship with agtos. They cover
        common operations across different tool categories:
        
        1. File Operations: 'show files', 'list directory', etc.
        2. Git Operations: 'save my work', 'check changes', etc.
        3. Project Management: 'run tests', 'build project', etc.
        4. System Operations: 'check status', 'show running', etc.
        
        Each category has multiple variations to accommodate different
        user phrasings and contexts.
    """
    # Load aliases by category
    _load_filesystem_aliases(registry)
    _load_git_aliases(registry)
    _load_testing_aliases(registry)
    _load_build_aliases(registry)
    _load_deployment_aliases(registry)
    _load_package_management_aliases(registry)
    _load_docker_aliases(registry)
    _load_process_management_aliases(registry)
    _load_system_status_aliases(registry)
    
    # Register pattern handlers
    _register_pattern_handlers(registry)


def _load_filesystem_aliases(registry: AliasRegistry):
    """Load file system operation aliases."""
    registry.register_alias(AliasMapping(
        alias="show files",
        tool_name="filesystem__list_directory",
        weight=0.9,
        description="List files in a directory"
    ))
    registry.register_alias(AliasMapping(
        alias="list files",
        tool_name="filesystem__list_directory",
        weight=0.9,
        description="List files in a directory"
    ))
    registry.register_alias(AliasMapping(
        alias="show directory",
        tool_name="filesystem__list_directory",
        weight=0.95,
        description="List directory contents"
    ))
    registry.register_alias(AliasMapping(
        alias="ls",
        tool_name="filesystem__list_directory",
        weight=1.0,
        description="List directory contents"
    ))


def _load_git_aliases(registry: AliasRegistry):
    """Load Git operation aliases."""
    git_aliases = [
        # Commit operations
        ("save my work", "cli__git__commit", 0.8, "Commit changes to git"),
        ("commit changes", "cli__git__commit", 0.95, "Commit changes to git"),
        
        # Status operations
        ("check status", "cli__git__status", 0.7, "Check git status"),
        ("git status", "cli__git__status", 1.0, "Check git status"),
        
        # Diff operations
        ("what changed", "cli__git__diff", 0.8, "Show git differences"),
        ("show changes", "cli__git__diff", 0.85, "Show git differences", 
         {"context_hints": ["tool:git"]}),
        
        # Push operations
        ("upload changes", "cli__git__push", 0.8, "Push changes to remote"),
        ("push code", "cli__git__push", 0.9, "Push changes to remote"),
        
        # Pull operations
        ("get updates", "cli__git__pull", 0.8, "Pull changes from remote"),
        ("pull code", "cli__git__pull", 0.9, "Pull changes from remote"),
        
        # Checkout operations
        ("switch branch", "cli__git__checkout", 0.9, "Switch git branches",
         {"parameter_hints": {"branch": "string"}}),
        ("change branch", "cli__git__checkout", 0.85, "Switch git branches",
         {"parameter_hints": {"branch": "string"}}),
    ]
    
    # Register all aliases
    for alias_data in git_aliases:
        alias, tool_name, weight, description = alias_data[:4]
        extra_params = alias_data[4] if len(alias_data) > 4 else {}
        
        mapping = AliasMapping(
            alias=alias,
            tool_name=tool_name,
            weight=weight,
            description=description
        )
        
        # Apply any extra parameters (context_hints, parameter_hints)
        for key, value in extra_params.items():
            setattr(mapping, key, value)
            
        registry.register_alias(mapping)


def _load_testing_aliases(registry: AliasRegistry):
    """Load testing operation aliases."""
    registry.register_alias(AliasMapping(
        alias="run tests",
        tool_name="cli__npm__test",
        weight=0.7,
        context_hints=["project:node"],
        description="Run project tests"
    ))
    registry.register_alias(AliasMapping(
        alias="run tests",
        tool_name="cli__pytest",
        weight=0.7,
        context_hints=["project:python"],
        description="Run Python tests"
    ))
    registry.register_alias(AliasMapping(
        alias="test code",
        tool_name="cli__npm__test",
        weight=0.65,
        context_hints=["project:node"],
        description="Run project tests"
    ))
    registry.register_alias(AliasMapping(
        alias="run unit tests",
        tool_name="cli__jest",
        weight=0.8,
        context_hints=["project:node", "tool:jest"],
        description="Run Jest unit tests"
    ))


def _load_build_aliases(registry: AliasRegistry):
    """Load build operation aliases."""
    registry.register_alias(AliasMapping(
        alias="build project",
        tool_name="cli__npm__build",
        weight=0.7,
        context_hints=["project:node"],
        description="Build the project"
    ))
    registry.register_alias(AliasMapping(
        alias="build project",
        tool_name="cli__make",
        weight=0.7,
        context_hints=["project:c", "project:cpp"],
        description="Build with make"
    ))
    registry.register_alias(AliasMapping(
        alias="compile code",
        tool_name="cli__npm__build",
        weight=0.65,
        context_hints=["project:node"],
        description="Compile the project"
    ))


def _load_deployment_aliases(registry: AliasRegistry):
    """Load deployment operation aliases."""
    registry.register_alias(AliasMapping(
        alias="deploy",
        tool_name="cli__vercel",
        weight=0.6,
        context_hints=["project:nextjs", "tool:vercel"],
        description="Deploy to Vercel"
    ))
    registry.register_alias(AliasMapping(
        alias="deploy",
        tool_name="cli__netlify__deploy",
        weight=0.6,
        context_hints=["tool:netlify"],
        description="Deploy to Netlify"
    ))
    registry.register_alias(AliasMapping(
        alias="deploy",
        tool_name="cli__heroku__deploy",
        weight=0.6,
        context_hints=["tool:heroku"],
        description="Deploy to Heroku"
    ))
    registry.register_alias(AliasMapping(
        alias="deploy app",
        tool_name="cli__fly__deploy",
        weight=0.7,
        context_hints=["tool:fly"],
        description="Deploy with Fly.io"
    ))


def _load_package_management_aliases(registry: AliasRegistry):
    """Load package management aliases."""
    registry.register_alias(AliasMapping(
        alias="install packages",
        tool_name="cli__npm__install",
        weight=0.8,
        context_hints=["project:node"],
        description="Install npm packages"
    ))
    registry.register_alias(AliasMapping(
        alias="install dependencies",
        tool_name="cli__npm__install",
        weight=0.85,
        context_hints=["project:node"],
        description="Install npm dependencies"
    ))
    registry.register_alias(AliasMapping(
        alias="install packages",
        tool_name="cli__pip__install",
        weight=0.8,
        context_hints=["project:python"],
        description="Install Python packages"
    ))


def _load_docker_aliases(registry: AliasRegistry):
    """Load Docker operation aliases."""
    registry.register_alias(AliasMapping(
        alias="list containers",
        tool_name="cli__docker__ps",
        weight=0.9,
        description="List Docker containers"
    ))
    registry.register_alias(AliasMapping(
        alias="show containers",
        tool_name="cli__docker__ps",
        weight=0.85,
        description="Show Docker containers"
    ))
    registry.register_alias(AliasMapping(
        alias="list images",
        tool_name="cli__docker__images",
        weight=0.9,
        description="List Docker images"
    ))
    registry.register_alias(AliasMapping(
        alias="start container",
        tool_name="cli__docker__run",
        weight=0.85,
        parameter_hints={"image": "string"},
        description="Start a Docker container"
    ))


def _load_process_management_aliases(registry: AliasRegistry):
    """Load process management aliases."""
    registry.register_alias(AliasMapping(
        alias="show processes",
        tool_name="cli__ps",
        weight=0.8,
        description="Show running processes"
    ))
    registry.register_alias(AliasMapping(
        alias="list processes",
        tool_name="cli__ps",
        weight=0.85,
        description="List running processes"
    ))
    registry.register_alias(AliasMapping(
        alias="kill process",
        tool_name="cli__kill",
        weight=0.9,
        parameter_hints={"pid": "number"},
        description="Kill a process"
    ))


def _load_system_status_aliases(registry: AliasRegistry):
    """Load system status aliases."""
    registry.register_alias(AliasMapping(
        alias="check disk space",
        tool_name="cli__df",
        weight=0.9,
        description="Check disk usage"
    ))
    registry.register_alias(AliasMapping(
        alias="show disk usage",
        tool_name="cli__du",
        weight=0.85,
        description="Show disk usage details"
    ))
    registry.register_alias(AliasMapping(
        alias="check memory",
        tool_name="cli__free",
        weight=0.9,
        description="Check memory usage"
    ))


def _register_pattern_handlers(registry: AliasRegistry):
    """Register pattern handlers for dynamic command matching."""
    registry.register_pattern(
        pattern=r"^(create|new|make)\s+(.+)$",
        handler=lambda m: _handle_create_pattern(m)
    )
    registry.register_pattern(
        pattern=r"^(delete|remove|rm)\s+(.+)$",
        handler=lambda m: _handle_delete_pattern(m)
    )
    registry.register_pattern(
        pattern=r"^(list|show|display)\s+(.+)$",
        handler=lambda m: _handle_list_pattern(m)
    )
    registry.register_pattern(
        pattern=r"^(run|execute|start)\s+(.+)$",
        handler=lambda m: _handle_run_pattern(m)
    )


def _handle_create_pattern(match: re.Match) -> List[AliasMapping]:
    """Handle 'create/new/make X' patterns."""
    thing = match.group(2).lower()
    mappings = []
    
    if thing in ["file", "document"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="filesystem__create_file",
            weight=0.8
        ))
    elif thing in ["directory", "folder"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="filesystem__create_directory",
            weight=0.8
        ))
    elif thing in ["branch"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__git__branch",
            weight=0.85
        ))
    elif thing in ["commit"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__git__commit",
            weight=0.85
        ))
    elif thing in ["tag"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__git__tag",
            weight=0.85
        ))
    elif thing in ["container"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__docker__create",
            weight=0.8
        ))
    
    return mappings


def _handle_delete_pattern(match: re.Match) -> List[AliasMapping]:
    """Handle 'delete/remove/rm X' patterns."""
    thing = match.group(2).lower()
    mappings = []
    
    if thing in ["file", "document"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="filesystem__delete_file",
            weight=0.8
        ))
    elif thing in ["directory", "folder"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="filesystem__delete_directory",
            weight=0.8
        ))
    elif thing in ["branch"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__git__branch",
            weight=0.8,
            parameter_hints={"delete": "true"}
        ))
    elif thing in ["container"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__docker__rm",
            weight=0.85
        ))
    elif thing in ["image"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__docker__rmi",
            weight=0.85
        ))
    
    return mappings


def _handle_list_pattern(match: re.Match) -> List[AliasMapping]:
    """Handle 'list/show/display X' patterns."""
    thing = match.group(2).lower()
    mappings = []
    
    if thing in ["files", "documents"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="filesystem__list_directory",
            weight=0.85
        ))
    elif thing in ["branches"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__git__branch",
            weight=0.9
        ))
    elif thing in ["commits", "history"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__git__log",
            weight=0.9
        ))
    elif thing in ["containers"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__docker__ps",
            weight=0.9
        ))
    elif thing in ["images"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__docker__images",
            weight=0.9
        ))
    elif thing in ["processes"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__ps",
            weight=0.85
        ))
    elif thing in ["packages"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__npm__list",
            weight=0.8,
            context_hints=["project:node"]
        ))
    
    return mappings


def _handle_run_pattern(match: re.Match) -> List[AliasMapping]:
    """Handle 'run/execute/start X' patterns."""
    thing = match.group(2).lower()
    mappings = []
    
    if thing in ["tests", "test"]:
        mappings.extend([
            AliasMapping(
                alias=match.group(0),
                tool_name="cli__npm__test",
                weight=0.7,
                context_hints=["project:node"]
            ),
            AliasMapping(
                alias=match.group(0),
                tool_name="cli__pytest",
                weight=0.7,
                context_hints=["project:python"]
            )
        ])
    elif thing in ["build"]:
        mappings.extend([
            AliasMapping(
                alias=match.group(0),
                tool_name="cli__npm__build",
                weight=0.75,
                context_hints=["project:node"]
            ),
            AliasMapping(
                alias=match.group(0),
                tool_name="cli__make",
                weight=0.7,
                context_hints=["project:c", "project:cpp"]
            )
        ])
    elif thing.startswith("script"):
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__npm__run",
            weight=0.8,
            context_hints=["project:node"]
        ))
    elif thing in ["server", "dev", "development"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__npm__start",
            weight=0.8,
            context_hints=["project:node"]
        ))
    elif thing in ["container"]:
        mappings.append(AliasMapping(
            alias=match.group(0),
            tool_name="cli__docker__run",
            weight=0.85
        ))
    
    return mappings


def add_custom_alias(registry: AliasRegistry, alias: str, tool_name: str, weight: float = 0.9):
    """Add a custom user-defined alias.
    
    Args:
        registry: The registry to add to
        alias: The natural language alias
        tool_name: The MCP tool name
        weight: Confidence weight (0-1)
    """
    mapping = AliasMapping(
        alias=alias,
        tool_name=tool_name,
        weight=weight,
        description=f"Custom alias for {tool_name}"
    )
    
    registry.register_alias(mapping)
    _save_custom_aliases(registry)


def remove_custom_alias(registry: AliasRegistry, alias: str) -> bool:
    """Remove a custom alias.
    
    Args:
        registry: The registry to remove from
        alias: The alias to remove
        
    Returns:
        True if removed, False if not found
    """
    alias_lower = alias.lower()
    removed = False
    
    # Remove from mappings
    registry.mappings = [m for m in registry.mappings if m.alias.lower() != alias_lower]
    
    # Remove from exact map
    if alias_lower in registry.exact_map:
        del registry.exact_map[alias_lower]
        removed = True
    
    if removed:
        _save_custom_aliases(registry)
    
    return removed


def _load_custom_aliases(registry: AliasRegistry):
    """Load custom aliases from disk."""
    if registry.aliases_file.exists():
        try:
            with open(registry.aliases_file, 'r') as f:
                data = json.load(f)
                
            for alias_data in data.get("custom_aliases", []):
                mapping = AliasMapping(**alias_data)
                registry.register_alias(mapping)
                
        except Exception as e:
            logger.error(f"Failed to load custom aliases: {e}")


def _save_custom_aliases(registry: AliasRegistry):
    """Save custom aliases to disk."""
    try:
        registry.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter custom aliases (those not loaded from built-in)
        custom = [m for m in registry.mappings if "Custom alias" in m.description]
        
        data = {
            "custom_aliases": [
                {
                    "alias": m.alias,
                    "tool_name": m.tool_name,
                    "weight": m.weight,
                    "context_hints": m.context_hints,
                    "parameter_hints": m.parameter_hints,
                    "description": m.description
                }
                for m in custom
            ]
        }
        
        with open(registry.aliases_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save custom aliases: {e}")


def _load_usage_stats(registry: AliasRegistry):
    """Load usage statistics from disk."""
    if registry.stats_file.exists():
        try:
            with open(registry.stats_file, 'r') as f:
                data = json.load(f)
                
            for tool_name, stats_data in data.items():
                stats = UsageStats()
                stats.total_uses = stats_data.get("total_uses", 0)
                stats.successful_uses = stats_data.get("successful_uses", 0)
                if stats_data.get("last_used"):
                    stats.last_used = datetime.fromisoformat(stats_data["last_used"])
                stats.parameter_patterns = stats_data.get("parameter_patterns", {})
                registry.usage_stats[tool_name] = stats
                
        except Exception as e:
            logger.error(f"Failed to load usage stats: {e}")


def _save_usage_stats(registry: AliasRegistry):
    """Save usage statistics to disk."""
    try:
        registry.config_dir.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for tool_name, stats in registry.usage_stats.items():
            data[tool_name] = {
                "total_uses": stats.total_uses,
                "successful_uses": stats.successful_uses,
                "last_used": stats.last_used.isoformat() if stats.last_used else None,
                "parameter_patterns": stats.parameter_patterns
            }
        
        with open(registry.stats_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save usage stats: {e}")