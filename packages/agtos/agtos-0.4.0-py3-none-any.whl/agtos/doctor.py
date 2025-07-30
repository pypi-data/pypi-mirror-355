"""Diagnostic utilities for agtos.

This module provides system health checks and diagnostics.
"""
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import os

def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None

def check_prerequisites() -> Dict[str, bool]:
    """Check all prerequisites for agtos.
    
    Returns:
        Dict mapping tool names to availability status
    """
    tools = {
        "git": check_command_exists("git"),
        "python3": check_command_exists("python3"),
        "pip": check_command_exists("pip") or check_command_exists("pip3"),
        "brew": check_command_exists("brew"),
        "op": check_command_exists("op"),  # 1Password CLI
    }
    return tools

def check_mcp_server_health(host: str = "localhost", port: int = 3000) -> Tuple[bool, str]:
    """Check if MCP server is healthy.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        Tuple of (is_healthy, message)
    """
    try:
        import requests
        response = requests.post(
            f"http://{host}:{port}/",
            json={"jsonrpc": "2.0", "method": "health", "id": 1},
            timeout=2
        )
        if response.status_code == 200:
            return True, "MCP server is running and healthy"
        else:
            return False, f"MCP server returned status {response.status_code}"
    except Exception as e:
        return False, f"Failed to connect to MCP server: {str(e)}"

def check_credential_providers() -> Dict[str, Dict[str, any]]:
    """Check available credential providers.
    
    Returns:
        Dict mapping provider names to their status info
    """
    from .providers import list_available_providers, get_provider
    
    providers = {}
    for name, info in list_available_providers().items():
        try:
            provider = get_provider(name)
            providers[name] = {
                "available": True,
                "name": info["name"],
                "security": info["security"],
                "error": None
            }
        except Exception as e:
            providers[name] = {
                "available": False,
                "name": info["name"],
                "security": info["security"],
                "error": str(e)
            }
    return providers

def run_diagnostics() -> Dict[str, any]:
    """Run full system diagnostics.
    
    Returns:
        Dict with diagnostic results
    """
    return {
        "prerequisites": check_prerequisites(),
        "credential_providers": check_credential_providers(),
        "config_dir": Path.home() / ".agtos",
        "config_exists": (Path.home() / ".agtos" / "config.yml").exists(),
        "projects_exists": (Path.home() / ".agtos" / "projects.yml").exists(),
    }

def format_diagnostics(results: Dict[str, any]) -> str:
    """Format diagnostic results for display."""
    lines = ["agtos System Diagnostics", "=" * 30, ""]
    
    # Prerequisites
    lines.append("Prerequisites:")
    for tool, available in results["prerequisites"].items():
        status = "✅" if available else "❌"
        lines.append(f"  {status} {tool}")
    
    lines.append("")
    
    # Credential Providers
    lines.append("Credential Providers:")
    for name, info in results["credential_providers"].items():
        status = "✅" if info["available"] else "❌"
        msg = f"  {status} {info['name']} (security: {info['security']})"
        if info["error"]:
            msg += f" - {info['error']}"
        lines.append(msg)
    
    lines.append("")
    
    # Configuration
    lines.append("Configuration:")
    lines.append(f"  Config directory: {results['config_dir']}")
    lines.append(f"  Config file: {'✅' if results['config_exists'] else '❌'}")
    lines.append(f"  Projects file: {'✅' if results['projects_exists'] else '❌'}")
    
    return "\n".join(lines)