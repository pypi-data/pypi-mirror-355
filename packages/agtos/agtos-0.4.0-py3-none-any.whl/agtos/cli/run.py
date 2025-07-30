"""
PURPOSE: Main run command for starting the MCP server
This module handles the orchestration of starting the MCP server
with proper configuration for use with Claude Code.

AI_CONTEXT: The run command is the most complex command in agtos.
It validates the environment, collects credentials, and starts the MCP server.
The server runs in the foreground and can be connected to by Claude Code.
The code is structured to minimize nesting and clearly separate concerns.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..project_store import ProjectStore
from ..config import Config
from ..providers import get_provider

console = Console()


class ProjectError(Exception):
    """Error related to project operations."""
    def __init__(self, project: str, message: str, suggestion: str = ""):
        self.project = project
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)



def register_run_command(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the run command with the main app.
    This is the primary command users interact with.
    """
    app.command()(run)


def run(
    project: Optional[str] = typer.Argument(None, help="Project slug to run (uses last/default if not specified)"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be run without starting services"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed startup process"),
) -> None:
    """Run agentctl MCP server for use with Claude Code."""
    try:
        # Show dry-run notice
        if dry_run:
            console.print("[yellow]DRY RUN MODE:[/yellow] No services will be started\n")
        
        # Step 1: Get project
        project_obj = get_project_for_run(project, verbose)
        
        # Step 2: Collect credentials
        credentials = collect_credentials(verbose)
        
        # Step 3: Prepare environment
        env = prepare_environment(project_obj, credentials, debug, verbose)
        
        # Step 4: Start MCP server
        if dry_run:
            show_dry_run_summary(project_obj, credentials, env)
        else:
            start_mcp_server(env, debug, verbose)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



def get_project_for_run(project_slug: Optional[str], verbose: bool = False) -> dict:
    """
    AI_CONTEXT: Gets the project to run, either specified or default.
    Extracted to reduce nesting in main run function.
    Returns a dictionary with project details.
    """
    store = ProjectStore()
    projects = store.load_projects()
    
    if not projects:
        raise ProjectError(
            project="none",
            message="No projects registered",
            suggestion="Add a project with: agentctl add <slug> <path>"
        )
    
    if project_slug:
        if project_slug not in projects:
            available = ", ".join(projects.keys())
            raise ProjectError(
                project=project_slug,
                message=f"Project '{project_slug}' not found",
                suggestion=f"Available projects: {available}\nUse 'agtos list' to see all projects."
            )
        project_data = projects[project_slug]
        slug = project_slug
    else:
        # Use the first project as default
        slug = list(projects.keys())[0]
        project_data = projects[slug]
        console.print(f"[cyan]Using project:[/cyan] {slug}")
    
    # Verify project path exists
    project_path = Path(project_data.get("path", ""))
    if not project_path.exists():
        raise ProjectError(
            project=slug,
            message=f"Project path does not exist: {project_path}",
            suggestion=f"Update the project path with: agentctl update {slug} <new-path>"
        )
    
    # Return project info as dict with slug included
    return {"slug": slug, "path": str(project_path), **project_data}


def collect_credentials(verbose: bool = False) -> Dict[str, str]:
    """
    AI_CONTEXT: Collects all stored credentials from the provider.
    Returns a dictionary of service:key pairs.
    """
    try:
        if verbose:
            console.print("[dim]Collecting credentials...[/dim]")
        
        provider = get_provider()
        services = provider.list_services()
        
        if not services:
            console.print("[yellow]Warning:[/yellow] No credentials found")
            return {}
        
        if verbose:
            console.print(f"[dim]Found {len(services)} credential(s)[/dim]")
        
        credentials = {}
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Loading credentials...", total=len(services))
            
            for service in services:
                try:
                    key = provider.get_credential(service)
                    if key:
                        credentials[service] = key
                except Exception:
                    # Skip services that fail to load
                    pass
                progress.advance(task)
        
        console.print(f"[green]✓[/green] Loaded {len(credentials)} credentials")
        return credentials
        
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not load credentials: {e}")
        return {}


def show_dry_run_summary(project: dict, credentials: Dict[str, str], env: Dict[str, str]) -> None:
    """
    AI_CONTEXT: Shows what would happen in a dry run without starting services.
    Displays project, credentials, and environment information.
    """
    console.print("\n[yellow]DRY RUN SUMMARY:[/yellow]\n")
    
    # Show project info
    console.print("[cyan]Project:[/cyan]")
    console.print(f"  Slug: {project['slug']}")
    console.print(f"  Path: {project['path']}")
    
    # Show credentials
    console.print("\n[cyan]Credentials:[/cyan]")
    if credentials:
        for service in sorted(credentials.keys()):
            console.print(f"  - {service}: [dim](loaded)[/dim]")
    else:
        console.print("  [dim]No credentials found[/dim]")
    
    # Show key environment variables
    console.print("\n[cyan]Environment:[/cyan]")
    for key, value in sorted(env.items()):
        if key.startswith("AGTOS_") or key == "DEBUG":
            if "API_KEY" in key:
                console.print(f"  {key}: [dim](set)[/dim]")
            else:
                console.print(f"  {key}: {value}")
    
    console.print("\n[yellow]What would happen:[/yellow]")
    console.print("1. Start Meta-MCP server on port 8585")
    console.print("2. Server will wait for connections from Claude Code")
    console.print("\n[dim]Run without --dry-run to start the server[/dim]")


def prepare_environment(project: dict, credentials: Dict[str, str], debug: bool, verbose: bool = False) -> Dict[str, str]:
    """
    AI_CONTEXT: Prepares the environment variables for the MCP server.
    Includes project path, credentials, and debug settings.
    """
    env = os.environ.copy()
    
    # Set project directory
    env["AGTOS_PROJECT_DIR"] = project["path"]
    
    if verbose:
        console.print(f"[dim]Project directory: {project['path']}[/dim]")
    
    # Add credentials with AGTOS_ prefix
    for service, key in credentials.items():
        env_key = f"AGTOS_{service.upper()}_API_KEY"
        env[env_key] = key
        if verbose:
            console.print(f"[dim]Added credential: {env_key}[/dim]")
    
    # Debug mode
    if debug:
        env["AGTOS_DEBUG"] = "1"
        env["DEBUG"] = "agtos:*"
    
    return env


def start_mcp_server(env: Dict[str, str], debug: bool, verbose: bool = False) -> None:
    """
    AI_CONTEXT: Starts the MCP server in the current terminal.
    The server runs in the foreground and can be connected to by Claude Code.
    """
    # Display startup message
    show_startup_message()
    
    if verbose:
        console.print("[dim]Starting MCP server...[/dim]")
    
    # Build the command
    cmd = [sys.executable, "-m", "agtos", "mcp-server"]
    if debug:
        cmd.append("--debug")
    
    # Start the server directly in the current process
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        console.print("\n[yellow]MCP server stopped[/yellow]")
        sys.exit(0)


def show_startup_message() -> None:
    """
    AI_CONTEXT: Shows a nice startup message to the user.
    Extracted to keep main function clean.
    """
    message = """
[green]Starting agentctl MCP server...[/green]

• Server will run on port 8585
• Keep this terminal open while using Claude
• Press Ctrl+C to stop the server

[yellow]Connect from Claude Code:[/yellow]
• Run: [cyan]claude[/cyan]
• The server will be auto-discovered

[yellow]Tips:[/yellow]
• Check server health: [cyan]agentctl status[/cyan]
• View logs in this terminal window
"""
    console.print(Panel(message.strip(), title="🚀 agtos", border_style="green"))