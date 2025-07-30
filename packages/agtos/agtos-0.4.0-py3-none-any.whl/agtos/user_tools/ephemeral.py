"""Ephemeral tool system for dynamic, single-use tools with natural naming.

This module provides a system for creating temporary tools that:
- Are generated on-the-fly based on user intent
- Have natural, descriptive names that match the user's request
- Auto-cleanup after use or expiration
- Don't accumulate in the file system

AI_CONTEXT:
    This solves the verbosity problem in a different way than conversational wrappers:
    - Instead of permanent wrappers with generic names, we create ephemeral tools
    - Tool names match exactly what the user asked for (e.g., get_top_7_cryptos)
    - Tools are garbage collected automatically
    - No permanent storage unless explicitly requested
"""

import asyncio
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import weakref

logger = logging.getLogger(__name__)


@dataclass
class EphemeralTool:
    """Represents an ephemeral tool with lifecycle management."""
    
    name: str
    natural_name: str  # The user-friendly name like "get_top_7_cryptos"
    base_tool: str
    parameters: Dict[str, Any]
    created_at: datetime
    ttl_seconds: int = 300  # 5 minutes default
    usage_count: int = 0
    max_uses: Optional[int] = None  # Tool expires after N uses
    
    def is_expired(self) -> bool:
        """Check if the tool has expired."""
        # Check time expiration
        if datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds):
            return True
        
        # Check usage expiration
        if self.max_uses and self.usage_count >= self.max_uses:
            return True
            
        return False
    
    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count += 1


class EphemeralToolManager:
    """Manages lifecycle of ephemeral tools.
    
    This manager creates temporary tools with natural names that:
    - Match the user's intent exactly
    - Are stored in memory or temporary files
    - Are automatically garbage collected
    - Can be persisted if the user wants to keep them
    """
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """Initialize the ephemeral tool manager.
        
        Args:
            temp_dir: Custom temporary directory (uses system temp if not provided)
        """
        # Use system temp or custom directory
        if temp_dir:
            self.temp_dir = temp_dir
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="agtos_ephemeral_"))
        
        # Active tools tracked by ID
        self._tools: Dict[str, EphemeralTool] = {}
        
        # Map natural names to tool IDs for easy lookup
        self._name_to_id: Dict[str, str] = {}
        
        # Weak references for automatic cleanup
        self._tool_refs: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task for periodic cleanup."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(60)  # Check every minute
                self.cleanup_expired()
        
        # Run in background
        loop = asyncio.new_event_loop()
        self._cleanup_task = loop.create_task(cleanup_loop())
    
    def create_ephemeral_tool(
        self,
        natural_name: str,
        base_tool: str,
        parameters: Dict[str, Any],
        ttl_seconds: int = 300,
        max_uses: Optional[int] = None
    ) -> str:
        """Create an ephemeral tool with a natural name.
        
        Args:
            natural_name: Natural language name (e.g., "get_top_7_cryptos")
            base_tool: The underlying tool to wrap
            parameters: Parameters to bind to the tool
            ttl_seconds: Time to live in seconds
            max_uses: Maximum number of uses before expiration
            
        Returns:
            Tool ID for the created tool
        """
        with self._lock:
            # Generate unique ID
            tool_id = self._generate_tool_id(natural_name, parameters)
            
            # Check if already exists
            if tool_id in self._tools:
                tool = self._tools[tool_id]
                # Reset expiration if recreated
                tool.created_at = datetime.now()
                tool.usage_count = 0
                logger.info(f"Refreshed ephemeral tool: {natural_name}")
                return tool_id
            
            # Create new tool
            tool = EphemeralTool(
                name=tool_id,
                natural_name=natural_name,
                base_tool=base_tool,
                parameters=parameters,
                created_at=datetime.now(),
                ttl_seconds=ttl_seconds,
                max_uses=max_uses
            )
            
            # Store tool
            self._tools[tool_id] = tool
            self._name_to_id[natural_name] = tool_id
            
            # Generate tool code in temp directory
            self._generate_tool_code(tool)
            
            logger.info(f"Created ephemeral tool: {natural_name} (TTL: {ttl_seconds}s)")
            return tool_id
    
    def _generate_tool_id(self, natural_name: str, parameters: Dict[str, Any]) -> str:
        """Generate unique tool ID from name and parameters."""
        # Create stable hash from name and params
        data = f"{natural_name}:{sorted(parameters.items())}"
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    def _generate_tool_code(self, tool: EphemeralTool) -> Path:
        """Generate Python code for the ephemeral tool."""
        # Clean natural name for Python function
        func_name = tool.natural_name.replace(" ", "_").replace("-", "_").lower()
        
        # Generate code that binds the parameters
        code = f'''"""Ephemeral tool: {tool.natural_name}
Generated at: {tool.created_at.isoformat()}
Expires: {tool.ttl_seconds}s after creation or {tool.max_uses or 'unlimited'} uses
"""

from typing import Dict, Any

# Bound parameters for this ephemeral tool
BOUND_PARAMS = {repr(tool.parameters)}

def {func_name}(**overrides) -> Dict[str, Any]:
    """Execute {tool.natural_name}.
    
    This is an ephemeral tool that wraps {tool.base_tool}
    with pre-configured parameters.
    """
    # Start with bound parameters
    params = BOUND_PARAMS.copy()
    
    # Apply any overrides
    params.update(overrides)
    
    # Import and execute base tool
    # Note: In production, this would call the actual tool
    return {{
        "tool": "{tool.base_tool}",
        "parameters": params,
        "ephemeral": True,
        "natural_name": "{tool.natural_name}"
    }}

# MCP metadata
__mcp_export__ = {{
    "name": "{func_name}",
    "description": "{tool.natural_name}",
    "inputSchema": {{
        "type": "object",
        "properties": {{}},
        "additionalProperties": True
    }}
}}
'''
        
        # Write to temp file
        tool_file = self.temp_dir / f"{tool.name}.py"
        tool_file.write_text(code)
        
        return tool_file
    
    def execute_ephemeral_tool(
        self,
        natural_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute an ephemeral tool by its natural name.
        
        Args:
            natural_name: The natural language name
            **kwargs: Additional parameters to override
            
        Returns:
            Tool execution result
        """
        with self._lock:
            # Find tool by natural name
            tool_id = self._name_to_id.get(natural_name)
            if not tool_id or tool_id not in self._tools:
                raise ValueError(f"Ephemeral tool '{natural_name}' not found")
            
            tool = self._tools[tool_id]
            
            # Check expiration
            if tool.is_expired():
                self._remove_tool(tool_id)
                raise ValueError(f"Ephemeral tool '{natural_name}' has expired")
            
            # Increment usage
            tool.increment_usage()
            
            # Merge parameters
            params = tool.parameters.copy()
            params.update(kwargs)
            
            # Execute (in real implementation, would call actual tool)
            result = {
                "tool": tool.base_tool,
                "parameters": params,
                "natural_name": natural_name,
                "usage": f"{tool.usage_count}/{tool.max_uses or '∞'}"
            }
            
            # Check if should expire after this use
            if tool.is_expired():
                self._remove_tool(tool_id)
                result["expired"] = True
            
            return result
    
    def persist_ephemeral_tool(self, natural_name: str, new_name: Optional[str] = None) -> Path:
        """Convert an ephemeral tool to a permanent tool.
        
        Args:
            natural_name: Natural name of the ephemeral tool
            new_name: New name for the permanent tool (uses natural_name if not provided)
            
        Returns:
            Path to the permanent tool file
        """
        with self._lock:
            tool_id = self._name_to_id.get(natural_name)
            if not tool_id or tool_id not in self._tools:
                raise ValueError(f"Ephemeral tool '{natural_name}' not found")
            
            tool = self._tools[tool_id]
            permanent_name = new_name or natural_name
            
            # Generate permanent tool code
            code = self._generate_permanent_code(tool, permanent_name)
            
            # Save to user tools directory
            user_tools_dir = Path.home() / ".agtos" / "user_tools"
            user_tools_dir.mkdir(parents=True, exist_ok=True)
            
            safe_name = permanent_name.replace(" ", "_").replace("-", "_").lower()
            permanent_file = user_tools_dir / f"{safe_name}.py"
            permanent_file.write_text(code)
            
            logger.info(f"Persisted ephemeral tool '{natural_name}' as '{permanent_name}'")
            return permanent_file
    
    def _generate_permanent_code(self, tool: EphemeralTool, permanent_name: str) -> str:
        """Generate code for a permanent version of an ephemeral tool."""
        func_name = permanent_name.replace(" ", "_").replace("-", "_").lower()
        
        return f'''"""Permanent tool: {permanent_name}
Converted from ephemeral tool: {tool.natural_name}
Created: {datetime.now().isoformat()}
"""

from typing import Dict, Any

# Default parameters from ephemeral tool
DEFAULT_PARAMS = {repr(tool.parameters)}

def {func_name}(**params) -> Dict[str, Any]:
    """Execute {permanent_name}.
    
    This tool wraps {tool.base_tool} with smart defaults.
    """
    # Start with defaults
    final_params = DEFAULT_PARAMS.copy()
    
    # Apply user parameters
    final_params.update(params)
    
    # Import and execute base tool
    from agtos.runtime import execute_tool
    return execute_tool("{tool.base_tool}", **final_params)

# MCP metadata
__mcp_export__ = {{
    "name": "{func_name}",
    "description": "{permanent_name}",
    "inputSchema": {{
        "type": "object",
        "properties": {{}},
        "additionalProperties": True
    }}
}}
'''
    
    def cleanup_expired(self) -> int:
        """Remove expired tools from memory and disk.
        
        Returns:
            Number of tools cleaned up
        """
        with self._lock:
            expired_tools = []
            
            # Find expired tools
            for tool_id, tool in self._tools.items():
                if tool.is_expired():
                    expired_tools.append(tool_id)
            
            # Remove expired tools
            for tool_id in expired_tools:
                self._remove_tool(tool_id)
            
            if expired_tools:
                logger.info(f"Cleaned up {len(expired_tools)} expired ephemeral tools")
            
            return len(expired_tools)
    
    def _remove_tool(self, tool_id: str):
        """Remove a tool from memory and disk."""
        if tool_id not in self._tools:
            return
        
        tool = self._tools[tool_id]
        
        # Remove from mappings
        del self._tools[tool_id]
        if tool.natural_name in self._name_to_id:
            del self._name_to_id[tool.natural_name]
        
        # Remove temp file
        tool_file = self.temp_dir / f"{tool.name}.py"
        if tool_file.exists():
            tool_file.unlink()
        
        logger.debug(f"Removed ephemeral tool: {tool.natural_name}")
    
    def list_active_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all active ephemeral tools.
        
        Returns:
            Dictionary of natural_name -> tool info
        """
        with self._lock:
            active_tools = {}
            
            for tool in self._tools.values():
                if not tool.is_expired():
                    active_tools[tool.natural_name] = {
                        "base_tool": tool.base_tool,
                        "parameters": tool.parameters,
                        "created_at": tool.created_at.isoformat(),
                        "expires_in": max(0, tool.ttl_seconds - (datetime.now() - tool.created_at).seconds),
                        "usage": f"{tool.usage_count}/{tool.max_uses or '∞'}"
                    }
            
            return active_tools
    
    def cleanup_all(self):
        """Clean up all ephemeral tools and temporary directory."""
        with self._lock:
            # Remove all tools
            for tool_id in list(self._tools.keys()):
                self._remove_tool(tool_id)
            
            # Remove temp directory if it's our managed one
            if self.temp_dir.name.startswith("agtos_ephemeral_"):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        logger.info("Cleaned up all ephemeral tools")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.cleanup_all()
        except:
            pass  # Ignore errors during cleanup


# Global manager instance
_ephemeral_manager: Optional[EphemeralToolManager] = None


def get_ephemeral_manager() -> EphemeralToolManager:
    """Get or create the global ephemeral tool manager."""
    global _ephemeral_manager
    
    if _ephemeral_manager is None:
        _ephemeral_manager = EphemeralToolManager()
    
    return _ephemeral_manager


def create_natural_tool(
    user_intent: str,
    base_tool: str,
    parameters: Dict[str, Any],
    ttl_seconds: int = 300,
    single_use: bool = False
) -> str:
    """Create an ephemeral tool with a natural name based on user intent.
    
    Args:
        user_intent: What the user asked for (e.g., "check top 7 cryptocurrencies")
        base_tool: The underlying tool to use
        parameters: Parameters to bind to the tool
        ttl_seconds: How long the tool should live
        single_use: If True, tool expires after one use
        
    Returns:
        Natural tool name that can be used to execute it
    """
    manager = get_ephemeral_manager()
    
    # Convert intent to natural function name
    # "check top 7 cryptocurrencies" -> "check_top_7_cryptocurrencies"
    natural_name = user_intent.lower().replace(" ", "_").replace("-", "_")
    
    # Create the tool
    manager.create_ephemeral_tool(
        natural_name=natural_name,
        base_tool=base_tool,
        parameters=parameters,
        ttl_seconds=ttl_seconds,
        max_uses=1 if single_use else None
    )
    
    return natural_name


def execute_natural_tool(natural_name: str, **kwargs) -> Dict[str, Any]:
    """Execute an ephemeral tool by its natural name.
    
    Args:
        natural_name: The natural language name
        **kwargs: Additional parameters
        
    Returns:
        Tool execution result
    """
    manager = get_ephemeral_manager()
    return manager.execute_ephemeral_tool(natural_name, **kwargs)