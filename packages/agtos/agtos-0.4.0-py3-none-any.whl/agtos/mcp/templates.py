"""Template generation for MCP servers and documentation.

AI_CONTEXT:
    This module contains all template generation logic for MCP export,
    including server code templates, README generation, and other
    documentation. Separating templates makes them easier to maintain
    and modify without affecting core logic.
"""
from typing import Dict, Any, List
from .utils import MCP_VERSION, DEFAULT_PORT


def generate_mcp_server(plugin_name: str, plugin: Dict[str, Any]) -> str:
    """Generate a standalone MCP server for the plugin.
    
    AI_CONTEXT:
        This generates a complete FastAPI-based MCP server that can host
        the plugin's tools. The server implements the MCP protocol with
        JSON-RPC 2.0 endpoints for tool listing and execution.
    
    Args:
        plugin_name: Name of the plugin
        plugin: Plugin definition (unused but kept for compatibility)
        
    Returns:
        Complete Python server code as a string
    """
    return MCP_SERVER_TEMPLATE.format(
        plugin_name=plugin_name,
        mcp_version=MCP_VERSION,
        default_port=DEFAULT_PORT
    )


def generate_readme(plugin_name: str, metadata: Dict[str, Any]) -> str:
    """Generate README for an exported MCP tool.
    
    Args:
        plugin_name: Name of the plugin
        metadata: Tool metadata including description, tools, etc.
        
    Returns:
        Complete README content as markdown
    """
    readme = f"""# MCP Tool: {plugin_name}

{metadata.get('description', f'MCP tool for {plugin_name} integration')}

## Overview

This is a standalone MCP (Model Context Protocol) tool exported from agtos.
It provides AI assistants with access to {plugin_name} functionality.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As MCP Server

Run the MCP server:

```bash
python run.py
```

The server will start on `http://localhost:{DEFAULT_PORT}`

### Direct Import

You can also import and use the plugin directly:

```python
from {plugin_name}_plugin import TOOLS

# List available tools
for tool_name, tool_def in TOOLS.items():
    print(f"Tool: {{tool_name}}")
    print(f"  Description: {{tool_def.get('description', '')}}")
```

## Available Tools

"""
    
    # Add tools documentation
    for tool in metadata.get("tools", []):
        readme += _format_tool_documentation(tool)
    
    # Add optional sections
    if metadata.get("knowledge_included"):
        readme += _get_knowledge_section()
    
    if metadata.get("examples_included"):
        readme += _get_examples_section()
    
    # Add metadata section
    readme += _format_metadata_section(metadata)
    
    # Add original package info if available
    if "original_package" in metadata:
        readme += _format_original_package_section(metadata["original_package"])
    
    return readme


def generate_package_readme(package_name: str, tools: List[Dict[str, Any]]) -> str:
    """Generate README for an MCP tool package/bundle.
    
    Args:
        package_name: Name of the package
        tools: List of tool information dictionaries
        
    Returns:
        Package README content as markdown
    """
    readme = f"""# {package_name}

A bundle of MCP (Model Context Protocol) tools exported from agtos.

## Contents

This package contains {len(tools)} MCP tools:

"""
    
    for tool in tools:
        name = tool["name"]
        metadata = tool["metadata"]
        readme += f"### {name}\n"
        readme += f"{metadata.get('description', f'MCP tool for {name}')}\n\n"
    
    readme += """
## Installation

1. Extract this package
2. Install dependencies for each tool:
   ```bash
   cd <tool-directory>
   pip install -r requirements.txt
   ```

## Usage

Each tool can be used independently. See the README in each tool's directory for specific usage instructions.

## About

These tools were exported from agtos, a local AI-driven development utility that provides:
- MCP server functionality
- Plugin management
- Knowledge acquisition
- Tool generation

For more information, visit: https://github.com/agtos-ai/agtos
"""
    
    return readme


def generate_run_script() -> str:
    """Generate a run.py script for starting the MCP server.
    
    Returns:
        Python script content
    """
    return f'''#!/usr/bin/env python3
"""Run script for MCP server."""
import uvicorn
from server import app

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port={DEFAULT_PORT})
'''


# Private helper functions

def _format_tool_documentation(tool: Dict[str, Any]) -> str:
    """Format documentation for a single tool."""
    doc = f"\n### {tool['name']}\n\n"
    doc += f"{tool['description']}\n\n"
    
    if tool.get('schema', {}).get('properties'):
        doc += "**Parameters:**\n"
        for param, details in tool['schema']['properties'].items():
            required = param in tool['schema'].get('required', [])
            req_marker = " *(required)*" if required else ""
            desc = details.get('description', 'No description')
            doc += f"- `{param}`: {desc}{req_marker}\n"
        doc += "\n"
    
    return doc


def _get_knowledge_section() -> str:
    """Get the knowledge base section for README."""
    return """
## Knowledge Base

This export includes a knowledge base with information about:
- API endpoints and schemas
- CLI commands and options  
- Usage examples and patterns

See `knowledge.json` for details.
"""


def _get_examples_section() -> str:
    """Get the examples section for README."""
    return """
## Examples

Usage examples are included in `examples.json`.
"""


def _format_metadata_section(metadata: Dict[str, Any]) -> str:
    """Format the metadata section for README."""
    return f"""
## Metadata

- **Created**: {metadata.get('created_at', 'Unknown')}
- **Source**: agentctl v{metadata.get('source_version', '1.0')}
- **MCP Version**: {metadata.get('mcp_version', MCP_VERSION)}
"""


def _format_original_package_section(pkg: Dict[str, Any]) -> str:
    """Format the original package section for README."""
    section = f"""
## Original Package

- **Name**: {pkg.get('name', 'Unknown')}
- **Version**: {pkg.get('version', 'Unknown')}
- **Type**: {pkg.get('type', 'Unknown')}"""
    
    if pkg.get('homepage'):
        section += f"\n- **Homepage**: {pkg['homepage']}"
    if pkg.get('author'):
        section += f"\n- **Author**: {pkg['author']}"
    
    return section + "\n"


# Server template constant
MCP_SERVER_TEMPLATE = '''"""Standalone MCP server for {plugin_name} tool.
Auto-generated by agtos.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from typing import Dict, Any, List
import importlib

# Import the plugin
plugin_module = importlib.import_module("{plugin_name}_plugin")

app = FastAPI()
logger = logging.getLogger(__name__)

# MCP protocol version
MCP_VERSION = "{mcp_version}"

@app.get("/")
async def root():
    """Root endpoint with MCP protocol info."""
    return {{
        "mcp_version": MCP_VERSION,
        "name": "mcp-tool-{plugin_name}",
        "description": "MCP tool for {plugin_name} integration"
    }}

@app.post("/rpc")
async def handle_rpc(request: Request):
    """Handle JSON-RPC 2.0 requests."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={{
                "jsonrpc": "2.0",
                "error": {{
                    "code": -32700,
                    "message": "Parse error"
                }},
                "id": None
            }}
        )
    
    # Extract request details
    method = body.get("method")
    params = body.get("params", {{}})
    request_id = body.get("id")
    
    # Route to appropriate handler
    if method == "tools/list":
        result = await list_tools()
    elif method == "tools/execute":
        result = await execute_tool(params)
    else:
        return JSONResponse(
            content={{
                "jsonrpc": "2.0",
                "error": {{
                    "code": -32601,
                    "message": f"Method not found: {{method}}"
                }},
                "id": request_id
            }}
        )
    
    return JSONResponse(
        content={{
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }}
    )

async def list_tools() -> List[Dict[str, Any]]:
    """List available tools."""
    tools = []
    
    # Get tools from plugin
    plugin_tools = getattr(plugin_module, "TOOLS", {{}})
    
    for tool_name, tool_def in plugin_tools.items():
        tools.append({{
            "name": tool_name,
            "description": tool_def.get("description", ""),
            "schema": tool_def.get("schema", {{}}),
            "version": tool_def.get("version", "1.0")
        }})
    
    return tools

async def execute_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool."""
    tool_name = params.get("name")
    tool_params = params.get("params", {{}})
    
    # Get tools from plugin
    plugin_tools = getattr(plugin_module, "TOOLS", {{}})
    
    if tool_name not in plugin_tools:
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {{tool_name}}"
        )
    
    tool_def = plugin_tools[tool_name]
    func = tool_def.get("func")
    
    if not func:
        # Try to get function by name
        func_name = tool_def.get("func_name")
        if func_name and hasattr(plugin_module, func_name):
            func = getattr(plugin_module, func_name)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Tool function not found: {{tool_name}}"
            )
    
    try:
        # Execute the function
        result = func(**tool_params)
        
        # Ensure result is JSON serializable
        if isinstance(result, dict):
            return result
        else:
            return {{"result": str(result)}}
            
    except Exception as e:
        logger.error(f"Error executing tool {{tool_name}}: {{e}}")
        return {{
            "error": str(e),
            "success": False
        }}

# Add CORS support for web-based MCP clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''