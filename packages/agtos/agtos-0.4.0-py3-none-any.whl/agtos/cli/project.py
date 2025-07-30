"""
PURPOSE: Project management commands for agentctl
This module handles all project-related operations including adding,
listing, removing, and getting project information.

AI_CONTEXT: Projects are the core organizational unit in agtos.
Each project has its own configuration and credentials. The project
registry is stored in ~/.agtos/projects.json.
"""

from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..project_store import ProjectStore
# Remove get_agtos_dir import - not needed with ProjectStore()

console = Console()


def register_project_commands(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers all project-related commands with the main app.
    This is called from cli/__init__.py during app initialization.
    """
    app.command()(add)
    app.command()(ls)
    app.command()(rm)
    app.command()(get)


def add(
    slug: str = typer.Argument(..., help="Unique identifier for the project"),
    path: str = typer.Argument(..., help="Path to the project directory"),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite existing project"),
) -> None:
    """Add a new project to the registry."""
    try:
        project_path = Path(path).expanduser().resolve()
        
        if not project_path.exists():
            console.print(f"[red]Error:[/red] Path does not exist: {project_path}")
            raise typer.Exit(1)
            
        if not project_path.is_dir():
            console.print(f"[red]Error:[/red] Path is not a directory: {project_path}")
            raise typer.Exit(1)
        
        store = ProjectStore()
        
        # Check if project exists
        projects = store.list_projects()
        if slug in projects and not force:
            console.print(f"[red]Error:[/red] Project '{slug}' already exists. Use --force to overwrite.")
            raise typer.Exit(1)
        
        # Add project
        store.add_project(slug, str(project_path))
        console.print(f"[green]✓[/green] Added project '[cyan]{slug}[/cyan]' at {project_path}")
        
    except Exception as e:
        console.print(f"[red]Error adding project:[/red] {e}")
        raise typer.Exit(1)


def ls() -> None:
    """List all registered projects."""
    try:
        store = ProjectStore()
        projects = store.list_projects()
        
        if not projects:
            console.print("[yellow]No projects registered yet.[/yellow]")
            console.print("Add a project with: [cyan]agentctl add <slug> <path>[/cyan]")
            return
        
        table = Table(title="Registered Projects")
        table.add_column("Slug", style="cyan", no_wrap=True)
        table.add_column("Path", style="green")
        
        for slug, details in projects.items():
            path = details.get("path", "Unknown")
            table.add_row(slug, path)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing projects:[/red] {e}")
        raise typer.Exit(1)


def rm(
    slug: str = typer.Argument(..., help="Project slug to remove"),
    force: bool = typer.Option(False, "-f", "--force", help="Skip confirmation"),
) -> None:
    """Remove a project from the registry."""
    try:
        store = ProjectStore()
        projects = store.list_projects()
        
        if slug not in projects:
            console.print(f"[red]Error:[/red] Project '{slug}' not found")
            raise typer.Exit(1)
        
        if not force:
            confirm = typer.confirm(f"Are you sure you want to remove project '{slug}'?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)
        
        store.remove_project(slug)
        console.print(f"[green]✓[/green] Removed project '[cyan]{slug}[/cyan]'")
        
    except Exception as e:
        console.print(f"[red]Error removing project:[/red] {e}")
        raise typer.Exit(1)


def get(
    slug: str = typer.Argument(..., help="Project slug to get information for")
) -> None:
    """Get information about a specific project."""
    try:
        store = ProjectStore()
        projects = store.list_projects()
        
        if slug not in projects:
            console.print(f"[red]Error:[/red] Project '{slug}' not found")
            raise typer.Exit(1)
        
        project = projects[slug]
        
        # Check if path exists
        path = Path(project.get("path", ""))
        path_status = "[green]✓ Exists[/green]" if path.exists() else "[red]✗ Not found[/red]"
        
        info = f"""
[cyan]Slug:[/cyan] {slug}
[cyan]Path:[/cyan] {project.get("path", "Unknown")}
[cyan]Status:[/cyan] {path_status}
"""
        
        console.print(Panel(info.strip(), title=f"Project: {slug}", border_style="cyan"))
        
    except Exception as e:
        console.print(f"[red]Error getting project:[/red] {e}")
        raise typer.Exit(1)