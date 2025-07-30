"""
AI_CONTEXT: Authentication CLI commands
Commands for managing authentication, users, and invite codes.
"""

import typer
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ..auth import AuthManager
from ..auth.invite import InviteManager
from ..utils import get_logger

logger = get_logger(__name__)
console = Console()
app = typer.Typer(help="Authentication and invite code management")


@app.command()
def status():
    """Check authentication status."""
    auth_manager = AuthManager()
    user = auth_manager.get_current_user()
    
    if user:
        console.print(f"✅ Authenticated as: {user.email}")
        console.print(f"   Name: {user.name or 'Not set'}")
        console.print(f"   Status: {user.subscription_status}")
        console.print(f"   Member since: {user.created_at.strftime('%Y-%m-%d')}")
    else:
        console.print("❌ Not authenticated")
        console.print("   Run 'agtos auth login' to sign in")


@app.command()
def login():
    """Sign in to agtOS."""
    auth_manager = AuthManager()
    
    # Check if already logged in
    if auth_manager.get_current_user():
        if not Confirm.ask("Already logged in. Sign in with a different account?"):
            return
        auth_manager.logout()
    
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)
    
    with console.status("Signing in..."):
        user, error = auth_manager.login(email, password)
    
    if user:
        console.print(f"✅ Welcome back, {user.name or user.email}!")
    else:
        console.print(f"❌ Login failed: {error}")


@app.command()
def signup():
    """Sign up for agtOS with an invite code."""
    auth_manager = AuthManager()
    
    console.print("🎟️  Sign up for agtOS Beta")
    console.print()
    
    invite_code = Prompt.ask("Invite code")
    
    # Validate invite code first
    with console.status("Validating invite code..."):
        invite = auth_manager.validate_invite_code(invite_code)
    
    if not invite:
        console.print("❌ Invalid or expired invite code")
        console.print("   Request an invite at https://agtos.ai")
        return
    
    console.print("✅ Valid invite code!")
    console.print()
    
    email = Prompt.ask("Email")
    password = Prompt.ask("Password", password=True)
    confirm = Prompt.ask("Confirm password", password=True)
    
    if password != confirm:
        console.print("❌ Passwords don't match")
        return
    
    name = Prompt.ask("Name (optional)", default="")
    
    with console.status("Creating account..."):
        user, error = auth_manager.signup_with_invite(
            email=email,
            password=password,
            invite_code=invite_code,
            name=name or None
        )
    
    if user:
        console.print(f"✅ Welcome to agtOS, {user.name or user.email}!")
        console.print("   You're all set to start using agtOS")
    else:
        console.print(f"❌ Signup failed: {error}")


@app.command()
def logout():
    """Sign out of agtOS."""
    auth_manager = AuthManager()
    
    if not auth_manager.get_current_user():
        console.print("Not currently logged in")
        return
    
    if Confirm.ask("Are you sure you want to sign out?"):
        auth_manager.logout()
        console.print("✅ Signed out successfully")


@app.command()
def refresh():
    """Refresh authentication token."""
    auth_manager = AuthManager()
    
    if not auth_manager.get_current_user():
        console.print("❌ Not authenticated")
        return
    
    with console.status("Refreshing token..."):
        if auth_manager.refresh_token():
            console.print("✅ Token refreshed successfully")
        else:
            console.print("❌ Failed to refresh token")
            console.print("   Please sign in again")


# Invite commands (admin only)
invite_app = typer.Typer(help="Invite code management (admin only)")
app.add_typer(invite_app, name="invite")


@invite_app.command("create")
def create_invite(
    expires_days: Optional[int] = typer.Option(30, help="Days until expiration"),
    max_uses: Optional[int] = typer.Option(1, help="Maximum uses"),
    code: Optional[str] = typer.Option(None, help="Specific code to use")
):
    """Create a new invite code."""
    invite_manager = InviteManager()
    
    with console.status("Creating invite code..."):
        invite = invite_manager.create_invite(
            expires_days=expires_days,
            max_uses=max_uses,
            code=code
        )
    
    if invite:
        console.print(f"✅ Created invite code: {invite.code}")
        console.print(f"   Expires: {invite.expires_at or 'Never'}")
        console.print(f"   Max uses: {invite.max_uses or 'Unlimited'}")
    else:
        console.print("❌ Failed to create invite code")


@invite_app.command("list")
def list_invites(active_only: bool = typer.Option(True, help="Show only active codes")):
    """List invite codes."""
    # This would need admin authentication
    console.print("🔒 This command requires admin privileges")


@invite_app.command("stats")
def invite_stats(code: str):
    """Show statistics for an invite code."""
    invite_manager = InviteManager()
    
    with console.status("Loading invite stats..."):
        stats = invite_manager.get_invite_stats(code)
    
    if stats:
        table = Table(title=f"Invite Code: {code}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Valid", "✅ Yes" if stats["is_valid"] else "❌ No")
        table.add_row("Created", stats["created_at"].strftime("%Y-%m-%d"))
        table.add_row("Expires", stats["expires_at"].strftime("%Y-%m-%d") if stats["expires_at"] else "Never")
        table.add_row("Uses", f"{stats['used_count']} / {stats['max_uses'] or '∞'}")
        table.add_row("Remaining", str(stats["remaining_uses"]))
        
        console.print(table)
    else:
        console.print(f"❌ Invite code not found: {code}")


if __name__ == "__main__":
    app()