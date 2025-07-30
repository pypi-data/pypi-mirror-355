"""API Discovery Integration for Tool Creator.

This module bridges the existing knowledge acquisition system with tool creation,
enabling agents to automatically discover and create tools from APIs.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from agtos.knowledge.api import APIKnowledge
from agtos.user_tools import APIAnalyzer, ToolGenerator, ToolValidator
from agtos.user_tools.models import (
    APIEndpoint, 
    HTTPMethod, 
    Parameter,
    ParameterLocation,
    AuthenticationMethod,
    AuthType,
    ToolSpecification
)

logger = logging.getLogger(__name__)


def discover_and_create_api_tool(
    task_description: str,
    api_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Discover an API for a task and create a tool automatically.
    
    Args:
        task_description: What the user wants to do (e.g., "get weather data")
        api_hint: Optional hint about which API to use
        
    Returns:
        Result dictionary with tool creation status
    """
    try:
        # Initialize knowledge system
        api_knowledge = APIKnowledge()
        
        # Try to find a relevant API
        if api_hint:
            # User provided a hint, try that first
            base_url = _extract_base_url(api_hint)
            knowledge = api_knowledge.discover_api_from_docs(base_url)
        else:
            # Search for APIs based on task
            # TODO: Implement web search integration
            return {
                "success": False,
                "message": "Automatic API discovery without hints coming soon. Please provide an API URL."
            }
        
        if not knowledge or not knowledge.get("endpoints"):
            return {
                "success": False,
                "message": f"Could not discover API endpoints for {api_hint}"
            }
        
        # Convert discovered knowledge to tool specification
        spec = _convert_knowledge_to_spec(knowledge, task_description)
        
        # Generate and validate the tool
        generator = ToolGenerator()
        tool = generator.generate(spec)
        
        validator = ToolValidator()
        errors = validator.validate(tool)
        
        if errors:
            return {
                "success": False,
                "message": f"Tool validation failed: {', '.join(errors)}"
            }
        
        # Save the tool
        from agtos.plugins.tool_creator import _save_tool_with_versioning
        _save_tool_with_versioning(spec, tool)
        
        return {
            "success": True,
            "message": f"✅ Discovered and created '{spec.name}' tool with {len(spec.endpoints)} endpoints!",
            "tool_name": spec.name,
            "endpoints": [ep.url for ep in spec.endpoints]
        }
        
    except Exception as e:
        logger.error(f"Error in API discovery: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to discover API: {str(e)}"
        }


def _extract_base_url(api_hint: str) -> str:
    """Extract base URL from user hint."""
    # Handle various formats
    hint = api_hint.strip()
    
    # If it's already a URL
    if hint.startswith(('http://', 'https://')):
        # Extract just the base
        parts = hint.split('/')
        return '/'.join(parts[:3])
    
    # If it's a domain
    if '.' in hint:
        return f"https://{hint}"
    
    # Otherwise assume it's a service name
    # Could enhance this with a known services map
    return f"https://api.{hint}.com"


def _convert_knowledge_to_spec(knowledge: Dict[str, Any], task: str) -> ToolSpecification:
    """Convert API knowledge to tool specification."""
    # Extract service name from base URL
    base_url = knowledge.get("base_url", "")
    service_name = _extract_service_name(base_url)
    
    # Convert endpoints
    endpoints = []
    for ep_data in knowledge.get("endpoints", []):
        endpoint = APIEndpoint(
            url=base_url + ep_data["path"],
            method=HTTPMethod(ep_data["method"]),
            description=ep_data.get("summary", ep_data.get("description", "")),
            parameters=_convert_parameters(ep_data.get("parameters", [])),
            authentication=_convert_auth(knowledge.get("security"))
        )
        endpoints.append(endpoint)
    
    # Create specification
    spec = ToolSpecification(
        name=service_name,
        description=f"Tool to {task} using {service_name} API",
        natural_language_spec=f"Discovered from {base_url} to {task}",
        endpoints=endpoints,
        tags=["discovered", "api", service_name]
    )
    
    return spec


def _extract_service_name(url: str) -> str:
    """Extract service name from URL."""
    # Remove protocol
    if url.startswith(('http://', 'https://')):
        url = url.split('://', 1)[1]
    
    # Extract domain parts
    parts = url.split('.')
    
    # Common patterns
    if parts[0] == "api" and len(parts) > 1:
        return parts[1]  # api.service.com -> service
    elif parts[0] != "www":
        return parts[0]  # service.com -> service
    else:
        return parts[1] if len(parts) > 1 else "api"


def _convert_parameters(params: List[Dict]) -> List[Parameter]:
    """Convert OpenAPI parameters to our Parameter model."""
    converted = []
    
    for param in params:
        location = param.get("in", "query")
        location_map = {
            "query": ParameterLocation.QUERY,
            "path": ParameterLocation.PATH,
            "header": ParameterLocation.HEADER,
            "body": ParameterLocation.BODY
        }
        
        converted.append(Parameter(
            name=param.get("name", ""),
            type=param.get("type", "string"),
            location=location_map.get(location, ParameterLocation.QUERY),
            required=param.get("required", False),
            description=param.get("description", "")
        ))
    
    return converted


def _convert_auth(security: Optional[List[Dict]]) -> Optional[AuthenticationMethod]:
    """Convert OpenAPI security to our auth model."""
    if not security:
        return None
    
    # Take first security scheme
    for scheme in security:
        if "bearerAuth" in scheme or "BearerAuth" in scheme:
            return AuthenticationMethod(
                type=AuthType.BEARER,
                location="header",
                key_name="Authorization",
                value_prefix="Bearer "
            )
        elif "apiKey" in scheme or "ApiKeyAuth" in scheme:
            # Need more info to determine location
            return AuthenticationMethod(
                type=AuthType.API_KEY,
                location="header",
                key_name="X-API-Key"
            )
    
    return None


def check_if_tool_needed(task: str) -> Dict[str, Any]:
    """Check if we need to create a tool for a task.
    
    Args:
        task: User's task description
        
    Returns:
        Dict with need_tool boolean and suggested API if found
    """
    # Check if we already have a tool for this
    # TODO: Implement semantic search through existing tools
    
    # For now, return that we need a tool
    return {
        "need_tool": True,
        "reason": "No existing tool found for this task",
        "suggested_api": None
    }


# Plugin interface for Meta-MCP
def get_api_discoverer_tools():
    """Return tools for the Meta-MCP plugin system."""
    return {
        "discover_api_tool": {
            "description": "Discover an API and create a tool automatically",
            "schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "What the user wants to do"
                    },
                    "api_hint": {
                        "type": "string",
                        "description": "Optional API URL or service name"
                    }
                },
                "required": ["task"]
            },
            "func": discover_and_create_api_tool
        },
        "check_tool_needed": {
            "description": "Check if a tool needs to be created for a task",
            "schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The task description"
                    }
                },
                "required": ["task"]
            },
            "func": check_if_tool_needed
        }
    }