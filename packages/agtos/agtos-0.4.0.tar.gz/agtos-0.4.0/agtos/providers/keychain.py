"""macOS Keychain credential provider."""
import subprocess
import json
from typing import Dict, List, Optional
from .base import CredentialProvider

class KeychainProvider(CredentialProvider):
    """macOS Keychain credential provider using security CLI.
    
    This is the default provider for agentctl, offering good security
    without requiring any additional tools. Credentials are stored in
    the user's login keychain.
    """
    
    def __init__(self):
        self.service_prefix = "agtos"
        self.account_name = "agtos"
    
    @property
    def name(self) -> str:
        return "macOS Keychain"
    
    @property
    def security_level(self) -> str:
        return "medium"  # Secure but local-only
    
    def get_secret(self, service: str) -> Optional[str]:
        """Retrieve secret from macOS Keychain."""
        self.validate_service_name(service)
        
        try:
            result = subprocess.run([
                "security", "find-generic-password",
                "-s", f"{self.service_prefix}-{service}",
                "-a", self.account_name,
                "-w"  # Print only the password
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def set_secret(self, service: str, value: str) -> None:
        """Store secret in macOS Keychain."""
        self.validate_service_name(service)
        
        # First try to delete existing (if any) to avoid duplicates
        try:
            subprocess.run([
                "security", "delete-generic-password",
                "-s", f"{self.service_prefix}-{service}",
                "-a", self.account_name
            ], capture_output=True, check=False)
        except:
            pass  # Ignore if doesn't exist
        
        # Add new secret
        try:
            subprocess.run([
                "security", "add-generic-password",
                "-s", f"{self.service_prefix}-{service}",
                "-a", self.account_name,
                "-w", value,
                "-U"  # Update if exists
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to store secret in Keychain: {e.stderr.decode()}")
    
    def delete_secret(self, service: str) -> None:
        """Delete secret from macOS Keychain."""
        self.validate_service_name(service)
        
        try:
            subprocess.run([
                "security", "delete-generic-password",
                "-s", f"{self.service_prefix}-{service}",
                "-a", self.account_name
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # Ignore if doesn't exist
    
    def list_services(self) -> List[str]:
        """List all services with stored secrets."""
        try:
            # Use security find-generic-password to search
            result = subprocess.run([
                "security", "find-generic-password",
                "-a", self.account_name
            ], capture_output=True, text=True)
            
            services = []
            for line in result.stdout.split('\n'):
                if line.strip().startswith('"svce"'):
                    # Extract service name from the line
                    # Format: "svce"<blob>="agtos-servicename"
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        service_full = parts[1].strip('"')
                        if service_full.startswith(f'{self.service_prefix}-'):
                            service = service_full[len(f'{self.service_prefix}-'):]
                            services.append(service)
            
            return list(set(services))  # Remove duplicates
        except Exception:
            return []
    
    def export_all(self) -> Dict[str, str]:
        """Export all secrets as environment variables."""
        env_vars = {}
        for service in self.list_services():
            secret = self.get_secret(service)
            if secret:
                # Convert service name to env var format
                # e.g., cloudflare -> CLOUDFLARE_API_KEY
                env_var_name = f"{service.upper().replace('-', '_')}_API_KEY"
                env_vars[env_var_name] = secret
        return env_vars