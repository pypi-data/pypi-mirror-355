"""Tutorial management commands for agtOS.

This module provides CLI commands for managing the tutorial system,
including resetting tutorial progress for testing.

AI_CONTEXT:
    This is primarily for developers and testing. Normal users
    should access the tutorial through the TUI's help menu.
"""

import typer
from pathlib import Path

from ..config import get_config_dir
from ..tui_tutorial import reset_tutorial as reset_tutorial_progress
from ..utils import get_logger

logger = get_logger(__name__)

app = typer.Typer(help="Tutorial management commands")


@app.command()
def reset():
    """Reset tutorial progress (marks as first run).
    
    This is useful for testing the first-run experience.
    """
    try:
        reset_tutorial_progress()
        typer.echo("✅ Tutorial progress reset. Next TUI launch will show tutorial.")
        
        # Show additional info
        config_dir = get_config_dir()
        typer.echo(f"📁 Config directory: {config_dir}")
        
        first_run_file = config_dir / ".first_run"
        if first_run_file.exists():
            typer.echo("🆕 First run marker created")
        
        progress_file = config_dir / "tutorial_progress.json"
        if not progress_file.exists():
            typer.echo("🗑️  Tutorial progress cleared")
            
    except Exception as e:
        logger.error(f"Failed to reset tutorial: {e}")
        typer.echo(f"❌ Error resetting tutorial: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def status():
    """Check tutorial completion status."""
    import json
    
    config_dir = get_config_dir()
    first_run_file = config_dir / ".first_run"
    progress_file = config_dir / "tutorial_progress.json"
    
    typer.echo("📚 Tutorial Status:")
    typer.echo(f"📁 Config directory: {config_dir}")
    typer.echo("")
    
    # Check first run marker
    if first_run_file.exists():
        typer.echo("🆕 First run: Yes (tutorial will show)")
    else:
        typer.echo("✅ First run: No")
    
    # Check progress
    if progress_file.exists():
        try:
            with open(progress_file) as f:
                progress = json.load(f)
            
            typer.echo("")
            typer.echo("📊 Tutorial Progress:")
            if progress.get("completed"):
                typer.echo(f"✅ Completed: Yes")
                if progress.get("completed_at"):
                    typer.echo(f"📅 Completed at: {progress['completed_at']}")
            else:
                typer.echo(f"⏳ Completed: No")
                if progress.get("last_step") is not None:
                    typer.echo(f"📍 Last step: {progress['last_step']}")
        except Exception as e:
            typer.echo(f"⚠️  Could not read progress: {e}")
    else:
        typer.echo("")
        typer.echo("📊 No tutorial progress found")


if __name__ == "__main__":
    app()