"""Metadata creation and management for MCP tools.

AI_CONTEXT:
    This module handles all metadata operations for MCP export, including
    creating tool metadata, extracting requirements from plugin files,
    and managing package information. Separated from the main exporter
    to keep responsibilities focused.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from .utils import MCP_VERSION, IMPORT_TO_REQUIREMENT


def create_metadata(plugin_name: str, 
                   plugin: Dict[str, Any], 
                   knowledge_store: Any) -> Dict[str, Any]:
    """Create MCP tool metadata for a plugin.
    
    AI_CONTEXT:
        This function creates comprehensive metadata for an exported MCP tool,
        including tool definitions, requirements, and knowledge base information.
        It queries the knowledge store to enrich metadata with discovered information.
    
    Args:
        plugin_name: Name of the plugin
        plugin: Plugin definition dictionary
        knowledge_store: Knowledge store instance for retrieving plugin info
        
    Returns:
        Complete metadata dictionary for the MCP tool
    """
    # Get knowledge about the plugin
    knowledge = knowledge_store.retrieve("comprehensive", plugin_name)
    
    tools = plugin.get("TOOLS", {})
    
    metadata = {
        "name": f"mcp-tool-{plugin_name}",
        "version": "1.0.0",
        "description": f"MCP tool for {plugin_name} integration",
        "author": "agtos",
        "created_at": datetime.now().isoformat(),
        "source": "agtos",
        "mcp_version": MCP_VERSION,
        "tools": [],
        "requirements": [],
        "knowledge_included": False,
        "examples_included": False
    }
    
    # Add tool definitions
    for tool_name, tool_def in tools.items():
        metadata["tools"].append({
            "name": tool_name,
            "description": tool_def.get("description", ""),
            "schema": tool_def.get("schema", {}),
            "version": tool_def.get("version", "1.0")
        })
    
    # Enrich with knowledge-based information
    if knowledge:
        _enrich_metadata_from_knowledge(metadata, plugin_name, knowledge)
    
    return metadata


def _enrich_metadata_from_knowledge(metadata: Dict[str, Any], 
                                   plugin_name: str,
                                   knowledge: Dict[str, Any]) -> None:
    """Enrich metadata with information from knowledge store.
    
    Args:
        metadata: Metadata dictionary to enrich (modified in place)
        plugin_name: Name of the plugin
        knowledge: Knowledge entry from the store
    """
    data = knowledge.get("data", {})
    
    # Add package information if available
    if data.get("package"):
        pkg_info = data["package"].get("info", {})
        metadata["description"] = pkg_info.get("summary", metadata["description"])
        metadata["original_package"] = {
            "name": plugin_name,
            "version": pkg_info.get("version", ""),
            "type": data["package"].get("type", "unknown"),
            "homepage": pkg_info.get("home_page", ""),
            "author": pkg_info.get("author", "")
        }
    
    # Add API information if available
    elif data.get("api"):
        api_info = data["api"]
        metadata["description"] = api_info.get("description", metadata["description"])
        metadata["api_info"] = {
            "base_url": api_info.get("base_url", ""),
            "version": api_info.get("version", ""),
            "auth_required": bool(api_info.get("auth_methods"))
        }
        if api_info.get("servers"):
            metadata["api_info"]["servers"] = api_info["servers"]
    
    # Add CLI information if available
    elif data.get("cli"):
        cli_info = data["cli"]
        metadata["cli_info"] = {
            "command": plugin_name,
            "subcommands": len(cli_info.get("subcommands", {})),
            "has_help": bool(cli_info.get("help_text"))
        }


def extract_requirements(plugin_file: Path) -> List[str]:
    """Extract Python requirements from a plugin file.
    
    AI_CONTEXT:
        This function analyzes import statements in a Python file to determine
        likely package requirements. It uses a mapping of common imports to
        their corresponding pip packages with recommended versions.
    
    Args:
        plugin_file: Path to the plugin Python file
        
    Returns:
        List of requirement strings (e.g., ["requests>=2.31.0"])
    """
    requirements: Set[str] = set()
    
    # Read plugin file
    content = plugin_file.read_text()
    
    # Look for imports
    import_lines = [
        line.strip() for line in content.split('\n')
        if line.strip().startswith(('import ', 'from '))
    ]
    
    # Check each import against our mapping
    for line in import_lines:
        for pkg, req in IMPORT_TO_REQUIREMENT.items():
            if pkg in line:
                requirements.add(req)
                break
    
    # Always include base requirements for MCP tools
    base_requirements = [
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "requests>=2.31.0"
    ]
    
    requirements.update(base_requirements)
    
    return sorted(requirements)


def validate_metadata(metadata: Dict[str, Any]) -> List[str]:
    """Validate MCP tool metadata for completeness.
    
    Args:
        metadata: Metadata dictionary to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ["name", "version", "description", "tools", "mcp_version"]
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    # Validate tools
    if "tools" in metadata:
        if not isinstance(metadata["tools"], list):
            errors.append("Tools must be a list")
        else:
            for i, tool in enumerate(metadata["tools"]):
                if not isinstance(tool, dict):
                    errors.append(f"Tool {i} must be a dictionary")
                elif "name" not in tool:
                    errors.append(f"Tool {i} missing name")
    
    # Validate version format
    if "version" in metadata:
        version = metadata["version"]
        if not isinstance(version, str) or not version:
            errors.append("Version must be a non-empty string")
    
    return errors


def merge_metadata(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge metadata dictionaries, with updates taking precedence.
    
    Args:
        base: Base metadata dictionary
        updates: Updates to apply
        
    Returns:
        Merged metadata dictionary
    """
    result = base.copy()
    
    for key, value in updates.items():
        if key == "tools" and key in result:
            # Merge tools lists by name
            existing_tools = {t["name"]: t for t in result[key]}
            for tool in value:
                if tool["name"] in existing_tools:
                    existing_tools[tool["name"]].update(tool)
                else:
                    result[key].append(tool)
        elif key == "requirements" and key in result:
            # Merge and deduplicate requirements
            all_reqs = set(result[key]) | set(value)
            result[key] = sorted(all_reqs)
        else:
            result[key] = value
    
    return result