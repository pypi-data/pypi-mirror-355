"""Knowledge export functionality for MCP tools.

AI_CONTEXT:
    This module handles exporting knowledge base information related to
    plugins. It extracts and formats knowledge from the store, including
    CLI help, API documentation, and usage examples.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


def export_plugin_knowledge(store: Any, plugin_name: str, output_path: Path) -> None:
    """Export knowledge related to a plugin.
    
    AI_CONTEXT:
        This function gathers all available knowledge about a plugin from
        different sources (comprehensive, CLI, API) and exports it to a
        JSON file. The exported knowledge can be used to enhance the MCP
        tool's documentation or provide context to AI assistants.
    
    Args:
        store: Knowledge store instance
        plugin_name: Name of the plugin
        output_path: Path where to save the knowledge JSON file
    """
    knowledge = {
        "plugin": plugin_name,
        "exported_at": datetime.now().isoformat(),
        "entries": []
    }
    
    # Get comprehensive knowledge
    comp_knowledge = store.retrieve("comprehensive", plugin_name)
    if comp_knowledge:
        knowledge["entries"].append({
            "type": "comprehensive",
            "data": comp_knowledge["data"]
        })
    
    # Get CLI knowledge
    cli_knowledge = store.retrieve("cli", plugin_name)
    if cli_knowledge:
        knowledge["entries"].append({
            "type": "cli",
            "data": cli_knowledge["data"]
        })
    
    # Get API knowledge
    api_knowledge = store.retrieve("api", plugin_name)
    if api_knowledge:
        knowledge["entries"].append({
            "type": "api",
            "data": api_knowledge["data"]
        })
    
    # Get examples
    examples = store.get_examples("plugin", plugin_name)
    if examples:
        knowledge["examples"] = examples
    
    # Write knowledge file
    with open(output_path, 'w') as f:
        json.dump(knowledge, f, indent=2)


def format_knowledge_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Format a knowledge entry for export.
    
    Args:
        entry: Raw knowledge entry from store
        
    Returns:
        Formatted entry suitable for export
    """
    formatted = {
        "type": entry.get("type", "unknown"),
        "acquired_at": entry.get("acquired_at", ""),
        "source": entry.get("source", ""),
        "data": {}
    }
    
    data = entry.get("data", {})
    
    # Format based on type
    if formatted["type"] == "cli":
        formatted["data"] = _format_cli_knowledge(data)
    elif formatted["type"] == "api":
        formatted["data"] = _format_api_knowledge(data)
    elif formatted["type"] == "package":
        formatted["data"] = _format_package_knowledge(data)
    else:
        # Keep original data for unknown types
        formatted["data"] = data
    
    return formatted


def extract_examples(store: Any, plugin_name: str) -> List[Dict[str, Any]]:
    """Extract and format examples for a plugin.
    
    Args:
        store: Knowledge store instance
        plugin_name: Name of the plugin
        
    Returns:
        List of formatted example dictionaries
    """
    examples = store.get_examples("plugin", plugin_name)
    
    if not examples:
        # Try to get examples from comprehensive knowledge
        knowledge = store.retrieve("comprehensive", plugin_name)
        if knowledge and "examples" in knowledge.get("data", {}):
            examples = knowledge["data"]["examples"]
    
    # Format examples for export
    formatted_examples = []
    for example in (examples or []):
        formatted = {
            "title": example.get("title", "Example"),
            "description": example.get("description", ""),
            "code": example.get("code", ""),
            "language": example.get("language", "python")
        }
        
        # Add optional fields if present
        if "output" in example:
            formatted["expected_output"] = example["output"]
        if "tags" in example:
            formatted["tags"] = example["tags"]
            
        formatted_examples.append(formatted)
    
    return formatted_examples


def merge_knowledge_sources(comprehensive: Optional[Dict[str, Any]],
                          cli: Optional[Dict[str, Any]],
                          api: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge knowledge from different sources into a unified structure.
    
    Args:
        comprehensive: Comprehensive knowledge entry
        cli: CLI-specific knowledge entry
        api: API-specific knowledge entry
        
    Returns:
        Merged knowledge dictionary
    """
    merged = {
        "sources": [],
        "combined_data": {}
    }
    
    # Add available sources
    if comprehensive:
        merged["sources"].append("comprehensive")
        merged["combined_data"].update(comprehensive.get("data", {}))
    
    if cli:
        merged["sources"].append("cli")
        if "cli" not in merged["combined_data"]:
            merged["combined_data"]["cli"] = cli.get("data", {})
    
    if api:
        merged["sources"].append("api")
        if "api" not in merged["combined_data"]:
            merged["combined_data"]["api"] = api.get("data", {})
    
    return merged


# Private helper functions

def _format_cli_knowledge(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format CLI knowledge for export."""
    return {
        "help_text": data.get("help_text", ""),
        "subcommands": data.get("subcommands", {}),
        "global_options": data.get("global_options", []),
        "patterns": data.get("patterns", {}),
        "examples": data.get("examples", [])
    }


def _format_api_knowledge(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format API knowledge for export."""
    return {
        "base_url": data.get("base_url", ""),
        "version": data.get("version", ""),
        "endpoints": data.get("endpoints", []),
        "auth_methods": data.get("auth_methods", []),
        "rate_limits": data.get("rate_limits", {}),
        "schemas": data.get("schemas", {})
    }


def _format_package_knowledge(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format package knowledge for export."""
    info = data.get("info", {})
    return {
        "name": info.get("name", ""),
        "version": info.get("version", ""),
        "summary": info.get("summary", ""),
        "homepage": info.get("home_page", ""),
        "author": info.get("author", ""),
        "license": info.get("license", ""),
        "dependencies": data.get("dependencies", []),
        "type": data.get("type", "python")
    }