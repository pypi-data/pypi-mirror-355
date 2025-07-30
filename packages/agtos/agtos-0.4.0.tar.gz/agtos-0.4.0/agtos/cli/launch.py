"""
PURPOSE: Launch command for starting MCP server and Claude together
This module provides a convenient way to start both the MCP server
and Claude Code in separate terminals with a single command.

AI_CONTEXT: The launch command orchestrates starting the MCP server
in the current terminal and opening Claude in a new terminal window.
This provides the best user experience by keeping logs visible while
allowing interaction with Claude in a dedicated window.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.panel import Panel

from ..utils import open_terminal_tab, ensure_tool_installed, wait_for_port
from ..context import ContextManager
from .run import (
    get_project_for_run,
    collect_credentials,
    prepare_environment,
    start_mcp_server,
    ProjectError
)

console = Console()


def register_launch_command(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the launch command with the main app.
    This command starts both MCP server and Claude Code.
    """
    app.command()(launch)


def launch(
    project: Optional[str] = typer.Argument(None, help="Project slug to run (uses last/default if not specified)"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
    no_claude: bool = typer.Option(False, "--no-claude", help="Don't open Claude (just start MCP server)"),
    claude_command: str = typer.Option("claude", "--claude-command", help="Command to run Claude"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed startup process"),
) -> None:
    """Launch agentctl MCP server and Claude Code together.
    
    This command:
    1. Starts the MCP server in the current terminal
    2. Opens Claude Code in a new terminal window
    3. Shows server logs in the current terminal
    
    Perfect for getting started quickly with both components running.
    """
    try:
        # Step 1: Check Claude is installed (unless --no-claude)
        if not no_claude:
            check_claude_installed(claude_command, verbose)
        
        # Step 2: Get project (reuse from run.py)
        project_obj = get_project_for_run(project, verbose)
        
        # Step 3: Collect credentials (reuse from run.py)
        credentials = collect_credentials(verbose)
        
        # Step 4: Prepare environment (reuse from run.py)
        env = prepare_environment(project_obj, credentials, debug, verbose)
        
        # Step 5: Check for restored context and show launch message
        context_info = check_restored_context(project_obj.get("slug", "default"), verbose)
        show_launch_message(no_claude, context_info)
        
        # Step 6: Launch Claude in new terminal (unless --no-claude)
        if not no_claude:
            launch_claude_terminal(project_obj["path"], claude_command, verbose)
        
        # Step 7: Start MCP server in current terminal
        # This blocks until server is stopped
        start_mcp_server(env, debug, verbose)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Launch cancelled by user[/yellow]")
        sys.exit(0)
    except ProjectError as e:
        console.print(f"[red]Project Error:[/red] {e.message}")
        if e.suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {e.suggestion}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def check_claude_installed(claude_command: str, verbose: bool = False) -> None:
    """
    AI_CONTEXT: Checks if Claude CLI is installed and accessible.
    Extracts the base command from the full command string.
    """
    # Extract the base command (e.g., "claude" from "claude")
    base_command = claude_command.split()[0]
    
    if not ensure_tool_installed(base_command):
        console.print(f"[red]Error:[/red] {base_command} CLI not found")
        console.print("\n[yellow]To install Claude Code:[/yellow]")
        console.print("  npm install -g @anthropic-ai/claude-code")
        console.print("  # or")
        console.print("  brew install claude")
        console.print("\nThen run this command again.")
        raise typer.Exit(1)
    
    if verbose:
        console.print(f"[green]✓[/green] {base_command} CLI found")


def check_restored_context(project_name: str, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    AI_CONTEXT: Checks if there's a previous conversation context that can be restored.
    Returns context info if available, None otherwise.
    """
    try:
        context_manager = ContextManager(project_name)
        
        # Check for last conversation
        last_conversation_id = context_manager.get_preference("last_conversation_id")
        
        if last_conversation_id:
            conversations = context_manager.list_conversations()
            if conversations:
                # Find the last conversation
                for conv in conversations:
                    if conv["conversation_id"] == last_conversation_id:
                        if verbose:
                            console.print(f"[dim]Found previous session: {conv['message_count']} messages[/dim]")
                        return {
                            "conversation_id": last_conversation_id,
                            "message_count": conv["message_count"],
                            "last_activity": conv["last_activity"]
                        }
        
        return None
        
    except Exception as e:
        if verbose:
            console.print(f"[dim]No previous context found: {e}[/dim]")
        return None


def show_launch_message(no_claude: bool, context_info: Optional[Dict[str, Any]] = None) -> None:
    """
    AI_CONTEXT: Shows an informative message about what's being launched.
    Adapts message based on whether Claude is being opened and if context was restored.
    """
    # Build context restoration message if applicable
    context_msg = ""
    if context_info:
        from datetime import datetime
        try:
            last_activity = datetime.fromisoformat(context_info["last_activity"])
            time_ago = datetime.now() - last_activity
            
            if time_ago.days > 0:
                time_str = f"{time_ago.days} day(s) ago"
            elif time_ago.seconds > 3600:
                time_str = f"{time_ago.seconds // 3600} hour(s) ago"
            else:
                time_str = f"{time_ago.seconds // 60} minute(s) ago"
                
            context_msg = f"\n[cyan]✨ Restored context:[/cyan] {context_info['message_count']} messages from {time_str}"
        except:
            context_msg = f"\n[cyan]✨ Restored context:[/cyan] {context_info['message_count']} messages from previous session"
    
    if no_claude:
        message = f"""
[green]Starting agentctl MCP server...[/green]

• Server will run on port 8585
• Keep this terminal open for logs
• Press Ctrl+C to stop the server{context_msg}

[yellow]To connect Claude Code:[/yellow]
Run in another terminal: [cyan]claude[/cyan]
"""
    else:
        message = f"""
[green]Launching agentctl + Claude Code...[/green]

• MCP server starting on port 8585
• Claude opening in new terminal
• Keep this terminal open for logs
• Press Ctrl+C to stop everything{context_msg}

[yellow]What's happening:[/yellow]
1. MCP server starts here (logs visible)
2. New terminal opens with Claude
3. Claude auto-connects to agentctl
"""
    
    console.print(Panel(message.strip(), title="🚀 agentctl launch", border_style="green"))


def launch_claude_terminal(project_path: str, claude_command: str, verbose: bool = False) -> None:
    """
    AI_CONTEXT: Opens a new terminal tab and runs Claude.
    Uses the Terminal automation from utils.py.
    Waits briefly to ensure MCP server is ready first.
    """
    if verbose:
        console.print("[dim]Opening Claude in new terminal...[/dim]")
    
    # Give MCP server a moment to start
    console.print("[dim]Waiting for MCP server to be ready...[/dim]")
    
    # Wait for port 8585 to be available
    if wait_for_port(8585, timeout=5):
        console.print("[green]✓[/green] MCP server is ready")
    else:
        console.print("[yellow]⚠[/yellow] MCP server may still be starting")
    
    # Open Claude in new terminal
    try:
        open_terminal_tab(project_path, claude_command)
        console.print("[green]✓[/green] Claude launched in new terminal")
        console.print("[dim]Switch to the new terminal tab to interact with Claude[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not open new terminal: {e}")
        console.print(f"[yellow]Please run manually:[/yellow] {claude_command}")
    
    # Brief pause to let terminal open
    time.sleep(1)