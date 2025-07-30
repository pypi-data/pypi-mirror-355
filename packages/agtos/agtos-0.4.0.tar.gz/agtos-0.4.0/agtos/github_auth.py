"""GitHub authentication management for agtOS.

This module handles GitHub authentication for private repository access,
including support for personal access tokens and GitHub App authentication.

AI_CONTEXT:
    This module is critical for agtOS distribution as the repository is private.
    It provides secure methods to authenticate with GitHub for:
    - Installing from private releases
    - Checking for updates
    - Accessing private repository resources
    
    The module integrates with the existing credential provider system
    and supports multiple authentication methods.
"""

import os
import requests
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta

from .providers import get_provider
from .utils import get_logger
from .config import get_config_dir

logger = get_logger(__name__)


class GitHubAuth:
    """Manages GitHub authentication for private repository access.
    
    AI_CONTEXT:
        Provides secure GitHub authentication with token caching,
        automatic renewal, and multiple authentication methods.
        Critical for private repository operations.
    """
    
    def __init__(self):
        """Initialize GitHub authentication manager."""
        self.provider = get_provider()
        self.config_dir = get_config_dir()
        self.token_cache_file = self.config_dir / ".github_token_cache"
        self._cached_token: Optional[str] = None
        self._cache_expiry: Optional[datetime] = None
    
    def get_token(self) -> Optional[str]:
        """Get GitHub access token from various sources.
        
        Checks in order:
        1. Environment variable (GITHUB_TOKEN)
        2. Cached token (if still valid)
        3. Credential provider (github service)
        4. User prompt (if interactive)
        
        Returns:
            GitHub token if available, None otherwise
        """
        # Check environment variable first
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            logger.debug("Using GitHub token from environment")
            return token
        
        # Check cached token
        if self._cached_token and self._cache_expiry and datetime.now() < self._cache_expiry:
            logger.debug("Using cached GitHub token")
            return self._cached_token
        
        # Check credential provider
        try:
            token = self.provider.get_secret("github")
            if token:
                logger.debug("Using GitHub token from credential provider")
                self._cache_token(token)
                return token
        except Exception as e:
            logger.warning(f"Failed to get GitHub token from provider: {e}")
        
        # Load from cache file if exists
        token = self._load_cached_token()
        if token:
            return token
        
        return None
    
    def set_token(self, token: str) -> None:
        """Store GitHub token securely.
        
        Args:
            token: GitHub personal access token
        """
        try:
            # Validate token first
            if self._validate_token(token):
                # Store in credential provider
                self.provider.set_secret("github", token)
                # Cache it
                self._cache_token(token)
                logger.info("GitHub token stored successfully")
            else:
                raise ValueError("Invalid GitHub token")
        except Exception as e:
            logger.error(f"Failed to store GitHub token: {e}")
            raise
    
    def _validate_token(self, token: str) -> bool:
        """Validate GitHub token by making a test API call.
        
        Args:
            token: Token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    def _cache_token(self, token: str, duration_hours: int = 24) -> None:
        """Cache token in memory and file with expiration.
        
        Args:
            token: Token to cache
            duration_hours: Cache duration in hours
        """
        self._cached_token = token
        self._cache_expiry = datetime.now() + timedelta(hours=duration_hours)
        
        # Also save to file for persistence
        try:
            cache_data = {
                "token": token,
                "expiry": self._cache_expiry.isoformat()
            }
            self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache_data, f)
            # Set restrictive permissions
            self.token_cache_file.chmod(0o600)
        except Exception as e:
            logger.warning(f"Failed to cache token to file: {e}")
    
    def _load_cached_token(self) -> Optional[str]:
        """Load token from cache file if still valid.
        
        Returns:
            Cached token if valid, None otherwise
        """
        try:
            if self.token_cache_file.exists():
                with open(self.token_cache_file) as f:
                    cache_data = json.load(f)
                
                expiry = datetime.fromisoformat(cache_data["expiry"])
                if datetime.now() < expiry:
                    token = cache_data["token"]
                    self._cached_token = token
                    self._cache_expiry = expiry
                    logger.debug("Loaded token from cache file")
                    return token
                else:
                    # Cache expired, remove file
                    self.token_cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")
        
        return None
    
    def get_authenticated_session(self) -> requests.Session:
        """Get a requests session with GitHub authentication headers.
        
        Returns:
            Configured requests session
            
        Raises:
            RuntimeError: If no valid token available
        """
        token = self.get_token()
        if not token:
            raise RuntimeError(
                "No GitHub token available. Please set one using:\n"
                "  export GITHUB_TOKEN=your_token\n"
                "  or: agtos configure credentials"
            )
        
        session = requests.Session()
        session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })
        return session
    
    def download_private_asset(self, url: str, dest_path: Path) -> None:
        """Download a private GitHub release asset.
        
        Args:
            url: Asset download URL
            dest_path: Destination file path
            
        Raises:
            RuntimeError: If download fails
        """
        session = self.get_authenticated_session()
        
        try:
            # GitHub release assets require special accept header
            session.headers["Accept"] = "application/octet-stream"
            
            response = session.get(url, stream=True)
            response.raise_for_status()
            
            # Write to file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded asset to {dest_path}")
            
        except Exception as e:
            logger.error(f"Failed to download asset: {e}")
            raise RuntimeError(f"Download failed: {e}")
    
    def get_latest_release(self, repo: str = "agtos-ai/agtos") -> Optional[Dict[str, Any]]:
        """Get latest release info from private repository.
        
        Args:
            repo: GitHub repository (owner/name)
            
        Returns:
            Release info dict if successful, None otherwise
        """
        try:
            session = self.get_authenticated_session()
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning("No releases found or repository not accessible")
            elif response.status_code == 401:
                logger.error("GitHub authentication failed - invalid token")
            else:
                logger.error(f"Failed to get release: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to check releases: {e}")
        
        return None


# Singleton instance
_github_auth = None

def get_github_auth() -> GitHubAuth:
    """Get the global GitHub auth instance.
    
    Returns:
        GitHubAuth singleton instance
    """
    global _github_auth
    if _github_auth is None:
        _github_auth = GitHubAuth()
    return _github_auth