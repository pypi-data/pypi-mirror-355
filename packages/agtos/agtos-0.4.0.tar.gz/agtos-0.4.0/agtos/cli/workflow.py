"""Workflow management CLI commands for agtos.

This module provides commands for recording, replaying, and managing workflows.

AI_CONTEXT: CLI interface for the workflow system. Provides user-friendly
commands for recording tool executions, replaying workflows, and managing
the workflow library. Integrates with the recorder and replay modules.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from ..workflows.recorder import WorkflowRecorder
from ..workflows.replay import WorkflowPlayer
from ..workflows.library import get_library, WorkflowLibrary
from ..utils import get_logger

logger = get_logger(__name__)
console = Console()

# CLI app for workflow commands
app = typer.Typer(help="Workflow recording and replay commands")

# Global recorder instance (for session persistence)
_recorder: Optional[WorkflowRecorder] = None


def get_recorder() -> WorkflowRecorder:
    """Get or create the global recorder instance.
    
    AI_CONTEXT: Maintains a single recorder instance across commands
    to preserve recording state between 'record start' and 'record stop'.
    """
    global _recorder
    if _recorder is None:
        _recorder = WorkflowRecorder()
    return _recorder


@app.command("record")
def record_workflow(
    action: str = typer.Argument(..., help="Action: 'start' or 'stop'"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Workflow name (required for start)"),
    description: Optional[str] = typer.Option("", "--description", "-d", help="Workflow description"),
    no_review: bool = typer.Option(False, "--no-review", help="Skip review before saving"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path for workflow file")
):
    """Record tool executions into a replayable workflow.
    
    Examples:
        agentctl workflow record start --name "deploy-app" --description "Deploy to production"
        agentctl workflow record stop
        
    AI_CONTEXT: Controls workflow recording. 'start' begins capturing all tool
    executions, 'stop' ends recording and saves the workflow after security review.
    """
    recorder = get_recorder()
    
    if action == "start":
        _handle_record_start(recorder, name, description)
    elif action == "stop":
        _handle_record_stop(recorder, no_review, output)
    else:
        console.print(f"[red]Invalid action: {action}. Use 'start' or 'stop'[/red]")
        raise typer.Exit(1)


def _handle_record_start(
    recorder: WorkflowRecorder,
    name: Optional[str],
    description: str
) -> None:
    """Handle starting a workflow recording.
    
    AI_CONTEXT: Validates inputs, starts recording, and sets environment
    variables to signal Meta-MCP to begin capturing tool executions.
    """
    if not name:
        console.print("[red]Error: --name is required for 'record start'[/red]")
        raise typer.Exit(1)
    
    if recorder.recording:
        console.print("[yellow]Already recording a workflow. Stop the current recording first.[/yellow]")
        raise typer.Exit(1)
    
    try:
        recorder.start_recording(name, description)
        console.print(f"[green]Started recording workflow: {name}[/green]")
        console.print("[dim]All tool executions will be recorded until you run 'workflow record stop'[/dim]")
        
        # Set environment variable to signal Meta-MCP to record
        import os
        os.environ["AGTOS_RECORDING"] = "1"
        os.environ["AGTOS_WORKFLOW_NAME"] = name
        
    except Exception as e:
        console.print(f"[red]Error starting recording: {e}[/red]")
        raise typer.Exit(1)


def _handle_record_stop(
    recorder: WorkflowRecorder,
    no_review: bool,
    output: Optional[Path]
) -> None:
    """Handle stopping a workflow recording.
    
    AI_CONTEXT: Clears environment variables, stops recording, optionally
    reviews for security, and saves workflow to the specified location.
    """
    if not recorder.recording:
        console.print("[yellow]No workflow is currently being recorded[/yellow]")
        raise typer.Exit(1)
    
    try:
        # Clear recording environment variables
        import os
        os.environ.pop("AGTOS_RECORDING", None)
        os.environ.pop("AGTOS_WORKFLOW_NAME", None)
        
        # Stop and save
        saved_path = recorder.stop_recording(save=True, review=not no_review)
        
        if saved_path:
            console.print(f"[green]Workflow saved to: {saved_path}[/green]")
            
            # Move to custom output path if specified
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                saved_path.rename(output)
                console.print(f"[green]Moved to: {output}[/green]")
        else:
            console.print("[yellow]Workflow recording cancelled or empty[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error stopping recording: {e}[/red]")
        raise typer.Exit(1)


@app.command("replay")
def replay_workflow(
    workflow: str = typer.Argument(..., help="Workflow name or path"),
    params: Optional[str] = typer.Option(None, "--params", "-p", help="JSON parameters for substitution"),
    param: Optional[list[str]] = typer.Option(None, "--param", help="Individual parameter (format: key=value)"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Prompt for missing parameters"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show execution plan without running")
):
    """Replay a recorded workflow.
    
    Examples:
        agentctl workflow replay deploy-app
        agentctl workflow replay deploy-app --param ENV=staging --param VERSION=1.2.3
        agentctl workflow replay deploy-app --params '{"ENV": "prod", "VERSION": "1.2.3"}'
        agentctl workflow replay deploy-app --dry-run
        
    AI_CONTEXT: Loads and executes a saved workflow. Handles parameter substitution
    for {{variable}} placeholders and prompts for missing credentials securely.
    """
    player = WorkflowPlayer()
    
    # Parse parameters
    parameters = _parse_workflow_parameters(params, param)
    
    # Replay workflow
    success = player.replay(
        workflow,
        parameters=parameters,
        interactive=interactive,
        dry_run=dry_run
    )
    
    if not success and not dry_run:
        raise typer.Exit(1)


def _parse_workflow_parameters(
    params: Optional[str],
    param: Optional[list[str]]
) -> Dict[str, Any]:
    """Parse workflow parameters from JSON and key=value formats.
    
    AI_CONTEXT: Combines parameters from --params JSON and individual
    --param key=value arguments into a single dictionary.
    """
    parameters = {}
    
    # JSON parameters
    if params:
        try:
            parameters.update(json.loads(params))
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON parameters: {e}[/red]")
            raise typer.Exit(1)
    
    # Individual parameters
    if param:
        for p in param:
            if '=' not in p:
                console.print(f"[red]Invalid parameter format: {p} (expected key=value)[/red]")
                raise typer.Exit(1)
            key, value = p.split('=', 1)
            parameters[key] = value
    
    return parameters


@app.command("list")
def list_workflows(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """List all recorded workflows.
    
    AI_CONTEXT: Shows all workflows in the workflow directory with summary
    information. Useful for discovering available workflows.
    """
    recorder = WorkflowRecorder()
    workflows = recorder.list_workflows()
    
    if not workflows:
        console.print("[yellow]No workflows found[/yellow]")
        console.print("[dim]Record your first workflow with: agentctl workflow record start --name my-workflow[/dim]")
        return
    
    if detailed:
        _display_workflows_detailed(workflows)
    else:
        _display_workflows_table(workflows)


def _display_workflows_detailed(workflows: List[Dict[str, Any]]) -> None:
    """Display workflows in detailed format.
    
    AI_CONTEXT: Shows each workflow with full information including
    description, creation time, step count, and file path.
    """
    for workflow in workflows:
        console.print(f"\n[bold]{workflow['name']}[/bold]")
        console.print(f"[dim]{workflow['description'] or 'No description'}[/dim]")
        console.print(f"Created: {workflow['created_at']}")
        console.print(f"Steps: {workflow['steps']}")
        console.print(f"Path: {workflow['filepath']}")


def _display_workflows_table(workflows: List[Dict[str, Any]]) -> None:
    """Display workflows in table format.
    
    AI_CONTEXT: Shows workflows in a compact table with key information
    for quick overview and selection.
    """
    table = Table(title="Recorded Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Steps", justify="right")
    table.add_column("Created", style="dim")
    
    for workflow in workflows:
        created = workflow['created_at']
        if created:
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        table.add_row(
            workflow['name'],
            workflow['description'] or "-",
            str(workflow['steps']),
            created or "-"
        )
    
    console.print(table)


@app.command("show")
def show_workflow(
    workflow: str = typer.Argument(..., help="Workflow name or path"),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format: yaml, json, or pretty"),
    no_redacted: bool = typer.Option(False, "--no-redacted", help="Hide redacted values")
):
    """Display the contents of a workflow.
    
    AI_CONTEXT: Shows the full workflow definition including all steps and
    parameters. Useful for reviewing workflows before replay or editing.
    """
    player = WorkflowPlayer()
    
    # Find workflow file
    workflow_path = player._find_workflow(workflow)
    if not workflow_path:
        console.print(f"[red]Workflow not found: {workflow}[/red]")
        raise typer.Exit(1)
    
    try:
        # Load workflow
        import yaml
        with open(workflow_path, 'r') as f:
            workflow_data = yaml.safe_load(f)
        
        # Filter redacted values if requested
        if no_redacted:
            workflow_data = _remove_redacted_values(workflow_data)
        
        # Display based on format
        if format == "json":
            console.print_json(data=workflow_data)
        elif format == "pretty":
            _display_workflow_pretty(workflow_data)
        else:
            _display_workflow_yaml(workflow_data)
            
    except Exception as e:
        console.print(f"[red]Error loading workflow: {e}[/red]")
        raise typer.Exit(1)


def _remove_redacted_values(data: Any) -> Any:
    """Recursively remove redacted values from workflow data.
    
    AI_CONTEXT: Filters out any values marked as [REDACTED] from the
    workflow data structure while preserving the overall structure.
    """
    if isinstance(data, dict):
        return {k: _remove_redacted_values(v) for k, v in data.items() 
               if v != "[REDACTED]"}
    elif isinstance(data, list):
        return [_remove_redacted_values(item) for item in data]
    else:
        return data


def _display_workflow_pretty(workflow_data: Dict[str, Any]) -> None:
    """Display workflow in pretty format with Rich formatting.
    
    AI_CONTEXT: Formats workflow data for human-readable console output
    with colors and structured sections.
    """
    # Display header information
    console.print(f"\n[bold]Workflow: {workflow_data['name']}[/bold]")
    console.print(f"[dim]{workflow_data.get('description', 'No description')}[/dim]")
    console.print(f"Version: {workflow_data.get('version', '1.0')}")
    console.print(f"Created: {workflow_data.get('created_at', 'Unknown')}")
    console.print(f"\n[bold]Steps ({len(workflow_data.get('executions', []))}):[/bold]")
    
    # Display each execution step
    for i, execution in enumerate(workflow_data.get('executions', []), 1):
        _display_execution_step(i, execution)


def _display_execution_step(index: int, execution: Dict[str, Any]) -> None:
    """Display a single execution step with formatting.
    
    AI_CONTEXT: Formats individual workflow execution steps including
    tool info, parameters, and results.
    """
    console.print(f"\n[cyan]{index}. {execution['tool_name']} ({execution['tool_type']})[/cyan]")
    
    if execution.get('parameters'):
        console.print("   Parameters:")
        for key, value in execution['parameters'].items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            console.print(f"     {key}: {value}")
    
    if execution.get('error'):
        console.print(f"   [red]Error: {execution['error']}[/red]")
    elif execution.get('duration'):
        console.print(f"   [green]Duration: {execution['duration']:.2f}s[/green]")


def _display_workflow_yaml(workflow_data: Dict[str, Any]) -> None:
    """Display workflow in YAML format with syntax highlighting.
    
    AI_CONTEXT: Formats workflow data as YAML with syntax highlighting
    for easy reading and editing.
    """
    import yaml
    yaml_str = yaml.dump(workflow_data, default_flow_style=False, sort_keys=False)
    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)


@app.command("edit")
def edit_workflow(
    workflow: str = typer.Argument(..., help="Workflow name or path"),
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="Editor to use (default: $EDITOR)")
):
    """Edit a workflow file in your editor.
    
    AI_CONTEXT: Opens the workflow YAML file in the user's editor for manual
    editing. Useful for fixing parameters or modifying workflow steps.
    """
    import os
    import subprocess
    
    player = WorkflowPlayer()
    
    # Find workflow file
    workflow_path = player._find_workflow(workflow)
    if not workflow_path:
        console.print(f"[red]Workflow not found: {workflow}[/red]")
        raise typer.Exit(1)
    
    # Determine editor
    if not editor:
        editor = os.environ.get('EDITOR', 'nano')  # Default to nano if no EDITOR set
    
    console.print(f"[dim]Opening {workflow_path} in {editor}...[/dim]")
    
    try:
        # Open in editor
        subprocess.run([editor, str(workflow_path)], check=True)
        console.print("[green]Workflow edited successfully[/green]")
        
        # Validate the edited workflow
        try:
            player.load_workflow(workflow_path)
            console.print("[green]✓ Workflow is valid[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Workflow may have errors: {e}[/yellow]")
            
    except subprocess.CalledProcessError:
        console.print(f"[red]Error: Failed to open editor {editor}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(f"[red]Error: Editor '{editor}' not found[/red]")
        console.print("[dim]Set your preferred editor with --editor or $EDITOR environment variable[/dim]")
        raise typer.Exit(1)


@app.command("delete")
def delete_workflow(
    workflow: str = typer.Argument(..., help="Workflow name or path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a recorded workflow.
    
    AI_CONTEXT: Removes a workflow file from the workflow directory.
    Requires confirmation unless --force is used.
    """
    player = WorkflowPlayer()
    
    # Find workflow file
    workflow_path = player._find_workflow(workflow)
    if not workflow_path:
        console.print(f"[red]Workflow not found: {workflow}[/red]")
        raise typer.Exit(1)
    
    # Load to show summary
    try:
        workflow_data = player.load_workflow(workflow_path)
        console.print(f"\n[bold]Workflow: {workflow_data['name']}[/bold]")
        console.print(f"[dim]{workflow_data.get('description', 'No description')}[/dim]")
        console.print(f"Steps: {len(workflow_data.get('executions', []))}")
        console.print(f"Path: {workflow_path}")
    except:
        console.print(f"Path: {workflow_path}")
    
    # Confirm deletion
    if not force:
        confirm = typer.confirm("\nDelete this workflow?")
        if not confirm:
            console.print("[yellow]Deletion cancelled[/yellow]")
            return
    
    # Delete file
    try:
        workflow_path.unlink()
        console.print(f"[green]Workflow deleted: {workflow_path.name}[/green]")
    except Exception as e:
        console.print(f"[red]Error deleting workflow: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def workflow_status():
    """Show current workflow recording status.
    
    AI_CONTEXT: Shows whether a workflow is currently being recorded and
    provides information about the recording session.
    """
    recorder = get_recorder()
    
    if not recorder.recording:
        console.print("[dim]No workflow is currently being recorded[/dim]")
        console.print("\nStart recording with: agentctl workflow record start --name my-workflow")
        return
    
    workflow = recorder.current_workflow
    if workflow:
        console.print(f"\n[bold green]Recording Active[/bold green]")
        console.print(f"Workflow: {workflow.name}")
        if workflow.description:
            console.print(f"Description: {workflow.description}")
        console.print(f"Started: {workflow.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"Steps recorded: {len(workflow.executions)}")
        
        # Show recent executions
        if workflow.executions:
            console.print("\n[dim]Recent executions:[/dim]")
            for execution in workflow.executions[-3:]:  # Last 3
                console.print(f"  - {execution.tool_name} ({execution.tool_type})")
        
        console.print("\n[dim]Stop recording with: agentctl workflow record stop[/dim]")


@app.command("library")
def library_command(
    action: str = typer.Argument("list", help="Action: list, show, search, validate, or export"),
    name: Optional[str] = typer.Argument(None, help="Workflow name (for show/validate)"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Filter by tag(s)"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (for export)")
):
    """Browse and use official workflow library.
    
    AI_CONTEXT: Entry point for workflow library commands. Delegates to
    specific handlers based on action. Provides access to curated library
    of production-ready workflows.
    """
    library = get_library()
    
    # Dispatch to appropriate handler
    if action == "list":
        _handle_list_action(library, query, category, tag)
    elif action == "show":
        _handle_show_action(library, name)
    elif action == "search":
        _handle_search_action(library, query)
    elif action == "validate":
        _handle_validate_action(library, name)
    elif action == "export":
        _handle_export_action(library, output)
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: list, show, search, validate, export")
        raise typer.Exit(1)


def _handle_list_action(
    library: WorkflowLibrary,
    query: Optional[str],
    category: Optional[str],
    tags: Optional[List[str]]
) -> None:
    """List workflows with optional filtering.
    
    Groups workflows by category and displays in formatted tables.
    """
    workflows = library.search_workflows(
        query=query,
        category=category,
        tags=tags
    )
    
    if not workflows:
        console.print("[yellow]No workflows found matching criteria[/yellow]")
        return
    
    # Group by category and display
    by_category = _group_workflows_by_category(workflows)
    _display_workflows_by_category(by_category)


def _group_workflows_by_category(
    workflows: List[Any]
) -> Dict[str, List[Any]]:
    """Group workflows by their category."""
    by_category = {}
    for workflow in workflows:
        if workflow.category not in by_category:
            by_category[workflow.category] = []
        by_category[workflow.category].append(workflow)
    return by_category


def _display_workflows_by_category(
    by_category: Dict[str, List[Any]]
) -> None:
    """Display workflows grouped by category in tables."""
    for cat, cat_workflows in sorted(by_category.items()):
        table = Table(title=f"{cat.title()} Workflows")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Version", justify="center")
        table.add_column("Tags", style="dim")
        
        for workflow in sorted(cat_workflows, key=lambda w: w.name):
            table.add_row(
                workflow.name,
                workflow.description[:60] + "..." if len(workflow.description) > 60 else workflow.description,
                workflow.version,
                ", ".join(workflow.tags[:3]) if workflow.tags else "-"
            )
        
        console.print(table)
        console.print()


def _handle_show_action(
    library: WorkflowLibrary,
    name: Optional[str]
) -> None:
    """Show detailed workflow information."""
    if not name:
        console.print("[red]Error: Workflow name required for 'show' action[/red]")
        raise typer.Exit(1)
    
    workflow = library.get_workflow(name)
    metadata = library.get_metadata(name)
    
    if not workflow:
        console.print(f"[red]Workflow '{name}' not found[/red]")
        raise typer.Exit(1)
    
    _display_workflow_details(workflow, metadata)
    _display_workflow_parameters(workflow)
    _display_workflow_requirements(metadata)
    _display_workflow_usage(name)


def _display_workflow_details(
    workflow: Dict[str, Any],
    metadata: Any
) -> None:
    """Display basic workflow information."""
    console.print(f"\n[bold]{workflow['name']}[/bold]")
    console.print(f"[dim]{workflow['description']}[/dim]")
    console.print(f"\nVersion: {workflow['version']}")
    console.print(f"Category: {metadata.category}")
    if metadata.tags:
        console.print(f"Tags: {', '.join(metadata.tags)}")


def _display_workflow_parameters(
    workflow: Dict[str, Any]
) -> None:
    """Display workflow parameters if present."""
    if not workflow.get('parameters'):
        return
    
    console.print("\n[bold]Parameters:[/bold]")
    for param_name, param_def in workflow['parameters'].items():
        required = "[red]*[/red]" if param_def.get('required') else ""
        console.print(f"  {param_name}{required}: {param_def.get('description', 'No description')}")
        console.print(f"    Type: {param_def.get('type', 'string')}, Default: {param_def.get('default', 'None')}")


def _display_workflow_requirements(
    metadata: Any
) -> None:
    """Display required tools and environment variables."""
    if metadata.required_tools:
        console.print(f"\n[bold]Required Tools:[/bold] {', '.join(metadata.required_tools)}")
    if metadata.required_env:
        console.print(f"[bold]Required Environment Variables:[/bold] {', '.join(metadata.required_env)}")


def _display_workflow_usage(
    name: str
) -> None:
    """Display usage examples for the workflow."""
    console.print(f"\n[bold]Usage:[/bold]")
    console.print(f"  agentctl workflow replay {name}")
    console.print(f"\n[dim]View full workflow: agentctl workflow show {name}[/dim]")


def _handle_search_action(
    library: WorkflowLibrary,
    query: Optional[str]
) -> None:
    """Search workflows by query string."""
    if not query:
        console.print("[red]Error: --query required for search[/red]")
        raise typer.Exit(1)
    
    workflows = library.search_workflows(query=query)
    
    if not workflows:
        console.print(f"[yellow]No workflows found matching '{query}'[/yellow]")
        return
    
    console.print(f"\n[bold]Search Results for '{query}':[/bold]\n")
    
    for workflow in workflows:
        console.print(f"[cyan]{workflow.name}[/cyan] - {workflow.description}")
        console.print(f"  Category: {workflow.category}, Tags: {', '.join(workflow.tags) if workflow.tags else 'None'}")
        console.print()


def _handle_validate_action(
    library: WorkflowLibrary,
    name: Optional[str]
) -> None:
    """Validate a workflow for correctness."""
    if not name:
        console.print("[red]Error: Workflow name required for 'validate' action[/red]")
        raise typer.Exit(1)
    
    errors = library.validate_workflow(name)
    
    if errors:
        console.print(f"[red]Validation failed for '{name}':[/red]")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)
    else:
        console.print(f"[green]✓ Workflow '{name}' is valid[/green]")


def _handle_export_action(
    library: WorkflowLibrary,
    output: Optional[Path]
) -> None:
    """Export workflow catalog to file."""
    if not output:
        output = Path("workflow-catalog.json")
    
    library.export_catalog(output)
    console.print(f"[green]Exported workflow catalog to {output}[/green]")


@app.command("docs")
def generate_docs(
    workflow: str = typer.Argument(..., help="Workflow name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (default: stdout)")
):
    """Generate documentation for a workflow.
    
    AI_CONTEXT: Creates comprehensive markdown documentation for a workflow,
    including all parameters, steps, and usage examples.
    """
    library = get_library()
    
    doc = library.generate_documentation(workflow)
    
    if output:
        output.write_text(doc)
        console.print(f"[green]Documentation written to {output}[/green]")
    else:
        # Use markdown rendering if available
        try:
            from rich.markdown import Markdown
            console.print(Markdown(doc))
        except ImportError:
            console.print(doc)


@app.command("run")
def run_library_workflow(
    workflow: str = typer.Argument(..., help="Official workflow name"),
    params: Optional[str] = typer.Option(None, "--params", "-p", help="JSON parameters"),
    param: Optional[List[str]] = typer.Option(None, "--param", help="Individual parameter (key=value)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show execution plan without running")
):
    """Run an official library workflow.
    
    Examples:
        agentctl workflow run release-management --param version=1.2.0
        agentctl workflow run security-audit --param scan_type=comprehensive
        agentctl workflow run database-migration --param environment=staging --dry-run
        
    AI_CONTEXT: Convenience command that loads and runs workflows from the
    official library without needing to know the file path.
    """
    library = get_library()
    
    # Check if workflow exists in library
    _validate_library_workflow(library, workflow)
    
    # Build parameters
    parameters = _parse_workflow_parameters(params, param)
    
    # Use the library path for the workflow
    workflow_path = library.library_path / f"{workflow}.yaml"
    
    # Run using the player
    player = WorkflowPlayer()
    success = player.replay(
        str(workflow_path),
        parameters=parameters,
        interactive=True,
        dry_run=dry_run
    )
    
    if not success and not dry_run:
        raise typer.Exit(1)


def _validate_library_workflow(
    library: WorkflowLibrary,
    workflow: str
) -> None:
    """Validate that a workflow exists in the library.
    
    AI_CONTEXT: Checks if the requested workflow is available and provides
    helpful error messages with suggestions if not found.
    """
    if not library.get_workflow(workflow):
        console.print(f"[red]Workflow '{workflow}' not found in library[/red]")
        console.print("\n[dim]Available workflows:[/dim]")
        for metadata in library.discover_workflows()[:5]:
            console.print(f"  - {metadata.name}")
        console.print("\n[dim]Use 'agtos workflow library list' to see all workflows[/dim]")
        raise typer.Exit(1)


def register_workflow_command(parent_app: typer.Typer):
    """Register the workflow command group with the parent app.
    
    AI_CONTEXT: Called by the main CLI to add the workflow command group.
    This maintains the modular structure of the CLI.
    """
    parent_app.add_typer(app, name="workflow", help="Record and replay tool execution workflows")


# Export app for registration in main CLI
__all__ = ["app", "register_workflow_command"]