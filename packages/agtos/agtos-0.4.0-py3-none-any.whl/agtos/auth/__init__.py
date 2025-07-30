"""
AI_CONTEXT: agtos auth module
Module for handling authentication, user management, and invite codes using Supabase.

Components:
- client.py: Supabase client initialization and configuration
- models.py: Pydantic models for auth data structures
- manager.py: Auth operations (login, signup, token management)
- invite.py: Invite code generation and validation
- token.py: Offline token management and persistence
"""

from .client import get_supabase_client
from .manager import AuthManager
from .models import User, InviteCode, AuthToken

__all__ = [
    "get_supabase_client",
    "AuthManager",
    "User",
    "InviteCode",
    "AuthToken",
]