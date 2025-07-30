"""Refactored handlers for Meta-MCP server - AI-First compliant.

AI_CONTEXT:
    This module contains refactored request handlers that comply with
    AI-First principles (50-line function limit). The original
    _handle_tool_call function (177 lines) has been split into:
    - Workflow recording management
    - Conversation tracking
    - Cache operations
    - Service execution routing
    - Error handling
    
    Each function now has a single, clear responsibility.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from agtos.errors import MCPError
from agtos.metamcp.argument_transformer import ArgumentTransformer, ArgumentValidationError
from agtos.metamcp.types import ToolSpec

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages workflow recording operations.
    
    AI_CONTEXT:
        Extracted from _handle_tool_call to handle workflow recording
        initialization and tracking. Keeps recording logic separate
        from tool execution logic.
    """
    
    def __init__(self):
        self._workflow_recorder = None
    
    def initialize_if_needed(self) -> None:
        """Initialize workflow recorder if recording is active."""
        if os.environ.get("AGTOS_RECORDING") != "1":
            return
            
        if not self._workflow_recorder:
            from agtos.workflows.recorder import WorkflowRecorder
            self._workflow_recorder = WorkflowRecorder()
            workflow_name = os.environ.get("AGTOS_WORKFLOW_NAME", "recorded_workflow")
            self._workflow_recorder.start_recording(workflow_name, "Auto-recorded workflow")
            logger.info(f"Workflow recording started: {workflow_name}")
    
    def record_execution_start(
        self,
        tool_name: str,
        tool_type: str,
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """Record workflow execution start if recording is active."""
        if not self.is_recording_active():
            return None
            
        return self._workflow_recorder.record_execution(
            tool_name=tool_name,
            tool_type=tool_type,
            parameters=parameters
        )
    
    def record_execution_result(
        self,
        execution_id: Optional[str],
        result: Any = None,
        error: Optional[str] = None
    ) -> None:
        """Record workflow execution result."""
        if not execution_id or not self.is_recording_active():
            return
            
        if error:
            self._workflow_recorder.record_result(execution_id, error=error)
        else:
            self._workflow_recorder.record_result(execution_id, result=result)
    
    def is_recording_active(self) -> bool:
        """Check if workflow recording is active."""
        return (
            os.environ.get("AGTOS_RECORDING") == "1" and
            self._workflow_recorder is not None and
            self._workflow_recorder.recording
        )


class ConversationTracker:
    """Tracks conversation messages for context.
    
    AI_CONTEXT:
        Extracted from _handle_tool_call to manage conversation history.
        Handles adding messages and periodic context saving.
    """
    
    def __init__(self, conversation_messages: list, save_callback):
        self.conversation_messages = conversation_messages
        self._save_callback = save_callback
    
    def add_tool_call(self, tool_name: str, tool_args: Dict[str, Any]) -> None:
        """Add tool call to conversation history."""
        self.conversation_messages.append({
            "role": "user",
            "content": f"Execute tool: {tool_name}",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_tool_result(
        self,
        tool_name: str,
        success: bool,
        result: Any = None,
        error: Optional[str] = None
    ) -> None:
        """Add tool execution result to conversation history."""
        message = {
            "role": "assistant",
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            message["content"] = f"Tool {tool_name} executed successfully"
            message["result_summary"] = str(result)[:200] if result else None
        else:
            message["content"] = f"Tool {tool_name} failed with {'MCP ' if error else ''}error"
            message["error"] = error
        
        self.conversation_messages.append(message)
        
        # Save context every 10 tool calls
        if len(self.conversation_messages) % 20 == 0:
            self._save_callback()


class ServiceExecutor:
    """Executes tools based on service type.
    
    AI_CONTEXT:
        Extracted from _handle_tool_call to handle routing and execution
        of different service types (CLI, MCP, REST, Plugin).
    """
    
    def __init__(self, handler_instance):
        """Initialize with reference to handler instance."""
        self.handler = handler_instance
    
    async def execute_tool(
        self,
        service_name: str,
        service_info: Any,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Any:
        """Execute tool based on service type."""
        service_type = service_info.config.type.value
        
        if service_type == "cli":
            return await self.handler._execute_cli_tool(tool_name, tool_args)
        elif service_type == "mcp":
            return await self.handler._execute_mcp_tool(service_name, tool_name, tool_args)
        elif service_type == "rest":
            return await self.handler._execute_rest_tool(service_name, tool_name, tool_args)
        elif service_type == "plugin":
            return await self.handler._execute_plugin_tool(service_name, tool_name, tool_args)
        else:
            raise MCPError(
                code=-32000,
                message="Unknown service type",
                data={"type": service_type}
            )
    


class ErrorHandler:
    """Handles error formatting and context.
    
    AI_CONTEXT:
        Extracted from _handle_tool_call to provide context-specific
        error messages and debugging information.
    """
    
    @staticmethod
    def format_error(
        error: Exception,
        service_name: str,
        tool_name: str,
        debug: bool = False,
        debug_context: Optional[Dict] = None
    ) -> MCPError:
        """Format error with helpful context."""
        error_msg = str(error)
        
        # Add context-specific help
        if "timeout" in error_msg.lower():
            error_msg += "\n\nTip: The operation timed out. Try again or check if the service is responding."
        elif "permission" in error_msg.lower() or "denied" in error_msg.lower():
            error_msg += "\n\nTip: Permission denied. Check your credentials or access rights."
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            error_msg += "\n\nTip: Connection error. Check if the service is running and accessible."
        
        return MCPError(
            code=-32000,
            message="Service error",
            data={
                "service": service_name,
                "tool": tool_name,
                "error": error_msg,
                "debug": debug_context if debug else None
            }
        )


async def handle_tool_call_refactored(
    handler_instance,
    params: Dict[str, Any]
) -> Any:
    """Refactored tool call handler - orchestrates the execution.
    
    AI_CONTEXT:
        This is the refactored version of _handle_tool_call, now under
        50 lines. It orchestrates the various components:
        1. Extract parameters
        2. Initialize managers
        3. Check cache
        4. Execute tool
        5. Handle results
        
        The complex logic is delegated to specialized classes.
    """
    tool_name = params["name"]
    raw_args = params.get("arguments", {})
    
    # Initialize components
    workflow_mgr, conv_tracker = _initialize_tool_call_components(handler_instance)
    
    # Transform and validate arguments
    tool_spec, tool_args = await _validate_and_transform_arguments(
        handler_instance, tool_name, raw_args
    )
    conv_tracker.add_tool_call(tool_name, tool_args)
    
    # Check cache
    cached_result = await _check_tool_cache(
        handler_instance, tool_name, tool_args, conv_tracker
    )
    if cached_result is not None:
        return cached_result
    
    # Route and validate service
    service_name, service_info = _route_and_validate_service(
        handler_instance, tool_name
    )
    
    # Record workflow and execute
    execution_id = _record_workflow_execution(
        workflow_mgr, tool_name, service_info, tool_args
    )
    
    # Format arguments if needed
    tool_args = _format_arguments_for_service(
        tool_spec, service_info, tool_name, tool_args
    )
    
    # Execute and handle results
    return await _execute_and_handle_result(
        handler_instance, workflow_mgr, conv_tracker,
        service_name, service_info, tool_name, tool_args,
        execution_id
    )


def _initialize_tool_call_components(handler_instance):
    """Initialize workflow manager and conversation tracker.
    
    Returns:
        Tuple of (workflow_mgr, conv_tracker)
    """
    workflow_mgr = WorkflowManager()
    workflow_mgr.initialize_if_needed()
    
    conv_tracker = ConversationTracker(
        handler_instance.conversation_messages,
        handler_instance._save_session_context
    )
    
    return workflow_mgr, conv_tracker


async def _validate_and_transform_arguments(
    handler_instance, tool_name: str, raw_args: Dict[str, Any]
):
    """Validate and transform tool arguments.
    
    Args:
        handler_instance: The handler instance
        tool_name: Name of the tool
        raw_args: Raw arguments from request
        
    Returns:
        Tuple of (tool_spec, transformed_args)
    """
    from agtos.tool_config import get_tool_config
    
    # Check if tool is disabled
    tool_config = get_tool_config()
    if tool_config.is_tool_disabled(tool_name):
        raise MCPError(
            code=-32601,
            message=f"Tool '{tool_name}' is disabled",
            data={
                "tool": tool_name,
                "reason": "This tool has been disabled in the configuration"
            }
        )
    
    transformer = ArgumentTransformer()
    
    # Get tool spec from registry
    tool_spec = _find_tool_spec(handler_instance.registry, tool_name)
    
    if tool_spec:
        tool_args, validation_errors = transformer.transform_arguments(tool_spec, raw_args)
        _handle_validation_errors(validation_errors, tool_name)
        return tool_spec, tool_args
    else:
        # No spec found, use raw arguments
        logger.warning(f"No tool spec found for {tool_name}, using raw arguments")
        return None, raw_args


def _find_tool_spec(registry, tool_name: str):
    """Find tool specification in registry.
    
    Args:
        registry: Service registry
        tool_name: Name of tool to find
        
    Returns:
        Tool spec or None if not found
    """
    for service_info in registry.services.values():
        for tool in service_info.tools:
            if tool.name == tool_name:
                return tool
    return None


def _handle_validation_errors(validation_errors: list, tool_name: str):
    """Handle validation errors, raising exception for critical errors.
    
    Args:
        validation_errors: List of validation errors
        tool_name: Name of the tool
        
    Raises:
        MCPError: If critical validation errors found
    """
    critical_errors = [e for e in validation_errors if "Required" in e.message]
    if critical_errors:
        error_messages = [e.message for e in critical_errors]
        raise MCPError(
            code=-32602,
            message="Invalid arguments",
            data={"errors": error_messages, "tool": tool_name}
        )
    
    # Log non-critical validation warnings
    for error in validation_errors:
        if error not in critical_errors:
            logger.warning(f"Argument validation warning for {tool_name}: {error.message}")


async def _check_tool_cache(
    handler_instance, tool_name: str, tool_args: Dict[str, Any], conv_tracker
):
    """Check cache for tool result.
    
    Args:
        handler_instance: The handler instance
        tool_name: Name of the tool
        tool_args: Tool arguments
        conv_tracker: Conversation tracker
        
    Returns:
        Cached result or None if not found
    """
    cache_key = handler_instance.cache.generate_key(tool_name, tool_args)
    if cached_result := await handler_instance.cache.get(cache_key):
        handler_instance.stats["cache_hits"] += 1
        logger.debug(f"Cache hit for {tool_name}")
        conv_tracker.add_tool_result(tool_name, success=True, result=cached_result)
        return cached_result
    
    handler_instance.stats["cache_misses"] += 1
    return None


def _route_and_validate_service(handler_instance, tool_name: str):
    """Route tool to service and validate service exists.
    
    Args:
        handler_instance: The handler instance
        tool_name: Name of the tool
        
    Returns:
        Tuple of (service_name, service_info)
        
    Raises:
        MCPError: If service not found
    """
    service_name = handler_instance.router.route_tool(tool_name)
    logger.info(f"Routing {tool_name} to {service_name}")
    
    service_info = handler_instance.registry.services.get(service_name)
    if not service_info:
        raise MCPError(
            code=-32000,
            message="Service not found",
            data={"service": service_name}
        )
    
    return service_name, service_info


def _record_workflow_execution(workflow_mgr, tool_name: str, service_info, tool_args: Dict[str, Any]):
    """Record workflow execution start.
    
    Args:
        workflow_mgr: Workflow manager
        tool_name: Name of the tool
        service_info: Service information
        tool_args: Tool arguments
        
    Returns:
        Execution ID
    """
    return workflow_mgr.record_execution_start(
        tool_name,
        service_info.config.type.value,
        tool_args
    )


def _format_arguments_for_service(tool_spec, service_info, tool_name: str, tool_args: Dict[str, Any]):
    """Format arguments based on service type.
    
    Args:
        tool_spec: Tool specification
        service_info: Service information
        tool_name: Name of the tool
        tool_args: Tool arguments
        
    Returns:
        Formatted arguments
    """
    if tool_spec and service_info.config.type.value == "cli":
        transformer = ArgumentTransformer()
        return transformer.format_for_cli(tool_name, tool_args)
    elif tool_spec and service_info.config.type.value == "rest":
        # For REST, we need endpoint info - pass through for now
        # The REST bridge will handle its own formatting
        return tool_args
    
    return tool_args


async def _execute_and_handle_result(
    handler_instance, workflow_mgr, conv_tracker,
    service_name: str, service_info, tool_name: str, 
    tool_args: Dict[str, Any], execution_id: str
):
    """Execute tool and handle result or errors.
    
    Args:
        handler_instance: The handler instance
        workflow_mgr: Workflow manager
        conv_tracker: Conversation tracker
        service_name: Name of the service
        service_info: Service information
        tool_name: Name of the tool
        tool_args: Tool arguments
        execution_id: Workflow execution ID
        
    Returns:
        Tool execution result
        
    Raises:
        MCPError: For MCP-specific errors
        Exception: For other errors
    """
    executor = ServiceExecutor(handler_instance)
    cache_key = handler_instance.cache.generate_key(tool_name, tool_args)
    
    try:
        result = await executor.execute_tool(
            service_name, service_info, tool_name, tool_args
        )
        
        # Cache and record success
        await handler_instance.cache.set(cache_key, result, tool_name=tool_name)
        workflow_mgr.record_execution_result(execution_id, result=result)
        conv_tracker.add_tool_result(tool_name, success=True, result=result)
        
        return result
        
    except MCPError as e:
        # Record and re-raise MCP errors
        workflow_mgr.record_execution_result(execution_id, error=str(e))
        conv_tracker.add_tool_result(tool_name, success=False, error=str(e))
        raise
        
    except Exception as e:
        # Handle other errors
        logger.error(f"Error executing {tool_name}: {e}")
        workflow_mgr.record_execution_result(execution_id, error=str(e))
        conv_tracker.add_tool_result(tool_name, success=False, error=str(e))
        
        raise ErrorHandler.format_error(
            e, service_name, tool_name,
            handler_instance.debug,
            handler_instance._get_debug_context() if handler_instance.debug else None
        )


# Usage in the actual handlers.py:
# Replace the large _handle_tool_call method with:
# async def _handle_tool_call(self, params: Dict[str, Any]) -> Any:
#     return await handle_tool_call_refactored(self, params)