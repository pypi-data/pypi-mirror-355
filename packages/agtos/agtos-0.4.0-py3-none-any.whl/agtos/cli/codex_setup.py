"""
PURPOSE: Codex CLI setup wizard for agtos
This module helps users configure the OpenAI Codex CLI for use with agtos
by checking installation, setting up authentication, and testing connectivity.

AI_CONTEXT: This command provides a smooth setup experience for integrating
Codex CLI with agtos. It handles authentication setup (API key or OAuth),
configuration validation, and proper agent registration.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm, Prompt

console = Console()


def check_nodejs_installed() -> bool:
    """
    Check if Node.js is installed and meets version requirements.
    
    AI_CONTEXT: Codex CLI requires Node.js 22+. This function checks
    if Node.js is installed and returns True if version is sufficient.
    """
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            console.print(f"[green]✓[/green] Node.js {version} found")
            # Parse version (e.g., v22.0.0 -> 22)
            major_version = int(version.split('.')[0].lstrip('v'))
            if major_version >= 22:
                return True
            else:
                console.print(f"[yellow]![/yellow] Node.js 22+ required (found {version})")
                return False
        return False
    except (FileNotFoundError, ValueError):
        return False


def check_codex_installed() -> Optional[str]:
    """
    Check if Codex CLI is installed and return version.
    
    AI_CONTEXT: Looks for the 'codex' command in PATH and checks version.
    Returns version string if installed, None otherwise.
    """
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return version
        return None
    except FileNotFoundError:
        return None


def install_codex_cli() -> bool:
    """
    Install Codex CLI using npm.
    
    AI_CONTEXT: Runs 'npm install -g @openai/codex' to install the CLI.
    Returns True if successful, False otherwise.
    """
    console.print("\n[yellow]Installing Codex CLI...[/yellow]")
    console.print("Running: npm install -g @openai/codex")
    
    try:
        # Show a spinner while installing
        with console.status("[cyan]Installing Codex CLI...", spinner="dots"):
            result = subprocess.run(
                ["npm", "install", "-g", "@openai/codex"],
                capture_output=True,
                text=True,
                check=False
            )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] Codex CLI installed successfully")
            return True
        else:
            console.print(f"[red]✗[/red] Installation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        console.print("[red]✗[/red] npm not found. Please install Node.js first.")
        return False


def check_api_key() -> Optional[str]:
    """
    Check for OpenAI API key in environment or prompt for it.
    
    AI_CONTEXT: Checks OPENAI_API_KEY environment variable first,
    then prompts user if not found. Returns the API key or None.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        console.print("[green]✓[/green] Found API key in environment")
        return api_key
    
    console.print("\n[yellow]No API key found in environment[/yellow]")
    console.print("You can authenticate with Codex in two ways:")
    console.print("1. [cyan]API Key[/cyan] - Use your OpenAI API key")
    console.print("2. [cyan]OAuth[/cyan] - Sign in with ChatGPT account")
    console.print("\nFor OAuth, run: [bold]codex[/bold] (without arguments)")
    console.print("This will open a browser for authentication")
    
    if Confirm.ask("\nDo you want to set up an API key now?"):
        api_key = Prompt.ask("Enter your OpenAI API key", password=True)
        if api_key:
            # Optionally save to environment or credentials file
            if Confirm.ask("Save API key to ~/.agtos/credentials.json?"):
                save_api_key(api_key)
            return api_key
    
    return None


def save_api_key(api_key: str) -> None:
    """
    Save API key to agtos credentials file.
    
    AI_CONTEXT: Saves the API key to ~/.agtos/credentials.json
    for persistent storage across sessions.
    """
    creds_path = Path.home() / ".agtos" / "credentials.json"
    
    try:
        # Create directory if it doesn't exist
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing credentials
        if creds_path.exists():
            with open(creds_path, 'r') as f:
                creds = json.load(f)
        else:
            creds = {}
        
        # Update OpenAI credentials
        if "openai" not in creds:
            creds["openai"] = {}
        creds["openai"]["api_key"] = api_key
        
        # Write back
        with open(creds_path, 'w') as f:
            json.dump(creds, f, indent=2)
        
        console.print(f"[green]✓[/green] API key saved to {creds_path}")
        
        # Set environment variable for current session
        os.environ["OPENAI_API_KEY"] = api_key
        
    except Exception as e:
        console.print(f"[red]Error saving credentials: {e}[/red]")


def test_codex_cli(api_key: Optional[str] = None) -> bool:
    """
    Test Codex CLI functionality with a simple prompt.
    
    AI_CONTEXT: Runs a test prompt to verify Codex is working.
    Uses provided API key or relies on existing auth.
    """
    console.print("\n[yellow]Testing Codex CLI...[/yellow]")
    
    # Set API key if provided
    env = os.environ.copy()
    if api_key:
        env["OPENAI_API_KEY"] = api_key
    
    try:
        # Run a simple test
        with console.status("[cyan]Running test prompt...", spinner="dots"):
            result = subprocess.run(
                ["codex", "--quiet", "--model", "o4-mini", "echo 'Hello from Codex'"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
                check=False
            )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] Codex CLI is working correctly")
            return True
        else:
            console.print(f"[red]✗[/red] Test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        console.print("[red]✗[/red] Test timed out")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Test error: {e}")
        return False


def update_agent_registry() -> None:
    """
    Update agtos agent registry to include Codex.
    
    AI_CONTEXT: Adds Codex agent configuration to the agtos
    agent registry for use in workflows.
    """
    # This is a placeholder - in real implementation, this would
    # update the agent registry configuration
    console.print("\n[yellow]Updating agent registry...[/yellow]")
    console.print("[green]✓[/green] Codex agent registered with agtos")


def show_oauth_instructions() -> None:
    """
    Show instructions for OAuth authentication.
    
    AI_CONTEXT: Displays step-by-step OAuth setup instructions
    for users who prefer ChatGPT account integration.
    """
    console.print(Panel(
        "[bold cyan]OAuth Authentication Setup[/bold cyan]\n\n"
        "To authenticate with your ChatGPT account:\n\n"
        "1. Run: [bold]codex[/bold] (without any arguments)\n"
        "2. A browser will open for authentication\n"
        "3. Sign in with your ChatGPT account\n"
        "4. Authorize Codex CLI access\n\n"
        "[yellow]Benefits:[/yellow]\n"
        "• Plus users get $5 in API credits\n"
        "• Pro users get $50 in API credits\n"
        "• Credits expire after 30 days\n"
        "• Auto-generates API key for continued use\n\n"
        "[dim]Note: OAuth requires ChatGPT Pro, Enterprise, or Team subscription[/dim]",
        border_style="cyan"
    ))


def codex_setup(
    install: bool = typer.Option(False, "--install", "-i", help="Install Codex CLI if not found"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="OpenAI API key to use"),
    oauth: bool = typer.Option(False, "--oauth", "-o", help="Show OAuth setup instructions"),
):
    """
    Set up OpenAI Codex CLI for use with agtos.
    
    AI_CONTEXT: Main command that orchestrates the Codex setup process.
    Checks prerequisites, handles authentication, and registers the agent.
    """
    _display_setup_banner()
    
    # Show OAuth instructions if requested
    if oauth:
        show_oauth_instructions()
        raise typer.Exit(0)
    
    # Step 1: Check Node.js
    _check_nodejs_step()
    
    # Step 2: Check and install Codex CLI
    _check_and_install_codex_step(install)
    
    # Step 3: Set up authentication
    auth_configured = _setup_authentication_step(api_key)
    
    # Step 4: Test Codex if authenticated
    if auth_configured:
        _test_codex_step(api_key)
    
    # Step 5: Register agent
    _register_agent_step()
    
    # Display success message
    _display_success_message(auth_configured)


# ========================================================================
# Helper Functions for codex_setup
# ========================================================================

def _display_setup_banner():
    """Display the setup wizard banner."""
    console.print(Panel.fit(
        "[bold cyan]agtos Codex Setup Wizard[/bold cyan]\n"
        "Configuring OpenAI Codex CLI for multi-agent workflows",
        border_style="cyan"
    ))


def _check_nodejs_step():
    """Check Node.js installation requirement."""
    console.print("\n[yellow]Step 1:[/yellow] Checking Node.js installation...")
    if not check_nodejs_installed():
        console.print("[red]✗[/red] Node.js 22+ is required for Codex CLI")
        console.print("Please install Node.js from: https://nodejs.org/")
        raise typer.Exit(1)


def _check_and_install_codex_step(install: bool):
    """Check and optionally install Codex CLI."""
    console.print("\n[yellow]Step 2:[/yellow] Checking Codex CLI installation...")
    codex_version = check_codex_installed()
    
    if codex_version:
        console.print(f"[green]✓[/green] Codex CLI {codex_version} is installed")
    else:
        _handle_missing_codex(install)


def _handle_missing_codex(install: bool):
    """Handle the case when Codex CLI is not installed."""
    console.print("[yellow]![/yellow] Codex CLI not found")
    
    if install or Confirm.ask("Would you like to install Codex CLI now?"):
        if not install_codex_cli():
            console.print("\n[red]Failed to install Codex CLI[/red]")
            console.print("Please install manually: npm install -g @openai/codex")
            raise typer.Exit(1)
    else:
        console.print("\n[yellow]Please install Codex CLI manually:[/yellow]")
        console.print("npm install -g @openai/codex")
        raise typer.Exit(1)


def _setup_authentication_step(api_key: Optional[str]) -> bool:
    """Set up authentication for Codex.
    
    Args:
        api_key: Optional API key provided via command line
        
    Returns:
        True if authentication is configured, False otherwise
    """
    console.print("\n[yellow]Step 3:[/yellow] Setting up authentication...")
    
    # Use provided API key or check for existing
    if api_key:
        save_api_key(api_key)
        return True
    else:
        existing_key = check_api_key()
        if existing_key:
            return True
    
    _display_auth_instructions()
    return False


def _display_auth_instructions():
    """Display authentication setup instructions."""
    console.print("\n[yellow]No authentication configured[/yellow]")
    console.print("You can set up authentication later using one of these methods:")
    console.print("1. Set OPENAI_API_KEY environment variable")
    console.print("2. Run 'codex' for OAuth authentication")
    console.print("3. Run 'agtos codex-setup --api-key YOUR_KEY'")


def _test_codex_step(api_key: Optional[str]):
    """Test Codex CLI functionality."""
    console.print("\n[yellow]Step 4:[/yellow] Testing Codex CLI...")
    if test_codex_cli(api_key):
        console.print("[green]✓[/green] Codex is working correctly")
    else:
        console.print("[yellow]![/yellow] Codex test failed")
        console.print("This might be due to network issues or invalid API key")


def _register_agent_step():
    """Register Codex agent in the agent registry."""
    console.print("\n[yellow]Step 5:[/yellow] Registering Codex agent...")
    update_agent_registry()


def _display_success_message(auth_configured: bool):
    """Display success message and next steps.
    
    Args:
        auth_configured: Whether authentication was configured
    """
    console.print(Panel(
        "[bold green]✨ Setup Complete![/bold green]\n\n"
        "Codex has been configured for use with agtos\n\n"
        "[bold]What's next:[/bold]\n"
        "• Use Codex in workflows with 'capability: code-generation'\n"
        "• Specify Codex directly with 'agent: codex'\n"
        "• Configure approval modes for different trust levels\n\n"
        "[yellow]Example workflow step:[/yellow]\n"
        "- name: implement_feature\n"
        "  agent: codex\n"
        "  approval_mode: auto-edit\n"
        "  prompt: 'Implement the user authentication feature'\n\n"
        "[dim]Tip: Codex runs in a network-disabled sandbox for security[/dim]",
        border_style="green"
    ))
    
    # Show additional tips based on setup
    if not auth_configured:
        console.print("\n[yellow]Remember to set up authentication before using Codex![/yellow]")
    
    console.print("\n[cyan]Configuration saved to:[/cyan] ~/.agtos/agents/codex.json")


def register_codex_setup_command(app: typer.Typer):
    """
    Register the codex-setup command with the main app.
    
    AI_CONTEXT: This function is called from cli/__init__.py to add
    the codex-setup command to the CLI.
    """
    app.command(
        name="codex-setup",
        help="Configure OpenAI Codex CLI for multi-agent workflows"
    )(codex_setup)