"""GitHub authentication management commands.

This module provides CLI commands for managing GitHub authentication,
essential for working with the private agtOS repository.

AI_CONTEXT:
    This module provides user-friendly commands to configure GitHub access
    for private repository operations. It's designed to be simple for users
    who may not be familiar with GitHub tokens or authentication.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from ..github_auth import get_github_auth
from ..utils import get_logger

logger = get_logger(__name__)
console = Console()

# Create the github subcommand app
app = typer.Typer(
    name="github",
    help="Manage GitHub authentication for private repository access",
    no_args_is_help=True
)


@app.command("login")
def login(
    token: Optional[str] = typer.Option(
        None,
        "--token", "-t",
        help="GitHub personal access token (will prompt if not provided)"
    ),
):
    """Configure GitHub authentication for private repository access.
    
    This command helps you set up GitHub authentication which is required for:
    - Installing agtOS from private releases
    - Checking for updates
    - Accessing private repository resources
    
    You'll need a GitHub personal access token with 'repo' scope.
    To create one:
    1. Go to https://github.com/settings/tokens
    2. Click "Generate new token (classic)"
    3. Select 'repo' scope
    4. Generate and copy the token
    """
    github_auth = get_github_auth()
    
    # Check if token already exists
    existing_token = github_auth.get_token()
    if existing_token:
        console.print("[yellow]⚠️  GitHub token already configured[/yellow]")
        if not Confirm.ask("Replace existing token?"):
            return
    
    # Get token if not provided
    if not token:
        console.print("\n[bold]GitHub Authentication Setup[/bold]")
        console.print("You need a personal access token with 'repo' scope.")
        console.print("Create one at: [link]https://github.com/settings/tokens[/link]\n")
        
        token = Prompt.ask(
            "Enter your GitHub token",
            password=True,
            show_default=False
        )
    
    if not token:
        console.print("[red]❌ No token provided[/red]")
        raise typer.Exit(1)
    
    # Validate and store
    try:
        console.print("Validating token...")
        github_auth.set_token(token)
        console.print("[green]✅ GitHub authentication configured successfully![/green]")
        console.print("\nYou can now:")
        console.print("  • Install agtOS from private releases")
        console.print("  • Check for updates automatically")
        console.print("  • Access all agtOS features")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to configure GitHub token: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def status():
    """Check GitHub authentication status."""
    github_auth = get_github_auth()
    
    console.print("\n[bold]GitHub Authentication Status[/bold]\n")
    
    # Check for token
    token = github_auth.get_token()
    
    if token:
        # Validate token
        if github_auth._validate_token(token):
            console.print("[green]✅ Authenticated[/green]")
            
            # Get user info
            try:
                import requests
                headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                response = requests.get(
                    "https://api.github.com/user",
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    user_data = response.json()
                    console.print(f"User: [blue]{user_data.get('login', 'Unknown')}[/blue]")
                    console.print(f"Name: {user_data.get('name', 'Not set')}")
                    
                # Check repository access
                repo_response = requests.get(
                    "https://api.github.com/repos/agtos-ai/agtos",
                    headers=headers,
                    timeout=5
                )
                if repo_response.status_code == 200:
                    console.print("[green]✅ Repository access confirmed[/green]")
                else:
                    console.print("[yellow]⚠️  Cannot access agtOS repository[/yellow]")
                    
            except Exception as e:
                logger.error(f"Failed to get user info: {e}")
        else:
            console.print("[red]❌ Token is invalid or expired[/red]")
            console.print("Run 'agtos github login' to reconfigure")
    else:
        console.print("[yellow]⚠️  Not authenticated[/yellow]")
        console.print("\nTo configure GitHub access:")
        console.print("  agtos github login")
        console.print("\nOr set environment variable:")
        console.print("  export GITHUB_TOKEN=your_token")


@app.command("logout")
def logout(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Skip confirmation prompt"
    ),
):
    """Remove stored GitHub authentication."""
    if not force:
        if not Confirm.ask("Remove GitHub authentication?"):
            return
    
    try:
        github_auth = get_github_auth()
        
        # Clear from credential provider
        github_auth.provider.delete_secret("github")
        
        # Clear cache
        if github_auth.token_cache_file.exists():
            github_auth.token_cache_file.unlink()
        
        console.print("[green]✅ GitHub authentication removed[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to remove authentication: {e}[/red]")
        raise typer.Exit(1)


@app.command("test")
def test():
    """Test GitHub API access and repository permissions."""
    github_auth = get_github_auth()
    
    console.print("\n[bold]Testing GitHub Access[/bold]\n")
    
    # Create results table
    table = Table(show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    # Check token
    token = github_auth.get_token()
    if token:
        table.add_row("Token Found", "✅", "Token available")
        
        # Validate token
        if github_auth._validate_token(token):
            table.add_row("Token Valid", "✅", "Authentication successful")
            
            try:
                # Test API access
                import requests
                session = github_auth.get_authenticated_session()
                
                # Check rate limit
                rate_response = session.get("https://api.github.com/rate_limit")
                if rate_response.status_code == 200:
                    rate_data = rate_response.json()
                    core_limit = rate_data['rate']['limit']
                    core_remaining = rate_data['rate']['remaining']
                    table.add_row(
                        "API Rate Limit", 
                        "✅", 
                        f"{core_remaining}/{core_limit} requests remaining"
                    )
                
                # Check repository access
                repo_response = session.get("https://api.github.com/repos/agtos-ai/agtos")
                if repo_response.status_code == 200:
                    repo_data = repo_response.json()
                    table.add_row(
                        "Repository Access", 
                        "✅", 
                        f"Can access {repo_data['full_name']}"
                    )
                    
                    # Check releases
                    releases_response = session.get(
                        "https://api.github.com/repos/agtos-ai/agtos/releases"
                    )
                    if releases_response.status_code == 200:
                        releases = releases_response.json()
                        table.add_row(
                            "Release Access", 
                            "✅", 
                            f"Found {len(releases)} releases"
                        )
                    else:
                        table.add_row(
                            "Release Access", 
                            "❌", 
                            "Cannot access releases"
                        )
                else:
                    table.add_row(
                        "Repository Access", 
                        "❌", 
                        f"HTTP {repo_response.status_code}"
                    )
                    
            except Exception as e:
                table.add_row("API Test", "❌", str(e))
        else:
            table.add_row("Token Valid", "❌", "Invalid or expired token")
    else:
        table.add_row("Token Found", "❌", "No token configured")
    
    console.print(table)
    
    # Summary
    if token and github_auth._validate_token(token):
        console.print("\n[green]✅ All checks passed![/green]")
    else:
        console.print("\n[yellow]⚠️  Some checks failed[/yellow]")
        console.print("Run 'agtos github login' to configure authentication")


if __name__ == "__main__":
    app()