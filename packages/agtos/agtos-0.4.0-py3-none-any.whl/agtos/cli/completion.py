"""
CLI commands for managing agentctl auto-completion.

AI_CONTEXT:
    This module provides CLI commands for:
    1. Installing shell completions
    2. Generating completion scripts
    3. Testing completion functionality
    4. Managing completion settings
    
    The commands integrate with the completion engine and shell
    integration modules to provide a seamless experience.
"""

import sys
import json
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from ..completion.engine import AutoCompleteEngine, CompletionContext
from ..completion.shell import (
    ShellIntegration, CompletionFormatter, 
    generate_candidates_for_shell, detect_shell
)
from ..metamcp.registry import ServiceRegistry

console = Console()


def _detect_and_validate_shell(shell: Optional[str]) -> str:
    """Detect and validate shell type.
    
    AI_CONTEXT:
        Handles shell detection and validation logic.
        Returns validated shell name or exits on error.
    """
    if not shell:
        shell = detect_shell()
        if not shell:
            console.print("[red]Could not detect shell. Please specify with --shell[/red]")
            console.print("Supported shells: bash, zsh, fish")
            raise typer.Exit(1)
        console.print(f"[cyan]Detected shell: {shell}[/cyan]")
    
    if shell not in ["bash", "zsh", "fish"]:
        console.print(f"[red]Unsupported shell: {shell}[/red]")
        console.print("Supported shells: bash, zsh, fish")
        raise typer.Exit(1)
    
    return shell


def _handle_install_completion(
    shell: Optional[str] = typer.Option(
        None,
        "--shell", "-s",
        help="Shell to install for (bash/zsh/fish). Auto-detected if not specified."
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Force overwrite existing completion scripts"
    )
):
    """Install shell completion for agtos.
    
    AI_CONTEXT:
        Installs shell-specific completion scripts that enable tab completion
        for agentctl commands, tool names, and parameters.
    """
    shell = _detect_and_validate_shell(shell)
    integration = ShellIntegration()
    success, message = integration.install(shell, force=force)
    
    if success:
        console.print(Panel(
            f"[green]✓ Completion installed successfully![/green]\n\n{message}",
            title=f"{shell.title()} Completion",
            border_style="green"
        ))
        if Confirm.ask("\nWould you like to add this to your shell configuration file?"):
            _add_to_shell_config(shell, message)
    else:
        console.print(f"[red]✗ {message}[/red]")
        raise typer.Exit(1)


def _handle_generate_completion(
    shell: str = typer.Argument(
        ...,
        help="Shell to generate script for (bash/zsh/fish)"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file (prints to stdout if not specified)"
    )
):
    """Generate shell completion script.
    
    AI_CONTEXT:
        Generates completion scripts without installing them.
        Useful for reviewing, custom workflows, or packaging.
    """
    if shell not in ["bash", "zsh", "fish"]:
        console.print(f"[red]Unsupported shell: {shell}[/red]")
        console.print("Supported shells: bash, zsh, fish")
        raise typer.Exit(1)
    
    integration = ShellIntegration()
    try:
        script = integration.generate_script(shell)
        if output:
            output.write_text(script)
            console.print(f"[green]✓ Completion script written to {output}[/green]")
        else:
            print(script)
    except Exception as e:
        console.print(f"[red]Failed to generate script: {e}[/red]")
        raise typer.Exit(1)


def _create_completion_engine() -> AutoCompleteEngine:
    """Create auto-complete engine with optional registry.
    
    AI_CONTEXT:
        Tries to create engine with full registry support,
        falls back to basic engine if registry creation fails.
    """
    try:
        from ..mcp_server import create_registry
        registry = create_registry(debug=True)
        return AutoCompleteEngine(registry=registry)
    except:
        return AutoCompleteEngine()


def _handle_test_completion(
    input_text: str = typer.Argument(
        ...,
        help="Partial input to test completion for"
    ),
    position: Optional[int] = typer.Option(
        None,
        "--position", "-p",
        help="Cursor position (defaults to end of input)"
    ),
    style: str = typer.Option(
        "table",
        "--style", "-s",
        help="Display style: table, list, compact"
    )
):
    """Test completion suggestions for given input.
    
    AI_CONTEXT:
        Shows what completions would be suggested for the given input.
        Useful for testing and debugging completion functionality.
    """
    engine = _create_completion_engine()
    
    if position is None:
        position = len(input_text)
    
    context = CompletionContext(
        partial_input=input_text.split()[-1] if input_text else "",
        cursor_position=position,
        full_command=f"agtos {input_text}"
    )
    
    candidates = engine.complete(context)
    formatter = CompletionFormatter()
    formatter.format_candidates(candidates, style=style)
    
    if candidates:
        console.print("\n[dim]Raw completion values:[/dim]")
        values = [c.value for c in candidates[:10]]
        console.print(", ".join(values))


def _handle_generate_candidates(
    command_line: str = typer.Argument(...),
    cursor_pos: int = typer.Argument(...)
):
    """Generate completion candidates for shell integration.
    
    AI_CONTEXT:
        Internal command used by shell completion scripts.
        Outputs newline-separated completion values.
    """
    candidates = generate_candidates_for_shell(command_line, cursor_pos)
    for candidate in candidates:
        print(candidate)


def _display_usage_stats(engine: AutoCompleteEngine):
    """Display usage statistics from completion engine.
    
    AI_CONTEXT:
        Shows top used tools and common parameter patterns
        from the completion history.
    """
    console.print(Panel(
        "[bold]Completion Usage Statistics[/bold]",
        title="agtos completion",
        border_style="cyan"
    ))
    
    if engine.usage_history:
        console.print("\n[bold]Top Used Tools:[/bold]")
        sorted_tools = sorted(
            engine.usage_history.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        for tool, count in sorted_tools:
            bar = "█" * min(50, count)
            console.print(f"  {tool:40} {bar} {count}")
    else:
        console.print("\n[dim]No usage history yet[/dim]")


def _display_parameter_patterns(engine: AutoCompleteEngine):
    """Display common parameter patterns from history.
    
    AI_CONTEXT:
        Groups parameter history by parameter name and shows
        the most common values for each parameter.
    """
    if not engine.parameter_history:
        return
    
    console.print("\n[bold]Common Parameter Values:[/bold]")
    
    by_param = {}
    for key, values in engine.parameter_history.items():
        param = key.split('.')[-1]
        if param not in by_param:
            by_param[param] = []
        by_param[param].extend(values.keys())
    
    for param, values in sorted(by_param.items())[:5]:
        console.print(f"\n  [cyan]{param}:[/cyan]")
        unique_values = list(set(values))[:3]
        for value in unique_values:
            console.print(f"    • {value}")


def _handle_show_stats():
    """Show completion usage statistics.
    
    AI_CONTEXT:
        Displays most used tools, common parameter patterns,
        and completion effectiveness.
    """
    engine = AutoCompleteEngine()
    _display_usage_stats(engine)
    _display_parameter_patterns(engine)


def _handle_clear_history(
    confirm: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompt"
    )
):
    """Clear completion history and statistics.
    
    AI_CONTEXT:
        Removes learned patterns and usage statistics
        from the completion history file.
    """
    if not confirm:
        confirm = Confirm.ask(
            "[yellow]Clear all completion history and statistics?[/yellow]"
        )
    
    if not confirm:
        console.print("[dim]Cancelled[/dim]")
        return
    
    history_file = Path.home() / ".agtos" / "completion_history.json"
    if history_file.exists():
        history_file.unlink()
        console.print("[green]✓ Completion history cleared[/green]")
    else:
        console.print("[dim]No history to clear[/dim]")


def register_completion_commands(app: typer.Typer):
    """Register completion-related commands with the main app.
    
    AI_CONTEXT:
        Creates the 'completion' command group and registers all
        completion-related subcommands. Each command handler is
        kept in a separate function to maintain modularity.
    """
    completion_app = typer.Typer(
        name="completion",
        help="Manage shell auto-completion for agtos",
        no_args_is_help=True
    )
    
    completion_app.command("install")(_handle_install_completion)
    completion_app.command("generate")(_handle_generate_completion)
    completion_app.command("test")(_handle_test_completion)
    completion_app.command("generate-candidates", hidden=True)(_handle_generate_candidates)
    completion_app.command("stats")(_handle_show_stats)
    completion_app.command("clear-history")(_handle_clear_history)
    
    app.add_typer(completion_app)


def _find_shell_config_file(shell: str) -> Optional[Path]:
    """Find or create the appropriate shell configuration file.
    
    AI_CONTEXT:
        Looks for existing shell config files in standard locations.
        Creates the config file if it doesn't exist.
    """
    config_files = {
        "bash": [".bashrc", ".bash_profile"],
        "zsh": [".zshrc"],
        "fish": [".config/fish/config.fish"]
    }
    
    home = Path.home()
    files = config_files.get(shell, [])
    
    # Find existing config file
    for fname in files:
        fpath = home / fname
        if fpath.exists():
            return fpath
    
    # Create the first one if none exist
    if files:
        config_file = home / files[0]
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.touch()
        return config_file
    
    return None


def _extract_source_command(instructions: str) -> Optional[str]:
    """Extract the source command from shell instructions.
    
    AI_CONTEXT:
        Parses the installation instructions to find the
        source or fpath command needed for activation.
    """
    import re
    source_match = re.search(r'(source .+|fpath\+=.+)', instructions)
    return source_match.group(1) if source_match else None


def _update_shell_config(config_file: Path, source_cmd: str) -> bool:
    """Update shell config file with completion source command.
    
    AI_CONTEXT:
        Adds the source command to the shell config file,
        checking for existing configuration first.
    """
    try:
        content = config_file.read_text()
        
        # Check if already added
        if "agtos completion" in content:
            console.print(f"[yellow]Completion already configured in {config_file}[/yellow]")
            return False
        
        # Add to end of file
        if not content.endswith('\n'):
            content += '\n'
        
        content += f"\n# agtos completion\n{source_cmd}\n"
        config_file.write_text(content)
        
        console.print(f"[green]✓ Added to {config_file}[/green]")
        console.print("[cyan]Restart your shell or run:[/cyan]")
        console.print(f"  source {config_file}")
        return True
        
    except Exception as e:
        console.print(f"[red]Failed to update config file: {e}[/red]")
        return False


def _add_to_shell_config(shell: str, instructions: str):
    """Add completion source command to shell config file.
    
    AI_CONTEXT:
        Orchestrates the process of adding completion to shell config:
        1. Finds the appropriate config file
        2. Extracts the source command
        3. Updates the config file
    """
    config_file = _find_shell_config_file(shell)
    if not config_file:
        console.print("[yellow]Could not find shell config file[/yellow]")
        return
    
    source_cmd = _extract_source_command(instructions)
    if not source_cmd:
        console.print("[yellow]Could not extract source command[/yellow]")
        return
    
    _update_shell_config(config_file, source_cmd)