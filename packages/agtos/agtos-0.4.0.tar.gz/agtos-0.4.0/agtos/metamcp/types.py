"""Type definitions for Meta-MCP Server.

AI_CONTEXT:
    This module contains all the type definitions, data classes, and
    protocol specifications used throughout the Meta-MCP server.
    These types ensure type safety and provide clear interfaces
    between components.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# JSON-RPC 2.0 Types

@dataclass
class MCPRequest:
    """MCP request following JSON-RPC 2.0 specification."""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        """Create request from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method", ""),
            params=data.get("params"),
            id=data.get("id")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        if self.id is not None:
            result["id"] = self.id
        return result


@dataclass
class MCPResponse:
    """MCP response following JSON-RPC 2.0 specification."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"jsonrpc": self.jsonrpc}
        
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
        if self.id is not None:
            result["id"] = self.id
            
        return result


@dataclass
class MCPError(Exception):
    """MCP error following JSON-RPC 2.0 error specification."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"MCPError({self.code}): {self.message}"


# MCP Protocol Types

@dataclass
class ToolSpec:
    """Specification for an MCP tool."""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    displayName: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP tool format."""
        # Only include standard MCP fields to ensure compatibility
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }


@dataclass
class ResourceSpec:
    """Specification for an MCP resource."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        result = {
            "uri": self.uri,
            "name": self.name
        }
        if self.description:
            result["description"] = self.description
        if self.mimeType:
            result["mimeType"] = self.mimeType
        return result


@dataclass
class PromptSpec:
    """Specification for an MCP prompt."""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP prompt format."""
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


@dataclass
class ServerCapabilities:
    """Server capabilities declaration."""
    tools: bool = False
    resources: bool = False
    prompts: bool = False
    logging: bool = False
    experimental: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP capabilities format."""
        result = {}
        if self.tools:
            result["tools"] = {}
        if self.resources:
            result["resources"] = {}
        if self.prompts:
            result["prompts"] = {}
        if self.logging:
            result["logging"] = {}
        if self.experimental:
            result["experimental"] = self.experimental
        return result


# Service Management Types

@dataclass
class ServiceHealth:
    """Health status of a service."""
    service: str
    healthy: bool
    status: str
    last_check: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[int] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "service": self.service,
            "healthy": self.healthy,
            "status": self.status,
            "last_check": self.last_check.isoformat()
        }
        if self.response_time_ms is not None:
            result["response_time_ms"] = self.response_time_ms
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class Credential:
    """Authentication credential."""
    type: str  # "api_key", "oauth2", "basic", etc.
    data: Dict[str, Any]
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if credential is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


# Connection Types

class ConnectionState(Enum):
    """State of a service connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class ConnectionInfo:
    """Information about a service connection."""
    service_name: str
    state: ConnectionState
    connected_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


# Cache Types

@dataclass
class CacheEntry:
    """Entry in the cache."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    size_bytes: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


# Dashboard Types

@dataclass
class ServiceStats:
    """Statistics for a service."""
    service_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    last_request: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return 1.0 - self.success_rate


@dataclass 
class SystemStats:
    """Overall system statistics."""
    start_time: datetime
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    active_connections: int = 0
    registered_services: int = 0
    available_tools: int = 0
    
    @property
    def uptime_seconds(self) -> float:
        """Calculate uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total


# Error Types

class MetaMCPError(Exception):
    """Base exception for Meta-MCP errors."""
    pass


class ServiceNotFoundError(MetaMCPError):
    """Raised when a requested service is not found."""
    pass


class ToolNotFoundError(MetaMCPError):
    """Raised when a requested tool is not found."""
    pass


class AuthenticationError(MetaMCPError):
    """Raised when authentication fails."""
    pass


class ConnectionError(MetaMCPError):
    """Raised when connection to a service fails."""
    pass


class CacheError(MetaMCPError):
    """Raised when cache operations fail."""
    pass