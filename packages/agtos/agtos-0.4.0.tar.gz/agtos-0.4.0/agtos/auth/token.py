"""
AI_CONTEXT: Token storage and management
Handles secure offline token storage with keychain integration.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ..providers.keychain import KeychainProvider
from .models import AuthToken


class TokenStore:
    """
    Manages offline token storage for authentication.
    
    AI_CONTEXT: Secure token persistence
    Uses keychain for secure storage and local file for metadata.
    Implements 7-day token expiry with 3-day offline grace period.
    """
    
    def __init__(self):
        self.keychain = KeychainProvider()
        self.config_dir = Path.home() / ".agtos"
        self.config_dir.mkdir(exist_ok=True)
        self.token_file = self.config_dir / "auth.json"
        
    def save_token(self, token: AuthToken):
        """
        Save auth token securely.
        
        Args:
            token: AuthToken to save
        """
        # Save token to keychain
        self.keychain.set_credential("agtos", "auth_token", token.access_token)
        if token.refresh_token:
            self.keychain.set_credential("agtos", "refresh_token", token.refresh_token)
        
        # Save metadata to file
        metadata = {
            "user_id": str(token.user_id),
            "expires_at": token.expires_at.isoformat(),
            "created_at": token.created_at.isoformat(),
            "last_verified": datetime.now(timezone.utc).isoformat()
        }
        
        with open(self.token_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def get_token(self) -> Optional[AuthToken]:
        """
        Get stored auth token.
        
        Returns:
            AuthToken if found, None otherwise
        """
        if not self.token_file.exists():
            return None
        
        try:
            # Load metadata
            with open(self.token_file) as f:
                metadata = json.load(f)
            
            # Get tokens from keychain
            access_token = self.keychain.get_credential("agtos", "auth_token")
            refresh_token = self.keychain.get_credential("agtos", "refresh_token")
            
            if not access_token:
                return None
            
            return AuthToken(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.fromisoformat(metadata["expires_at"]),
                user_id=metadata["user_id"],
                created_at=datetime.fromisoformat(metadata["created_at"])
            )
        except:
            return None
    
    def get_valid_token(self) -> Optional[AuthToken]:
        """
        Get token if valid (not expired or within grace period).
        
        AI_CONTEXT: Offline grace period logic
        - Tokens valid for 7 days when online
        - 3-day grace period for offline usage
        - Last verified timestamp tracks online validation
        
        Returns:
            Valid AuthToken or None
        """
        token = self.get_token()
        if not token:
            return None
        
        # Check if expired
        if not token.is_expired:
            return token
        
        # Check offline grace period
        try:
            with open(self.token_file) as f:
                metadata = json.load(f)
            
            last_verified = datetime.fromisoformat(metadata.get("last_verified", metadata["created_at"]))
            grace_period_end = last_verified + timedelta(days=10)  # 7 days + 3 days grace
            
            if datetime.now(timezone.utc) < grace_period_end:
                return token
        except:
            pass
        
        return None
    
    def update_last_verified(self):
        """Update last verified timestamp for online validation."""
        if not self.token_file.exists():
            return
        
        try:
            with open(self.token_file, "r") as f:
                metadata = json.load(f)
            
            metadata["last_verified"] = datetime.now(timezone.utc).isoformat()
            
            with open(self.token_file, "w") as f:
                json.dump(metadata, f, indent=2)
        except:
            pass
    
    def clear_tokens(self):
        """Clear all stored tokens."""
        try:
            self.keychain.delete_credential("agtos", "auth_token")
            self.keychain.delete_credential("agtos", "refresh_token")
            if self.token_file.exists():
                self.token_file.unlink()
        except:
            pass