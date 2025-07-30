# Meta-MCP Server Package

This package contains the refactored Meta-MCP server implementation, split into focused modules following AI-First development principles.

## Module Structure

### core.py (402 lines)
Core server class and initialization:
- `MetaMCPServer` class definition
- Component initialization (registry, router, auth, cache)
- Service discovery and auto-discovery
- Statistics tracking
- Shutdown handling

### handlers.py (427 lines)
Request handling logic:
- `_handle_initialize`: Server initialization
- `_handle_tools_list`: List available tools
- `_handle_tool_call`: Execute tool calls
- `_handle_resources_*`: Resource operations
- Tool execution methods for each service type

### session.py (196 lines)
Session and context management:
- `_restore_session_context`: Restore previous session
- `_save_session_context`: Save current session
- `_restore_saved_tokens`: Token persistence
- `_clear_session_context`: Clear session data
- `_get_session_summary`: Session status reporting

### transport.py (316 lines)
Transport-specific implementations:
- HTTP route setup via FastAPI
- Stdio mode for Claude Code
- WebSocket support (future)
- Common JSON-RPC processing

## AI-First Features

Each module includes:
- **AI_CONTEXT docstrings** explaining the module's purpose
- **Navigation aids** pointing to related code
- **Clear separation of concerns** for easier AI comprehension
- **Focused functionality** with files under 500 lines

## Usage

The refactoring maintains full backward compatibility:

```python
from agtos.metamcp.server import MetaMCPServer

# Works exactly as before
server = MetaMCPServer(config)
await server.start()  # HTTP mode
# or
await server.start_stdio()  # Stdio mode
```

## Architecture

The server uses a mixin pattern to compose functionality:

1. `MetaMCPServer` (core.py) - Main class with initialization
2. `HandlerMixin` (handlers.py) - Request handling methods
3. `SessionMixin` (session.py) - Session management methods
4. `TransportMixin` (transport.py) - Transport-specific methods

Methods from mixins are bound to the main class during initialization, providing a clean separation while maintaining a unified API.