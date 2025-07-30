"""
PURPOSE: MCP export command for agentctl
This module handles exporting plugins as standalone MCP tools that can
be shared and used independently.

AI_CONTEXT: Export functionality converts agentctl plugins into standard
MCP tools. It generates a complete package with server code, requirements,
and documentation. Supports both single plugins and bundles.
"""

from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..mcp import export_plugin, create_tool_bundle
from ..errors import AgentCtlError, handle_error

# Make plugins import conditional
try:
    from ..plugins import get_plugin
    PLUGINS_AVAILABLE = True
except ImportError:
    get_plugin = None
    PLUGINS_AVAILABLE = False

console = Console()


def register_export_command(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers the export command with the main app.
    Export is a standalone command that can export single or multiple plugins.
    """
    app.command()(export)


def export(
    plugin_names: List[str] = typer.Argument(..., help="Plugin name(s) to export"),
    output_dir: Path = typer.Option(
        Path("./mcp-tools"),
        "--output",
        "-o",
        help="Output directory for MCP tool"
    ),
    bundle_name: Optional[str] = typer.Option(
        None,
        "--bundle",
        "-b",
        help="Create a bundle with multiple plugins"
    ),
    include_knowledge: bool = typer.Option(
        True,
        "--knowledge/--no-knowledge",
        help="Include knowledge base data"
    ),
    create_package: bool = typer.Option(
        False,
        "--package",
        "-p",
        help="Create distributable package"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be exported without creating files"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed export process"
    ),
) -> None:
    """Export plugin(s) as standalone MCP tool(s)."""
    try:
        # Show dry-run notice
        if dry_run:
            console.print("[yellow]DRY RUN MODE:[/yellow] No files will be created\n")
        
        # Validate plugins exist
        validate_plugins(plugin_names, verbose)
        
        # Handle bundle vs individual export
        if bundle_name and len(plugin_names) > 1:
            export_bundle(plugin_names, bundle_name, output_dir, include_knowledge, create_package, dry_run, verbose)
        else:
            export_individual(plugin_names, output_dir, include_knowledge, create_package, dry_run, verbose)
            
    except Exception as e:
        # Check for common issues and provide better error messages
        error_str = str(e).lower()
        if "not found" in error_str and "plugin" in error_str:
            # Extract plugin name if possible
            plugin_name = plugin_names[0] if plugin_names else "unknown"
            error = AgentCtlError(
                message=str(e),
                suggestion=(
                    f"Make sure the plugin exists:\n"
                    f"1. List available plugins: agentctl list-plugins\n"
                    f"2. Create the plugin: agentctl integrate {plugin_name}"
                ),
                category="export"
            )
        else:
            error = e
        
        handle_error(error, debug=verbose)
        raise typer.Exit(1)


def validate_plugins(plugin_names: List[str], verbose: bool = False) -> None:
    """
    AI_CONTEXT: Validates that all requested plugins exist and can be loaded.
    Fails fast with helpful error messages.
    """
    if verbose:
        console.print(f"[dim]Validating {len(plugin_names)} plugin(s)...[/dim]")
    
    # Check if plugins are available
    if not PLUGINS_AVAILABLE:
        raise AgentCtlError(
            message="Plugins module not available - plugin export disabled",
            suggestion="Enable plugins by renaming agtos/plugins.disabled back to agtos/plugins"
        )
        
    for name in plugin_names:
        try:
            plugin = get_plugin(name)
            if not plugin:
                raise Exception(f"Plugin '{name}' not found")
            if verbose:
                console.print(f"[green]✓[/green] Plugin '{name}' validated")
        except Exception as e:
            raise AgentCtlError(
                message=f"Cannot load plugin '{name}': {e}",
                suggestion=(
                    f"Check that the plugin file exists at:\n"
                    f"  agentctl/plugins/{name}.py\n\n"
                    f"If not, create it with: agentctl integrate {name}"
                ),
                category="export",
                details={"plugin": name}
            )


def export_bundle(
    plugin_names: List[str],
    bundle_name: str,
    output_dir: Path,
    include_knowledge: bool,
    create_package: bool,
    dry_run: bool = False,
    verbose: bool = False
) -> None:
    """
    AI_CONTEXT: Exports multiple plugins as a single MCP tool bundle.
    Useful for creating cohesive tool sets.
    """
    console.print(f"\n[cyan]Creating bundle:[/cyan] {bundle_name}")
    console.print(f"[cyan]Plugins:[/cyan] {', '.join(plugin_names)}")
    
    if verbose:
        console.print(f"[dim]Output directory: {output_dir}[/dim]")
        console.print(f"[dim]Include knowledge: {include_knowledge}[/dim]")
        console.print(f"[dim]Create package: {create_package}[/dim]")
    
    show_export_progress("Creating bundle structure...")
    
    if dry_run:
        console.print(f"\n[yellow]DRY RUN:[/yellow] Would create bundle at: {output_dir / bundle_name}")
        for plugin in plugin_names:
            console.print(f"  - Would include plugin: {plugin}")
        if include_knowledge:
            console.print("  - Would include knowledge base data")
        if create_package:
            console.print("  - Would create distributable package")
    else:
        result = create_tool_bundle(
            plugin_names=plugin_names,
            bundle_name=bundle_name,
            output_dir=output_dir,
            include_knowledge=include_knowledge
        )
        
        show_bundle_results(result, bundle_name, create_package)


def export_individual(
    plugin_names: List[str],
    output_dir: Path,
    include_knowledge: bool,
    create_package: bool,
    dry_run: bool = False,
    verbose: bool = False
) -> None:
    """
    AI_CONTEXT: Exports plugins individually as separate MCP tools.
    Each plugin gets its own directory and can be run independently.
    """
    results = []
    
    for plugin_name in plugin_names:
        console.print(f"\n[cyan]Exporting plugin:[/cyan] {plugin_name}")
        
        if verbose:
            console.print(f"[dim]Output: {output_dir / plugin_name}[/dim]")
        
        show_export_progress(f"Generating MCP tool for {plugin_name}...")
        
        if dry_run:
            console.print(f"[yellow]DRY RUN:[/yellow] Would export to {output_dir / plugin_name}")
            results.append((plugin_name, output_dir / plugin_name))
        else:
            result = export_plugin(
                plugin_name=plugin_name,
                output_dir=output_dir,
                include_knowledge=include_knowledge,
                create_package=create_package
            )
            results.append((plugin_name, result))
    
    if not dry_run:
        show_individual_results(results, create_package)


def show_export_progress(message: str) -> None:
    """
    AI_CONTEXT: Shows a progress message during export.
    Simple visual feedback for the user.
    """
    console.print(f"[yellow]→[/yellow] {message}")


def show_bundle_results(result: Path, bundle_name: str, create_package: bool) -> None:
    """
    AI_CONTEXT: Shows results for bundle export with next steps.
    Provides clear instructions for using the exported bundle.
    """
    console.print(f"\n[green]✓[/green] Bundle created: [cyan]{result}[/cyan]")
    
    next_steps = f"""
[yellow]Bundle Ready![/yellow]

Your MCP tool bundle '{bundle_name}' has been created at:
[cyan]{result}[/cyan]

[yellow]To use this bundle:[/yellow]

1. Install dependencies:
   [cyan]cd {result}[/cyan]
   [cyan]pip install -r requirements.txt[/cyan]

2. Run the MCP server:
   [cyan]python server.py[/cyan]

3. Configure in Claude Code:
   Add to your MCP settings with the bundle path
"""
    
    if create_package:
        next_steps += "\n\n[yellow]Package created:[/yellow] Ready for distribution!"
    
    console.print(Panel(next_steps.strip(), border_style="green"))


def show_individual_results(results: List[tuple], create_package: bool) -> None:
    """
    AI_CONTEXT: Shows results for individual plugin exports.
    Creates a summary table when multiple plugins are exported.
    """
    if len(results) == 1:
        # Single plugin - show detailed instructions
        plugin_name, result_path = results[0]
        
        console.print(f"\n[green]✓[/green] Exported: [cyan]{result_path}[/cyan]")
        
        next_steps = f"""
[yellow]MCP Tool Ready![/yellow]

Your plugin '{plugin_name}' has been exported as an MCP tool at:
[cyan]{result_path}[/cyan]

[yellow]To use this tool:[/yellow]

1. Install dependencies:
   [cyan]cd {result_path}[/cyan]
   [cyan]pip install -r requirements.txt[/cyan]

2. Run the MCP server:
   [cyan]python server.py[/cyan]

3. Configure in Claude Code:
   Add to your MCP settings with the tool path

[yellow]To share this tool:[/yellow]
- Upload to GitHub
- Share the directory
- Publish to MCP registry
"""
        
        if create_package:
            next_steps += "\n\n[yellow]Package created:[/yellow] Ready for distribution!"
        
        console.print(Panel(next_steps.strip(), border_style="green"))
        
    else:
        # Multiple plugins - show summary table
        console.print(f"\n[green]✓[/green] Exported {len(results)} plugins:")
        
        table = Table(title="Exported MCP Tools")
        table.add_column("Plugin", style="cyan")
        table.add_column("Output Path", style="green")
        table.add_column("Status", style="yellow")
        
        for plugin_name, result_path in results:
            status = "✓ Ready" if create_package else "✓ Exported"
            table.add_row(plugin_name, str(result_path), status)
        
        console.print(table)
        
        console.print("\n[yellow]Tip:[/yellow] Each tool can be run independently with [cyan]python server.py[/cyan]")