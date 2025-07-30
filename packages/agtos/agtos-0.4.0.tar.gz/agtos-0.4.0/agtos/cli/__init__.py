"""
PURPOSE: CLI module initialization and command registration
This module serves as the entry point for all CLI commands, maintaining
backward compatibility while organizing commands into focused submodules.

AI_CONTEXT: This is the main orchestrator for CLI commands. Each command
group is implemented in its own module for better AI navigation. The main
app instance is created here and commands are registered from submodules.
"""

from typing import Optional
import typer
from pathlib import Path
import os
import sys

# Create the main Typer app
app = typer.Typer(
    help="""agtos - Agent Operating System

The Operating System for AI Agents. Run 'agtos' to launch the interactive terminal.

[bold cyan]Primary Usage:[/bold cyan]
  agtos              Launch the interactive Terminal UI in current directory
  agtos [PATH]       Launch in a specific project directory
  agtos --help       Show this help message
  agtos --version    Show version information

[bold yellow]Examples:[/bold yellow]
  agtos              Start in current directory
  agtos ~/project    Start in ~/project directory
  agtos .            Explicitly start in current directory

[bold yellow]For Complex Tasks:[/bold yellow]
  Use the Terminal UI and select "Open Claude" to work through natural language.
  Claude can handle git operations, deployments, API calls, and complex workflows.

[bold green]Quick Admin Tasks:[/bold green]
  Use the Terminal UI for project switching, credential management, and status checks.

[dim]Run 'agtos' without arguments to get started![/dim]""",
    no_args_is_help=False,  # Changed to False to handle smart default behavior
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,  # Allow callback to handle no arguments
)

# Import command groups from submodules
from .project import register_project_commands
from .credentials import register_credential_commands
from .run import register_run_command
from .launch import register_launch_command
from .integration import register_integration_commands
from .export import register_export_command
from .knowledge import register_knowledge_command
from .diagnostics import register_diagnostic_commands
from .claude_setup import register_claude_setup_command
from .codex_setup import register_codex_setup_command
from .mcp_server import register_mcp_server_command
from .mcp_stop import register_mcp_stop_command
from .workflow import register_workflow_command
from .completion import register_completion_commands
# from .interactive import register_interactive_command  # TODO: Add prompt_toolkit to dependencies

# Make tools import conditional
try:
    from .tools import register_tools_commands
    TOOLS_COMMANDS_AVAILABLE = True
except ImportError:
    register_tools_commands = None
    TOOLS_COMMANDS_AVAILABLE = False

# Import workflow updates app
try:
    from .workflow_updates import app as workflow_updates_app
    WORKFLOW_UPDATES_AVAILABLE = True
except ImportError:
    workflow_updates_app = None
    WORKFLOW_UPDATES_AVAILABLE = False
    
from .github import app as github_app
from .auth import app as auth_app
from .tutorial import app as tutorial_app

# Import error handling
from ..errors import handle_error

# Check if we're in developer mode
IS_DEV_MODE = "--dev" in sys.argv or os.environ.get("AGTOS_DEV_MODE", "").lower() == "true"

# Always register essential commands
register_claude_setup_command(app)
register_mcp_server_command(app)
register_mcp_stop_command(app)
register_diagnostic_commands(app)
# Register tools commands if available
if TOOLS_COMMANDS_AVAILABLE:
    register_tools_commands(app)  # Keep visible for browsing available tools
# Register workflow updates commands if available
if WORKFLOW_UPDATES_AVAILABLE:
    app.add_typer(workflow_updates_app, name="workflow-updates", help="Check and manage workflow dependencies")
app.add_typer(github_app, name="github")  # GitHub auth is essential for private repo
app.add_typer(auth_app, name="auth")  # Authentication commands

# Deprecated user-facing commands (hidden unless --dev)
if IS_DEV_MODE:
    # Developer tools
    register_project_commands(app)
    register_credential_commands(app)
    register_run_command(app)
    register_launch_command(app)
    register_integration_commands(app)
    register_export_command(app)
    register_knowledge_command(app)
    register_workflow_command(app)
    register_completion_commands(app)
    register_codex_setup_command(app)
    app.add_typer(tutorial_app, name="tutorial", help="Tutorial management (dev only)")
    # register_interactive_command(app)  # TODO: Add to dev tools

# Import bootstrap wizard from utils
from ..utils import bootstrap_wizard

# Import for smart default behavior
from rich.console import Console
from rich.panel import Panel
from .claude_setup import find_claude_config, read_claude_config
import json

console = Console()

def handle_smart_default(project_path=None):
    """
    AI_CONTEXT: Implements smart default behavior when agentctl is run without arguments.
    Checks system state and decides whether to run setup, launch, or show status.
    Can optionally accept a project path to change directory before launching.
    """
    # Handle project path if provided (from command line argument)
    # Note: Environment variable is already handled in main_callback
    if project_path:
        project_path = Path(project_path).expanduser().resolve()
        
        # Validate the path
        if not project_path.exists():
            console.print(f"[red]Error: Path does not exist: {project_path}[/red]")
            raise typer.Exit(1)
        
        if not project_path.is_dir():
            console.print(f"[red]Error: Path is not a directory: {project_path}[/red]")
            raise typer.Exit(1)
        
        # Change to the project directory
        try:
            os.chdir(project_path)
            console.print(f"[green]Changed to project directory: {project_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error changing directory: {e}[/red]")
            raise typer.Exit(1)
    
    config_dir = Path.home() / ".agtos"
    first_run_marker = config_dir / ".initialized"
    
    # Check initialization state
    is_initialized = first_run_marker.exists()
    
    # Check Claude configuration
    claude_config_path = find_claude_config()
    has_claude_config = False
    is_agtos_configured = False
    
    if claude_config_path and claude_config_path.exists():
        has_claude_config = True
        try:
            config = read_claude_config(claude_config_path)
            # Check if agentctl is configured
            if "agtos" in config.get("mcpServers", {}):
                is_agtos_configured = True
        except:
            pass
    
    # Decision logic
    if not is_initialized:
        # First time running - show welcome and run setup
        console.print(Panel.fit(
            "[bold cyan]Welcome to agtOS![/bold cyan]\n\n"
            "The Operating System for AI Agents\n\n"
            "Let's get you set up for the first time.",
            border_style="cyan"
        ))
        bootstrap_wizard()
        # Mark as initialized
        first_run_marker.parent.mkdir(parents=True, exist_ok=True)
        first_run_marker.touch()
        
        # After bootstrap, prompt for Claude setup
        console.print("\n[yellow]Would you like to configure agtOS with Claude Code?[/yellow]")
        from rich.prompt import Confirm
        if Confirm.ask("Set up Claude integration now?", default=True):
            from .claude_setup import claude_setup
            # Run claude setup with defaults - no context needed
            claude_setup(port=8585, name="agtos", force=False)
    
    elif is_initialized and is_agtos_configured:
        # Everything is set up - launch the TUI!
        from ..tui import launch_tui
        
        # Don't start an HTTP server - Claude will use stdio mode
        # The TUI is just for configuration and monitoring
        # When user clicks "Open Claude", Claude will start its own
        # stdio server instance based on the configuration
        
        # Launch the interactive TUI
        launch_tui()
    
    elif is_initialized and not is_agtos_configured:
        # Initialized but not configured with Claude
        console.print(Panel.fit(
            "[bold yellow]Almost there![/bold yellow]\n\n"
            "agtos is initialized but not configured with Claude Code.",
            border_style="yellow"
        ))
        
        console.print("\nTo complete setup:")
        console.print("1. Configure Claude: [cyan]agentctl claude-setup[/cyan]")
        console.print("2. Then run: [cyan]agentctl[/cyan] to launch both")
        console.print("\nOr run the MCP server directly: [cyan]agentctl mcp-server[/cyan]")
    
    else:
        # Shouldn't happen, but show help as fallback
        ctx = typer.Context(command=app)
        print(ctx.get_help())

# First-run check
def check_first_run():
    """
    AI_CONTEXT: Checks if this is the first run and runs bootstrap wizard.
    This maintains compatibility with the original CLI behavior.
    """
    config_dir = Path.home() / ".agtos"
    first_run_marker = config_dir / ".initialized"
    
    if not first_run_marker.exists():
        # Run bootstrap wizard from utils
        bootstrap_wizard()
        first_run_marker.parent.mkdir(parents=True, exist_ok=True)
        first_run_marker.touch()

# Add callback for first-run check and global error handling
@app.callback()
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode with detailed error output"),
    dev: bool = typer.Option(False, "--dev", help="Enable developer mode with advanced commands", hidden=True),
    version: Optional[bool] = typer.Option(None, "--version", "-v", help="Show version information")
):
    """
    AI_CONTEXT: Main callback that runs before any command.
    Implements smart default behavior when no command is specified.
    Also sets up global error handling context.
    """
    # Handle version flag
    if version:
        from .. import __version__
        typer.echo(f"agtos version {__version__}")
        raise typer.Exit()
    
    # Store flags in context for error handling
    ctx.obj = ctx.obj or {}
    ctx.obj["debug"] = debug
    ctx.obj["dev"] = dev
    
    # Skip smart behavior for help/version commands
    if any(arg in sys.argv for arg in ["--help", "-h"]):
        return
    
    # Check for working directory from environment
    env_path = os.environ.get('AGTOS_WORKING_DIR')
    if env_path:
        try:
            os.chdir(env_path)
            # Don't print unless in debug mode to avoid cluttering output
            if debug:
                console.print(f"[dim]Changed to directory from AGTOS_WORKING_DIR: {env_path}[/dim]")
        except Exception as e:
            if debug:
                console.print(f"[yellow]Warning: Could not change to AGTOS_WORKING_DIR: {e}[/yellow]")
    
    # If a subcommand was invoked, run normal first-run check
    if ctx.invoked_subcommand is not None:
        check_first_run()
        return
    
    # No subcommand - check if first argument might be a path
    project_path = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Check if it looks like a path (exists as directory)
        potential_path = Path(sys.argv[1]).expanduser().resolve()
        if potential_path.exists() and potential_path.is_dir():
            project_path = sys.argv[1]
            # Remove it from sys.argv so it doesn't interfere
            sys.argv.pop(1)
    
    # No subcommand - implement smart default behavior
    handle_smart_default(project_path)


# Install custom exception handler
def exception_handler(exception_type, exception, traceback):
    """Global exception handler for better error messages."""
    # Don't handle KeyboardInterrupt specially here
    if exception_type == KeyboardInterrupt:
        sys.__excepthook__(exception_type, exception, traceback)
        return
    
    # Use our error handler for all other exceptions
    # Try to get debug flag from somewhere (fallback to checking argv)
    debug = "--debug" in sys.argv or "-d" in sys.argv
    handle_error(exception, debug=debug)
    sys.exit(1)

# Install the exception handler
sys.excepthook = exception_handler

# Export the app for backward compatibility
__all__ = ["app"]