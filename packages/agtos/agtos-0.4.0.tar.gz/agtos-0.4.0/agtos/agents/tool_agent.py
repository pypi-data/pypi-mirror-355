"""Tool execution agent for agtOS.

This agent executes tools through the Meta-MCP server, bridging the gap between
the orchestration engine and the tool ecosystem.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import asyncio
import re

from .base import BaseAgent, AgentCapability, ExecutionResult

logger = logging.getLogger(__name__)


class ToolAgent(BaseAgent):
    """Agent that executes tools through Meta-MCP.
    
    This agent serves as the bridge between the orchestration engine and
    the tool ecosystem. It can execute any tool registered with Meta-MCP
    including CLI tools, REST APIs, user-created tools, and plugins.
    """
    
    name = "tool_executor"
    description = "Execute tools and integrations through Meta-MCP"
    
    capabilities = [
        AgentCapability.TOOL_EXECUTION,
        AgentCapability.API_INTERACTION,
        AgentCapability.SCRIPTING,
        AgentCapability.FILE_OPERATIONS,
        AgentCapability.WEB_AUTOMATION
    ]
    
    # Cost is minimal as this just routes to tools
    cost_per_1k_tokens = 0.001
    
    def __init__(self):
        """Initialize the tool agent."""
        super().__init__()
        self.tool_registry = None
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize connection to tool registry."""
        try:
            # Import here to avoid circular dependencies
            from agtos.metamcp.registry import ToolRegistry
            self.tool_registry = ToolRegistry()
        except ImportError:
            logger.warning("MetaMCP registry not available, using direct tool access")
            self.tool_registry = None
    
    async def execute(self, prompt: str, context: Dict[str, Any]) -> ExecutionResult:
        """Execute a tool based on the prompt.
        
        The prompt can be:
        1. Natural language: "run git status"
        2. Tool specification: "execute cli__git__status"
        3. Structured format from workflow metadata
        
        Args:
            prompt: Description of what tool to execute
            context: Execution context including parameters
            
        Returns:
            ExecutionResult with tool output
        """
        try:
            # Extract tool information from prompt and context
            tool_info = self._parse_tool_request(prompt, context)
            
            if not tool_info:
                return ExecutionResult(
                    success=False,
                    content="",
                    error="Could not determine which tool to execute",
                    metadata={"prompt": prompt}
                )
            
            # Execute the tool
            result = await self._execute_tool(
                tool_info['name'],
                tool_info['type'],
                tool_info['parameters'],
                context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ExecutionResult(
                success=False,
                content="",
                error=str(e),
                metadata={"tool": tool_info.get('name', 'unknown')}
            )
    
    def _parse_tool_request(self, prompt: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse tool information from prompt and context.
        
        Args:
            prompt: Natural language or tool specification
            context: May contain tool_name, tool_type, parameters
            
        Returns:
            Dict with name, type, and parameters or None
        """
        # First check if context has explicit tool information
        if context.get('tool_name'):
            return {
                'name': context['tool_name'],
                'type': context.get('tool_type', 'unknown'),
                'parameters': context.get('parameters', {})
            }
        
        # Check metadata for workflow step information
        metadata = context.get('metadata', {})
        if metadata.get('tool_name'):
            return {
                'name': metadata['tool_name'],
                'type': metadata.get('tool_type', 'unknown'),
                'parameters': metadata.get('parameters', {})
            }
        
        # Try to parse from prompt
        # Pattern 1: "execute tool_name with params"
        exec_match = re.match(r'execute\s+(\S+)(?:\s+with\s+(.+))?', prompt.lower())
        if exec_match:
            tool_name = exec_match.group(1)
            params_str = exec_match.group(2)
            
            parameters = {}
            if params_str:
                # Try to parse as JSON first
                try:
                    parameters = json.loads(params_str)
                except:
                    # Parse key=value pairs
                    for pair in params_str.split(','):
                        if '=' in pair:
                            key, value = pair.strip().split('=', 1)
                            parameters[key.strip()] = value.strip()
            
            return {
                'name': tool_name,
                'type': self._infer_tool_type(tool_name),
                'parameters': parameters
            }
        
        # Pattern 2: Natural language like "run git status"
        # This would require more sophisticated NLP
        # For now, return None to indicate we couldn't parse
        return None
    
    def _infer_tool_type(self, tool_name: str) -> str:
        """Infer tool type from tool name patterns."""
        if tool_name.startswith('cli__'):
            return 'cli'
        elif tool_name.startswith('rest__'):
            return 'rest'
        elif tool_name.startswith('plugin__'):
            return 'plugin'
        elif tool_name.startswith('user__'):
            return 'user'
        else:
            return 'unknown'
    
    async def _execute_tool(self, tool_name: str, tool_type: str,
                           parameters: Dict[str, Any], 
                           context: Dict[str, Any]) -> ExecutionResult:
        """Execute a specific tool through the appropriate mechanism.
        
        Args:
            tool_name: Name of the tool to execute
            tool_type: Type of tool (cli, rest, plugin, user)
            parameters: Tool parameters
            context: Execution context
            
        Returns:
            ExecutionResult with tool output
        """
        # If we have MetaMCP registry, use it
        if self.tool_registry:
            try:
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    result = await tool.execute(parameters)
                    return ExecutionResult(
                        success=result.get('success', False),
                        content=result.get('output', ''),
                        error=result.get('error'),
                        metadata={
                            'tool_name': tool_name,
                            'tool_type': tool_type,
                            'execution_time': result.get('execution_time')
                        }
                    )
            except Exception as e:
                logger.error(f"Registry execution failed: {e}")
        
        # Fallback to direct execution based on tool type
        if tool_type == 'cli':
            return await self._execute_cli_tool(tool_name, parameters)
        elif tool_type == 'rest':
            return await self._execute_rest_tool(tool_name, parameters)
        elif tool_type == 'plugin':
            return await self._execute_plugin_tool(tool_name, parameters)
        elif tool_type == 'user':
            return await self._execute_user_tool(tool_name, parameters)
        else:
            return ExecutionResult(
                success=False,
                content="",
                error=f"Unknown tool type: {tool_type}",
                metadata={'tool_name': tool_name}
            )
    
    async def _execute_cli_tool(self, tool_name: str, 
                               parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute a CLI tool."""
        try:
            # Import here to avoid circular dependencies
            from agtos.metamcp.bridges.cli_bridge import CLIBridge
            
            # Parse tool name: cli__command__subcommand
            parts = tool_name.split('__')
            if len(parts) < 2:
                raise ValueError(f"Invalid CLI tool name: {tool_name}")
            
            command = parts[1]
            subcommand = parts[2] if len(parts) > 2 else None
            
            # Create bridge instance
            bridge = CLIBridge()
            
            # Build arguments
            args = parameters.get('arguments', [])
            if subcommand:
                args = [subcommand] + args
            
            # Execute command
            result = await bridge.execute_command(command, args)
            
            return ExecutionResult(
                success=result['success'],
                content=result.get('stdout', ''),
                error=result.get('stderr'),
                metadata={
                    'exit_code': result.get('exit_code', 0),
                    'tool_name': tool_name
                }
            )
            
        except Exception as e:
            logger.error(f"CLI tool execution error: {e}")
            return ExecutionResult(
                success=False,
                content="",
                error=str(e),
                metadata={'tool_name': tool_name}
            )
    
    async def _execute_rest_tool(self, tool_name: str,
                                parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute a REST API tool."""
        try:
            # Import here to avoid circular dependencies
            from agtos.metamcp.bridges.rest_bridge import RESTBridge
            
            # REST tools would be registered with their configurations
            # For now, return not implemented
            return ExecutionResult(
                success=False,
                content="",
                error="REST tool execution not yet implemented",
                metadata={'tool_name': tool_name}
            )
            
        except Exception as e:
            logger.error(f"REST tool execution error: {e}")
            return ExecutionResult(
                success=False,
                content="",
                error=str(e),
                metadata={'tool_name': tool_name}
            )
    
    async def _execute_plugin_tool(self, tool_name: str,
                                  parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute a plugin tool."""
        try:
            # Import plugin system
            from agtos.plugins import get_all_tools
            
            # Get all available tools
            tools = get_all_tools()
            
            if tool_name in tools:
                tool_func = tools[tool_name].get('func')
                if tool_func:
                    # Execute the tool function
                    result = await asyncio.create_task(
                        asyncio.to_thread(tool_func, **parameters)
                    )
                    
                    # Handle different result formats
                    if isinstance(result, dict):
                        return ExecutionResult(
                            success=result.get('success', True),
                            content=result.get('message', str(result)),
                            error=result.get('error'),
                            metadata={'tool_name': tool_name}
                        )
                    else:
                        return ExecutionResult(
                            success=True,
                            content=str(result),
                            metadata={'tool_name': tool_name}
                        )
            
            return ExecutionResult(
                success=False,
                content="",
                error=f"Plugin tool not found: {tool_name}",
                metadata={'tool_name': tool_name}
            )
            
        except Exception as e:
            logger.error(f"Plugin tool execution error: {e}")
            return ExecutionResult(
                success=False,
                content="",
                error=str(e),
                metadata={'tool_name': tool_name}
            )
    
    async def _execute_user_tool(self, tool_name: str,
                                parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute a user-created tool."""
        try:
            # User tools are loaded as plugins
            return await self._execute_plugin_tool(f"user__{tool_name}", parameters)
            
        except Exception as e:
            logger.error(f"User tool execution error: {e}")
            return ExecutionResult(
                success=False,
                content="",
                error=str(e),
                metadata={'tool_name': tool_name}
            )
    
    def estimate_cost(self, prompt: str, context: Dict[str, Any]) -> float:
        """Estimate cost of executing a tool.
        
        Tool execution is generally very cheap as it's just routing.
        """
        # Rough estimate based on prompt length
        tokens = len(prompt.split()) * 1.5  # Rough token estimate
        return (tokens / 1000) * self.cost_per_1k_tokens