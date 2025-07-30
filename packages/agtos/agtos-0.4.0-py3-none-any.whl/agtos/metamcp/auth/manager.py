"""Authentication manager for Meta-MCP Server.

AI_CONTEXT:
    This module manages authentication credentials for all downstream services.
    It provides:
    - Unified credential retrieval across different providers
    - Credential caching with expiration handling
    - Service-specific authentication configuration
    - Integration with existing agtos providers (keychain, 1password, env)
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta

from ...providers import KeychainProvider, OnePasswordProvider, EnvironmentProvider
from ..types import Credential, AuthenticationError
from ...context import ContextManager

logger = logging.getLogger(__name__)


class AuthManager:
    """Centralized authentication manager for all services.
    
    AI_CONTEXT:
        The AuthManager is responsible for:
        1. Loading credentials from configured providers
        2. Caching credentials to avoid repeated lookups
        3. Handling credential expiration and refresh
        4. Managing service-specific auth configurations
        5. Providing a unified interface for auth across all service types
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, context_manager: Optional[ContextManager] = None):
        """Initialize authentication manager.
        
        Args:
            config: Authentication configuration including:
                - default_provider: Default credential provider
                - provider_configs: Provider-specific configurations
                - cache_ttl: Credential cache TTL in seconds
            context_manager: Optional context manager for token persistence
        """
        self.config = config or {}
        self.context_manager = context_manager
        
        # Initialize credential providers
        # For now, only initialize env provider to avoid dependency issues
        self.providers = {
            "env": EnvironmentProvider(),
        }
        
        # Credential cache
        self.credential_cache: Dict[str, Credential] = {}
        
        # Service auth configurations
        self.service_configs: Dict[str, Dict[str, Any]] = {}
        
        # Default settings
        self.default_provider = self.config.get("default_provider", "env")
        self.cache_ttl = self.config.get("cache_ttl", 3600)  # 1 hour default
    
    async def get_credentials(self, service_name: str) -> Credential:
        """Get credentials for a service.
        
        Args:
            service_name: Name of the service requiring credentials
            
        Returns:
            Credential object containing auth data
            
        Raises:
            AuthenticationError: If credentials cannot be retrieved
        """
        # Check cache first
        if cached_cred := self._get_cached_credential(service_name):
            logger.debug(f"Using cached credentials for {service_name}")
            return cached_cred
        
        # Get service auth configuration
        auth_config = self.service_configs.get(service_name, {})
        provider_name = auth_config.get("provider", self.default_provider)
        
        # Validate provider
        if provider_name not in self.providers:
            raise AuthenticationError(
                f"Unknown auth provider: {provider_name}"
            )
        
        # Get credentials from provider
        provider = self.providers[provider_name]
        
        try:
            logger.info(
                f"Retrieving credentials for {service_name} "
                f"from {provider_name} provider"
            )
            
            # Provider-specific credential retrieval
            if provider_name == "keychain":
                cred_data = await self._get_keychain_credential(
                    service_name,
                    auth_config
                )
            elif provider_name == "1password":
                cred_data = await self._get_1password_credential(
                    service_name,
                    auth_config
                )
            elif provider_name == "env":
                cred_data = await self._get_env_credential(
                    service_name,
                    auth_config
                )
            else:
                # Fallback for custom providers
                cred_data = await provider.get_credential(
                    service_name,
                    auth_config
                )
            
            # Create credential object
            credential = Credential(
                type=auth_config.get("type", "api_key"),
                data=cred_data,
                expires_at=self._calculate_expiration(auth_config)
            )
            
            # Cache the credential
            self._cache_credential(service_name, credential)
            
            # Save to context manager if available
            if self.context_manager and auth_config.get("persist", True):
                self._save_credential_to_context(service_name, credential, auth_config)
            
            return credential
            
        except Exception as e:
            logger.error(f"Failed to get credentials for {service_name}: {e}")
            raise AuthenticationError(
                f"Failed to retrieve credentials for {service_name}: {str(e)}"
            )
    
    def configure_service_auth(
        self,
        service_name: str,
        auth_config: Dict[str, Any]
    ):
        """Configure authentication for a service.
        
        Args:
            service_name: Name of the service
            auth_config: Authentication configuration including:
                - provider: Credential provider to use
                - type: Auth type (api_key, oauth2, basic, etc.)
                - key_name: Key name for keychain/1password
                - env_var: Environment variable name
                - ttl: Credential TTL in seconds
        """
        logger.info(f"Configuring auth for service: {service_name}")
        
        # Validate configuration
        self._validate_auth_config(auth_config)
        
        # Store configuration
        self.service_configs[service_name] = auth_config
        
        # Clear any cached credentials
        if service_name in self.credential_cache:
            del self.credential_cache[service_name]
    
    def clear_credentials(self, service_name: Optional[str] = None):
        """Clear cached credentials.
        
        Args:
            service_name: Service to clear credentials for,
                         or None to clear all
        """
        if service_name:
            if service_name in self.credential_cache:
                del self.credential_cache[service_name]
                logger.debug(f"Cleared credentials for {service_name}")
        else:
            self.credential_cache.clear()
            logger.debug("Cleared all cached credentials")
    
    async def _get_keychain_credential(
        self,
        service_name: str,
        auth_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get credential from macOS Keychain."""
        key_name = auth_config.get("key_name", service_name)
        
        # Use the keychain provider
        value = await self.providers["keychain"].get(
            key=key_name,
            service=auth_config.get("service", "agtos")
        )
        
        # Format based on auth type
        auth_type = auth_config.get("type", "api_key")
        if auth_type == "api_key":
            return {"api_key": value}
        elif auth_type == "basic":
            # Expect username:password format
            if ":" in value:
                username, password = value.split(":", 1)
                return {"username": username, "password": password}
            else:
                return {"password": value}
        else:
            return {"token": value}
    
    async def _get_1password_credential(
        self,
        service_name: str,
        auth_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get credential from 1Password."""
        item_name = auth_config.get("item_name", service_name)
        field_name = auth_config.get("field_name", "credential")
        vault = auth_config.get("vault")
        
        # Use the 1password provider
        value = await self.providers["1password"].get(
            item=item_name,
            field=field_name,
            vault=vault
        )
        
        # Format based on auth type
        auth_type = auth_config.get("type", "api_key")
        if auth_type == "api_key":
            return {"api_key": value}
        elif auth_type == "oauth2":
            # Could be a JSON token
            import json
            try:
                return json.loads(value)
            except:
                return {"access_token": value}
        else:
            return {"token": value}
    
    async def _get_env_credential(
        self,
        service_name: str,
        auth_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get credential from environment variables."""
        env_var = auth_config.get("env_var")
        if not env_var:
            # Default to SERVICE_NAME_API_KEY format
            env_var = f"{service_name.upper()}_API_KEY"
        
        # Use the env provider
        value = await self.providers["env"].get(key=env_var)
        
        if not value:
            # Try alternative formats
            alternatives = [
                f"{service_name.upper()}_TOKEN",
                f"{service_name.upper()}_KEY",
                service_name.upper()
            ]
            for alt in alternatives:
                value = await self.providers["env"].get(key=alt)
                if value:
                    break
        
        if not value:
            raise AuthenticationError(
                f"No credential found in environment for {service_name}"
            )
        
        # Format based on auth type
        auth_type = auth_config.get("type", "api_key")
        if auth_type == "api_key":
            return {"api_key": value}
        elif auth_type == "bearer":
            return {"bearer_token": value}
        else:
            return {"token": value}
    
    def _get_cached_credential(
        self,
        service_name: str
    ) -> Optional[Credential]:
        """Get credential from cache if valid."""
        if service_name not in self.credential_cache:
            return None
        
        credential = self.credential_cache[service_name]
        
        # Check expiration
        if credential.is_expired():
            logger.debug(f"Cached credential for {service_name} is expired")
            del self.credential_cache[service_name]
            return None
        
        return credential
    
    def _cache_credential(self, service_name: str, credential: Credential):
        """Cache a credential."""
        self.credential_cache[service_name] = credential
        logger.debug(f"Cached credential for {service_name}")
    
    def _calculate_expiration(
        self,
        auth_config: Dict[str, Any]
    ) -> Optional[datetime]:
        """Calculate credential expiration time."""
        ttl = auth_config.get("ttl", self.cache_ttl)
        if ttl <= 0:
            return None  # No expiration
        
        return datetime.now() + timedelta(seconds=ttl)
    
    def _validate_auth_config(self, auth_config: Dict[str, Any]):
        """Validate authentication configuration."""
        provider = auth_config.get("provider")
        if provider and provider not in self.providers:
            raise ValueError(f"Unknown auth provider: {provider}")
        
        auth_type = auth_config.get("type")
        valid_types = [
            "api_key", "bearer", "basic", "oauth2", "custom"
        ]
        if auth_type and auth_type not in valid_types:
            raise ValueError(f"Unknown auth type: {auth_type}")
    
    def _save_credential_to_context(
        self,
        service_name: str,
        credential: Credential,
        auth_config: Dict[str, Any]
    ):
        """Save credential to context manager for persistence.
        
        AI_CONTEXT: Saves non-sensitive credential metadata and the actual
        token securely via the context manager's keychain integration.
        """
        if not self.context_manager:
            return
        
        try:
            # Determine token name and value
            token_name = f"{service_name}_token"
            token_value = None
            
            # Extract token value based on type
            if "api_key" in credential.data:
                token_value = credential.data["api_key"]
                token_name = f"{service_name}_api_key"
            elif "bearer_token" in credential.data:
                token_value = credential.data["bearer_token"]
            elif "access_token" in credential.data:
                token_value = credential.data["access_token"]
            elif "token" in credential.data:
                token_value = credential.data["token"]
            
            if token_value:
                self.context_manager.save_token(
                    token_name=token_name,
                    token_value=token_value,
                    service_name=service_name,
                    expires_at=credential.expires_at
                )
                logger.debug(f"Saved {service_name} token to context")
                
        except Exception as e:
            logger.error(f"Failed to save credential to context: {e}")
    
    def restore_tokens_from_context(self, token_names: Optional[List[str]] = None):
        """Restore saved tokens from context manager.
        
        AI_CONTEXT: Called during server initialization to restore any
        previously saved authentication tokens. This enables seamless
        continuation across server restarts.
        
        Args:
            token_names: Optional list of specific tokens to restore.
                        If None, attempts to restore common tokens.
        """
        if not self.context_manager:
            return
        
        # Default token names if not specified
        if not token_names:
            token_names = [
                "openai_api_key",
                "anthropic_api_key",
                "github_token",
                "gitlab_token",
                "slack_token"
            ]
        
        restored_count = 0
        for token_name in token_names:
            try:
                result = self.context_manager.get_token(token_name)
                if result:
                    token_value, metadata = result
                    service_name = metadata.get("service_name", token_name.split("_")[0])
                    
                    # Create credential object
                    credential = Credential(
                        type="api_key",
                        data={"api_key": token_value},
                        expires_at=metadata.get("expires_at")
                    )
                    
                    # Cache it
                    self._cache_credential(service_name, credential)
                    restored_count += 1
                    
            except Exception as e:
                logger.debug(f"Could not restore token {token_name}: {e}")
        
        if restored_count > 0:
            logger.info(f"Restored {restored_count} tokens from context")