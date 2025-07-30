# Service Registry Module

This package contains the refactored Service Registry for the Meta-MCP Server, split into focused modules following AI-First Development principles.

## Module Structure

### `core.py` (~400 lines)
- Core `ServiceRegistry` class
- Data models (`ServiceType`, `ServiceStatus`, `ServiceConfig`, `ServiceInfo`)
- Service registration methods for all service types
- High-level service query methods

### `discovery.py` (~380 lines)
- `DiscoveryManager` class for tool discovery
- CLI tool discovery using knowledge base
- REST API discovery from OpenAPI specs
- Plugin tool extraction from Python objects
- Tool naming and aliasing strategies

### `connection.py` (~180 lines)
- `ConnectionManager` for MCP server connections
- Transport-specific connection handling (stdio, HTTP, WebSocket)
- Connection lifecycle management
- Tool discovery after connection

### `health.py` (~280 lines)
- `HealthMonitor` for service health checks
- Service-specific health check strategies
- Background health monitoring
- Response time tracking

### `execution.py` (~460 lines)
- `ExecutionManager` for tool execution
- Service-specific execution strategies
- Error handling and debugging
- Result formatting

## Key Features

1. **Separation of Concerns**: Each module focuses on a specific aspect of service management
2. **AI-Friendly Structure**: Each file is under 500 lines with clear navigation aids
3. **Comprehensive Documentation**: AI_CONTEXT docstrings on complex methods
4. **Backward Compatibility**: The package exports all necessary classes through `__init__.py`

## Usage

The refactored modules work exactly like the original monolithic file:

```python
from agtos.metamcp.registry import ServiceRegistry, ServiceType

# Create registry
registry = ServiceRegistry(debug=True)

# Register services
await registry.register_cli_tool("git", {"binary": "git"})
await registry.register_mcp_server("filesystem", {"url": "http://localhost:3000"})

# Execute tools
result = await registry.execute_tool("git", "cli__git__status", {})
```

## Benefits of Refactoring

1. **Maintainability**: Easier to find and modify specific functionality
2. **Testability**: Each module can be tested independently
3. **Extensibility**: New service types or features can be added without touching core logic
4. **AI Navigation**: Clearer structure helps AI assistants understand and modify code
5. **Performance**: Lazy loading of helper modules reduces initial import time