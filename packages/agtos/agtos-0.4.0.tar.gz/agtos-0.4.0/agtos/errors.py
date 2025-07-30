"""
PURPOSE: Centralized error handling for agentctl
This module provides user-friendly error messages and helpful suggestions
for common issues users might encounter.

AI_CONTEXT: This module improves the developer experience by providing
clear, actionable error messages. It includes suggestions for fixing
common issues and optionally shows stack traces only in debug mode.
"""

import sys
import traceback
import json
from typing import Optional, Dict, Any
from rich.console import Console

console = Console()


class AgentCtlError(Exception):
    """Base exception for all agentctl errors.
    
    AI_CONTEXT: This base class provides:
    - User-friendly error messages
    - Suggestions for fixing the error
    - Optional stack trace display
    - Error categorization for better handling
    """
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        category: str = "general",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        self.category = category
        self.details = details or {}


class CredentialError(AgentCtlError):
    """Raised when there are issues with credentials."""
    
    def __init__(self, service: str, message: str, suggestion: Optional[str] = None):
        if not suggestion:
            suggestion = f"Try adding the credential with: agentctl add-cred {service}"
        super().__init__(
            message=message,
            suggestion=suggestion,
            category="credential",
            details={"service": service}
        )


class ProjectError(AgentCtlError):
    """Raised when there are issues with projects."""
    
    def __init__(self, project: str, message: str, suggestion: Optional[str] = None):
        if not suggestion:
            suggestion = "List available projects with: agentctl list"
        super().__init__(
            message=message,
            suggestion=suggestion,
            category="project",
            details={"project": project}
        )


class IntegrationError(AgentCtlError):
    """Raised when integration fails."""
    
    def __init__(self, service: str, message: str, suggestion: Optional[str] = None):
        if not suggestion:
            suggestion = (
                f"Check if '{service}' is installed and accessible.\\n"
                "For CLI tools: Ensure it's in your PATH.\\n"
                "For APIs: Verify the service name and network connection."
            )
        super().__init__(
            message=message,
            suggestion=suggestion,
            category="integration",
            details={"service": service}
        )


class MCPError(AgentCtlError):
    """Raised when MCP operations fail."""
    
    def __init__(self, message: str, suggestion: Optional[str] = None):
        if not suggestion:
            suggestion = (
                "Check the Meta-MCP server logs with: agentctl mcp-server --debug\\n"
                "Verify Claude Code configuration with: agentctl claude-setup"
            )
        super().__init__(
            message=message,
            suggestion=suggestion,
            category="mcp"
        )


class ConfigurationError(AgentCtlError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, config_item: str, message: str, suggestion: Optional[str] = None):
        if not suggestion:
            suggestion = (
                f"Check your configuration for '{config_item}'.\\n"
                "Run 'agtos doctor' to diagnose configuration issues."
            )
        super().__init__(
            message=message,
            suggestion=suggestion,
            category="configuration",
            details={"config_item": config_item}
        )


class ToolExecutionError(AgentCtlError):
    """Raised when a tool execution fails."""
    
    def __init__(self, tool_name: str, message: str, suggestion: Optional[str] = None):
        if not suggestion:
            suggestion = (
                f"Check the tool '{tool_name}' implementation.\\n"
                "Verify all required parameters are provided correctly."
            )
        super().__init__(
            message=message,
            suggestion=suggestion,
            category="tool_execution",
            details={"tool": tool_name}
        )


def handle_error(error: Exception, debug: bool = False) -> None:
    """
    AI_CONTEXT: Central error handler that formats and displays errors.
    Shows user-friendly messages with suggestions, optionally showing
    stack traces in debug mode.
    """
    # Handle AgentCtlError with nice formatting
    if isinstance(error, AgentCtlError):
        console.print(f"\\n[red]Error:[/red] {error.message}")
        
        if error.suggestion:
            console.print(f"\\n[yellow]Suggestion:[/yellow] {error.suggestion}")
        
        if error.details and debug:
            console.print(f"\\n[dim]Details:[/dim]")
            for key, value in error.details.items():
                console.print(f"  {key}: {value}")
        
        if debug:
            console.print(f"\\n[dim]Category:[/dim] {error.category}")
            console.print("\\n[dim]Stack trace:[/dim]")
            traceback.print_exc()
    
    # Handle KeyboardInterrupt specially
    elif isinstance(error, KeyboardInterrupt):
        console.print("\\n[yellow]Interrupted by user[/yellow]")
    
    # Handle generic exceptions
    else:
        console.print(f"\\n[red]Error:[/red] {str(error)}")
        
        # Try to provide helpful suggestions based on error type
        suggestion = get_generic_suggestion(error)
        if suggestion:
            console.print(f"\\n[yellow]Suggestion:[/yellow] {suggestion}")
        
        if debug:
            console.print("\\n[dim]Stack trace:[/dim]")
            traceback.print_exc()
        else:
            console.print("\\n[dim]Run with --debug for more details[/dim]")


def get_generic_suggestion(error: Exception) -> Optional[str]:
    """
    AI_CONTEXT: Provides suggestions for common generic errors.
    This helps users even when we don't have specific error handling.
    """
    error_str = str(error).lower()
    
    # File/path errors
    if "no such file" in error_str or "not found" in error_str:
        return "Check that the file or directory exists and you have permission to access it."
    
    # Permission errors
    elif "permission denied" in error_str or "access denied" in error_str:
        return "Check file permissions or try running with appropriate privileges."
    
    # Network errors
    elif "connection" in error_str or "network" in error_str:
        return "Check your internet connection and firewall settings."
    
    # Import errors
    elif isinstance(error, ImportError) or isinstance(error, ModuleNotFoundError):
        return "Try reinstalling agentctl: pip install --upgrade agtos"
    
    # JSON errors
    elif isinstance(error, (json.JSONDecodeError, ValueError)) and "json" in error_str:
        return "Check that the file contains valid JSON format."
    
    return None


def wrap_command(func):
    """
    AI_CONTEXT: Decorator for CLI commands that provides consistent error handling.
    Use this to wrap command functions for better error messages.
    
    Example:
        @wrap_command
        def my_command(debug: bool = False):
            # command implementation
    """
    def wrapper(*args, **kwargs):
        debug = kwargs.get('debug', False)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e, debug=debug)
            sys.exit(1)
    
    return wrapper


# Common error messages as constants for consistency
ERROR_MESSAGES = {
    "CLAUDE_NOT_INSTALLED": "Claude Code CLI is not installed",
    "INVALID_PROJECT": "Project not found or invalid",
    "NO_CREDENTIALS": "No credentials found in storage",
    "PLUGIN_NOT_FOUND": "Plugin not found",
    "SERVICE_UNAVAILABLE": "Service is not available",
    "INVALID_CONFIG": "Configuration is invalid or corrupted",
    "MCP_CONNECTION_FAILED": "Failed to connect to MCP server",
    "KNOWLEDGE_ACQUISITION_FAILED": "Failed to acquire knowledge about the service",
}

# Export all error classes
__all__ = [
    "AgentCtlError",
    "CredentialError",
    "ProjectError",
    "IntegrationError",
    "MCPError",
    "ConfigurationError",
    "ToolExecutionError",
    "handle_error",
    "wrap_command",
    "ERROR_MESSAGES"
]