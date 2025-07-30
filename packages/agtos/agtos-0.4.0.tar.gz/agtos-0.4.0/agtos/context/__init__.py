"""Context preservation package for agtos.

This package provides conversation and state persistence functionality
for maintaining context across sessions.

AI_CONTEXT: The context package enables agentctl to preserve conversation
history, secure tokens, and project-specific settings across sessions using
SQLite for structured storage and keychain integration for secure data.
"""

from .manager import ContextManager

__all__ = ['ContextManager']