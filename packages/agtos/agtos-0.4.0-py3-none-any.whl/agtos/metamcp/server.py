"""Meta-MCP Server - Backward compatibility wrapper.

AI_CONTEXT:
    This file provides backward compatibility for imports that expect
    MetaMCPServer to be in agtos.metamcp.server. The actual implementation
    has been refactored into the server/ package following AI-First principles.
    
    The refactored structure:
    - server/core.py: Core server class and initialization
    - server/handlers.py: Request handlers for MCP operations  
    - server/session.py: Session and context management
    - server/transport.py: Transport implementations (HTTP/stdio)
    
    This wrapper ensures existing code continues to work without changes.
"""

# Re-export MetaMCPServer for backward compatibility
from .server import MetaMCPServer

__all__ = ["MetaMCPServer"]