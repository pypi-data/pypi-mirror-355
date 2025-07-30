"""Base utilities and shared imports for knowledge acquisition.

PURPOSE: Shared foundations for all knowledge acquisition modules
CONTEXT: Used by all knowledge classes for common functionality
AI_NOTE: Keep this minimal - only truly shared utilities belong here
"""
from typing import Dict, Any, Optional, Callable
from pathlib import Path


def safe_execute(func: Callable) -> Callable:
    """Decorator for safe execution with consistent error handling.
    
    AI_CONTEXT: This wrapper ensures all knowledge acquisition functions
    return a predictable structure, making error handling consistent.
    
    Returns:
        Dict with keys:
        - success (bool): Whether operation succeeded
        - data (Any): Result data if successful
        - error (str): Error message if failed
    """
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return wrapper


def validate_url(url: str) -> bool:
    """Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL format
    """
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def clean_command_output(output: str) -> str:
    """Clean ANSI codes and extra whitespace from command output.
    
    Args:
        output: Raw command output
        
    Returns:
        Cleaned output string
    """
    import re
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned = ansi_escape.sub('', output)
    
    # Normalize whitespace
    cleaned = '\n'.join(line.rstrip() for line in cleaned.splitlines())
    
    return cleaned.strip()