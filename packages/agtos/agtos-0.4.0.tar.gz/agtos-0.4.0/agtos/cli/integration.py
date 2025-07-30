"""
PURPOSE: Plugin integration commands for agentctl
This module handles creating new plugins with knowledge acquisition,
discovering CLI tools and REST APIs automatically.

AI_CONTEXT: The integrate command uses the knowledge acquisition system
to automatically discover how to use external tools and generate plugin
code. It can handle CLI tools, REST APIs, and Python packages.
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
import json
from ..integrations import IntegrationManager
from ..knowledge.intelligent import IntelligentKnowledge
from ..errors import IntegrationError, handle_error

console = Console()


def register_integration_commands(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the integrate command with the main app.
    This is a standalone command, not a command group.
    """
    app.command()(integrate)


def integrate(
    service_name: str = typer.Argument(..., help="Name of the service to integrate"),
    integration_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Type of integration: cli, rest, package, or auto (default: auto)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for the plugin (default: agentctl/plugins/)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output during integration"
    ),
) -> None:
    """Create a comprehensive plugin with knowledge acquisition."""
    try:
        # Validate integration type
        valid_types = ["cli", "rest", "package", "auto", None]
        if integration_type not in valid_types:
            console.print(f"[red]Error:[/red] Invalid type. Choose from: cli, rest, package, auto")
            raise typer.Exit(1)
        
        # Show initial analysis
        show_integration_start(service_name, integration_type)
        
        # If dry-run, show what would happen
        if dry_run:
            console.print("\n[yellow]DRY RUN MODE:[/yellow] No files will be created or modified")
        
        # Perform intelligent analysis if type not specified
        if not integration_type or integration_type == "auto":
            integration_type = analyze_service_type(service_name, verbose)
        
        # Run the integration
        result = run_integration(service_name, integration_type, output_dir, dry_run, verbose)
        
        # Show results
        show_integration_results(result)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Integration cancelled by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        # Check if it's a known integration issue
        if "not found" in str(e).lower() or "no such" in str(e).lower():
            error = IntegrationError(
                service=service_name,
                message=str(e),
                suggestion=f"Make sure '{service_name}' is installed and accessible from your terminal."
            )
        else:
            error = e
        
        handle_error(error, debug=verbose)
        raise typer.Exit(1)


def show_integration_start(service_name: str, integration_type: Optional[str]) -> None:
    """
    AI_CONTEXT: Shows the initial integration message.
    Extracted to reduce nesting in main function.
    """
    type_str = integration_type or "auto-detect"
    message = f"""
[cyan]Service:[/cyan] {service_name}
[cyan]Type:[/cyan] {type_str}
[cyan]Action:[/cyan] Discovering capabilities and generating plugin
"""
    console.print(Panel(message.strip(), title="🔍 Starting Integration", border_style="cyan"))


def analyze_service_type(service_name: str, verbose: bool = False) -> str:
    """
    AI_CONTEXT: Analyzes the service to determine its type.
    Shows analysis progress to the user.
    """
    console.print("\n[yellow]Analyzing service type...[/yellow]")
    
    if verbose:
        console.print(f"[dim]Checking if '{service_name}' is a CLI tool...[/dim]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Detecting integration type...", total=None)
        
        # Use IntegrationManager to determine type
        manager = IntegrationManager()
        
        # Try to get existing knowledge
        try:
            knowledge = manager.knowledge.acquire_comprehensive_knowledge(service_name, "auto")
            progress.update(task, completed=True)
            
            # Determine type from knowledge
            if knowledge.get("cli", {}).get("discovered"):
                if verbose:
                    console.print("[green]✓[/green] Detected as CLI tool")
                return "cli"
            elif knowledge.get("api", {}).get("discovered"):
                if verbose:
                    console.print("[green]✓[/green] Detected as REST API")
                return "api"
            elif knowledge.get("package", {}).get("discovered"):
                if verbose:
                    console.print("[green]✓[/green] Detected as Python package")
                return "package"
            else:
                console.print("[yellow]Could not determine type with high confidence, defaulting to package[/yellow]")
                return "package"
                
        except Exception as e:
            progress.update(task, completed=True)
            if verbose:
                console.print(f"[yellow]Analysis failed:[/yellow] {e}")
            console.print("[yellow]Could not analyze service type, defaulting to package[/yellow]")
            return "package"


# Removed show_analysis_results - no longer needed with simplified analysis


def run_integration(service_name: str, integration_type: str, output_dir: Optional[Path], dry_run: bool = False, verbose: bool = False) -> dict:
    """
    AI_CONTEXT: Runs the actual integration process with progress tracking.
    Returns the integration result dictionary.
    """
    # Set default output directory
    if not output_dir:
        output_dir = Path.cwd() / "agtos" / "plugins"
    
    console.print(f"\n[cyan]Integration type:[/cyan] {integration_type}")
    console.print(f"[cyan]Output directory:[/cyan] {output_dir}")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN:[/yellow] Simulating integration process...")
    
    # Create IntegrationManager
    manager = IntegrationManager()
    
    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        # Main task
        main_task = progress.add_task("Discovering and integrating...", total=100)
        
        # Acquire knowledge
        progress.update(main_task, advance=20, description="Acquiring knowledge...")
        
        if verbose:
            console.print(f"\n[dim]Acquiring {integration_type} knowledge for {service_name}...[/dim]")
        
        knowledge = manager.acquire_knowledge(service_name, integration_type)
        
        if verbose and knowledge:
            # Show some of what was discovered
            if integration_type == "cli" and knowledge.get("cli", {}).get("subcommands"):
                console.print(f"[dim]Found {len(knowledge['cli']['subcommands'])} subcommands[/dim]")
            elif integration_type == "api" and knowledge.get("api", {}).get("endpoints"):
                console.print(f"[dim]Found {len(knowledge['api']['endpoints'])} endpoints[/dim]")
        
        # Generate plugin
        progress.update(main_task, advance=40, description="Generating plugin...")
        try:
            if dry_run:
                # Simulate plugin generation
                plugin_path = output_dir / f"{service_name}.py"
                plugin_knowledge = knowledge
                console.print(f"\n[yellow]DRY RUN:[/yellow] Would create plugin at: {plugin_path}")
            else:
                plugin_path, plugin_knowledge = manager.generate_plugin(
                    service_name, 
                    output_path=output_dir / f"{service_name}.py"
                )
            
            progress.update(main_task, completed=100, description="Integration complete!")
            
            # Build result
            # First check if plugin_knowledge has the expected structure
            cli_data = plugin_knowledge.get("cli", {}) if plugin_knowledge else {}
            api_data = plugin_knowledge.get("api", {}) if plugin_knowledge else {}
            package_data = plugin_knowledge.get("package", {}) if plugin_knowledge else {}
            
            result = {
                "success": True,
                "plugin_name": service_name,
                "plugin_path": str(plugin_path),
                "discovered_items": {
                    "commands": cli_data.get("subcommands", []) if cli_data else [],
                    "endpoints": api_data.get("endpoints", []) if api_data else [],
                    "functions": package_data.get("functions", []) if package_data else [],
                    "examples": plugin_knowledge.get("examples", []) if plugin_knowledge else []
                }
            }
        except Exception as e:
            progress.update(main_task, completed=100)
            
            # Create a more specific error if possible
            if "knowledge" in str(e).lower():
                error = IntegrationError(
                    service=service_name,
                    message=f"Failed to acquire knowledge about '{service_name}': {e}",
                    suggestion=(
                        f"Try specifying the integration type explicitly:\n"
                        f"  agentctl integrate {service_name} --type cli\n"
                        f"  agentctl integrate {service_name} --type rest\n"
                        f"  agentctl integrate {service_name} --type package"
                    )
                )
                raise error
            else:
                raise
    
    return result


def show_integration_results(result: dict) -> None:
    """
    AI_CONTEXT: Shows the final integration results with discovered capabilities.
    Makes the output user-friendly and actionable.
    """
    if not result.get("success"):
        console.print(f"\n[red]Integration failed:[/red] {result.get('error', 'Unknown error')}")
        if result.get("traceback"):
            console.print("\n[dim]Traceback:[/dim]")
            console.print(result["traceback"])
        return
    
    # Success message
    console.print(f"\n[green]✓[/green] Successfully created plugin: [cyan]{result['plugin_name']}[/cyan]")
    
    # Show discovered capabilities
    if result.get("discovered_items"):
        show_discovered_capabilities(result["discovered_items"])
    
    # Show next steps
    next_steps = f"""
[yellow]Next Steps:[/yellow]

1. Review the generated plugin:
   [cyan]{result.get('plugin_path', 'agtos/plugins/')}[/cyan]

2. Test the plugin:
   [cyan]agentctl run[/cyan]

3. Export as MCP tool (optional):
   [cyan]agentctl export {result['plugin_name']}[/cyan]
"""
    console.print(Panel(next_steps.strip(), border_style="green"))


def show_discovered_capabilities(items: dict) -> None:
    """
    AI_CONTEXT: Shows what capabilities were discovered during integration.
    Organized by type (commands, endpoints, functions).
    """
    console.print("\n[green]Discovered Capabilities:[/green]")
    
    # CLI commands
    if items.get("commands"):
        console.print(f"  • [cyan]CLI Commands:[/cyan] {len(items['commands'])}")
        for cmd in items["commands"][:3]:
            console.print(f"    - {cmd}")
        if len(items["commands"]) > 3:
            console.print(f"    ... and {len(items['commands'])-3} more")
    
    # API endpoints
    if items.get("endpoints"):
        console.print(f"  • [cyan]API Endpoints:[/cyan] {len(items['endpoints'])}")
        for endpoint in items["endpoints"][:3]:
            console.print(f"    - {endpoint}")
        if len(items["endpoints"]) > 3:
            console.print(f"    ... and {len(items['endpoints'])-3} more")
    
    # Package functions
    if items.get("functions"):
        console.print(f"  • [cyan]Functions:[/cyan] {len(items['functions'])}")
        for func in items["functions"][:3]:
            console.print(f"    - {func}")
        if len(items["functions"]) > 3:
            console.print(f"    ... and {len(items['functions'])-3} more")
    
    # Examples
    if items.get("examples"):
        console.print(f"  • [cyan]Examples:[/cyan] {len(items['examples'])}")