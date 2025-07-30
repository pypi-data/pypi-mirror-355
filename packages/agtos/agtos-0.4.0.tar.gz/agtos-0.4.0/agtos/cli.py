"""
Main CLI entry point for agentctl - backward compatibility wrapper

AI_CONTEXT: This file maintains backward compatibility while delegating
to the new modular CLI structure. All actual implementation is in the
cli/ subdirectory modules. This ensures existing imports continue to work.
"""

# Import and re-export the main app from the new structure
from .cli import app

# Re-export for backward compatibility
__all__ = ["app"]

# The app is now created and configured in cli/__init__.py
# All commands are registered there through their respective modules