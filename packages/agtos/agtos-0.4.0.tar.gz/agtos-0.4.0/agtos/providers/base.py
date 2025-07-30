"""Base class for credential providers."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class CredentialProvider(ABC):
    """Abstract base class for credential providers.
    
    All credential providers must implement this interface to ensure
    compatibility with agtos's flexible credential management system.
    """
    
    @abstractmethod
    def get_secret(self, service: str) -> Optional[str]:
        """Retrieve a secret for a service.
        
        Args:
            service: The service name (e.g., 'cloudflare', 'mailerlite')
            
        Returns:
            The secret value if found, None otherwise
        """
        pass
    
    @abstractmethod
    def set_secret(self, service: str, value: str) -> None:
        """Store a secret for a service.
        
        Args:
            service: The service name
            value: The secret value to store
        """
        pass
    
    @abstractmethod
    def delete_secret(self, service: str) -> None:
        """Delete a secret for a service.
        
        Args:
            service: The service name
        """
        pass
    
    @abstractmethod
    def list_services(self) -> List[str]:
        """List all services with stored secrets.
        
        Returns:
            List of service names
        """
        pass
    
    @abstractmethod
    def export_all(self) -> Dict[str, str]:
        """Export all secrets as environment variables.
        
        Returns:
            Dict of environment variable names to values
            Format: {SERVICE}_API_KEY -> secret_value
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the provider."""
        pass
    
    @property
    @abstractmethod
    def security_level(self) -> str:
        """Security level: 'high', 'medium', or 'development'."""
        pass
    
    def validate_service_name(self, service: str) -> None:
        """Validate service name format.
        
        Args:
            service: The service name to validate
            
        Raises:
            ValueError: If service name is invalid
        """
        if not service:
            raise ValueError("Service name cannot be empty")
        
        # Allow alphanumeric, hyphens, and underscores
        if not service.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"Service name '{service}' is invalid. "
                f"Use only letters, numbers, hyphens, and underscores."
            )