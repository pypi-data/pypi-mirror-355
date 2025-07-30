"""Shared utilities for MCP export functionality.

AI_CONTEXT:
    This module contains common constants and utility functions used across
    the MCP export package. Keeping these centralized reduces duplication
    and makes the codebase more maintainable.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List
import zipfile

# Constants
MCP_VERSION = "2025-03-26"
DEFAULT_PORT = 4405
DEFAULT_HOST = "localhost"

# Common import mappings for requirement extraction
IMPORT_TO_REQUIREMENT = {
    "requests": "requests>=2.31.0",
    "yaml": "pyyaml>=6.0",
    "boto3": "boto3>=1.26.0",
    "google": "google-api-python-client>=2.0.0",
    "azure": "azure-core>=1.26.0",
    "pandas": "pandas>=2.0.0",
    "numpy": "numpy>=1.24.0",
    "aiohttp": "aiohttp>=3.8.0",
    "httpx": "httpx>=0.24.0",
    "pydantic": "pydantic>=2.0.0",
    "sqlalchemy": "sqlalchemy>=2.0.0",
    "psycopg2": "psycopg2-binary>=2.9.0",
    "redis": "redis>=4.5.0",
    "celery": "celery>=5.2.0",
    "jinja2": "jinja2>=3.1.0",
    "click": "click>=8.1.0",
    "typer": "typer>=0.9.0",
    "rich": "rich>=13.0.0"
}

def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        The path object for chaining
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

def write_json(path: Path, data: Dict[str, Any], indent: int = 2) -> None:
    """Write JSON data to a file.
    
    Args:
        path: File path to write to
        data: Data to serialize as JSON
        indent: Indentation level for pretty printing
    """
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent)

def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Write YAML data to a file.
    
    Args:
        path: File path to write to
        data: Data to serialize as YAML
    """
    with open(path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def write_requirements(path: Path, requirements: List[str]) -> None:
    """Write a requirements.txt file.
    
    Args:
        path: File path to write to
        requirements: List of requirement strings
    """
    # Sort and deduplicate requirements
    unique_reqs = sorted(set(requirements))
    path.write_text("\n".join(unique_reqs))

def create_zip_package(source_dir: Path, output_path: Path) -> Path:
    """Create a zip package from a directory.
    
    Args:
        source_dir: Directory to package
        output_path: Where to save the zip file
        
    Returns:
        Path to the created zip file
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                arc_name = file_path.relative_to(source_dir.parent)
                zf.write(file_path, arc_name)
    return output_path

def make_executable(path: Path) -> None:
    """Make a file executable (Unix-like systems).
    
    Args:
        path: File path to make executable
    """
    path.chmod(0o755)