"""Credential provider factory and utilities."""
import os
from typing import Optional
from .base import CredentialProvider
from .keychain import KeychainProvider
from .onepassword import OnePasswordProvider
from .env import EnvironmentProvider

def get_provider(provider_name: Optional[str] = None) -> CredentialProvider:
    """Get a credential provider by name.
    
    Args:
        provider_name: Name of the provider ('keychain', '1password', 'env')
                      If None, uses AGTOS_CRED_PROVIDER env var or defaults to 'keychain'
    
    Returns:
        CredentialProvider instance
    
    Raises:
        ValueError: If provider name is not recognized
    """
    if provider_name is None:
        provider_name = os.getenv("AGTOS_CRED_PROVIDER", "keychain")
    
    provider_name = provider_name.lower()
    
    if provider_name in ("keychain", "macos", "osx"):
        return KeychainProvider()
    elif provider_name in ("1password", "op", "onepassword"):
        return OnePasswordProvider()
    elif provider_name in ("env", "environment", "file"):
        return EnvironmentProvider()
    else:
        raise ValueError(
            f"Unknown credential provider: {provider_name}. "
            f"Valid options: keychain, 1password, env"
        )

def list_available_providers() -> dict:
    """List all available credential providers with their metadata."""
    providers = {
        "keychain": {
            "name": "macOS Keychain",
            "security": "medium",
            "description": "Built-in macOS credential storage (default, free, secure)"
        },
        "1password": {
            "name": "1Password",
            "security": "high",
            "description": "1Password CLI integration (requires 1Password app and CLI)"
        },
        "env": {
            "name": "Environment Variables",
            "security": "development",
            "description": "File-based storage for development (not for production use)"
        }
    }
    return providers

# Export public API
__all__ = ["get_provider", "list_available_providers", "CredentialProvider"]