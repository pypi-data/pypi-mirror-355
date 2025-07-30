"""
PURPOSE: Credential management commands for agentctl
This module handles credential provider configuration and API key management.

AI_CONTEXT: Credentials are managed through pluggable providers (keychain,
1password, env). The cred_provider command manages providers while the
key command manages actual credentials.
"""

from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from ..config import Config
from ..providers import get_provider

console = Console()


def register_credential_commands(app: typer.Typer) -> None:
    """
    AI_CONTEXT: Registers credential-related commands with the main app.
    Creates a command group for credential providers and key management.
    """
    # Create credential provider command group
    cred_app = typer.Typer(help="Manage credential providers")
    cred_app.command("set")(cred_provider_set)
    cred_app.command("show")(cred_provider_show)
    cred_app.command("list")(cred_provider_list)
    
    # Create key command group
    key_app = typer.Typer(help="Manage API keys and credentials")
    key_app.command("add")(key_add)
    key_app.command("get")(key_get)
    key_app.command("ls")(key_ls)
    key_app.command("rm")(key_rm)
    
    # Register command groups
    app.add_typer(cred_app, name="cred-provider")
    app.add_typer(key_app, name="key")


def cred_provider_set(
    provider: str = typer.Argument(..., help="Provider name (keychain, 1password, env)")
) -> None:
    """Set the credential provider."""
    valid_providers = ["keychain", "1password", "env"]
    
    if provider not in valid_providers:
        console.print(f"[red]Error:[/red] Invalid provider. Choose from: {', '.join(valid_providers)}")
        raise typer.Exit(1)
    
    config = Config()
    config.set("credential_provider", provider)
    
    console.print(f"[green]✓[/green] Credential provider set to: [cyan]{provider}[/cyan]")
    
    if provider == "1password":
        console.print("[yellow]Note:[/yellow] Make sure you have 1Password CLI installed and configured")
    elif provider == "keychain":
        console.print("[yellow]Note:[/yellow] Using macOS Keychain for credential storage")


def cred_provider_show() -> None:
    """Show the current credential provider."""
    config = Config()
    provider = config.get("credential_provider")
    
    info = f"""
[cyan]Current Provider:[/cyan] {provider}
[cyan]Status:[/cyan] {"[green]Active[/green]" if provider else "[red]Not set[/red]"}
"""
    
    console.print(Panel(info.strip(), title="Credential Provider", border_style="cyan"))


def cred_provider_list() -> None:
    """List available credential providers."""
    providers = [
        ("keychain", "macOS Keychain", "Secure system keychain storage"),
        ("1password", "1Password", "Integration with 1Password CLI"),
        ("env", "Environment", "Simple .env file storage"),
    ]
    
    table = Table(title="Available Credential Providers")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Description")
    
    for provider_id, name, desc in providers:
        table.add_row(provider_id, name, desc)
    
    console.print(table)


def key_add(
    service: str = typer.Argument(..., help="Service name (e.g., openai, github)"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="API key (will prompt if not provided)"),
) -> None:
    """Add an API key for a service."""
    try:
        provider = get_provider()
        
        if not key:
            key = Prompt.ask(f"Enter API key for [cyan]{service}[/cyan]", password=True)
        
        provider.set_credential(service, key)
        console.print(f"[green]✓[/green] Added API key for '[cyan]{service}[/cyan]'")
        
    except Exception as e:
        console.print(f"[red]Error adding key:[/red] {e}")
        raise typer.Exit(1)


def key_get(
    service: str = typer.Argument(..., help="Service name to retrieve key for")
) -> None:
    """Get an API key for a service."""
    try:
        provider = get_provider()
        key = provider.get_credential(service)
        
        if key:
            # Only show first/last 4 characters for security
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
            console.print(f"[cyan]{service}:[/cyan] {masked}")
        else:
            console.print(f"[yellow]No key found for service:[/yellow] {service}")
            
    except Exception as e:
        console.print(f"[red]Error getting key:[/red] {e}")
        raise typer.Exit(1)


def key_ls() -> None:
    """List all stored API keys."""
    try:
        provider = get_provider()
        services = provider.list_services()
        
        if not services:
            console.print("[yellow]No API keys stored yet.[/yellow]")
            console.print("Add a key with: [cyan]agentctl key add <service>[/cyan]")
            return
        
        table = Table(title="Stored API Keys")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        
        for service in services:
            table.add_row(service, "✓ Stored")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing keys:[/red] {e}")
        raise typer.Exit(1)


def key_rm(
    service: str = typer.Argument(..., help="Service name to remove key for"),
    force: bool = typer.Option(False, "-f", "--force", help="Skip confirmation"),
) -> None:
    """Remove an API key for a service."""
    try:
        if not force:
            confirm = typer.confirm(f"Are you sure you want to remove the key for '{service}'?")
            if not confirm:
                console.print("[yellow]Cancelled[/yellow]")
                raise typer.Exit(0)
        
        provider = get_provider()
        provider.delete_credential(service)
        console.print(f"[green]✓[/green] Removed API key for '[cyan]{service}[/cyan]'")
        
    except Exception as e:
        console.print(f"[red]Error removing key:[/red] {e}")
        raise typer.Exit(1)