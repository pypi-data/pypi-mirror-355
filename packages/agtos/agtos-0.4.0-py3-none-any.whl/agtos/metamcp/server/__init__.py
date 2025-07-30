"""Meta-MCP Server Package.

AI_CONTEXT:
    This package contains the refactored Meta-MCP server implementation
    split into focused modules following AI-First principles:
    
    - core.py: Core server class and initialization
    - handlers.py: Request handlers for MCP operations
    - session.py: Session and context management
    - transport.py: Transport-specific implementations (HTTP/stdio)
    
    The MetaMCPServer class is re-exported here for backward compatibility.
"""

from .core import MetaMCPServer

__all__ = ["MetaMCPServer"]