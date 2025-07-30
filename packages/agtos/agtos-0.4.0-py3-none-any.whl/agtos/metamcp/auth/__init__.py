"""Authentication management for Meta-MCP Server.

AI_CONTEXT:
    This package handles unified authentication across all downstream services.
    It integrates with agtos's existing credential providers and adds
    support for service-specific authentication methods.
"""

from .manager import AuthManager

__all__ = ["AuthManager"]