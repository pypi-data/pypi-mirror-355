"""Utility functions for agtos."""
import subprocess
import shutil
import time
import sys
import os
import logging
from typing import List, Optional
from pathlib import Path
import typer


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with standard configuration."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Always use stderr to avoid stdout pollution
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def open_terminal_tab(directory: str, command: str):
    """Open a new Terminal tab, cd to directory, and run command.
    
    Uses AppleScript to automate Terminal.app on macOS.
    """
    # Escape single quotes in the directory path for AppleScript
    directory = directory.replace("'", "'\"'\"'")
    
    script = f'''
    tell application "Terminal"
        activate
        
        -- Create new tab
        tell application "System Events" to keystroke "t" using command down
        
        -- Wait for new tab to be ready
        delay 0.5
        
        -- Change to project directory and run command
        do script "cd '{directory}' && echo '🚀 Starting {command}...' && {command}" in front window
    end tell
    '''
    
    try:
        subprocess.run(["osascript", "-e", script], check=True)
    except subprocess.CalledProcessError as e:
        # Fallback to simpler approach if the advanced script fails
        simple_script = f'''
        tell application "Terminal"
            activate
            do script "cd '{directory}' && {command}"
        end tell
        '''
        subprocess.run(["osascript", "-e", simple_script])

def detect_cli_tools() -> List[str]:
    """Detect which AI CLI tools are installed."""
    tools = []
    
    # Check for Claude Code CLI
    if shutil.which("claude"):
        tools.append("claude")
    
    # Check for OpenAI Codex CLI
    if shutil.which("codex"):
        tools.append("codex")
    
    return tools

def ensure_tool_installed(tool: str) -> bool:
    """Check if a CLI tool is installed."""
    return shutil.which(tool) is not None

def bootstrap_wizard():
    """Interactive setup wizard for first-time users."""
    typer.echo("🎯 Welcome to agentctl! Let's get you set up.")
    typer.echo("=" * 50)
    
    # 1. Check for Claude CLI
    if not ensure_tool_installed("claude"):
        typer.echo("\n📦 Claude CLI not found.")
        install_method = typer.prompt(
            "Install via npm (N) / Homebrew (H) / skip (S)?",
            default="N"
        ).upper()
        
        if install_method == "N":
            typer.echo("Installing Claude CLI via npm...")
            try:
                subprocess.run(["npm", "install", "-g", "@anthropic-ai/claude-code"], check=True)
                typer.echo("✅ Claude CLI installed successfully!")
            except subprocess.CalledProcessError:
                typer.echo("❌ Failed to install. Please run manually: npm install -g @anthropic-ai/claude-code")
        elif install_method == "H":
            typer.echo("Installing Claude CLI via Homebrew...")
            try:
                subprocess.run(["brew", "install", "claude"], check=True)
                typer.echo("✅ Claude CLI installed successfully!")
            except subprocess.CalledProcessError:
                typer.echo("❌ Failed to install. Please run manually: brew install claude")
    else:
        typer.echo("✅ Claude CLI detected")
    
    # 2. Check for Codex CLI (optional for now)
    if ensure_tool_installed("codex"):
        typer.echo("✅ Codex CLI detected (MCP support coming soon!)")
    else:
        typer.echo("ℹ️  OpenAI Codex CLI not found (optional - MCP support coming soon)")
        typer.echo("   Install from: https://github.com/openai/codex")
    
    # 3. Choose credential provider
    typer.echo("\n🔐 Choose your credential storage method:")
    typer.echo("1. macOS Keychain (default, secure, free)")
    typer.echo("2. 1Password (requires 1Password app)")
    typer.echo("3. Environment file (.env - development only)")
    
    choice = typer.prompt("Select [1-3]", default="1")
    
    provider_map = {
        "1": "keychain",
        "2": "1password", 
        "3": "env"
    }
    
    selected_provider = provider_map.get(choice, "keychain")
    
    # Save the choice
    config_dir = Path.home() / ".agtos"
    config_dir.mkdir(exist_ok=True)
    
    shell_rc = Path.home() / ".zshrc"  # or .bashrc
    
    typer.echo(f"\n✅ Selected {selected_provider} as credential provider")
    typer.echo(f"   To make this permanent, add to your {shell_rc}:")
    typer.echo(f"   export AGTOS_CRED_PROVIDER={selected_provider}")
    
    # Set for current session
    os.environ["AGTOS_CRED_PROVIDER"] = selected_provider
    
    typer.echo("\n🎉 Setup complete! You're ready to use agtos.")
    typer.echo("\nNext steps:")
    typer.echo("1. Add your first API key: agentctl key add cloudflare")
    typer.echo("2. Launch Claude: agentctl run")
    typer.echo("3. Talk naturally: 'Show me what tools you have'")
    
    typer.pause("\nPress any key to continue...")

def ensure_prerequisites(agent: str) -> bool:
    """Ensure required tools are installed, with interactive prompts."""
    if agent == "claude" and not ensure_tool_installed("claude"):
        typer.echo("\n📦 Claude CLI is required but not found.")
        
        install = typer.confirm("Would you like to install it now?")
        if install:
            install_method = typer.prompt(
                "Install via npm (N) or Homebrew (H)?", 
                default="N"
            ).upper()
            
            if install_method == "N":
                typer.echo("Installing Claude CLI...")
                try:
                    subprocess.run(["npm", "install", "-g", "@anthropic-ai/claude-code"], check=True)
                    typer.echo("✅ Claude CLI installed!")
                    return True
                except:
                    typer.echo("❌ Installation failed. Please install manually:")
                    typer.echo("   npm install -g @anthropic-ai/claude-code")
                    return False
            else:
                typer.echo("Please install manually: brew install claude")
                return False
        return False
    
    elif agent == "codex" and not ensure_tool_installed("codex"):
        typer.echo("\n📦 Codex CLI is required but not found.")
        typer.echo("⚠️  Note: Codex CLI doesn't have MCP support yet.")
        typer.echo("   Install from: https://github.com/openai/codex")
        typer.echo("   agentctl will support it when MCP lands!")
        return False
    
    return True

def get_tool_version(tool: str) -> str:
    """Get the version of an installed tool."""
    try:
        if tool == "claude":
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        elif tool == "codex":
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
    except:
        return "unknown"
    
    return "unknown"

def wait_for_port(port: int, timeout: int = 5) -> bool:
    """Wait for a port to become available.
    
    Args:
        port: Port number to check
        timeout: Maximum seconds to wait
        
    Returns:
        True if port is available, False if timeout
    """
    import socket
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.1)
    
    return False

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True

def format_size(bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"

def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH."""
    return shutil.which(command) is not None

def get_agtos_dir() -> Path:
    """Get the agentctl configuration directory."""
    return Path.home() / ".agtos"