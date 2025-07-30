"""
PURPOSE: MCP server stop command for gracefully shutting down the Meta-MCP server
This module provides the mcp-stop command that stops a running Meta-MCP
server by reading its PID file and sending a termination signal.

AI_CONTEXT: The mcp-stop command looks for a PID file created by mcp-server
when running in HTTP mode. It sends a SIGTERM signal to gracefully shut down
the server process. This doesn't apply to stdio mode since that's managed
by the parent process (Claude).
"""

import os
import signal
import sys
from pathlib import Path
import typer
from rich.console import Console

from ..utils import get_logger

console = Console()
logger = get_logger(__name__)

# PID file location (must match mcp_server.py)
PID_FILE = Path.home() / ".agtos" / "mcp-server.pid"


def register_mcp_stop_command(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the mcp-stop command with the main app.
    This command stops a running Meta-MCP server instance.
    """
    app.command("mcp-stop")(mcp_stop)


def mcp_stop(
    force: bool = typer.Option(False, "--force", "-f", help="Force kill the server process"),
) -> None:
    """Stop the running Meta-MCP server.
    
    AI_CONTEXT: Reads the PID file to find the running server process
    and sends a termination signal. Uses SIGTERM by default for graceful
    shutdown, or SIGKILL if --force is specified.
    """
    try:
        # Check if PID file exists
        if not PID_FILE.exists():
            console.print("[yellow]No running MCP server found[/yellow]")
            console.print("[dim]PID file not found at:[/dim]", PID_FILE)
            raise typer.Exit(0)
        
        # Read PID from file
        try:
            pid_str = PID_FILE.read_text().strip()
            pid = int(pid_str)
        except (ValueError, IOError) as e:
            console.print(f"[red]Error reading PID file:[/red] {e}")
            raise typer.Exit(1)
        
        # Check if process exists
        if not _is_process_running(pid):
            console.print(f"[yellow]Process {pid} is not running[/yellow]")
            _cleanup_stale_pid_file()
            raise typer.Exit(0)
        
        # Send termination signal
        sig = signal.SIGKILL if force else signal.SIGTERM
        sig_name = "SIGKILL" if force else "SIGTERM"
        
        try:
            os.kill(pid, sig)
            console.print(f"[green]Sent {sig_name} to MCP server (PID: {pid})[/green]")
            
            # Wait briefly for graceful shutdown
            if not force:
                import time
                time.sleep(1)
                
                # Check if process stopped
                if _is_process_running(pid):
                    console.print("[yellow]Server still running, use --force to kill[/yellow]")
                else:
                    console.print("[green]✓ MCP server stopped successfully[/green]")
                    _cleanup_stale_pid_file()
            else:
                console.print("[green]✓ MCP server forcefully terminated[/green]")
                _cleanup_stale_pid_file()
                
        except ProcessLookupError:
            console.print("[yellow]Process already terminated[/yellow]")
            _cleanup_stale_pid_file()
        except PermissionError:
            console.print(f"[red]Permission denied:[/red] Cannot stop process {pid}")
            console.print("[dim]Try running with sudo or check process ownership[/dim]")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Stop command cancelled[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running.
    
    Args:
        pid: Process ID to check
        
    Returns:
        True if process is running, False otherwise
    """
    try:
        # Send signal 0 to check if process exists
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't have permission
        return True


def _cleanup_stale_pid_file() -> None:
    """Remove stale PID file."""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.debug(f"Removed stale PID file {PID_FILE}")
    except Exception as e:
        logger.warning(f"Failed to remove PID file: {e}")