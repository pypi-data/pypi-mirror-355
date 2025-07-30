"""CLI commands for workflow dependency management.

This module provides commands to check workflow dependencies, analyze
update impacts, and manage workflow compatibility.

AI_CONTEXT:
    These commands enable users to manage workflow dependencies through
    natural language. The integration is seamless - users don't need to
    understand the underlying dependency tracking system.
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..config import get_config_dir
from ..utils import get_logger
from ..workflows import WorkflowPlayer, get_integration
from ..versioning import VersionManager, DependencyTracker

logger = get_logger(__name__)
console = Console()

app = typer.Typer(help="Workflow dependency management commands")


@app.command()
def check_updates(
    workflow_name: str = typer.Argument(..., help="Name or path of workflow to check"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """Check if any tools used by a workflow have updates available.
    
    AI_CONTEXT: This command helps users understand which of their workflows
    might benefit from tool updates, while also warning about compatibility issues.
    """
    player = WorkflowPlayer()
    
    console.print(f"\n🔍 Checking updates for workflow: {workflow_name}")
    
    # Check for updates
    update_info = player.check_workflow_updates(workflow_name)
    
    if "error" in update_info:
        console.print(f"[red]Error: {update_info['error']}[/red]")
        raise typer.Exit(1)
    
    # Display results
    total_deps = update_info.get("total_dependencies", 0)
    updates_available = update_info.get("updates_available", 0)
    
    if updates_available == 0:
        console.print(f"[green]✅ All {total_deps} tools are up to date![/green]")
        return
    
    console.print(f"\n📦 Found {updates_available} tool(s) with updates:")
    
    # Create table for updates
    table = Table(title="Available Updates")
    table.add_column("Tool", style="cyan")
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="green")
    table.add_column("Compatible", style="white")
    table.add_column("Usage", style="dim")
    
    for update in update_info.get("updates", []):
        compatible_icon = "✅" if update["compatible"] else "❌"
        usage_info = f"{update['usage_count']} calls"
        if update.get("critical"):
            usage_info += " (critical)"
        
        table.add_row(
            update["tool"],
            update["current_version"],
            update["latest_version"],
            compatible_icon,
            usage_info
        )
    
    console.print(table)
    
    # Show compatibility issues if requested
    if detailed:
        for update in update_info.get("updates", []):
            if not update["compatible"] and update.get("compatibility_issues"):
                console.print(f"\n⚠️  {update['tool']} compatibility issues:")
                for issue in update["compatibility_issues"]:
                    console.print(f"   - {issue}")


@app.command()
def analyze_impact(
    tool_name: str = typer.Argument(..., help="Name of tool to analyze"),
    from_version: Optional[str] = typer.Option(None, "--from", help="Current version (defaults to active)"),
    to_version: str = typer.Option(None, "--to", help="Target version to upgrade to")
):
    """Analyze the impact of upgrading a tool version.
    
    AI_CONTEXT: This command provides detailed analysis of what would happen
    if a tool is upgraded, including which workflows would be affected and
    what changes would be needed.
    """
    tools_dir = get_config_dir() / "tools"
    version_manager = VersionManager(tools_dir)
    dependency_tracker = DependencyTracker(tools_dir)
    
    # Get current version if not specified
    if not from_version:
        from_version = version_manager.get_active_version(tool_name)
        if not from_version:
            console.print(f"[red]No active version found for {tool_name}[/red]")
            raise typer.Exit(1)
    
    # Get latest version if not specified
    if not to_version:
        versions = version_manager.list_versions(tool_name)
        if not versions:
            console.print(f"[red]No versions found for {tool_name}[/red]")
            raise typer.Exit(1)
        to_version = max(versions)  # Simple max, could use version parsing
    
    console.print(f"\n🔄 Analyzing upgrade impact: {tool_name} {from_version} → {to_version}")
    
    try:
        # Analyze impact
        impact = dependency_tracker.analyze_upgrade_impact(
            tool_name, from_version, to_version, version_manager
        )
        
        # Display results
        console.print(Panel(
            f"Risk Level: [bold {_risk_color(impact.estimated_risk)}]{impact.estimated_risk.upper()}[/bold {_risk_color(impact.estimated_risk)}]",
            title="Upgrade Risk Assessment"
        ))
        
        # Affected items
        if impact.affected_workflows:
            console.print(f"\n📋 Affected Workflows ({len(impact.affected_workflows)}):")
            for workflow in impact.affected_workflows:
                console.print(f"   - {workflow}")
        
        if impact.affected_tools:
            console.print(f"\n🔧 Affected Tools ({len(impact.affected_tools)}):")
            for tool in impact.affected_tools:
                console.print(f"   - {tool}")
        
        # Breaking changes
        if impact.breaking_changes:
            console.print(f"\n⚠️  Breaking Changes ({len(impact.breaking_changes)}):")
            for change in impact.breaking_changes:
                console.print(f"   - {change.get('type', 'unknown')}: {change.get('instructions', 'No details')}")
        
        # Parameter conflicts
        if impact.parameter_conflicts:
            console.print(f"\n❌ Parameter Conflicts ({len(impact.parameter_conflicts)}):")
            for conflict in impact.parameter_conflicts:
                console.print(f"   - {conflict['parameter']} used by {conflict['used_by']} ({conflict['usage_type']})")
        
        # Migration info
        if impact.auto_migratable:
            console.print("\n[green]✅ This upgrade can be migrated automatically[/green]")
        else:
            console.print("\n[yellow]⚠️  Manual migration steps required:[/yellow]")
            for step in impact.manual_steps_required:
                console.print(f"   1. {step}")
                
    except Exception as e:
        console.print(f"[red]Error analyzing impact: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_dependencies(
    workflow_name: str = typer.Argument(..., help="Name or path of workflow"),
    show_parameters: bool = typer.Option(False, "--parameters", "-p", help="Show parameter usage")
):
    """List all tools used by a workflow and their dependencies.
    
    AI_CONTEXT: This command helps users understand the complete dependency
    tree of their workflows, making it easier to plan updates and migrations.
    """
    integration = get_integration()
    
    # Find workflow
    player = WorkflowPlayer()
    workflow_path = player._find_workflow(workflow_name)
    
    if not workflow_path:
        console.print(f"[red]Workflow not found: {workflow_name}[/red]")
        raise typer.Exit(1)
    
    # Analyze workflow
    analysis = integration.analyzer.analyze_workflow(workflow_path)
    
    console.print(f"\n📊 Dependencies for workflow: {analysis.workflow_name} v{analysis.workflow_version}")
    console.print(f"Total tool calls: {analysis.total_tool_calls}")
    console.print(f"Unique tools: {analysis.unique_tools}")
    
    if analysis.warnings:
        console.print("\n⚠️  Warnings:")
        for warning in analysis.warnings:
            console.print(f"   - {warning}")
    
    # Create dependency table
    table = Table(title="Tool Dependencies")
    table.add_column("Tool", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Usage", style="white")
    table.add_column("Critical", style="red")
    
    if show_parameters:
        table.add_column("Parameters Used", style="dim")
    
    for dep in analysis.dependencies:
        row = [
            dep.tool_name,
            dep.tool_type,
            f"{dep.usage_count} calls",
            "Yes" if dep.critical else "No"
        ]
        
        if show_parameters:
            params = ", ".join(sorted(dep.parameters_used)) if dep.parameters_used else "none"
            row.append(params)
        
        table.add_row(*row)
    
    console.print(table)


@app.command()
def scan_all():
    """Scan all workflows and build/update the dependency index.
    
    AI_CONTEXT: This command performs a full scan of all workflows to build
    a complete dependency graph. Useful after importing workflows or making
    major changes.
    """
    integration = get_integration()
    
    # Find all workflow directories
    workflow_dirs = [
        get_config_dir() / "workflows",
        Path.cwd() / "examples" / "workflows"
    ]
    
    total_analyzed = 0
    total_dependencies = 0
    
    console.print("\n🔍 Scanning all workflows for dependencies...")
    
    with console.status("[bold green]Analyzing workflows...") as status:
        for workflow_dir in workflow_dirs:
            if not workflow_dir.exists():
                continue
            
            status.update(f"Scanning {workflow_dir}...")
            results = integration.analyzer.analyze_all_workflows(workflow_dir)
            
            for name, analysis in results.items():
                total_analyzed += 1
                total_dependencies += len(analysis.dependencies)
                
                if analysis.warnings:
                    console.print(f"⚠️  {name}: {len(analysis.warnings)} warnings")
    
    console.print(f"\n✅ Scan complete!")
    console.print(f"   Workflows analyzed: {total_analyzed}")
    console.print(f"   Total dependencies tracked: {total_dependencies}")
    
    # Show summary of most used tools
    dep_tracker = integration.dependency_tracker
    tool_usage = {}
    
    for tool_name, versions in dep_tracker.dependency_index.get("dependencies", {}).items():
        total_usage = sum(v.get("total_usage_count", 0) for v in versions.values())
        if total_usage > 0:
            tool_usage[tool_name] = total_usage
    
    if tool_usage:
        console.print("\n📈 Most used tools:")
        sorted_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        for tool, count in sorted_tools:
            console.print(f"   - {tool}: {count} uses")


def _risk_color(risk: str) -> str:
    """Get color for risk level."""
    colors = {
        "low": "green",
        "medium": "yellow", 
        "high": "red"
    }
    return colors.get(risk.lower(), "white")


if __name__ == "__main__":
    app()