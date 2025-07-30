"""Tool creation plugin for Meta-MCP.

This plugin allows orchestrator agents (like Claude) to create new tools
on-demand based on natural language descriptions from users.

AI_CONTEXT:
    This enables the core agtOS feature of natural language tool creation.
    When a user asks Claude to do something that requires a tool that 
    doesn't exist, Claude can use this tool to create it dynamically.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from agtos.user_tools import APIAnalyzer, ToolGenerator, ToolValidator
from agtos.user_tools.clarification import (
    Clarifier, 
    ProviderKnowledgeBase,
    PatternLearner,
    DialogueManager,
    DialogueState
)
from agtos.user_tools.formatter import ToolCreationFormatter, should_use_clarification
from agtos.user_tools.modifier import ToolModifier
from agtos.user_tools.self_healer import SelfHealer, HealingAttempt
from agtos.user_tools.error_handler import ProgressiveErrorHandler, ErrorCategory
from agtos.versioning.version_manager import VersionManager
from agtos.versioning.dependency_tracker import DependencyTracker
from agtos.versioning.update_notifier import UpdateNotifier
from agtos.versioning.migration_assistant import MigrationAssistant
from agtos.knowledge.api import APIKnowledge
# MCPError not needed for this implementation

import functools
import logging

logger = logging.getLogger(__name__)

# Global clarifier instance
_clarifier = None

def reset_global_state():
    """Reset global state in case of corruption.
    
    WARNING: This will clear all active clarification sessions!
    Only use this as a last resort for recovery from critical errors.
    """
    global _clarifier
    if _clarifier:
        logger.warning("Resetting global clarifier state - all sessions will be lost!")
    _clarifier = None

def with_error_recovery(func):
    """Decorator to add error recovery to tool creator functions.
    
    Only resets global state for specific critical errors that indicate
    corruption, not for normal operational errors.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            
            # Only reset for specific critical errors
            critical_errors = [
                "AttributeError",  # Corrupted object state
                "TypeError: 'NoneType'",  # Unexpected None
                "cannot pickle",  # Serialization issues
            ]
            
            should_reset = any(err in str(e) or err in type(e).__name__ for err in critical_errors)
            
            if should_reset:
                logger.warning(f"Critical error detected, attempting recovery: {type(e).__name__}")
                try:
                    reset_global_state()
                    return func(*args, **kwargs)
                except Exception as retry_error:
                    # If retry fails, return a clean error
                    return {
                        "success": False,
                        "message": f"❌ {func.__name__} failed after recovery attempt: {str(retry_error)}",
                        "error": str(retry_error)
                    }
            else:
                # For non-critical errors, just return the error without reset
                return {
                    "success": False,
                    "message": f"❌ {func.__name__} failed: {str(e)}",
                    "error": str(e)
                }
    return wrapper


@with_error_recovery
def create_tool_from_description(
    description: str,
    name: Optional[str] = None,
    save: bool = True,
    version: Optional[str] = None,
    enable_self_healing: bool = False,
    test_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new tool from natural language description.
    
    This is meant to be called by orchestrator agents when they need
    to create a new tool based on user requirements.
    
    Args:
        description: Natural language description of the API/tool
        name: Optional tool name (will be inferred if not provided)
        save: Whether to save the tool to disk
        version: Optional version number
        enable_self_healing: Whether to attempt automatic error correction
        test_params: Optional parameters for testing the tool
        
    Returns:
        Dict with tool info and generated code
    """
    formatter = ToolCreationFormatter()
    error_handler = ProgressiveErrorHandler()
    
    # Check if we should recommend clarification
    if should_use_clarification(description):
        return {
            "success": False,
            "needs_clarification": True,
            "message": formatter.format_clarification_needed(description),
            "suggestion": "Use tool_creator_clarify to start an interactive clarification process"
        }
    
    try:
        # Check if description mentions a URL that we can discover
        api_knowledge = APIKnowledge()
        discovered_spec = None
        
        # Look for URLs in the description
        import re
        url_pattern = r'https?://[^\s<>"|\\^`\[\]]+|(?:api\.|/api/)[^\s<>"|\\^`\[\]]+|[a-zA-Z0-9][a-zA-Z0-9\-]*(?:\.[a-zA-Z0-9][a-zA-Z0-9\-]*)+(?:/[^\s<>"|\\^`\[\]]*)?'
        urls = re.findall(url_pattern, description)
        
        if urls:
            # Try to discover API from the URL
            for url in urls:
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                
                try:
                    # Try to fetch OpenAPI spec
                    base_url = '/'.join(url.split('/')[:3])
                    openapi_spec = api_knowledge.fetch_openapi_spec(base_url)
                    
                    if openapi_spec:
                        # Found OpenAPI spec! Use it
                        parsed = api_knowledge.parse_openapi_spec(openapi_spec)
                        
                        # Create a more detailed description with discovered endpoints
                        discovered_desc = f"API discovered from {base_url}. "
                        if parsed.get('endpoints'):
                            discovered_desc += f"Found {len(parsed['endpoints'])} endpoints. "
                            
                        return {
                            "success": True,
                            "message": f"✅ Discovered OpenAPI spec for {base_url}! Found {len(parsed.get('endpoints', []))} endpoints.",
                            "discovered": True,
                            "base_url": base_url,
                            "endpoints": parsed.get('endpoints', []),
                            "authentication": parsed.get('security', []),
                            "suggestion": "Review the discovered endpoints and create specific tools as needed."
                        }
                except Exception as e:
                    logger.debug(f"Could not discover OpenAPI spec from {url}: {e}")
        
        # Initialize components
        analyzer = APIAnalyzer()
        generator = ToolGenerator()
        validator = ToolValidator()
        
        # Analyze the description
        spec = analyzer.analyze(description, name)
        
        # Generate the tool
        tool = generator.generate(spec)
        
        # Apply self-healing if enabled
        healing_attempts = []
        healing_success = False
        if enable_self_healing:
            healer = SelfHealer(max_attempts=2)  # Limit to 2 attempts
            healing_success, healed_code, attempts = healer.heal_tool(
                spec, tool.tool_code, test_params, verbose=False
            )
            
            if healing_success:
                tool.tool_code = healed_code
                healing_attempts = attempts
            elif attempts:
                # Only show first attempt error to user
                healing_attempts = attempts[:1]
        
        # Validate the generated tool
        try:
            errors = validator.validate(tool)
            # Ensure errors is a list
            if not isinstance(errors, list):
                errors = []
        except Exception as ve:
            errors = [f"Validation error: {str(ve)}"]
        
        # Check for critical errors
        syntax_errors = [e for e in errors if isinstance(e, str) and "Syntax" in e]
        security_errors = [e for e in errors if isinstance(e, str) and ("Dangerous" in e or "security" in e.lower())]
        
        if syntax_errors or security_errors:
            error_result = {
                "success": False,
                "error": "Tool generation failed validation",
                "syntax_errors": syntax_errors,
                "security_errors": security_errors
            }
            return {
                "success": False,
                "message": formatter.format_error(error_result)
            }
        
        # Save if requested
        saved_path = None
        hot_reload_status = None
        if save:
            # Save to user_tools directory
            user_tools_dir = Path.home() / ".agtos" / "user_tools"
            user_tools_dir.mkdir(parents=True, exist_ok=True)
            
            # Save Python code
            tool_file = user_tools_dir / f"{spec.name}.py"
            tool_file.write_text(tool.tool_code)
            
            # Initialize version manager
            version_manager = VersionManager(user_tools_dir)
            
            # Determine version
            if not version:
                # Check if tool exists to determine version
                existing_versions = version_manager.get_available_versions(spec.name)
                if existing_versions:
                    # This is an update, bump patch version
                    latest = version_manager.parse_version(existing_versions[0])
                    version = str(latest.bump_patch())
                else:
                    # New tool, start at 1.0.0
                    version = "1.0.0"
            
            # Save metadata with version
            metadata = {
                "name": spec.name,
                "description": spec.description,
                "specification": spec.to_dict() if hasattr(spec, 'to_dict') else {},
                "mcp_schema": tool.mcp_schema,
                "created_at": datetime.now().isoformat(),
                "version": version,
                "version_info": {
                    "current": version,
                    "created_at": datetime.now().isoformat()
                },
                "breaking_changes": {},  # Will be populated by future updates
                "dependencies": []  # Tools or libraries this tool depends on
            }
            
            # Use version manager to install the new version
            version_dir = version_manager.install_version(
                spec.name, version, tool.tool_code, metadata
            )
            
            saved_path = str(version_dir / f"{spec.name}.py")
            
            # Activate this version to make it available
            version_manager.activate_version(spec.name, version)
            
            # Ensure files are fully written and synced to disk
            import time
            time.sleep(0.1)  # Small delay to ensure file system catches up
            
            # Verify the file exists before triggering reload
            py_file = Path(saved_path)
            max_retries = 5
            for i in range(max_retries):
                if py_file.exists() and py_file.stat().st_size > 0:
                    break
                time.sleep(0.1)
            
            # Trigger hot reload
            hot_reload_status = _trigger_hot_reload(spec.name)
        
        # Extract warnings (non-critical)
        validation_warnings = [e for e in errors if e not in syntax_errors + security_errors]
        
        # Handle endpoints safely
        endpoints_data = []
        try:
            if hasattr(spec, 'endpoints') and spec.endpoints:
                # Check if endpoints is iterable
                if hasattr(spec.endpoints, '__iter__'):
                    for ep in spec.endpoints:
                        endpoint_dict = {
                            "url": getattr(ep, 'url', ''),
                            "method": ep.method.value if hasattr(ep, 'method') and hasattr(ep.method, 'value') else str(getattr(ep, 'method', 'GET')),
                            "parameters": [],
                            "auth": None
                        }
                        
                        # Add parameters if they exist
                        if hasattr(ep, 'parameters') and hasattr(ep.parameters, '__iter__'):
                            endpoint_dict["parameters"] = [p.name for p in ep.parameters if hasattr(p, 'name')]
                        
                        # Add auth if it exists
                        if hasattr(ep, 'authentication') and ep.authentication:
                            if hasattr(ep.authentication, 'type') and hasattr(ep.authentication.type, 'value'):
                                endpoint_dict["auth"] = ep.authentication.type.value
                        
                        endpoints_data.append(endpoint_dict)
        except Exception as e:
            # Log endpoint processing error but don't fail
            pass
        
        success_result = {
            "success": True,
            "tool_name": spec.name,
            "description": spec.description,
            "endpoints": endpoints_data,
            "code_preview": tool.tool_code[:500] + "..." if len(tool.tool_code) > 500 else tool.tool_code,
            "validation_warnings": validation_warnings,
            "saved_to": saved_path,
            "hot_reload_status": hot_reload_status,
            "mcp_schema": tool.mcp_schema,
            "usage": f"The tool '{spec.name}' is now available for use.",
            "version": version
        }
        
        # Add healing summary if applicable
        if healing_attempts and healing_success:
            healer = SelfHealer()
            success_result["healing_summary"] = healer.get_healing_summary(healing_attempts)
        elif enable_self_healing and not healing_success and healing_attempts:
            # If healing was attempted but failed, include a note
            success_result["healing_note"] = "Note: Automatic correction was attempted but the tool may need manual adjustments."
        
        # Only return the formatted message to avoid showing technical details
        return {
            "success": True,
            "message": formatter.format_success(success_result),
            "tool_name": spec.name  # Include just the name for reference
        }
        
    except Exception as e:
        # Use progressive error handling
        error_context = error_handler.handle_error(e, {
            "description": description,
            "name": name,
            "action": "create_tool"
        })
        
        return {
            "success": False,
            "message": error_handler.format_error_response(error_context),
            "error_id": error_context.id,
            "category": error_context.category.value
        }


def analyze_api_description(description: str) -> Dict[str, Any]:
    """Analyze a natural language API description without creating the tool.
    
    Useful for agents to understand what would be created before committing.
    
    Args:
        description: Natural language description of the API
        
    Returns:
        Analysis results
    """
    try:
        analyzer = APIAnalyzer()
        spec = analyzer.analyze(description)
        
        # Handle endpoints safely
        endpoints_data = []
        if hasattr(spec, 'endpoints') and spec.endpoints:
            for ep in spec.endpoints:
                endpoint_info = {
                    "url": ep.url,
                    "method": ep.method.value if hasattr(ep.method, 'value') else str(ep.method),
                    "parameters": []
                }
                
                # Add parameters if they exist
                if hasattr(ep, 'parameters') and ep.parameters:
                    for p in ep.parameters:
                        endpoint_info["parameters"].append({
                            "name": p.name,
                            "type": getattr(p, 'type', 'string'),
                            "required": getattr(p, 'required', False),
                            "location": p.location.value if hasattr(p, 'location') and hasattr(p.location, 'value') else 'body'
                        })
                
                # Add authentication if it exists
                if hasattr(ep, 'authentication') and ep.authentication:
                    endpoint_info["authentication"] = {
                        "type": ep.authentication.type.value if hasattr(ep.authentication.type, 'value') else str(ep.authentication.type),
                        "location": getattr(ep.authentication, 'location', 'header')
                    }
                else:
                    endpoint_info["authentication"] = None
                    
                endpoints_data.append(endpoint_info)
        
        return {
            "success": True,
            "analysis": {
                "tool_name": spec.name,
                "description": spec.description,
                "endpoints": endpoints_data
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@with_error_recovery
def list_user_tools() -> Dict[str, Any]:
    """List all user-created tools."""
    user_tools_dir = Path.home() / ".agtos" / "user_tools"
    
    if not user_tools_dir.exists():
        return {
            "success": True,
            "tools": [],
            "total": 0
        }
    
    # Initialize version manager
    version_manager = VersionManager(user_tools_dir)
    
    tools = []
    # Get all tools with version info
    all_tools = version_manager.list_all_tools()
    
    for tool_name, active_version, total_versions in all_tools:
        # Get active version metadata
        if active_version != "none":
            metadata = version_manager.get_version_metadata(tool_name, active_version)
            if metadata:
                tools.append({
                    "name": tool_name,
                    "description": metadata.get("description", ""),
                    "created_at": metadata.get("created_at"),
                    "endpoints": len(metadata.get("specification", {}).get("endpoints", [])),
                    "active_version": active_version,
                    "total_versions": total_versions,
                    "has_updates": False  # Could check if newer versions exist
                })
    
    return {
        "success": True,
        "tools": tools,
        "total": len(tools)
    }


def _trigger_hot_reload(tool_name: str) -> str:
    """Trigger hot-reload for a newly created tool.
    
    AI_CONTEXT:
        This function attempts to notify the Meta-MCP server to reload
        the newly created tool. It uses a simple HTTP request to a
        reload endpoint if the server is running.
    
    Args:
        tool_name: Name of the tool to reload
        
    Returns:
        Status message about the reload attempt
    """
    try:
        # Since most users run in stdio mode, we can't use HTTP endpoint
        # Instead, we'll rely on file watching if available
        
        # Create a reload marker file that the hot reloader can detect
        reload_marker = Path.home() / ".agtos" / "user_tools" / ".reload_marker"
        reload_marker.parent.mkdir(parents=True, exist_ok=True)
        
        # Write tool name to reload marker (for file-based trigger)
        reload_marker.write_text(f"{tool_name}\n{datetime.now().isoformat()}")
        
        # Try HTTP endpoint just in case server is running in HTTP mode
        try:
            # Only try the default port to avoid delays
            response = requests.post(
                "http://localhost:8585/internal/reload-tool",
                json={"tool_name": tool_name},
                timeout=0.5  # Quick timeout
            )
            
            if response.status_code == 200:
                return "Tool loaded successfully"
        except requests.exceptions.RequestException:
            pass  # Expected in stdio mode
        
        # In stdio mode, the tool will be loaded on next startup
        # But we return success since the tool was created successfully
        return "Tool created successfully"
        
    except Exception as e:
        # Don't report reload errors to user - tool was still created
        logger.warning(f"Hot-reload marker creation failed: {str(e)}")
        return "Tool created successfully"


# Import datetime for timestamps
from datetime import datetime
import requests

def get_clarifier() -> Clarifier:
    """Get or create the global clarifier instance with error recovery.
    
    This maintains a singleton instance to preserve session state across calls.
    """
    global _clarifier
    
    # Fast path - return existing instance
    if _clarifier is not None:
        return _clarifier
    
    # Slow path - create new instance with proper error handling
    try:
        logger.info("Creating new clarifier instance")
        _clarifier = Clarifier()
        return _clarifier
    except Exception as e:
        logger.error(f"Failed to create clarifier: {str(e)}")
        # Only try once more for initialization
        try:
            logger.info("Retrying clarifier creation after error")
            _clarifier = Clarifier()
            return _clarifier
        except Exception as retry_error:
            logger.error(f"Failed to create clarifier after retry: {str(retry_error)}")
            # Don't set _clarifier to a broken instance
            _clarifier = None
            raise Exception(f"Failed to initialize clarifier: {str(e)} (retry: {str(retry_error)})")


def start_tool_clarification(intent: str) -> Dict[str, Any]:
    """Start the clarification process for creating a tool.
    
    This initiates a conversational flow to gather all necessary
    information for tool creation.
    
    Args:
        intent: Natural language description of what the user wants
        
    Returns:
        Dict with initial message and session ID
    """
    try:
        clarifier = get_clarifier()
        
        # Generate a unique session ID for tracking
        import uuid
        session_id = f"clarify_{uuid.uuid4().hex[:12]}"
        
        # Start clarification with session ID
        message, context = clarifier.start_clarification(intent, session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": message,
            "state": context.state.value,
            "requires_response": True,
            "suggestions": _get_state_suggestions(context.state)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def continue_tool_clarification(session_id: str, user_response: str) -> Dict[str, Any]:
    """Continue the clarification dialogue with user response.
    
    Args:
        session_id: The clarification session ID
        user_response: The user's response to the previous question
        
    Returns:
        Dict with next message or final tool configuration
    """
    try:
        # Validate session_id
        if not session_id:
            return {
                "success": False,
                "error": "No session ID provided. Please start a new clarification session.",
                "suggestion": "Use tool_creator_clarify to start a new session"
            }
        
        # Strip whitespace from session_id
        session_id = session_id.strip()
        
        # Validate session_id format
        if not session_id.startswith("clarify_"):
            logger.warning(f"Invalid session ID format: {session_id}")
            return {
                "success": False,
                "error": f"Invalid session ID format: '{session_id}'. Session IDs should start with 'clarify_'",
                "suggestion": "Use the session_id returned from tool_creator_clarify"
            }
        
        clarifier = get_clarifier()
        
        # Check if session exists before processing
        active_sessions = clarifier.get_active_sessions()
        if session_id not in active_sessions:
            logger.warning(f"Session {session_id} not found. Active sessions: {list(active_sessions.keys())}")
            return {
                "success": False,
                "error": f"Session '{session_id}' not found or has expired.",
                "active_sessions": len(active_sessions),
                "suggestion": "Sessions expire after 30 minutes of inactivity. Please start a new clarification session."
            }
        
        message, state, result = clarifier.process_user_response(user_response, session_id)
        
        response = {
            "success": True,
            "session_id": session_id,
            "message": message,
            "state": state.value,
            "requires_response": state != DialogueState.COMPLETE
        }
        
        if result and result.success:
            # Tool creation complete
            response["tool_created"] = True
            response["tool_config"] = result.tool_config
            response["confidence"] = result.confidence
            
            # Actually create the tool
            creation_result = _create_tool_from_config(result.tool_config)
            response["creation_result"] = creation_result
        else:
            response["suggestions"] = _get_state_suggestions(state)
        
        return response
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _create_tool_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a tool from a clarification-generated configuration."""
    # Build description from config
    description = _build_description_from_config(config)
    
    # Use existing create function
    return create_tool_from_description(
        description=description,
        name=config.get('name'),
        save=True
    )


def _build_description_from_config(config: Dict[str, Any]) -> str:
    """Build a natural language description from tool configuration."""
    parts = []
    
    # Add base URL and endpoint
    if 'base_url' in config and 'endpoint' in config:
        url = config['base_url'] + config['endpoint']
        parts.append(f"{config.get('method', 'GET')} to {url}")
    
    # Add auth info
    if 'auth' in config:
        auth_type = config['auth'].get('type', 'api_key')
        if auth_type == 'bearer_token':
            parts.append("with bearer token authentication")
        elif auth_type == 'api_key':
            parts.append("with API key authentication")
    
    # Add parameters
    if 'parameters' in config and config['parameters']:
        # Handle both dict and string cases
        if isinstance(config['parameters'], dict):
            param_list = ', '.join(config['parameters'].keys())
        elif isinstance(config['parameters'], str):
            # If it's a string, use it directly
            param_list = config['parameters']
        else:
            # If it's a list or other iterable, try to extract names
            try:
                param_list = ', '.join(str(p) for p in config['parameters'])
            except:
                param_list = str(config['parameters'])
        
        parts.append(f"with parameters: {param_list}")
    
    # Add description
    if 'description' in config:
        parts.append(f"to {config['description']}")
    
    return ' '.join(parts)


def _get_state_suggestions(state: DialogueState) -> Optional[Dict[str, Any]]:
    """Get suggestions for the current dialogue state."""
    if state == DialogueState.PROVIDER_SELECTION:
        return {
            "type": "provider_selection",
            "hint": "Choose by number (1, 2, 3) or name (Slack, Discord, etc.)"
        }
    elif state == DialogueState.AUTH_SETUP:
        return {
            "type": "auth_setup",
            "hint": "Provide your API credentials (they'll be stored securely)"
        }
    elif state == DialogueState.PARAMETER_MAPPING:
        return {
            "type": "parameter_mapping",
            "hint": "Specify how to fill in the required parameters"
        }
    elif state == DialogueState.CONFIRMATION:
        return {
            "type": "confirmation",
            "hint": "Say 'yes' to create, 'no' to cancel, or describe what to change"
        }
    return None


def suggest_providers(query: str) -> Dict[str, Any]:
    """Get provider suggestions for a query.
    
    Args:
        query: What the user wants to do
        
    Returns:
        List of suggested providers with details
    """
    try:
        clarifier = get_clarifier()
        providers = clarifier.provider_kb.suggest_providers(query)
        
        return {
            "success": True,
            "query": query,
            "providers": [
                {
                    "name": p.name,
                    "category": p.category,
                    "description": p.description,
                    "pros": p.pros[:3],
                    "cons": p.cons[:2],
                    "pricing": p.pricing,
                    "setup_difficulty": _estimate_setup_difficulty(p)
                }
                for p in providers[:5]
            ],
            "total": len(providers)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _estimate_setup_difficulty(provider) -> str:
    """Estimate setup difficulty based on auth type and requirements."""
    if provider.auth_type.value == "none":
        return "Easy"
    elif provider.auth_type.value in ["api_key", "bearer_token"]:
        return "Medium"
    else:
        return "Complex"


def edit_tool(tool_name: str, modification_request: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Edit an existing tool using natural language.
    
    Args:
        tool_name: Name of the tool to edit
        modification_request: Natural language description of changes
        version: Optional version to create (auto-determined if not provided)
        
    Returns:
        Edit result with formatted message
    """
    formatter = ToolCreationFormatter()
    modifier = ToolModifier()
    
    try:
        # Initialize version manager
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        version_manager = VersionManager(user_tools_dir)
        
        # Apply modifications with version awareness
        result = modifier.apply_modifications(tool_name, modification_request, version_manager, version)
        
        # Format the result
        return {
            "success": True,
            "message": formatter.format_edit_success(result)
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "message": f"❌ Tool '{tool_name}' not found. Use tool_creator_list to see available tools."
        }
    except Exception as e:
        return {
            "success": False,
            "message": formatter.format_error({"error": str(e)})
        }


@with_error_recovery
def delete_tool(tool_name: str) -> Dict[str, Any]:
    """Delete a user-created tool.
    
    Args:
        tool_name: Name of the tool to delete (supports both base and compound names)
        
    Returns:
        Deletion result
    """
    formatter = ToolCreationFormatter()
    modifier = ToolModifier()
    
    # Handle compound names (e.g., pokemon_stats_get_pokemon -> pokemon_stats)
    original_name = tool_name
    if "_get_" in tool_name or "_post_" in tool_name or "_put_" in tool_name or "_delete_" in tool_name:
        # Extract base name from compound name
        parts = tool_name.split("_")
        action_index = next((i for i, p in enumerate(parts) if p in ["get", "post", "put", "delete"]), -1)
        if action_index > 0:
            tool_name = "_".join(parts[:action_index])
            logger.info(f"Extracted base tool name '{tool_name}' from compound name '{original_name}'")
    
    try:
        # Delete the tool
        result = modifier.delete_tool(tool_name)
        
        # Format the result
        return {
            "success": True,
            "message": formatter.format_delete_confirmation(result)
        }
        
    except FileNotFoundError:
        # If we tried to extract a base name, mention both in error
        if original_name != tool_name:
            error_msg = f"❌ Tool '{tool_name}' (extracted from '{original_name}') not found. Use tool_creator_list to see available tools."
        else:
            error_msg = f"❌ Tool '{tool_name}' not found. Use tool_creator_list to see available tools."
        
        return {
            "success": False,
            "message": error_msg
        }
    except Exception as e:
        # Reset global state in case of corruption
        reset_global_state()
        return {
            "success": False,
            "message": f"❌ Failed to delete tool: {str(e)}"
        }


def get_tool_summary(tool_name: str) -> Dict[str, Any]:
    """Get a natural language summary of a tool's capabilities.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool summary
    """
    formatter = ToolCreationFormatter()
    modifier = ToolModifier()
    
    try:
        # Get tool summary
        summary = modifier.get_tool_summary(tool_name)
        
        # Format the result
        return {
            "success": True,
            "message": formatter.format_tool_summary(summary)
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "message": f"❌ Tool '{tool_name}' not found. Use tool_creator_list to see available tools."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to get tool summary: {str(e)}"
        }


def _apply_tool_modifications(
    tool_name: str,
    modifications: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply modifications to a tool without showing code.
    
    This is an internal function used by other features that need
    to modify tools programmatically.
    
    Args:
        tool_name: Name of the tool
        modifications: Dict of specific modifications to apply
        
    Returns:
        Result dict
    """
    modifier = ToolModifier()
    
    try:
        # Load tool
        metadata, spec = modifier.load_tool(tool_name)
        
        # Apply specific modifications
        modified_spec = modifier._apply_changes_to_spec(spec, modifications)
        
        # Regenerate and save
        generator = ToolGenerator()
        tool = generator.generate(modified_spec)
        
        # Save without full validation (trust the caller)
        modifier._save_modified_tool(tool_name, modified_spec, tool, metadata)
        
        return {
            "success": True,
            "tool_name": tool_name,
            "modifications_applied": modifications
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_active_clarification_sessions() -> Dict[str, Any]:
    """Get information about active clarification sessions.
    
    Returns:
        Dict with active session information
    """
    try:
        clarifier = get_clarifier()
        sessions = clarifier.get_active_sessions()
        
        return {
            "success": True,
            "active_sessions": sessions,
            "total": len(sessions),
            "message": f"Found {len(sessions)} active clarification session(s)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def upgrade_tool(tool_name: str, target_version: Optional[str] = None) -> Dict[str, Any]:
    """Upgrade a tool to a new version.
    
    Args:
        tool_name: Name of the tool
        target_version: Target version (latest if not specified)
        
    Returns:
        Upgrade result
    """
    formatter = ToolCreationFormatter()
    
    try:
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        version_manager = VersionManager(user_tools_dir)
        dependency_tracker = DependencyTracker(user_tools_dir)
        migration_assistant = MigrationAssistant(version_manager, dependency_tracker)
        
        # Get current version
        current_version = version_manager.get_active_version(tool_name)
        if not current_version:
            return {
                "success": False,
                "message": f"❌ Tool '{tool_name}' not found or has no active version."
            }
        
        # Get target version
        if not target_version:
            versions = version_manager.get_available_versions(tool_name)
            if not versions or versions[0] == current_version:
                return {
                    "success": False,
                    "message": f"✅ Tool '{tool_name}' is already at the latest version ({current_version})."
                }
            target_version = versions[0]
        
        # Create migration plan
        plan = migration_assistant.create_migration_plan(tool_name, target_version, current_version)
        
        # Check if automatic
        if plan.risk_level == "low" and all(s.step_type == "automatic" for s in plan.steps):
            # Apply automatic migration
            version_manager.activate_version(tool_name, target_version)
            
            return {
                "success": True,
                "message": formatter.format_upgrade_success({
                    "tool_name": tool_name,
                    "from_version": current_version,
                    "to_version": target_version,
                    "automatic": True,
                    "risk_level": plan.risk_level
                })
            }
        else:
            # Need manual intervention
            return {
                "success": True,
                "needs_confirmation": True,
                "message": formatter.format_migration_plan(plan),
                "migration_plan": plan
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to upgrade tool: {str(e)}"
        }


def check_tool_updates(tool_name: Optional[str] = None) -> Dict[str, Any]:
    """Check for available updates for tools.
    
    Args:
        tool_name: Specific tool to check (all if None)
        
    Returns:
        Update information
    """
    formatter = ToolCreationFormatter()
    
    try:
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        version_manager = VersionManager(user_tools_dir)
        dependency_tracker = DependencyTracker(user_tools_dir)
        update_notifier = UpdateNotifier(version_manager, dependency_tracker)
        
        if tool_name:
            # Check specific tool
            recommendation = update_notifier.get_update_for_tool(tool_name)
            if recommendation:
                return {
                    "success": True,
                    "message": formatter.format_update_available(recommendation),
                    "update_available": True,
                    "recommendation": recommendation
                }
            else:
                active_version = version_manager.get_active_version(tool_name)
                return {
                    "success": True,
                    "message": f"✅ '{tool_name}' is up to date (version {active_version})",
                    "update_available": False
                }
        else:
            # Check all tools
            recommendations = update_notifier.check_updates()
            summary = update_notifier.generate_update_summary()
            
            return {
                "success": True,
                "message": summary,
                "total_updates": len(recommendations),
                "recommendations": recommendations
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to check updates: {str(e)}"
        }


def show_tool_versions(tool_name: str) -> Dict[str, Any]:
    """Show version history for a tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Version history information
    """
    formatter = ToolCreationFormatter()
    
    try:
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        version_manager = VersionManager(user_tools_dir)
        
        versions = version_manager.get_available_versions(tool_name)
        if not versions:
            return {
                "success": False,
                "message": f"❌ Tool '{tool_name}' not found."
            }
        
        active_version = version_manager.get_active_version(tool_name)
        
        # Get metadata for each version
        version_info = []
        for version in versions:
            metadata = version_manager.get_version_metadata(tool_name, version)
            if metadata:
                version_info.append({
                    "version": version,
                    "created_at": metadata.get("version_info", {}).get("created_at", "Unknown"),
                    "description": metadata.get("description", ""),
                    "is_active": version == active_version,
                    "breaking_changes": bool(metadata.get("breaking_changes", {}))
                })
        
        return {
            "success": True,
            "message": formatter.format_version_info({
                "tool_name": tool_name,
                "active_version": active_version,
                "versions": version_info,
                "total_versions": len(versions)
            })
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to get version history: {str(e)}"
        }


def migrate_tool(tool_name: str, target_version: str, 
                 apply_automatic: bool = False) -> Dict[str, Any]:
    """Create or apply a migration plan for a tool.
    
    Args:
        tool_name: Name of the tool
        target_version: Target version to migrate to
        apply_automatic: Whether to apply automatic migrations
        
    Returns:
        Migration result
    """
    formatter = ToolCreationFormatter()
    
    try:
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        version_manager = VersionManager(user_tools_dir)
        dependency_tracker = DependencyTracker(user_tools_dir)
        migration_assistant = MigrationAssistant(version_manager, dependency_tracker)
        
        # Create migration plan
        plan = migration_assistant.create_migration_plan(tool_name, target_version)
        
        if apply_automatic:
            # Apply automatic migrations
            results = []
            for file_path in plan.affected_files:
                success, changes = migration_assistant.apply_automatic_migrations(
                    tool_name, file_path
                )
                results.append({
                    "file": str(file_path),
                    "success": success,
                    "changes": changes
                })
            
            # Activate new version if all successful
            if all(r["success"] for r in results):
                version_manager.activate_version(tool_name, target_version)
                
                return {
                    "success": True,
                    "message": formatter.format_migration_complete({
                        "tool_name": tool_name,
                        "from_version": plan.from_version,
                        "to_version": plan.to_version,
                        "files_migrated": len(results),
                        "changes_made": sum(len(r["changes"]) for r in results)
                    })
                }
            else:
                return {
                    "success": False,
                    "message": "❌ Some migrations failed. Please review and fix manually.",
                    "results": results
                }
        else:
            # Just return the plan
            interactive_data = migration_assistant.interactive_migration(tool_name, target_version)
            
            return {
                "success": True,
                "message": formatter.format_migration_plan(plan),
                "migration_plan": interactive_data
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to create migration plan: {str(e)}"
        }


def inspect_tool(
    tool_name: str,
    detail_level: str = "full"
) -> Dict[str, Any]:
    """Inspect any tool (plugin, user, or built-in) and get detailed information.
    
    Args:
        tool_name: Name of the tool to inspect
        detail_level: Level of detail (summary, full, debug)
        
    Returns:
        Tool information including parameters, usage stats, and documentation
    """
    from agtos.user_tools.inspector import ToolInspector, DetailLevel
    
    inspector = ToolInspector()
    formatter = ToolCreationFormatter()
    
    try:
        # Convert string to DetailLevel enum
        level = DetailLevel.SUMMARY if detail_level == "summary" else DetailLevel.DEBUG if detail_level == "debug" else DetailLevel.FULL
        
        # Inspect the tool
        result = inspector.inspect_tool(tool_name, level)
        
        if not result.get("success"):
            # Tool not found
            suggestions = result.get("suggestions", [])
            message = f"❌ Tool '{tool_name}' not found."
            if suggestions:
                message += "\n\n💡 Did you mean one of these?"
                for i, suggestion in enumerate(suggestions, 1):
                    message += f"\n   {i}. {suggestion}"
            
            return {
                "success": False,
                "message": message
            }
        
        # Format the successful result
        return {
            "success": True,
            "message": formatter.format_tool_info(result)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to inspect tool: {str(e)}"
        }


def get_error_details(error_id: str) -> Dict[str, Any]:
    """Get technical details for a specific error ID.
    
    Args:
        error_id: The error ID from a previous error response
        
    Returns:
        Full technical details of the error
    """
    error_handler = ProgressiveErrorHandler()
    
    try:
        details = error_handler.get_error_details(error_id)
        
        if not details:
            return {
                "success": False,
                "message": f"❌ Error ID '{error_id}' not found. Error logs may have been cleaned up."
            }
        
        # Format the error details
        error_info = details["error"]
        context = details.get("context", {})
        
        message_parts = [
            f"📋 Technical Details for Error {error_id}",
            f"\n⏰ Timestamp: {error_info['timestamp']}",
            f"📁 Category: {error_info['category']}",
            f"\n💬 User Message:\n{error_info['message']}",
            f"\n🔧 Technical Details:\n{error_info['technical_details']}"
        ]
        
        if context:
            message_parts.append(f"\n📍 Context:\n{json.dumps(context, indent=2)}")
        
        return {
            "success": True,
            "message": "\n".join(message_parts)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to retrieve error details: {str(e)}"
        }


def list_all_tools(
    source: Optional[str] = None,
    pattern: Optional[str] = None
) -> Dict[str, Any]:
    """List all available tools from all sources.
    
    Args:
        source: Filter by source (user, plugin, builtin, mcp)
        pattern: Name pattern to match
        
    Returns:
        Categorized list of all tools
    """
    from agtos.user_tools.inspector import ToolInspector, ToolSource
    
    inspector = ToolInspector()
    formatter = ToolCreationFormatter()
    
    try:
        # Convert string to ToolSource enum if provided
        source_filter = None
        if source:
            source_map = {
                "user": ToolSource.USER,
                "plugin": ToolSource.PLUGIN,
                "builtin": ToolSource.BUILTIN,
                "mcp": ToolSource.MCP
            }
            source_filter = source_map.get(source.lower())
        
        # Get all tools
        result = inspector.list_all_tools(source_filter, pattern)
        
        # Format the result
        message_parts = [f"🔧 Available Tools ({result['total']} total)"]
        
        if result["user"]:
            message_parts.append(f"\n👤 User-Created ({len(result['user'])})")
            for tool in result["user"][:5]:  # Show first 5
                message_parts.append(f"   • {tool['name']} (v{tool['version']}) - {tool['description'][:50]}...")
            if len(result["user"]) > 5:
                message_parts.append(f"   ... and {len(result['user']) - 5} more")
        
        if result["plugin"]:
            message_parts.append(f"\n🔌 Plugins ({len(result['plugin'])})")
            for tool in result["plugin"][:5]:
                message_parts.append(f"   • {tool['name']} - {tool['description'][:50]}...")
            if len(result["plugin"]) > 5:
                message_parts.append(f"   ... and {len(result['plugin']) - 5} more")
        
        if result["builtin"]:
            message_parts.append(f"\n🏗️ Built-in ({len(result['builtin'])})")
            for tool in result["builtin"][:5]:
                message_parts.append(f"   • {tool['name']} - {tool['description'][:50]}...")
            if len(result["builtin"]) > 5:
                message_parts.append(f"   ... and {len(result['builtin']) - 5} more")
        
        if source or pattern:
            filter_desc = []
            if source:
                filter_desc.append(f"source={source}")
            if pattern:
                filter_desc.append(f"pattern='{pattern}'")
            message_parts.append(f"\n🔍 Filters: {', '.join(filter_desc)}")
        
        return {
            "success": True,
            "message": "\n".join(message_parts),
            "tools": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Failed to list tools: {str(e)}"
        }


def get_tool_creator_tools() -> Dict[str, Dict[str, Any]]:
    """Get tool creator tools for the plugin system.
    
    Returns:
        Dictionary of tool configurations
    """
    tools = {
        "tool_creator_create": {
            "description": "Create a new tool from natural language API description. Use this when a user needs to integrate with an API that doesn't have an existing tool.",
            "schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the API (e.g., 'post messages to api.slack.com/messages with text and channel')"
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional tool name (will be inferred from API if not provided)"
                    },
                    "save": {
                        "type": "boolean",
                        "description": "Whether to save the tool to disk (default: true)",
                        "default": True
                    },
                    "version": {
                        "type": "string",
                        "description": "Optional version number (e.g., '1.0.0'). If not provided, will auto-increment based on existing versions"
                    },
                    "enable_self_healing": {
                        "type": "boolean",
                        "description": "Whether to attempt automatic error correction (default: false)",
                        "default": False
                    },
                    "test_params": {
                        "type": "object",
                        "description": "Optional parameters for testing the tool after creation"
                    }
                },
                "required": ["description"]
            },
            "func": create_tool_from_description
        },
        "tool_creator_clarify": {
            "description": "Start an interactive clarification process for creating a tool. Use this when the user's intent is vague or when you need to gather more information.",
            "schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "What the user wants to do (e.g., 'I need to send notifications to my team')"
                    }
                },
                "required": ["intent"]
            },
            "func": start_tool_clarification
        },
        "tool_creator_continue": {
            "description": "Continue a clarification dialogue with the user's response.",
            "schema": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "The clarification session ID from start_tool_clarification"
                    },
                    "user_response": {
                        "type": "string",
                        "description": "The user's response to the clarification question"
                    }
                },
                "required": ["session_id", "user_response"]
            },
            "func": continue_tool_clarification
        },
        "tool_creator_suggest": {
            "description": "Get provider suggestions for a specific use case without starting full clarification.",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What the user wants to do (e.g., 'send messages', 'check weather')"
                    }
                },
                "required": ["query"]
            },
            "func": suggest_providers
        },
        "tool_creator_analyze": {
            "description": "Analyze an API description to preview what tool would be created without actually creating it.",
            "schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the API to analyze"
                    }
                },
                "required": ["description"]
            },
            "func": analyze_api_description
        },
        "tool_creator_list": {
            "description": "List all user-created tools that have been saved.",
            "schema": {
                "type": "object",
                "properties": {}
            },
            "func": list_user_tools
        },
        "tool_creator_sessions": {
            "description": "Get information about active clarification sessions (for debugging).",
            "schema": {
                "type": "object",
                "properties": {}
            },
            "func": get_active_clarification_sessions
        },
        "tool_creator_edit": {
            "description": "Edit an existing tool using natural language. Use this to modify endpoints, rename parameters, change authentication, etc.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to edit"
                    },
                    "modification_request": {
                        "type": "string",
                        "description": "Natural language description of changes (e.g., 'change endpoint to v2 API', 'rename msg parameter to message', 'switch to bearer token')"
                    },
                    "version": {
                        "type": "string",
                        "description": "Optional version to create. If not provided, will auto-determine based on the type of changes (patch for minor, minor for features, major for breaking)"
                    }
                },
                "required": ["tool_name", "modification_request"]
            },
            "func": edit_tool
        },
        "tool_creator_delete": {
            "description": "Delete a user-created tool. This permanently removes the tool and its metadata.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to delete"
                    }
                },
                "required": ["tool_name"]
            },
            "func": delete_tool
        },
        "tool_creator_summary": {
            "description": "Get a natural language summary of a tool's capabilities without showing code. Use this to understand what a tool does.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to summarize"
                    }
                },
                "required": ["tool_name"]
            },
            "func": get_tool_summary
        },
        "tool_creator_upgrade": {
            "description": "Upgrade a tool to a new version. Handles migration planning and can apply automatic updates for low-risk changes.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to upgrade"
                    },
                    "target_version": {
                        "type": "string",
                        "description": "Target version to upgrade to (latest if not specified)"
                    }
                },
                "required": ["tool_name"]
            },
            "func": upgrade_tool
        },
        "tool_creator_check_updates": {
            "description": "Check for available updates for tools. Can check a specific tool or all tools.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Specific tool to check (check all if not provided)"
                    }
                }
            },
            "func": check_tool_updates
        },
        "tool_creator_versions": {
            "description": "Show version history for a tool, including when each version was created and whether it has breaking changes.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool"
                    }
                },
                "required": ["tool_name"]
            },
            "func": show_tool_versions
        },
        "tool_creator_migrate": {
            "description": "Create or apply a migration plan for upgrading a tool with breaking changes. Shows what needs to be done and can apply automatic migrations.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool"
                    },
                    "target_version": {
                        "type": "string",
                        "description": "Target version to migrate to"
                    },
                    "apply_automatic": {
                        "type": "boolean",
                        "description": "Whether to apply automatic migrations immediately (default: false)",
                        "default": False
                    }
                },
                "required": ["tool_name", "target_version"]
            },
            "func": migrate_tool
        },
        "tool_creator_info": {
            "description": "Get detailed information about any tool (plugin, user-created, or built-in). Shows parameters, usage stats, and documentation.",
            "schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to inspect"
                    },
                    "detail_level": {
                        "type": "string",
                        "description": "Level of detail: summary, full, or debug (default: full)",
                        "enum": ["summary", "full", "debug"],
                        "default": "full"
                    }
                },
                "required": ["tool_name"]
            },
            "func": inspect_tool
        },
        "tool_creator_error_details": {
            "description": "Get technical details for a specific error ID. Use this when you need to see the full error information that was hidden in the initial error message.",
            "schema": {
                "type": "object",
                "properties": {
                    "error_id": {
                        "type": "string",
                        "description": "The error ID from a previous error response (e.g., 'err_20250113_120530_authentication')"
                    }
                },
                "required": ["error_id"]
            },
            "func": get_error_details
        },
        "tool_creator_list_all": {
            "description": "List all available tools from all sources (user-created, plugins, built-in, MCP). Useful for discovering what tools are available.",
            "schema": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Filter by tool source",
                        "enum": ["user", "plugin", "builtin", "mcp"]
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Name pattern to match (case-insensitive)"
                    }
                }
            },
            "func": list_all_tools
        }
    }
    
    # Add API discovery tools
    try:
        from .api_discovery_tools import get_api_discovery_tools
        tools.update(get_api_discovery_tools())
    except ImportError:
        logger.warning("API discovery tools not available")
    
    return tools