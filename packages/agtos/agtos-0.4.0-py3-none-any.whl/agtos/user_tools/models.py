"""Data models for natural language tool creation.

AI_CONTEXT:
    This module defines the core data structures used throughout the
    natural language tool creation process. These models represent:
    - User input and specifications
    - API endpoints and parameters
    - Authentication methods
    - Generated tool code
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class HTTPMethod(Enum):
    """Supported HTTP methods for REST APIs."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class AuthType(Enum):
    """Supported authentication types."""
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2 = "oauth2"  # Future


class ParameterLocation(Enum):
    """Where parameters are sent in the request."""
    QUERY = "query"
    BODY = "body"
    PATH = "path"
    HEADER = "header"


@dataclass
class Parameter:
    """Represents an API parameter.
    
    AI_CONTEXT: Parameters can be inferred from natural language
    descriptions or explicitly defined by the user.
    """
    name: str
    type: str = "string"  # string, number, boolean, object, array
    location: ParameterLocation = ParameterLocation.QUERY
    required: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None
    example: Optional[Any] = None


@dataclass
class AuthenticationMethod:
    """Authentication configuration for an API."""
    type: AuthType
    location: str = "header"  # header, query, cookie
    key_name: str = "Authorization"  # e.g., "Authorization", "X-API-Key"
    value_prefix: str = ""  # e.g., "Bearer " for bearer tokens
    credentials_var: Optional[str] = None  # Environment variable name


@dataclass
class APIEndpoint:
    """Represents a single API endpoint.
    
    AI_CONTEXT: This is what gets extracted from user descriptions
    like "post messages to api.company.com/messages".
    """
    url: str
    method: HTTPMethod
    description: str
    parameters: List[Parameter] = field(default_factory=list)
    authentication: Optional[AuthenticationMethod] = None
    headers: Dict[str, str] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolSpecification:
    """User's specification for a new tool.
    
    AI_CONTEXT: This captures the user's intent before we generate
    the actual tool implementation.
    """
    name: str
    description: str
    natural_language_spec: str  # Original user description
    endpoints: List[APIEndpoint] = field(default_factory=list)
    category: str = "custom"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    author: str = "user"
    metadata: Dict[str, Any] = field(default_factory=dict)  # For SSL, timeout, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert specification to dictionary for storage."""
        return {
            "name": self.name,
            "description": self.description,
            "natural_language": self.natural_language_spec,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "author": self.author,
            "metadata": self.metadata,
            "endpoints": [
                {
                    "url": ep.url,
                    "method": ep.method.value,
                    "description": ep.description,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "location": p.location.value,
                            "required": p.required,
                            "description": p.description,
                            "default": p.default,
                            "example": p.example
                        }
                        for p in ep.parameters
                    ],
                    "authentication": {
                        "type": ep.authentication.type.value,
                        "location": ep.authentication.location,
                        "key_name": ep.authentication.key_name,
                        "value_prefix": ep.authentication.value_prefix,
                        "credentials_var": ep.authentication.credentials_var
                    } if ep.authentication else None,
                    "headers": ep.headers,
                    "examples": ep.examples
                }
                for ep in self.endpoints
            ]
        }


@dataclass
class GeneratedTool:
    """The generated tool code and metadata.
    
    AI_CONTEXT: This is the final output that gets saved and can be
    used immediately as an MCP tool.
    """
    spec: ToolSpecification
    tool_code: str  # The Python implementation
    mcp_schema: Dict[str, Any]  # MCP tool schema for registration
    validation_status: str = "not_validated"
    validation_errors: List[str] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClarificationResult:
    """Result from the clarification process."""
    success: bool
    tool_config: Optional[Dict[str, Any]] = None
    provider_info: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    session_id: Optional[str] = None
    error: Optional[str] = None