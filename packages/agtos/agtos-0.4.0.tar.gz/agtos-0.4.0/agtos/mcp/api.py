"""Public API functions for MCP export.

AI_CONTEXT:
    This module provides the main entry points for MCP export functionality.
    These functions are what external code should use to export plugins
    as MCP tools. They provide a simple interface while delegating to
    the MCPExporter class for implementation.
"""
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from .exporter import MCPExporter


def export_plugin(plugin_name: str, 
                 output_dir: Path,
                 include_knowledge: bool = True,
                 include_examples: bool = True,
                 standalone: bool = True,
                 **kwargs) -> Tuple[Path, Dict[str, Any]]:
    """Export a plugin as an MCP tool.
    
    This is the main entry point for exporting individual plugins.
    
    Args:
        plugin_name: Plugin to export
        output_dir: Where to export
        include_knowledge: Include knowledge base (default: True)
        include_examples: Include usage examples (default: True)
        standalone: Create fully standalone tool (default: True)
        **kwargs: Additional options passed to exporter
        
    Returns:
        Tuple of (export_path, metadata)
        
    Raises:
        ValueError: If plugin is not found
        FileNotFoundError: If plugin source file is not found
        
    Example:
        >>> path, metadata = export_plugin("github", Path("./exports"))
        >>> print(f"Exported to: {path}")
        >>> print(f"Tools: {len(metadata['tools'])}")
    """
    exporter = MCPExporter()
    return exporter.export_plugin_as_mcp(
        plugin_name, 
        output_dir,
        include_knowledge=include_knowledge,
        include_examples=include_examples,
        standalone=standalone,
        **kwargs
    )


def create_tool_bundle(plugin_names: List[str],
                      output_path: Path,
                      package_name: Optional[str] = None,
                      include_knowledge: bool = True,
                      **kwargs) -> Path:
    """Create a bundle of MCP tools.
    
    This function packages multiple plugins into a single distribution.
    
    Args:
        plugin_names: Plugins to bundle
        output_path: Where to save bundle
        package_name: Name for the bundle (default: mcp-tools-bundle)
        include_knowledge: Include knowledge bases (default: True)
        **kwargs: Additional options passed to exporter
        
    Returns:
        Path to the created bundle (zip file)
        
    Example:
        >>> bundle_path = create_tool_bundle(
        ...     ["github", "gitlab", "jira"],
        ...     Path("./bundles"),
        ...     package_name="devops-tools"
        ... )
        >>> print(f"Bundle created: {bundle_path}")
    """
    exporter = MCPExporter()
    return exporter.create_mcp_package(
        plugin_names,
        output_path,
        package_name=package_name,
        include_knowledge=include_knowledge,
        **kwargs
    )


def validate_export_options(**kwargs) -> List[str]:
    """Validate export options before processing.
    
    Args:
        **kwargs: Export options to validate
        
    Returns:
        List of validation errors (empty if valid)
        
    Example:
        >>> errors = validate_export_options(
        ...     standalone=True,
        ...     include_knowledge=True,
        ...     invalid_option="test"
        ... )
        >>> if errors:
        ...     print(f"Validation errors: {errors}")
    """
    errors = []
    
    # Check for valid boolean options
    bool_options = ["include_knowledge", "include_examples", "standalone"]
    for opt in bool_options:
        if opt in kwargs and not isinstance(kwargs[opt], bool):
            errors.append(f"{opt} must be a boolean value")
    
    # Check for unknown options
    valid_options = set(bool_options + ["package_name", "output_dir", "plugin_name", "plugin_names"])
    unknown_options = set(kwargs.keys()) - valid_options
    if unknown_options:
        errors.append(f"Unknown options: {', '.join(unknown_options)}")
    
    return errors