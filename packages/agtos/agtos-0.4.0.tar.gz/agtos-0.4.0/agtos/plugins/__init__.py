"""Minimal plugins module for MCP server.

This module provides a minimal implementation to allow the MCP server
to start without errors.
"""

from pathlib import Path
import json
import importlib.util
import logging
import os
from typing import Optional

from .tool_creator import get_tool_creator_tools
from .tool_simplifier import get_tool_simplifier_tools
from .ephemeral_creator import get_ephemeral_creator_tools

logger = logging.getLogger(__name__)


def get_all_tools():
    """Return production tools dictionary.
    
    AI_CONTEXT: This function returns tools for production use.
    Test tools are excluded unless AGTOS_DEV_MODE is set.
    
    Returns:
        Dictionary with production tools
    """
    tools = {}
    
    # Load test tools only in development mode
    if os.getenv('AGTOS_DEV_MODE', '').lower() in ('true', '1', 'yes'):
        # Add httpbin tools for testing
        try:
            from .httpbin import get_httpbin_tools
            httpbin_tools = get_httpbin_tools()
            tools.update(httpbin_tools)
            logger.info("Loaded httpbin test tools (dev mode)")
        except ImportError:
            logger.debug("httpbin tools not available")
    
    # Add tool creator tools (always available)
    tool_creator_tools = get_tool_creator_tools()
    tools.update(tool_creator_tools)
    
    # Add tool simplifier tools (always available)
    tool_simplifier_tools = get_tool_simplifier_tools()
    tools.update(tool_simplifier_tools)
    
    # Add ephemeral creator tools (always available)
    ephemeral_creator_tools = get_ephemeral_creator_tools()
    tools.update(ephemeral_creator_tools)
    
    # Add user-created tools (filtered)
    user_tools = load_user_tools()
    tools.update(user_tools)
    
    return tools


def load_user_tools() -> dict:
    """Load user-created tools from ~/.agtos/user_tools directory.
    
    AI_CONTEXT: This function provides basic user tool loading for the plugin system.
    The hot reloader handles dynamic updates, but this ensures user tools are available
    at startup even if hot reload is disabled.
    
    Test tools (prefixed with test_ or _test) are excluded in production.
    
    Returns:
        Dictionary of user tools
    """
    user_tools = {}
    user_tools_dir = Path.home() / ".agtos" / "user_tools"
    
    if not user_tools_dir.exists():
        return user_tools
    
    for tool_file in user_tools_dir.glob("*.py"):
        # Skip hidden files and test files
        if tool_file.name.startswith("_") or _is_test_tool(tool_file.stem):
            continue
            
        try:
            # Load the Python module
            spec = importlib.util.spec_from_file_location(
                f"user_tools.{tool_file.stem}",
                tool_file
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for a class that might be the tool
                for attr_name in dir(module):
                    if attr_name.startswith("_"):
                        continue
                        
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):  # It's a class
                        try:
                            # Create instance and extract methods
                            instance = attr()
                            
                            # Look for methods that should be tools
                            for method_name in dir(instance):
                                if method_name.startswith("_"):
                                    continue
                                
                                # Skip common Python object methods
                                if method_name in ['add_note', 'with_traceback', '__class__', '__delattr__', 
                                                  '__dict__', '__dir__', '__doc__', '__eq__', '__format__', 
                                                  '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__',
                                                  '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__',
                                                  '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
                                                  '__sizeof__', '__str__', '__subclasshook__', '__weakref__',
                                                  'name', 'description', '_session']:
                                    continue
                                    
                                method = getattr(instance, method_name)
                                if callable(method):
                                    # Get tool info from metadata (includes proper name)
                                    tool_name, description, schema = _get_tool_info_from_metadata(tool_file, method_name)
                                    
                                    # Skip test tools unless in dev mode
                                    if _is_test_tool(tool_name):
                                        continue
                                    
                                    # Use method docstring if no description in metadata
                                    if description == f"User tool: {method_name}" and method.__doc__:
                                        description = method.__doc__
                                    
                                    # Check if we should use compound name from MCP schema
                                    # This ensures Claude sees the same name as in the metadata
                                    compound_name = f"{tool_file.stem}_{method_name}"
                                    mcp_tool_name = _get_mcp_tool_name_from_metadata(tool_file, method_name)
                                    
                                    # Create tool entry
                                    tool_entry = {
                                        "func": method,
                                        "description": description,
                                        "schema": schema
                                    }
                                    
                                    # Register with both names if MCP name differs
                                    if mcp_tool_name and mcp_tool_name != tool_name:
                                        # Register with compound name (what Claude sees)
                                        user_tools[mcp_tool_name] = tool_entry
                                        logger.info(f"Loaded user tool: {mcp_tool_name}")
                                        
                                        # Also register with base name for backward compatibility
                                        user_tools[tool_name] = tool_entry
                                        logger.info(f"Also registered as: {tool_name}")
                                    else:
                                        # Just register with the single name
                                        user_tools[tool_name] = tool_entry
                                        logger.info(f"Loaded user tool: {tool_name}")
                                    
                        except Exception as e:
                            logger.warning(f"Failed to instantiate {attr_name} from {tool_file}: {e}")
                            
        except Exception as e:
            logger.error(f"Failed to load user tool {tool_file}: {e}")
    
    return user_tools


def _extract_schema_from_metadata(tool_file: Path, method_name: str) -> dict:
    """Extract schema from metadata JSON file if available.
    
    Args:
        tool_file: Path to the tool Python file
        method_name: Name of the method
        
    Returns:
        Schema dictionary or default schema
    """
    metadata_file = tool_file.with_suffix(".json")
    
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text())
            
            # Check if MCP schema is available
            if "mcp_schema" in metadata and "tools" in metadata["mcp_schema"]:
                # Find the schema for this specific method
                for tool in metadata["mcp_schema"]["tools"]:
                    if method_name in tool.get("name", ""):
                        return tool.get("inputSchema", {})
                        
        except Exception as e:
            logger.warning(f"Failed to load metadata for {tool_file}: {e}")
    
    # Return default schema
    return {
        "type": "object",
        "properties": {},
        "additionalProperties": True
    }


def _get_tool_info_from_metadata(tool_file: Path, method_name: str) -> tuple:
    """Extract tool name, description, and schema from metadata.
    
    Args:
        tool_file: Path to the tool Python file
        method_name: Name of the method
        
    Returns:
        Tuple of (tool_name, description, schema)
    """
    # Try active directory first, then fall back to user_tools root
    active_metadata = Path.home() / ".agtos" / "user_tools" / "active" / f"{tool_file.stem}.json"
    root_metadata = tool_file.with_suffix(".json")
    
    metadata_file = active_metadata if active_metadata.exists() else root_metadata
    
    # Default values
    default_tool_name = f"{tool_file.stem}_{method_name}"
    default_description = f"User tool: {method_name}"
    default_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": True
    }
    
    if not metadata_file.exists():
        return default_tool_name, default_description, default_schema
        
    try:
        metadata = json.loads(metadata_file.read_text())
        
        # Check if MCP schema is available
        if "mcp_schema" in metadata and "tools" in metadata["mcp_schema"]:
            # Find the schema for this specific method
            for tool in metadata["mcp_schema"]["tools"]:
                mcp_tool_name = tool.get("name", "")
                if method_name in mcp_tool_name:
                    # Use the top-level tool name from metadata
                    simple_name = metadata.get("name", tool_file.stem)
                    # Use description from the MCP tool or fall back to top-level description
                    description = tool.get("description", metadata.get("description", default_description))
                    schema = tool.get("inputSchema", default_schema)
                    
                    # Always use the simple name from metadata
                    # The MCP schema already has the full name if needed
                    return simple_name, description, schema
                    
    except Exception as e:
        logger.warning(f"Failed to load metadata for {tool_file}: {e}")
    
    return default_tool_name, default_description, default_schema


def _get_mcp_tool_name_from_metadata(tool_file: Path, method_name: str) -> Optional[str]:
    """Get the MCP tool name from metadata for a specific method.
    
    Args:
        tool_file: Path to the tool Python file
        method_name: Name of the method
        
    Returns:
        MCP tool name or None if not found
    """
    # Try active directory first, then fall back to user_tools root
    active_metadata = Path.home() / ".agtos" / "user_tools" / "active" / f"{tool_file.stem}.json"
    root_metadata = tool_file.with_suffix(".json")
    
    metadata_file = active_metadata if active_metadata.exists() else root_metadata
    
    if not metadata_file.exists():
        return None
        
    try:
        metadata = json.loads(metadata_file.read_text())
        
        # Check if MCP schema is available
        if "mcp_schema" in metadata and "tools" in metadata["mcp_schema"]:
            # Find the schema for this specific method
            for tool in metadata["mcp_schema"]["tools"]:
                mcp_tool_name = tool.get("name", "")
                # Check if this tool corresponds to our method
                if method_name in mcp_tool_name or mcp_tool_name.endswith(f"_{method_name}"):
                    return mcp_tool_name
                    
    except Exception as e:
        logger.warning(f"Failed to get MCP tool name from metadata for {tool_file}: {e}")
    
    return None


def _is_test_tool(name: str) -> bool:
    """Check if a tool name indicates it's a test tool.
    
    Args:
        name: Tool name to check
        
    Returns:
        True if it's a test tool, False otherwise
    """
    # Skip test tools unless in dev mode
    if os.getenv('AGTOS_DEV_MODE', '').lower() in ('true', '1', 'yes'):
        return False
    
    # Common test patterns
    test_patterns = [
        'test_', '_test', 'testing', 'demo_', '_demo',
        'example_', '_example', 'sample_', '_sample',
        'tmp_', '_tmp', 'temp_', '_temp'
    ]
    
    name_lower = name.lower()
    
    # Check if name starts or ends with test patterns
    for pattern in test_patterns:
        if name_lower.startswith(pattern) or name_lower.endswith(pattern):
            return True
    
    # Check for specific test tool names
    test_names = {'echo', 'hello_world', 'foo', 'bar', 'baz'}
    if name_lower in test_names:
        return True
    
    return False


def validate_tool_schema(tool_name: str, tool_data: dict) -> bool:
    """Validate a tool schema.
    
    Args:
        tool_name: Name of the tool
        tool_data: Tool data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["schema", "func", "description"]
    
    # Check required fields
    for field in required_fields:
        if field not in tool_data:
            return False
    
    # Check func is callable
    if not callable(tool_data.get("func")):
        return False
    
    # Check schema is dict
    if not isinstance(tool_data.get("schema"), dict):
        return False
    
    return True