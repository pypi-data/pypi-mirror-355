"""
PURPOSE: MCP server command for running the Meta-MCP server
This module provides the mcp-server command that starts the Meta-MCP
server with context preservation and service aggregation capabilities.

AI_CONTEXT: The mcp-server command starts the Meta-MCP server which acts
as a unified endpoint for Claude Code to connect to. It aggregates multiple
downstream services (CLI tools, REST APIs, other MCP servers, and plugins)
and includes context preservation for maintaining conversation history.
"""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import signal

from ..metamcp.server import MetaMCPServer
from ..project_store import ProjectStore
from ..utils import get_logger

console = Console()
logger = get_logger(__name__)

# PID file location
PID_FILE = Path.home() / ".agtos" / "mcp-server.pid"


def register_mcp_server_command(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the mcp-server command with the main app.
    This command starts the Meta-MCP server for Claude Code integration.
    """
    app.command("mcp-server")(mcp_server)


def mcp_server(
    port: int = typer.Option(8585, "--port", "-p", help="Port to run the server on"),
    host: str = typer.Option("localhost", "--host", help="Host to bind the server to"),
    stdio: bool = typer.Option(True, "--stdio", help="Use stdio transport instead of HTTP"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logs"),
    project: Optional[str] = typer.Option(None, "--project", help="Project name for context isolation"),
    log_requests: bool = typer.Option(False, "--log-requests", help="Log all MCP requests/responses"),
    no_tools: bool = typer.Option(False, "--no-tools", help="Start server without loading any tools"),
) -> None:
    """Start the Meta-MCP server for Claude Code integration.
    
    AI_CONTEXT: Main entry point for MCP server. Handles project resolution,
    server configuration, and delegates to appropriate transport mode.
    """
    try:
        # Resolve project name
        project = _resolve_project_name(project, verbose)
        
        # Show startup message for HTTP mode
        if not stdio:
            show_server_startup_message(host, port, project, debug)
        
        # Create and configure server
        config = _create_server_config(host, port, debug, log_requests, project, no_tools)
        server = MetaMCPServer(config)
        
        # Write PID file for HTTP mode
        if not stdio:
            _write_pid_file()
        
        # Start server in appropriate mode
        _run_server(server, stdio, debug, host, port)
        
    except KeyboardInterrupt:
        _handle_keyboard_interrupt()
    except Exception as e:
        _handle_server_error(e, debug)


def _resolve_project_name(
    project: Optional[str],
    verbose: bool
) -> str:
    """Resolve project name, using default if not specified.
    
    Attempts to get the first available project from ProjectStore,
    falls back to 'default' if none found or on error.
    """
    if project:
        return project
    
    try:
        project_store = ProjectStore()
        projects_dict = project_store.list_projects()
        
        if projects_dict:
            # Get the first project slug
            project = next(iter(projects_dict.keys()), "default")
            if verbose:
                console.print(f"[dim]Using project: {project}[/dim]")
        else:
            project = "default"
            if verbose:
                console.print("[dim]No projects found, using default context[/dim]")
    except Exception:
        # If project store fails, just use default
        project = "default"
        if verbose:
            console.print("[dim]Using default project context[/dim]")
    
    return project


def _create_server_config(
    host: str,
    port: int,
    debug: bool,
    log_requests: bool,
    project: str,
    no_tools: bool
) -> Dict[str, Any]:
    """Create server configuration dictionary."""
    return {
        "host": host,
        "port": port,
        "debug": debug,
        "log_requests": log_requests,
        "project_name": project,
        "no_tools": no_tools,
        "services": []  # Services will be auto-discovered unless no_tools is True
    }


def _run_server(
    server: MetaMCPServer,
    stdio: bool,
    debug: bool,
    host: str,
    port: int
) -> None:
    """Run the server in appropriate transport mode."""
    if stdio:
        _run_stdio_mode(server, debug)
    else:
        _run_http_mode(server, host, port)


def _run_stdio_mode(
    server: MetaMCPServer,
    debug: bool
) -> None:
    """Run server in stdio mode for Claude Code.
    
    Redirects stdout to stderr when not in debug mode to avoid
    interfering with JSON-RPC communication.
    """
    if not debug:
        # Redirect stdout to stderr to avoid interfering with JSON-RPC
        import logging
        for handler in logging.root.handlers:
            if hasattr(handler, 'stream') and handler.stream == sys.stdout:
                handler.stream = sys.stderr
    
    logger.info("Starting Meta-MCP server in stdio mode")
    asyncio.run(server.start_stdio())


def _run_http_mode(
    server: MetaMCPServer,
    host: str,
    port: int
) -> None:
    """Run server in HTTP mode."""
    logger.info(f"Starting Meta-MCP server on {host}:{port}")
    try:
        asyncio.run(server.start(host, port))
    finally:
        _cleanup_on_exit()


def _handle_keyboard_interrupt() -> None:
    """Handle Ctrl+C gracefully."""
    console.print("\n[yellow]Server stopped by user[/yellow]")
    _remove_pid_file()
    sys.exit(0)


def _handle_server_error(
    error: Exception,
    debug: bool
) -> None:
    """Handle server errors with optional traceback."""
    console.print(f"[red]Error:[/red] {error}")
    if debug:
        import traceback
        traceback.print_exc()
    raise typer.Exit(1)


def show_server_startup_message(host: str, port: int, project: str, debug: bool) -> None:
    """
    AI_CONTEXT: Shows a helpful startup message with connection instructions.
    Includes information about context preservation if available.
    """
    from ..context import ContextManager
    
    # Check for existing context
    context_info = ""
    try:
        context_manager = ContextManager(project)
        conversations = context_manager.list_conversations()
        if conversations:
            context_info = f"\n[cyan]✨ Found {len(conversations)} previous conversation(s)[/cyan]"
    except:
        pass
    
    debug_info = "\n[yellow]Debug mode enabled - verbose logging active[/yellow]" if debug else ""
    
    message = f"""
[green]Starting Meta-MCP Server[/green]

• Server: http://{host}:{port}
• Project: {project}{context_info}{debug_info}
• Press Ctrl+C to stop

[yellow]Connect from Claude Code:[/yellow]
1. Run: [cyan]claude[/cyan]
2. The server will be auto-discovered
3. All tools will be available immediately

[dim]Aggregating: CLI tools, REST APIs, Plugins, MCP servers[/dim]
"""
    
    console.print(Panel(message.strip(), title="🚀 Meta-MCP Server", border_style="green"))


def _write_pid_file() -> None:
    """Write the current process ID to a PID file."""
    try:
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()))
        logger.debug(f"Wrote PID {os.getpid()} to {PID_FILE}")
    except Exception as e:
        logger.warning(f"Failed to write PID file: {e}")


def _remove_pid_file() -> None:
    """Remove the PID file if it exists."""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.debug(f"Removed PID file {PID_FILE}")
    except Exception as e:
        logger.warning(f"Failed to remove PID file: {e}")


def _cleanup_on_exit() -> None:
    """Clean up PID file on normal exit."""
    _remove_pid_file()