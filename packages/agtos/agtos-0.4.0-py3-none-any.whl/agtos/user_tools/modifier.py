"""Tool modification system for editing existing tools.

This module handles natural language modifications of existing tools,
allowing users to change endpoints, rename parameters, update authentication,
and more without needing to understand the code.

AI_CONTEXT:
    This enables users to modify tools through conversation:
    - "Change the endpoint to use v2 API"
    - "Add a new parameter for filtering"
    - "Switch from API key to bearer token"
    - "Rename the 'msg' parameter to 'message'"
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from agtos.user_tools.models import (
    ToolSpecification, APIEndpoint, Parameter, 
    AuthenticationMethod, HTTPMethod, AuthType, ParameterLocation
)
from agtos.user_tools.generator import ToolGenerator
from agtos.user_tools.validator import ToolValidator
from agtos.versioning.version_manager import VersionManager, Version


class ToolModifier:
    """Handles modifications to existing tools."""
    
    def __init__(self):
        self.generator = ToolGenerator()
        self.validator = ToolValidator()
        self.user_tools_dir = Path.home() / ".agtos" / "user_tools"
    
    def load_tool(self, tool_name: str) -> Tuple[Dict[str, Any], ToolSpecification]:
        """Load a tool's metadata and specification.
        
        Args:
            tool_name: Name of the tool to load
            
        Returns:
            Tuple of (metadata dict, ToolSpecification)
            
        Raises:
            FileNotFoundError: If tool doesn't exist
        """
        # Initialize version manager
        version_manager = VersionManager(self.user_tools_dir)
        
        # Check if tool exists via version manager
        active_version = version_manager.get_active_version(tool_name)
        if active_version:
            # Load from version manager
            metadata = version_manager.get_version_metadata(tool_name, active_version)
            if not metadata:
                raise FileNotFoundError(f"Tool '{tool_name}' not found")
        else:
            # Fall back to legacy location
            metadata_file = self.user_tools_dir / f"{tool_name}.json"
            
            if not metadata_file.exists():
                raise FileNotFoundError(f"Tool '{tool_name}' not found")
            
            # Load metadata
            metadata = json.loads(metadata_file.read_text())
        
        # Reconstruct specification
        spec = self._reconstruct_specification(metadata)
        
        return metadata, spec
    
    def apply_modifications(
        self, 
        tool_name: str, 
        modification_request: str,
        version_manager: Optional[Any] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply natural language modifications to a tool.
        
        Args:
            tool_name: Name of the tool to modify
            modification_request: Natural language description of changes
            
        Returns:
            Dict describing what changed
        """
        # Initialize version manager if not provided
        if not version_manager:
            version_manager = VersionManager(self.user_tools_dir)
        
        # Load existing tool from active version
        active_version = version_manager.get_active_version(tool_name)
        if not active_version:
            raise FileNotFoundError(f"Tool '{tool_name}' not found")
            
        metadata = version_manager.get_version_metadata(tool_name, active_version)
        if not metadata:
            raise FileNotFoundError(f"Metadata for tool '{tool_name}' not found")
            
        spec = self._reconstruct_specification(metadata)
        
        # Parse modification request
        changes = self._parse_modification_request(modification_request, spec)
        
        # Determine version based on changes if not provided
        if not version:
            version = self._determine_new_version(active_version, changes)
        
        # Apply changes to specification
        modified_spec = self._apply_changes_to_spec(spec, changes)
        
        # Regenerate tool code
        tool = self.generator.generate(modified_spec)
        
        # Validate
        errors = self.validator.validate(tool)
        if errors:
            critical_errors = [e for e in errors if isinstance(e, str) and ("Syntax" in e or "security" in e.lower())]
            if critical_errors:
                raise ValueError(f"Validation failed: {critical_errors}")
        
        # Track breaking changes in metadata if major version bump
        current_v = Version.parse(active_version)
        new_v = Version.parse(version)
        if new_v.major > current_v.major:
            if "breaking_changes" not in metadata:
                metadata["breaking_changes"] = {}
            metadata["breaking_changes"][version] = self._extract_breaking_changes(changes)
        
        # Save new version using version manager
        changelog = self._generate_changelog(changes, spec, modified_spec)
        version_manager.install_version(
            tool_name, version, tool.tool_code, metadata, changelog
        )
        
        # Return summary of changes
        result = self._summarize_changes(spec, modified_spec, changes)
        result["new_version"] = version
        result["previous_version"] = active_version
        return result
    
    def delete_tool(self, tool_name: str) -> Dict[str, Any]:
        """Delete a tool and its metadata.
        
        Args:
            tool_name: Name of the tool to delete
            
        Returns:
            Confirmation dict
        """
        # Initialize version manager
        version_manager = VersionManager(self.user_tools_dir)
        
        # Check if tool exists via version manager
        active_version = version_manager.get_active_version(tool_name)
        if not active_version:
            # Check for legacy non-versioned tools
            tool_file = self.user_tools_dir / f"{tool_name}.py"
            metadata_file = self.user_tools_dir / f"{tool_name}.json"
            
            if not metadata_file.exists():
                raise FileNotFoundError(f"Tool '{tool_name}' not found")
            
            # Load metadata for summary
            metadata = json.loads(metadata_file.read_text())
            description = metadata.get("description", "No description")
            
            # Delete legacy files
            if tool_file.exists():
                tool_file.unlink()
            metadata_file.unlink()
        else:
            # Handle versioned tool deletion
            # Get metadata before deletion
            metadata = version_manager.get_version_metadata(tool_name, active_version)
            description = metadata.get("description", "No description") if metadata else "No description"
            
            # Delete all versions
            tool_versions_dir = self.user_tools_dir / "versions" / tool_name
            if tool_versions_dir.exists():
                import shutil
                shutil.rmtree(tool_versions_dir)
            
            # Remove active symlinks
            active_py = self.user_tools_dir / "active" / f"{tool_name}.py"
            active_json = self.user_tools_dir / "active" / f"{tool_name}.json"
            
            if active_py.exists() or active_py.is_symlink():
                active_py.unlink()
            if active_json.exists() or active_json.is_symlink():
                active_json.unlink()
            
            # Also check for any legacy files with same name
            legacy_py = self.user_tools_dir / f"{tool_name}.py"
            legacy_json = self.user_tools_dir / f"{tool_name}.json"
            if legacy_py.exists():
                legacy_py.unlink()
            if legacy_json.exists():
                legacy_json.unlink()
        
        # Trigger hot reload marker
        self._create_reload_marker(tool_name, action="delete")
        
        return {
            "success": True,
            "deleted_tool": tool_name,
            "description": description,
            "message": f"Tool '{tool_name}' has been deleted"
        }
    
    def get_tool_summary(self, tool_name: str) -> Dict[str, Any]:
        """Get a natural language summary of a tool's capabilities.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Summary dict without code
        """
        metadata, spec = self.load_tool(tool_name)
        
        summary = {
            "name": tool_name,
            "description": spec.description,
            "created": metadata.get("created_at", "Unknown"),
            "endpoints": []
        }
        
        for endpoint in spec.endpoints:
            ep_summary = {
                "method": endpoint.method.value,
                "url": endpoint.url,
                "description": endpoint.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "description": p.description or f"{p.name} parameter"
                    }
                    for p in endpoint.parameters
                ],
                "authentication": None
            }
            
            if endpoint.authentication:
                ep_summary["authentication"] = {
                    "type": endpoint.authentication.type.value,
                    "location": endpoint.authentication.location
                }
            
            summary["endpoints"].append(ep_summary)
        
        return summary
    
    def _parse_modification_request(
        self, 
        request: str, 
        current_spec: ToolSpecification
    ) -> Dict[str, Any]:
        """Parse natural language modification request.
        
        Returns dict of changes to apply.
        """
        changes = {}
        request_lower = request.lower()
        
        # Check for endpoint URL changes
        url_patterns = [
            r"change.*endpoint.*to\s+(\S+)",
            r"use\s+(\S+)\s+instead",
            r"update.*url.*to\s+(\S+)",
            r"switch.*to\s+(\S+)\s+api"
        ]
        
        for pattern in url_patterns:
            if match := re.search(pattern, request_lower):
                new_url = match.group(1)
                # Extract full URL from original request (case-sensitive)
                url_match = re.search(match.group(1), request, re.IGNORECASE)
                if url_match:
                    changes["endpoint_url"] = url_match.group(0)
                break
        
        # Check for API version changes
        if "v2" in request_lower or "version 2" in request_lower:
            changes["api_version"] = "v2"
        elif "v3" in request_lower or "version 3" in request_lower:
            changes["api_version"] = "v3"
        
        # Check for parameter renames
        rename_patterns = [
            r"rename\s+(?:the\s+)?['\"]?(\w+)['\"]?\s+(?:parameter\s+)?to\s+['\"]?(\w+)['\"]?",
            r"change\s+(?:the\s+)?['\"]?(\w+)['\"]?\s+(?:parameter\s+)?to\s+['\"]?(\w+)['\"]?"
        ]
        
        for pattern in rename_patterns:
            if matches := re.findall(pattern, request_lower):
                changes["parameter_renames"] = {
                    old: new for old, new in matches
                }
                break
        
        # Check for new parameters
        if "add" in request_lower and "parameter" in request_lower:
            # Extract parameter name - try multiple patterns
            # Order matters: more specific patterns first
            param_patterns = [
                # Look for "X parameter" pattern (e.g., "q parameter for city")
                r"(\w+)\s+parameter\s+(?:for|is|to)",
                # Look for explicit naming patterns
                r"parameter\s+(?:called|named)\s+['\"]?(\w+)['\"]?",
                r"add\s+['\"]?(\w+)['\"]?\s+parameter",
                # Generic patterns (last resort)
                r"add\s+(?:a\s+)?(?:new\s+)?(?:required\s+)?parameter\s+(?:called\s+)?['\"]?(\w+)['\"]?",
                r"parameter\s+['\"]?(\w+)['\"]?"
            ]
            
            param_name = None
            for pattern in param_patterns:
                if match := re.search(pattern, request_lower):
                    param_name = match.group(1)
                    # Skip common words that aren't parameter names
                    if param_name not in ["a", "the", "new", "parameter", "required", "optional"]:
                        break
            
            if param_name and param_name not in ["a", "the", "new", "parameter", "required", "optional"]:
                changes["new_parameters"] = [{
                    "name": param_name,
                    "type": "string",
                    "required": "required" in request_lower,
                    "location": "query" if "query" in request_lower else "body"
                }]
        
        # Check for authentication changes
        if "bearer" in request_lower or "bearer token" in request_lower:
            changes["auth_type"] = "bearer"
        elif "api key" in request_lower or "api-key" in request_lower:
            changes["auth_type"] = "api_key"
        elif "no auth" in request_lower or "remove auth" in request_lower:
            changes["auth_type"] = "none"
        
        # Check for provider changes
        provider_patterns = [
            r"change.*provider.*to\s+(\w+)",
            r"switch.*to\s+(\w+)",
            r"use\s+(\w+)\s+instead"
        ]
        
        for pattern in provider_patterns:
            if match := re.search(pattern, request_lower):
                provider = match.group(1)
                if provider in ["slack", "discord", "teams", "github", "jira"]:
                    changes["provider"] = provider
                    break
        
        return changes
    
    def _apply_changes_to_spec(
        self, 
        spec: ToolSpecification, 
        changes: Dict[str, Any]
    ) -> ToolSpecification:
        """Apply parsed changes to the specification."""
        # Create a copy to modify
        import copy
        modified_spec = copy.deepcopy(spec)
        
        # Apply endpoint URL changes
        if "endpoint_url" in changes:
            for endpoint in modified_spec.endpoints:
                endpoint.url = changes["endpoint_url"]
        
        # Apply API version changes
        if "api_version" in changes:
            version = changes["api_version"]
            for endpoint in modified_spec.endpoints:
                # Replace v1, v2, etc. in URLs
                endpoint.url = re.sub(r'/v\d+/', f'/{version}/', endpoint.url)
                if not re.search(r'/v\d+/', endpoint.url):
                    # Add version if not present
                    parts = endpoint.url.split('/', 3)
                    if len(parts) >= 3:
                        parts.insert(3, version)
                        endpoint.url = '/'.join(parts)
        
        # Apply parameter renames
        if "parameter_renames" in changes:
            for endpoint in modified_spec.endpoints:
                for param in endpoint.parameters:
                    if param.name in changes["parameter_renames"]:
                        param.name = changes["parameter_renames"][param.name]
        
        # Add new parameters
        if "new_parameters" in changes:
            for new_param_data in changes["new_parameters"]:
                new_param = Parameter(
                    name=new_param_data["name"],
                    type=new_param_data["type"],
                    required=new_param_data["required"],
                    location=ParameterLocation(new_param_data["location"])
                )
                for endpoint in modified_spec.endpoints:
                    endpoint.parameters.append(new_param)
        
        # Apply authentication changes
        if "auth_type" in changes:
            auth_type = changes["auth_type"]
            for endpoint in modified_spec.endpoints:
                if auth_type == "none":
                    endpoint.authentication = None
                elif auth_type == "bearer":
                    endpoint.authentication = AuthenticationMethod(
                        type=AuthType.BEARER,
                        location="header",
                        key_name="Authorization",
                        value_prefix="Bearer "
                    )
                elif auth_type == "api_key":
                    endpoint.authentication = AuthenticationMethod(
                        type=AuthType.API_KEY,
                        location="header",
                        key_name="X-API-Key",
                        value_prefix=""
                    )
        
        # Apply provider changes
        if "provider" in changes:
            provider = changes["provider"]
            # Update tool name and description based on provider
            modified_spec.name = f"{provider}_tool"
            modified_spec.description = f"Tool for interacting with {provider.title()} API"
            
            # Update endpoint URLs for known providers
            provider_urls = {
                "slack": "https://slack.com/api",
                "discord": "https://discord.com/api",
                "teams": "https://graph.microsoft.com/v1.0",
                "github": "https://api.github.com",
                "jira": "https://your-domain.atlassian.net/rest/api/3"
            }
            
            if provider in provider_urls:
                base_url = provider_urls[provider]
                for endpoint in modified_spec.endpoints:
                    # Keep the path part, just change the base
                    path = endpoint.url.split('/', 3)[-1] if '/' in endpoint.url else ""
                    endpoint.url = f"{base_url}/{path}".rstrip('/')
        
        return modified_spec
    
    def _save_modified_tool(
        self, 
        tool_name: str, 
        spec: ToolSpecification, 
        tool: Any,
        original_metadata: Dict[str, Any]
    ):
        """Save the modified tool and update metadata."""
        # Save Python code
        tool_file = self.user_tools_dir / f"{tool_name}.py"
        tool_file.write_text(tool.tool_code)
        
        # Update metadata
        metadata = {
            "name": spec.name,
            "description": spec.description,
            "specification": {
                "natural_language": spec.natural_language_spec,
                "endpoints": [
                    {
                        "url": ep.url,
                        "method": ep.method.value,
                        "description": ep.description,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "location": p.location.value,
                                "required": p.required,
                                "description": p.description
                            }
                            for p in ep.parameters
                        ],
                        "authentication": {
                            "type": ep.authentication.type.value,
                            "location": ep.authentication.location
                        } if ep.authentication else None
                    }
                    for ep in spec.endpoints
                ]
            },
            "mcp_schema": tool.mcp_schema,
            "created_at": original_metadata.get("created_at"),
            "modified_at": datetime.now().isoformat(),
            "modification_history": original_metadata.get("modification_history", []) + [{
                "date": datetime.now().isoformat(),
                "changes": self._get_change_summary(spec)
            }]
        }
        
        metadata_file = self.user_tools_dir / f"{tool_name}.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Trigger hot reload
        self._create_reload_marker(tool_name, action="modify")
    
    def _reconstruct_specification(self, metadata: Dict[str, Any]) -> ToolSpecification:
        """Reconstruct a ToolSpecification from stored metadata."""
        spec_data = metadata.get("specification", {})
        
        # Reconstruct endpoints
        endpoints = []
        for ep_data in spec_data.get("endpoints", []):
            # Reconstruct parameters
            parameters = []
            for p_data in ep_data.get("parameters", []):
                param = Parameter(
                    name=p_data["name"],
                    type=p_data.get("type", "string"),
                    location=ParameterLocation(p_data.get("location", "query")),
                    required=p_data.get("required", False),
                    description=p_data.get("description")
                )
                parameters.append(param)
            
            # Reconstruct authentication
            auth = None
            if auth_data := ep_data.get("authentication"):
                auth = AuthenticationMethod(
                    type=AuthType(auth_data["type"]),
                    location=auth_data.get("location", "header"),
                    key_name=auth_data.get("key_name", "Authorization"),
                    value_prefix=auth_data.get("value_prefix", "")
                )
            
            endpoint = APIEndpoint(
                url=ep_data["url"],
                method=HTTPMethod(ep_data["method"]),
                description=ep_data.get("description", ""),
                parameters=parameters,
                authentication=auth
            )
            endpoints.append(endpoint)
        
        return ToolSpecification(
            name=metadata["name"],
            description=metadata["description"],
            natural_language_spec=spec_data.get("natural_language", ""),
            endpoints=endpoints
        )
    
    def _summarize_changes(
        self, 
        original: ToolSpecification, 
        modified: ToolSpecification,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a summary of what changed."""
        summary = {
            "tool_name": original.name,
            "changes_applied": []
        }
        
        # Check endpoint changes
        if "endpoint_url" in changes:
            summary["changes_applied"].append({
                "type": "endpoint_url",
                "from": original.endpoints[0].url if original.endpoints else "N/A",
                "to": changes["endpoint_url"]
            })
        
        # Check API version
        if "api_version" in changes:
            summary["changes_applied"].append({
                "type": "api_version",
                "description": f"Updated to API {changes['api_version']}"
            })
        
        # Check parameter renames
        if "parameter_renames" in changes:
            for old, new in changes["parameter_renames"].items():
                summary["changes_applied"].append({
                    "type": "parameter_rename",
                    "from": old,
                    "to": new
                })
        
        # Check new parameters
        if "new_parameters" in changes:
            for param in changes["new_parameters"]:
                summary["changes_applied"].append({
                    "type": "new_parameter",
                    "name": param["name"],
                    "details": f"{param['type']} parameter in {param['location']}"
                })
        
        # Check auth changes
        if "auth_type" in changes:
            old_auth = "none"
            if original.endpoints and original.endpoints[0].authentication:
                old_auth = original.endpoints[0].authentication.type.value
            
            summary["changes_applied"].append({
                "type": "authentication",
                "from": old_auth,
                "to": changes["auth_type"]
            })
        
        # Check provider changes
        if "provider" in changes:
            summary["changes_applied"].append({
                "type": "provider",
                "description": f"Switched to {changes['provider'].title()}"
            })
        
        summary["total_changes"] = len(summary["changes_applied"])
        
        return summary
    
    def _get_change_summary(self, spec: ToolSpecification) -> str:
        """Get a brief summary of the specification for history."""
        endpoint_count = len(spec.endpoints)
        param_count = sum(len(ep.parameters) for ep in spec.endpoints)
        
        return f"{endpoint_count} endpoints, {param_count} parameters"
    
    def _create_reload_marker(self, tool_name: str, action: str = "modify"):
        """Create a reload marker for hot reload."""
        reload_marker = self.user_tools_dir / ".reload_marker"
        reload_marker.write_text(
            f"{tool_name}:{action}\n{datetime.now().isoformat()}"
        )
    
    def _determine_new_version(self, current_version: str, changes: Dict[str, Any]) -> str:
        """Determine appropriate new version based on changes."""
        current_v = Version.parse(current_version)
        
        # Check for breaking changes
        breaking_change_types = ["auth_type", "parameter_renames", "endpoint_url"]
        has_breaking_changes = any(change_type in changes for change_type in breaking_change_types)
        
        if has_breaking_changes:
            # Major version bump for breaking changes
            return str(current_v.bump_major())
        elif "new_parameters" in changes or "provider" in changes:
            # Minor version bump for new features
            return str(current_v.bump_minor())
        else:
            # Patch version for bug fixes and minor changes
            return str(current_v.bump_patch())
    
    def _extract_breaking_changes(self, changes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract breaking changes for documentation."""
        breaking_changes = []
        
        if "parameter_renames" in changes:
            for old, new in changes["parameter_renames"].items():
                breaking_changes.append({
                    "type": "parameter_rename",
                    "from": old,
                    "to": new,
                    "migration": "automatic",
                    "description": f"Parameter '{old}' renamed to '{new}'"
                })
        
        if "auth_type" in changes:
            breaking_changes.append({
                "type": "auth_change",
                "from": "previous",
                "to": changes["auth_type"],
                "migration": "manual",
                "description": f"Authentication changed to {changes['auth_type']}",
                "instructions": "Update your credentials configuration"
            })
        
        if "endpoint_url" in changes:
            breaking_changes.append({
                "type": "endpoint_change",
                "migration": "automatic",
                "description": "API endpoint URL changed"
            })
        
        return breaking_changes
    
    def _generate_changelog(self, changes: Dict[str, Any], 
                          old_spec: ToolSpecification, 
                          new_spec: ToolSpecification) -> str:
        """Generate changelog for the version."""
        lines = ["# Changelog\n"]
        
        if "endpoint_url" in changes:
            lines.append(f"- Changed API endpoint to: {changes['endpoint_url']}")
        
        if "parameter_renames" in changes:
            for old, new in changes["parameter_renames"].items():
                lines.append(f"- Renamed parameter '{old}' to '{new}'")
        
        if "new_parameters" in changes:
            for param in changes["new_parameters"]:
                lines.append(f"- Added new parameter '{param['name']}' ({param['type']})")
        
        if "auth_type" in changes:
            lines.append(f"- Changed authentication to {changes['auth_type']}")
        
        if "api_version" in changes:
            lines.append(f"- Updated to API {changes['api_version']}")
        
        return "\n".join(lines)