"""1Password credential provider."""
import subprocess
import json
from typing import Dict, List, Optional
from .base import CredentialProvider

class OnePasswordProvider(CredentialProvider):
    """1Password CLI credential provider.
    
    Requires 1Password app and CLI (op) to be installed and configured.
    Offers the highest security level with biometric authentication and
    cloud sync across devices.
    """
    
    def __init__(self):
        self.vault = "agtos"
        self.item_prefix = "agtos"
        self._ensure_op_installed()
        self._ensure_vault_exists()
    
    @property
    def name(self) -> str:
        return "1Password"
    
    @property
    def security_level(self) -> str:
        return "high"
    
    def _ensure_op_installed(self):
        """Check if 1Password CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["op", "--version"], 
                capture_output=True, 
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "1Password CLI (op) is not installed. "
                "Install from: https://developer.1password.com/docs/cli/get-started/"
            )
        
        # Check if signed in
        try:
            subprocess.run(
                ["op", "account", "list"],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Not signed in to 1Password. "
                "Run: eval $(op signin)"
            )
    
    def _ensure_vault_exists(self):
        """Ensure the agentctl vault exists."""
        try:
            # Check if vault exists
            result = subprocess.run(
                ["op", "vault", "get", self.vault, "--format=json"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # Create vault if it doesn't exist
                subprocess.run(
                    ["op", "vault", "create", self.vault],
                    check=True,
                    capture_output=True
                )
        except subprocess.CalledProcessError:
            # Try to create vault
            try:
                subprocess.run(
                    ["op", "vault", "create", self.vault],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to create 1Password vault: {e}")
    
    def get_secret(self, service: str) -> Optional[str]:
        """Retrieve secret from 1Password."""
        self.validate_service_name(service)
        item_name = f"{self.item_prefix}-{service}"
        
        try:
            result = subprocess.run([
                "op", "item", "get", item_name,
                f"--vault={self.vault}",
                "--fields", "api_key"
            ], capture_output=True, text=True, check=True)
            
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def set_secret(self, service: str, value: str) -> None:
        """Store secret in 1Password."""
        self.validate_service_name(service)
        item_name = f"{self.item_prefix}-{service}"
        
        # Check if item exists
        existing = self.get_secret(service)
        
        try:
            if existing is not None:
                # Update existing item
                subprocess.run([
                    "op", "item", "edit", item_name,
                    f"api_key={value}",
                    f"--vault={self.vault}"
                ], capture_output=True, check=True)
            else:
                # Create new item
                subprocess.run([
                    "op", "item", "create",
                    "--category=API Credential",
                    f"--title={item_name}",
                    f"--vault={self.vault}",
                    f"api_key[password]={value}",
                    f"service={service}",
                    f"notes=Created by agtos"
                ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to store secret in 1Password: {e.stderr.decode()}")
    
    def delete_secret(self, service: str) -> None:
        """Delete secret from 1Password."""
        self.validate_service_name(service)
        item_name = f"{self.item_prefix}-{service}"
        
        try:
            subprocess.run([
                "op", "item", "delete", item_name,
                f"--vault={self.vault}"
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # Ignore if doesn't exist
    
    def list_services(self) -> List[str]:
        """List all services with stored secrets."""
        try:
            result = subprocess.run([
                "op", "item", "list",
                f"--vault={self.vault}",
                "--format=json"
            ], capture_output=True, text=True, check=True)
            
            items = json.loads(result.stdout)
            services = []
            
            for item in items:
                title = item.get("title", "")
                if title.startswith(f"{self.item_prefix}-"):
                    service = title[len(f"{self.item_prefix}-"):]
                    services.append(service)
            
            return services
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    def export_all(self) -> Dict[str, str]:
        """Export all secrets as environment variables."""
        env_vars = {}
        for service in self.list_services():
            secret = self.get_secret(service)
            if secret:
                env_var_name = f"{service.upper().replace('-', '_')}_API_KEY"
                env_vars[env_var_name] = secret
        return env_vars