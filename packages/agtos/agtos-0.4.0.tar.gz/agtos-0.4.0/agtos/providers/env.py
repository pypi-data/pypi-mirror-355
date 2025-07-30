"""Environment variable and file-based credential provider."""
import os
from pathlib import Path
from typing import Dict, List, Optional
from .base import CredentialProvider

class EnvironmentProvider(CredentialProvider):
    """Environment variable and .env file credential provider.
    
    This provider is intended for development use only. It stores
    credentials in a plain text file and should not be used for
    production or sensitive data.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or os.getenv("AGTOS_ENV_FILE", str(Path.home() / ".agtos" / ".env"))
        self._env_vars: Dict[str, str] = {}
        self._ensure_env_file()
        self._load_env_file()
    
    @property
    def name(self) -> str:
        return "Environment Variables"
    
    @property
    def security_level(self) -> str:
        return "development"
    
    def _ensure_env_file(self):
        """Ensure the env file and directory exist."""
        env_path = Path(self.env_file)
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not env_path.exists():
            # Create with warning header
            env_path.write_text(
                "# agentctl credential file (DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION)\n"
                "# Add this file to .gitignore!\n"
                "# Consider using 'agtos cred-provider set keychain' for better security\n\n"
            )
            # Set restrictive permissions (owner read/write only)
            env_path.chmod(0o600)
    
    def _load_env_file(self):
        """Load environment variables from file."""
        env_path = Path(self.env_file)
        if env_path.exists():
            self._env_vars.clear()
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        self._env_vars[key] = value
    
    def _save_env_file(self):
        """Save environment variables to file."""
        env_path = Path(self.env_file)
        with open(env_path, 'w') as f:
            f.write("# agentctl credential file (DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION)\n")
            f.write("# Add this file to .gitignore!\n")
            f.write("# Consider using 'agtos cred-provider set keychain' for better security\n\n")
            
            # Group by service for readability
            services = {}
            for key, value in sorted(self._env_vars.items()):
                if key.endswith("_API_KEY"):
                    service = key[:-8]  # Remove _API_KEY suffix
                    services[service] = (key, value)
            
            for service, (key, value) in sorted(services.items()):
                f.write(f"# {service.lower()} credentials\n")
                f.write(f"{key}={value}\n\n")
        
        # Ensure restrictive permissions
        env_path.chmod(0o600)
    
    def get_secret(self, service: str) -> Optional[str]:
        """Retrieve secret from environment."""
        self.validate_service_name(service)
        env_key = f"{service.upper().replace('-', '_')}_API_KEY"
        
        # Check runtime environment first (takes precedence)
        value = os.getenv(env_key)
        if value:
            return value
        
        # Then check loaded env file
        return self._env_vars.get(env_key)
    
    def set_secret(self, service: str, value: str) -> None:
        """Store secret in environment file."""
        self.validate_service_name(service)
        env_key = f"{service.upper().replace('-', '_')}_API_KEY"
        
        # Update in-memory store
        self._env_vars[env_key] = value
        
        # Save to file
        self._save_env_file()
    
    def delete_secret(self, service: str) -> None:
        """Delete secret from environment."""
        self.validate_service_name(service)
        env_key = f"{service.upper().replace('-', '_')}_API_KEY"
        
        # Remove from in-memory store
        self._env_vars.pop(env_key, None)
        
        # Save updated file
        self._save_env_file()
    
    def list_services(self) -> List[str]:
        """List all services with stored secrets."""
        services = []
        
        # Check both runtime env and file
        all_keys = set(os.environ.keys()) | set(self._env_vars.keys())
        
        for key in all_keys:
            if key.endswith("_API_KEY"):
                # Convert env var format back to service name
                # e.g., CLOUDFLARE_API_KEY -> cloudflare
                service = key[:-8].lower().replace('_', '-')
                services.append(service)
        
        return sorted(list(set(services)))  # Remove duplicates and sort
    
    def export_all(self) -> Dict[str, str]:
        """Export all secrets as environment variables."""
        env_vars = {}
        
        # Start with file vars
        env_vars.update(self._env_vars)
        
        # Override with runtime env (runtime takes precedence)
        for key, value in os.environ.items():
            if key.endswith("_API_KEY"):
                env_vars[key] = value
        
        return env_vars