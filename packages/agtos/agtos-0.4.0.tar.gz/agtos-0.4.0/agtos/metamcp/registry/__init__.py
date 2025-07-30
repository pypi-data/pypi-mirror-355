"""Service Registry for Meta-MCP Server.

This package manages the registration and discovery of all downstream services:
- MCP servers (filesystem, github, etc.)
- CLI tools (kubectl, docker, etc.)
- REST APIs (stripe, openai, etc.)
- Custom plugins from agtos

The registry is split into focused modules for better maintainability:
- core: Core ServiceRegistry class and data models
- discovery: Tool discovery for different service types
- connection: MCP server connection management
- health: Health monitoring for all services
- execution: Tool execution across different service types
"""

# Re-export main classes for backward compatibility
from .core import (
    ServiceRegistry,
    ServiceType,
    ServiceStatus,
    ServiceConfig,
    ServiceInfo
)

__all__ = [
    'ServiceRegistry',
    'ServiceType',
    'ServiceStatus',
    'ServiceConfig',
    'ServiceInfo'
]