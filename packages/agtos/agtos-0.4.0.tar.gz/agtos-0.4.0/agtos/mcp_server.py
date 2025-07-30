"""Local MCP server implementation with full spec compliance."""
import asyncio
import json
import os
import signal
import subprocess
import sys
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .plugins import get_all_tools
from .utils import is_port_in_use
from .user_tools.natural_naming import NaturalNamer

# Global reference to loaded tools
TOOLS: Dict[str, Any] = {}
# Mapping between natural names and actual tool names
NATURAL_NAME_MAP: Dict[str, str] = {}
ACTUAL_NAME_MAP: Dict[str, str] = {}
NATURAL_NAMER = NaturalNamer(style="conversational")
MCP_VERSION = "2025-03-26"  # Latest MCP spec version
SERVER_INFO = {
    "name": "agtos",
    "version": "0.3.0",
    "vendor": "agtos"
}

# Method handler registry
METHOD_HANDLERS: Dict[str, Callable[[Dict[str, Any], Any], Awaitable[Dict[str, Any]]]] = {}

# Lock for thread-safe tool reloading
reload_lock = asyncio.Lock()

async def reload_tools():
    """Reload all tools and update natural name mappings.
    
    AI_CONTEXT: This function reloads all tools from plugins,
    updating the global TOOLS dict and natural name mappings.
    Called when new tools are created via tool_creator.
    """
    global TOOLS, NATURAL_NAME_MAP, ACTUAL_NAME_MAP
    
    async with reload_lock:
        # Get fresh tools list
        new_tools = get_all_tools()
        
        # Update TOOLS dict
        TOOLS.clear()
        TOOLS.update(new_tools)
        
        # Rebuild natural name mappings
        NATURAL_NAME_MAP.clear()
        ACTUAL_NAME_MAP.clear()
        
        for tool_name, tool_data in TOOLS.items():
            # Generate natural name based on tool description or name
            description = tool_data.get("description", "")
            
            # For tool_creator functions, create more conversational names
            if tool_name.startswith("tool_creator_"):
                if tool_name == "tool_creator_create":
                    natural_name = "creating_new_tool"
                elif tool_name == "tool_creator_list":
                    natural_name = "listing_all_your_tools"
                elif tool_name == "tool_creator_edit":
                    natural_name = "editing_an_existing_tool"
                elif tool_name == "tool_creator_delete":
                    natural_name = "deleting_tool"
                elif tool_name == "tool_creator_analyze":
                    natural_name = "analyzing_tool_creation_request"
                elif tool_name == "tool_creator_info":
                    natural_name = "getting_tool_information"
                elif tool_name == "tool_creator_list_all":
                    natural_name = "showing_all_available_tools"
                elif tool_name == "tool_creator_check_updates":
                    natural_name = "checking_for_tool_updates"
                elif tool_name == "tool_creator_clarify":
                    natural_name = "clarifying_tool_requirements"
                elif tool_name == "tool_creator_continue":
                    natural_name = "continuing_clarification"
                elif tool_name == "tool_creator_suggest":
                    natural_name = "suggesting_tool_providers"
                elif tool_name == "tool_creator_sessions":
                    natural_name = "viewing_active_sessions"
                elif tool_name == "tool_creator_summary":
                    natural_name = "summarizing_tool_capabilities"
                elif tool_name == "tool_creator_versions":
                    natural_name = "showing_tool_versions"
                elif tool_name == "tool_creator_migrate":
                    natural_name = "migrating_tool_version"
                elif tool_name == "tool_creator_upgrade":
                    natural_name = "upgrading_tool"
                elif tool_name == "tool_creator_error_details":
                    natural_name = "viewing_error_details"
                else:
                    natural_name = NATURAL_NAMER.create_natural_name(description or tool_name)
            elif tool_name.startswith("ephemeral_"):
                if tool_name == "ephemeral_create":
                    natural_name = "creating_temporary_tool_now"
                elif tool_name == "ephemeral_execute":
                    natural_name = "running_temporary_tool"
                else:
                    natural_name = NATURAL_NAMER.create_natural_name(description or tool_name)
            elif "_get_" in tool_name or "_post_" in tool_name or "_put_" in tool_name or "_delete_" in tool_name:
                # Handle user tool method patterns like pokemon_stats_get_pokemon
                parts = tool_name.split("_")
                
                # Find the action verb
                action_index = next((i for i, p in enumerate(parts) if p in ["get", "post", "put", "delete"]), -1)
                
                if action_index >= 0:
                    # Extract base tool name and target
                    base_name = "_".join(parts[:action_index])
                    action = parts[action_index]
                    target = "_".join(parts[action_index+1:]) if action_index+1 < len(parts) else ""
                    
                    # Create natural names based on known patterns
                    if base_name == "pokemon_stats":
                        natural_name = "getting_pokemon_stats"
                    elif base_name == "weather_check":
                        natural_name = "checking_weather"
                    elif base_name == "coingecko_prices":
                        natural_name = "getting_crypto_prices"
                    elif base_name == "xano_ultrathink":
                        natural_name = "querying_xano_database"
                    else:
                        # Generic pattern
                        if action == "get":
                            natural_name = f"getting_{base_name}_data"
                        elif action == "post":
                            natural_name = f"posting_to_{base_name}"
                        elif action == "put":
                            natural_name = f"updating_{base_name}"
                        elif action == "delete":
                            natural_name = f"deleting_from_{base_name}"
                        else:
                            natural_name = NATURAL_NAMER.create_natural_name(tool_name)
                else:
                    natural_name = NATURAL_NAMER.create_natural_name(description or tool_name)
            else:
                # For other tools, use their description or name
                intent = description if description else tool_name.replace("_", " ")
                natural_name = NATURAL_NAMER.create_natural_name(intent)
            
            # Store bidirectional mapping
            NATURAL_NAME_MAP[tool_name] = natural_name
            ACTUAL_NAME_MAP[natural_name] = tool_name
        
        print(f"🔄 Reloaded {len(TOOLS)} tools with natural names")

async def watch_reload_marker():
    """Watch for reload marker file created by tool_creator.
    
    AI_CONTEXT: This background task checks for a .reload_marker file
    that tool_creator writes when a new tool is created. When detected,
    it triggers a tool reload.
    """
    reload_marker = Path.home() / ".agtos" / "user_tools" / ".reload_marker"
    last_mtime = None
    
    while True:
        try:
            if reload_marker.exists():
                current_mtime = reload_marker.stat().st_mtime
                if last_mtime is None or current_mtime > last_mtime:
                    last_mtime = current_mtime
                    # Read the marker to see which tool was created
                    content = reload_marker.read_text().strip()
                    if content:
                        tool_name = content.split('\n')[0]
                        print(f"🔄 Detected new tool: {tool_name}")
                        await reload_tools()
                    # Delete the marker after processing
                    reload_marker.unlink(missing_ok=True)
        except Exception as e:
            print(f"⚠️ Error in reload watcher: {e}")
        
        # Check every 2 seconds
        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    global TOOLS, NATURAL_NAME_MAP, ACTUAL_NAME_MAP
    
    # Initial tool load
    await reload_tools()
    
    # Start background reload watcher
    reload_task = asyncio.create_task(watch_reload_marker())
    
    yield
    
    # Shutdown
    reload_task.cancel()
    try:
        await reload_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="agtos MCP Server", lifespan=lifespan)

# Add CORS middleware for broad compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_initialize(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request.
    
    AI_CONTEXT: Establishes MCP session with capability negotiation.
    Returns server info and supported capabilities.
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": MCP_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {
                "tools": True,
                "resources": False,  # Can add file/URL resources later
                "prompts": False,    # Can add prompt templates later
                "logging": True
            }
        }
    }


async def handle_tools_list(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request.
    
    AI_CONTEXT: Returns all available tools with their schemas.
    Each tool includes name, description, and input schema.
    """
    tools_list = []
    for tool_name, tool_data in TOOLS.items():
        # Use natural name for display
        natural_name = NATURAL_NAME_MAP.get(tool_name, tool_name)
        tools_list.append({
            "name": natural_name,
            "description": tool_data.get("description", ""),
            "inputSchema": tool_data["schema"]
        })
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": tools_list}
    }


async def handle_tools_call(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request.
    
    AI_CONTEXT: Executes a specific tool with provided parameters.
    Includes timeout handling and detailed error reporting.
    """
    natural_name = params.get("name")
    arguments = params.get("arguments", {})
    
    # Convert natural name back to actual tool name
    tool_name = ACTUAL_NAME_MAP.get(natural_name, natural_name)
    
    if tool_name not in TOOLS:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": f"Tool not found: {tool_name}"
            }
        }
    
    # For tool creation, generate a more specific natural name based on the description
    display_name = natural_name
    if tool_name == "tool_creator_create" and "description" in arguments:
        # Use the natural namer to create a context-aware name
        desc = arguments["description"]
        tool_name_arg = arguments.get("name", "")
        
        # Create a descriptive intent from the description
        if "pokemon" in desc.lower() or "pokeapi" in desc.lower():
            display_name = "creating_pokemon_stats_tool"
        elif "weather" in desc.lower():
            display_name = "creating_weather_tool"
        elif "slack" in desc.lower():
            display_name = "creating_slack_messaging_tool" 
        elif "crypto" in desc.lower() or "coin" in desc.lower() or "coingecko" in desc.lower():
            display_name = "creating_cryptocurrency_price_tool"
        elif tool_name_arg:
            # Use the tool name being created
            display_name = f"creating_{tool_name_arg}_tool"
        else:
            # Try to extract meaningful name from description
            natural_desc = NATURAL_NAMER.create_natural_name(f"create {desc}")
            display_name = natural_desc
    elif tool_name == "tool_creator_list_all":
        # Make the list_all more contextual
        if "source" in arguments:
            source = arguments["source"]
            display_name = f"showing_all_{source}_tools"
        else:
            display_name = "showing_all_available_tools"
    elif tool_name == "ephemeral_create" and "intent" in arguments:
        # Use the intent for ephemeral tool creation
        intent = arguments["intent"]
        display_name = NATURAL_NAMER.create_natural_name(f"create ephemeral {intent}")
    
    # Log tool execution with natural name
    print(f"⚡ Executing {display_name} with args: {json.dumps(arguments, indent=2)}")
    
    try:
        # Execute tool with timeout
        tool_func = TOOLS[tool_name]["func"]
        result = await asyncio.wait_for(
            asyncio.to_thread(tool_func, **arguments),
            timeout=30.0
        )
        
        print(f"✅ {display_name} completed successfully")
        
        # If this was a tool creation, reload tools to make it immediately available
        if tool_name == "tool_creator_create" and result.get("success", False):
            await reload_tools()
            print(f"🔄 Reloaded tools after creating {arguments.get('name', 'new tool')}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    except asyncio.TimeoutError:
        print(f"⏱️  {display_name} timed out after 30s")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Tool execution timed out after 30 seconds"
            }
        }
    except Exception as e:
        print(f"❌ {display_name} failed: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": f"Tool execution failed: {str(e)}"
            }
        }


async def handle_logging_setlevel(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle logging/setLevel request.
    
    AI_CONTEXT: Updates the logging level for the server.
    Currently accepts the level but doesn't apply it.
    """
    level = params.get("level", "info")
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"level": level}
    }


# Register method handlers
METHOD_HANDLERS["initialize"] = handle_initialize
METHOD_HANDLERS["tools/list"] = handle_tools_list
METHOD_HANDLERS["tools/call"] = handle_tools_call
METHOD_HANDLERS["logging/setLevel"] = handle_logging_setlevel

@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC 2.0 requests per MCP specification.
    
    AI_CONTEXT: Main entry point for MCP requests. Parses JSON-RPC,
    validates structure, and dispatches to appropriate handler.
    Uses method registry pattern for clean routing.
    
    Returns:
        JSONResponse with result or error per JSON-RPC 2.0 spec
    """
    # Parse JSON body
    body, parse_error = await _parse_json_body(request)
    if parse_error:
        return parse_error
    
    # Extract request components
    method = body.get("method")
    request_id = body.get("id")
    params = body.get("params", {})
    
    # Validate request structure
    validation_error = _validate_request_structure(method, request_id)
    if validation_error:
        return validation_error
    
    # Dispatch to handler
    return await _dispatch_to_handler(method, request_id, params)


async def _parse_json_body(request: Request):
    """Parse JSON body from request.
    
    Args:
        request: The HTTP request
        
    Returns:
        Tuple of (body dict, error response or None)
    """
    try:
        body = await request.json()
        return body, None
    except Exception:
        error = JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        )
        return None, error


def _validate_request_structure(method: str, request_id: Any):
    """Validate JSON-RPC request structure.
    
    Args:
        method: The method name
        request_id: The request ID
        
    Returns:
        Error response dict or None if valid
    """
    if not method:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32600,
                "message": "Invalid request: missing method"
            }
        }
    return None


async def _dispatch_to_handler(method: str, request_id: Any, params: Dict[str, Any]):
    """Dispatch request to appropriate handler.
    
    Args:
        method: The method name
        request_id: The request ID
        params: Request parameters
        
    Returns:
        Handler response or error for unknown method
    """
    handler = METHOD_HANDLERS.get(method)
    if handler:
        return await handler(request_id, params)
    
    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "tools_loaded": len(TOOLS),
        "mcp_version": MCP_VERSION,
        "server_info": SERVER_INFO,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/tools")
async def list_tools():
    """List available tools (non-MCP endpoint for debugging)."""
    return {
        "tools": list(TOOLS.keys()),
        "count": len(TOOLS)
    }

def start_mcp_server(port: int, env_vars: Dict[str, str]) -> subprocess.Popen:
    """Start the MCP server as a subprocess.
    
    Args:
        port: Port to run the server on
        env_vars: Environment variables to pass to the server
        
    Returns:
        subprocess.Popen instance for the server process
    """
    # Check if port is already in use
    if is_port_in_use(port):
        # Try to find an available port
        for alt_port in range(port + 1, port + 10):
            if not is_port_in_use(alt_port):
                port = alt_port
                print(f"⚠️  Port {port - 1} in use, using {port} instead")
                break
        else:
            raise RuntimeError(f"Could not find available port near {port}")
    
    # Merge env vars with current environment
    env = os.environ.copy()
    env.update(env_vars)
    
    # Get the path to the current Python interpreter
    python_path = sys.executable
    
    # Start uvicorn in subprocess - show output for logging
    cmd = [
        python_path, "-m", "uvicorn",
        "agtos.mcp_server:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--log-level", "info",  # Show info level logs
    ]
    
    # Start process with output to console for monitoring
    process = subprocess.Popen(
        cmd, 
        env=env,
        # Let stdout/stderr flow to console
        stdout=None,
        stderr=None
    )
    
    # Give the server a moment to start
    import time
    time.sleep(1.5)
    
    # Check if process is still running
    if process.poll() is not None:
        raise RuntimeError("MCP server failed to start")
    
    return process

# For direct testing
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=4405)