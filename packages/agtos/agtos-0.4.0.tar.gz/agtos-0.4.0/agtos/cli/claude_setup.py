"""
PURPOSE: Claude Code setup wizard for agentctl
This module helps users configure agentctl as an MCP server in Claude Code
by automatically detecting and updating the Claude configuration.

AI_CONTEXT: This command provides a smooth setup experience for integrating
agentctl with Claude Code. It handles config file detection, JSON parsing,
and proper MCP server configuration.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

console = Console()


def find_claude_config() -> Optional[Path]:
    """
    Find Claude Code configuration file location.
    
    AI_CONTEXT: Searches for Claude Code configuration files.
    Claude Code uses ~/.claude.json for user config or .mcp.json for project config.
    Returns the first valid config path found.
    """
    config_locations = [
        # Claude Code (CLI) - user config (primary location)
        Path.home() / ".claude.json",
        
        # Project-specific config (for team sharing)
        Path.cwd() / ".mcp.json",
        
        # Legacy locations (for compatibility)
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        Path(os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json")),
        Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
    ]
    
    for config_path in config_locations:
        if config_path.exists():
            return config_path
    
    # If no config found, determine the most likely location
    if sys.platform == "darwin":
        # Check if legacy Claude app exists
        desktop_path = Path.home() / "Library" / "Application Support" / "Claude"
        if desktop_path.exists():
            return desktop_path / "claude_desktop_config.json"
        # Default to Claude Code location
        return Path.home() / ".claude.json"
    elif sys.platform == "win32":
        # Windows default
        return Path(os.path.expandvars(r"%APPDATA%\Claude\claude_desktop_config.json"))
    else:
        # Linux/other default
        return Path.home() / ".claude.json"


def read_claude_config(config_path: Path) -> Dict[str, Any]:
    """
    Read and parse Claude configuration file.
    
    AI_CONTEXT: Safely reads JSON config with error handling.
    Returns empty dict with mcpServers key if file doesn't exist.
    """
    if not config_path.exists():
        return {"mcpServers": {}}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Ensure mcpServers key exists
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            return config
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing config file: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error reading config file: {e}[/red]")
        raise typer.Exit(1)


def write_claude_config(config_path: Path, config: Dict[str, Any]) -> None:
    """
    Write Claude configuration file with proper formatting.
    
    AI_CONTEXT: Writes JSON with 2-space indentation for readability.
    Creates parent directories if they don't exist.
    """
    try:
        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
    except PermissionError:
        console.print(f"[red]Permission denied writing to {config_path}[/red]")
        console.print("[yellow]Try running with sudo or check file permissions[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error writing config file: {e}[/red]")
        raise typer.Exit(1)


def check_port_availability(port: int) -> bool:
    """
    Check if a port is available for use.
    
    AI_CONTEXT: Attempts to bind to the port to check availability.
    Returns True if port is free, False if in use.
    """
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False


def create_agtos_server_config() -> Dict[str, Any]:
    """
    Create the agentctl MCP server configuration.
    
    AI_CONTEXT: Returns the configuration dict for agentctl as an MCP server.
    Uses stdio type for direct communication with Claude Code.
    """
    # Check if we're in development mode (running from source)
    project_root = Path(__file__).parent.parent.parent
    stdio_wrapper = project_root / "agtos-mcp-stdio"
    
    if stdio_wrapper.exists():
        # Development mode - use the wrapper script
        return {
            "type": "stdio", 
            "command": str(stdio_wrapper),
            "args": [],
            "env": {}
        }
    
    # Production mode - use installed agtos command
    import shutil
    agtos_path = shutil.which("agtos")
    
    if not agtos_path:
        console.print("[red]Could not find agtos executable[/red]")
        console.print("[yellow]Make sure agtos is installed and in your PATH[/yellow]")
        raise typer.Exit(1)
    
    return {
        "type": "stdio",
        "command": agtos_path,
        "args": ["mcp-server", "--stdio"],
        "env": {}
    }


def claude_setup(
    name: str = typer.Option("agtos", "--name", "-n", help="Name for the MCP server entry"),
    force: bool = typer.Option(False, "--force", "-f", help="Force overwrite existing configuration"),
):
    """
    Set up agentctl as an MCP server in Claude Code.
    
    AI_CONTEXT: Main command that orchestrates the setup process.
    Detects Claude config, updates it with agentctl server, and provides
    clear feedback to the user.
    """
    console.print(Panel.fit(
        "[bold cyan]agentctl Claude Setup Wizard[/bold cyan]\n"
        "Configuring agentctl as an MCP server in Claude",
        border_style="cyan"
    ))
    
    # Step 1: Find Claude config
    console.print("\n[yellow]Step 1:[/yellow] Detecting Claude configuration...")
    config_path = find_claude_config()
    
    if config_path and config_path.exists():
        console.print(f"[green]✓[/green] Found config at: {config_path}")
    else:
        console.print(f"[yellow]![/yellow] Config not found, will create at: {config_path}")
    
    # Step 2: Check agentctl installation
    console.print("\n[yellow]Step 2:[/yellow] Checking agentctl installation...")
    import shutil
    if shutil.which("agtos"):
        console.print("[green]✓[/green] agentctl is installed and available")
    else:
        console.print("[red]✗[/red] agentctl is not in PATH")
        console.print("[yellow]Make sure agentctl is installed correctly[/yellow]")
        raise typer.Exit(1)
    
    # Step 3: Read existing config
    console.print("\n[yellow]Step 3:[/yellow] Reading configuration...")
    config = read_claude_config(config_path)
    
    # Check if agentctl already exists
    if name in config.get("mcpServers", {}):
        if not force:
            console.print(f"\n[yellow]![/yellow] MCP server '{name}' already exists in configuration")
            
            # Show existing config
            existing = config["mcpServers"][name]
            syntax = Syntax(json.dumps(existing, indent=2), "json", theme="monokai")
            console.print(Panel(syntax, title="Existing Configuration", border_style="yellow"))
            
            if not Confirm.ask("Do you want to update this configuration?"):
                console.print("[red]Setup cancelled[/red]")
                raise typer.Exit(0)
        else:
            console.print(f"[yellow]![/yellow] Overwriting existing '{name}' configuration")
    
    # Step 4: Update configuration
    console.print("\n[yellow]Step 4:[/yellow] Updating configuration...")
    server_config = create_agtos_server_config()
    config["mcpServers"][name] = server_config
    
    # Show new configuration
    syntax = Syntax(json.dumps(server_config, indent=2), "json", theme="monokai")
    console.print(Panel(syntax, title=f"New '{name}' Configuration", border_style="green"))
    
    # Step 5: Write configuration
    console.print("\n[yellow]Step 5:[/yellow] Writing configuration...")
    write_claude_config(config_path, config)
    console.print(f"[green]✓[/green] Configuration saved to {config_path}")
    
    # Success message with instructions
    console.print(Panel(
        "[bold green]✨ Setup Complete![/bold green]\n\n"
        f"agtos has been configured as an MCP server named '{name}'\n\n"
        "[bold]Next steps:[/bold]\n"
        "1. Restart Claude Code for changes to take effect\n"
        "2. Claude will automatically start agentctl when needed\n"
        "3. Look for the agentctl tools in Claude's interface\n\n"
        "[yellow]Tip:[/yellow] agentctl will now communicate with Claude using stdio\n"
        "transport for seamless integration.",
        border_style="green"
    ))
    
    # Show config file location info
    if config_path.name == ".claude.json":
        console.print("\n[cyan]User Configuration:[/cyan] Saved to ~/.claude.json (available in all projects)")
    elif config_path.name == ".mcp.json":
        console.print("\n[cyan]Project Configuration:[/cyan] Saved to .mcp.json (commit to share with team)")
    elif "claude_desktop_config.json" in str(config_path):
        console.print("\n[cyan]Legacy Configuration:[/cyan] Configuration saved to legacy location")


def register_claude_setup_command(app: typer.Typer):
    """
    Register the claude-setup command with the main app.
    
    AI_CONTEXT: This function is called from cli/__init__.py to add
    the claude-setup command to the CLI.
    """
    app.command(
        name="claude-setup",
        help="Configure agentctl as an MCP server in Claude Code"
    )(claude_setup)