"""Insomnia Collection Parser for agtOS.

This parser handles Insomnia Collection format (v4) and extracts:
- Workspace metadata
- Requests with methods, URLs, headers, body, auth
- Environment variables
- Folder structure (request groups)
- Authentication configuration
- Request dependencies and chains

Insomnia format differences from Postman:
- Uses _type field for object types
- Environment stored with _type: "environment"
- Requests have _type: "request"
- Folders have _type: "request_group"
- Uses {{ _.variable }} syntax for environment variables
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InsomniaParser:
    """Parser for Insomnia Collection format."""
    
    def __init__(self):
        self.environment = {}  # Environment variables
        self.base_environment = {}  # Base environment
        self.resources = {}  # All resources by ID
        self.folders = {}  # Request groups
        
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse Insomnia collection and extract API information.
        
        Args:
            content: JSON string containing Insomnia collection export
            
        Returns:
            Dictionary with parsed API information
        """
        try:
            # Insomnia exports as array of resources
            collection = json.loads(content)
            
            # Verify it's an Insomnia export
            if not self._is_insomnia_collection(collection):
                return {
                    "success": False,
                    "error": "Not a valid Insomnia collection",
                    "endpoints": []
                }
            
            # Build resource index
            self._build_resource_index(collection)
            
            # Extract workspace info
            workspace = self._find_workspace()
            result = {
                "success": True,
                "name": workspace.get("name", "Unknown Workspace") if workspace else "Insomnia Collection",
                "description": workspace.get("description", "") if workspace else "",
                "version": "v4",  # Insomnia export version
                "endpoints": [],
                "authentication": None,
                "base_url": None,
                "variables": {}
            }
            
            # Extract environments
            self._extract_environments()
            result["variables"] = self.environment.copy()
            
            # Extract workspace-level authentication
            workspace_auth = None
            if workspace and "authentication" in workspace:
                workspace_auth = self._parse_auth(workspace["authentication"])
                result["authentication"] = workspace_auth
            
            # Process requests
            endpoints = []
            requests = self._find_requests()
            
            for request in requests:
                endpoint = self._extract_endpoint(request, workspace_auth)
                if endpoint:
                    endpoints.append(endpoint)
            
            result["endpoints"] = endpoints
            
            # Try to determine base URL
            if endpoints:
                result["base_url"] = self._infer_base_url(endpoints)
            elif self.environment.get("base_url"):
                result["base_url"] = self.environment["base_url"]
            
            # Add statistics
            auth_types = []
            for ep in endpoints:
                if ep.get("authentication"):
                    auth_types.append(ep["authentication"].get("type", "none"))
                else:
                    auth_types.append("none")
            
            result["statistics"] = {
                "total_endpoints": len(endpoints),
                "total_folders": len(self.folders),
                "methods": list(set(ep.get("method", "GET") for ep in endpoints)),
                "auth_types": list(set(auth_types))
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {
                "success": False,
                "error": f"Invalid JSON: {str(e)}",
                "endpoints": []
            }
        except Exception as e:
            logger.error(f"Insomnia parser error: {e}")
            return {
                "success": False,
                "error": str(e),
                "endpoints": []
            }
    
    def _is_insomnia_collection(self, data: Any) -> bool:
        """Check if data is a valid Insomnia collection."""
        # Insomnia exports as an array of resources
        if not isinstance(data, list):
            return False
        
        # Check for Insomnia-specific _type fields
        has_workspace = any(
            isinstance(item, dict) and item.get("_type") == "workspace"
            for item in data
        )
        has_requests = any(
            isinstance(item, dict) and item.get("_type") == "request"
            for item in data
        )
        
        return has_workspace or has_requests
    
    def _build_resource_index(self, collection: List[Dict]):
        """Build index of all resources by ID."""
        for resource in collection:
            if isinstance(resource, dict) and "_id" in resource:
                self.resources[resource["_id"]] = resource
                
                # Index specific types
                if resource.get("_type") == "request_group":
                    self.folders[resource["_id"]] = resource
    
    def _find_workspace(self) -> Optional[Dict]:
        """Find the workspace resource."""
        for resource in self.resources.values():
            if resource.get("_type") == "workspace":
                return resource
        return None
    
    def _find_requests(self) -> List[Dict]:
        """Find all request resources."""
        requests = []
        for resource in self.resources.values():
            if resource.get("_type") == "request":
                requests.append(resource)
        return requests
    
    def _extract_environments(self):
        """Extract environment variables."""
        # Find base environment
        for resource in self.resources.values():
            if resource.get("_type") == "environment" and resource.get("parentId") is None:
                self.base_environment = resource.get("data", {})
        
        # Find sub-environments and merge with base
        for resource in self.resources.values():
            if resource.get("_type") == "environment" and resource.get("parentId") is not None:
                env_data = resource.get("data", {})
                # Merge with base environment
                self.environment = {**self.base_environment, **env_data}
                break  # Use first sub-environment found
        
        # If no sub-environment, use base
        if not self.environment and self.base_environment:
            self.environment = self.base_environment.copy()
    
    def _parse_auth(self, auth: Dict) -> Optional[Dict[str, Any]]:
        """Parse authentication configuration."""
        if not auth:
            return None
        
        auth_type = auth.get("type", "").lower()
        
        if auth_type == "bearer":
            token = auth.get("token", "")
            return {
                "type": "bearer",
                "token": self._substitute_variables(token),
                "description": "Bearer token authentication"
            }
        
        elif auth_type == "basic":
            username = auth.get("username", "")
            password = auth.get("password", "")
            return {
                "type": "basic",
                "username": self._substitute_variables(username),
                "password": self._substitute_variables(password),
                "description": "Basic authentication"
            }
        
        elif auth_type == "apikey":
            return {
                "type": "api_key",
                "key_name": auth.get("key", ""),
                "key_value": self._substitute_variables(auth.get("value", "")),
                "location": auth.get("addTo", "header"),
                "description": f"API key authentication"
            }
        
        elif auth_type == "oauth2":
            return {
                "type": "oauth2",
                "description": "OAuth 2.0 authentication",
                "access_token": self._substitute_variables(auth.get("accessToken", "")),
                "token_type": auth.get("tokenType", "Bearer"),
                "grant_type": auth.get("grantType", ""),
                "client_id": self._substitute_variables(auth.get("clientId", "")),
                "client_secret": self._substitute_variables(auth.get("clientSecret", ""))
            }
        
        elif auth_type == "aws":
            return {
                "type": "aws",
                "description": "AWS signature authentication",
                "access_key_id": self._substitute_variables(auth.get("accessKeyId", "")),
                "secret_access_key": self._substitute_variables(auth.get("secretAccessKey", "")),
                "region": auth.get("region", ""),
                "service": auth.get("service", "")
            }
        
        return None
    
    def _extract_endpoint(self, request: Dict, workspace_auth: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Extract endpoint information from a request."""
        endpoint = {
            "name": request.get("name", "Unknown Request"),
            "description": request.get("description", ""),
            "folder_path": self._get_folder_path(request.get("parentId"))
        }
        
        # Extract method
        endpoint["method"] = request.get("method", "GET").upper()
        
        # Extract URL
        url = request.get("url", "")
        endpoint["url"] = self._substitute_variables(url)
        
        # Extract headers
        headers = request.get("headers", [])
        endpoint["headers"] = self._extract_headers(headers)
        
        # Extract authentication
        if "authentication" in request and request["authentication"]:
            endpoint["authentication"] = self._parse_auth(request["authentication"])
        elif workspace_auth:
            endpoint["authentication"] = workspace_auth
        
        # Extract body
        body = request.get("body", {})
        if body:
            endpoint["body"] = self._extract_body(body)
        
        # Extract query parameters
        parameters = request.get("parameters", [])
        if parameters:
            endpoint["query_params"] = self._extract_query_params(parameters)
        
        # Extract path parameters from URL
        endpoint["path_params"] = self._extract_path_params(endpoint["url"])
        
        # Note if request has tests or pre-request scripts
        if request.get("settingPreRequestScript"):
            endpoint["has_prerequest_script"] = True
        if request.get("settingFollowRedirects") is False:
            endpoint["follow_redirects"] = False
        
        return endpoint
    
    def _get_folder_path(self, parent_id: Optional[str]) -> str:
        """Get the folder path for a request."""
        if not parent_id or parent_id not in self.folders:
            return ""
        
        folder = self.folders[parent_id]
        path_parts = [folder.get("name", "")]
        
        # Traverse up the hierarchy
        current_parent_id = folder.get("parentId")
        while current_parent_id and current_parent_id in self.folders:
            parent_folder = self.folders[current_parent_id]
            path_parts.insert(0, parent_folder.get("name", ""))
            current_parent_id = parent_folder.get("parentId")
        
        return "/".join(path_parts)
    
    def _substitute_variables(self, text: str) -> str:
        """Substitute {{ _.variable }} with actual values."""
        if not text:
            return text
        
        # Insomnia uses {{ _.variable }} syntax
        pattern = r'\{\{\s*_\.([^}]+)\s*\}\}'
        
        def replacer(match):
            var_name = match.group(1).strip()
            # Check environment variables
            if var_name in self.environment:
                return str(self.environment[var_name])
            # Return placeholder for undefined variables
            return f"{{{var_name}}}"
        
        return re.sub(pattern, replacer, text)
    
    def _extract_headers(self, headers: List[Dict]) -> Dict[str, str]:
        """Extract headers from request."""
        header_dict = {}
        for header in headers:
            if isinstance(header, dict):
                name = header.get("name", "")
                value = header.get("value", "")
                if name and not header.get("disabled", False):
                    header_dict[name] = self._substitute_variables(value)
        return header_dict
    
    def _extract_body(self, body: Dict) -> Dict[str, Any]:
        """Extract request body information."""
        mime_type = body.get("mimeType", "")
        body_info = {"mode": self._get_body_mode(mime_type)}
        
        if mime_type == "application/json":
            body_info["content"] = self._substitute_variables(body.get("text", ""))
            body_info["content_type"] = "application/json"
        
        elif mime_type == "application/x-www-form-urlencoded":
            params = body.get("params", [])
            body_info["content"] = self._extract_form_data(params)
            body_info["content_type"] = "application/x-www-form-urlencoded"
        
        elif mime_type == "multipart/form-data":
            params = body.get("params", [])
            body_info["content"] = self._extract_form_data(params)
            body_info["content_type"] = "multipart/form-data"
        
        elif mime_type in ["text/plain", "text/xml", "application/xml"]:
            body_info["content"] = self._substitute_variables(body.get("text", ""))
            body_info["content_type"] = mime_type
        
        elif mime_type == "application/graphql":
            body_info["mode"] = "graphql"
            body_info["query"] = self._substitute_variables(body.get("text", ""))
        
        elif body.get("fileName"):
            body_info["mode"] = "file"
            body_info["file_path"] = body.get("fileName", "")
        
        else:
            # Default to raw text
            body_info["content"] = self._substitute_variables(body.get("text", ""))
            body_info["content_type"] = mime_type or "text/plain"
        
        return body_info
    
    def _get_body_mode(self, mime_type: str) -> str:
        """Convert MIME type to body mode."""
        if mime_type == "application/x-www-form-urlencoded":
            return "urlencoded"
        elif mime_type == "multipart/form-data":
            return "formdata"
        elif mime_type == "application/graphql":
            return "graphql"
        else:
            return "raw"
    
    def _extract_form_data(self, params: List[Dict]) -> Dict[str, str]:
        """Extract form data fields."""
        form_dict = {}
        for param in params:
            if isinstance(param, dict) and not param.get("disabled", False):
                name = param.get("name", "")
                value = param.get("value", "")
                if name:
                    form_dict[name] = self._substitute_variables(value)
        return form_dict
    
    def _extract_query_params(self, params: List[Dict]) -> List[Dict[str, Any]]:
        """Extract query parameters."""
        query_params = []
        for param in params:
            if isinstance(param, dict) and not param.get("disabled", False):
                query_params.append({
                    "name": param.get("name", ""),
                    "value": self._substitute_variables(param.get("value", "")),
                    "description": param.get("description", "")
                })
        return query_params
    
    def _extract_path_params(self, url: str) -> List[Dict[str, str]]:
        """Extract path parameters from URL."""
        params = []
        
        # Look for :param style
        for match in re.finditer(r':([a-zA-Z_]\w*)', url):
            params.append({
                "name": match.group(1),
                "in": "path",
                "required": True
            })
        
        # Look for {param} style
        for match in re.finditer(r'\{([^}]+)\}', url):
            param_name = match.group(1)
            # Skip if it's a variable reference (contains .)
            if "." not in param_name:
                params.append({
                    "name": param_name,
                    "in": "path",
                    "required": True
                })
        
        return params
    
    def _infer_base_url(self, endpoints: List[Dict]) -> Optional[str]:
        """Infer base URL from endpoints."""
        urls = []
        for endpoint in endpoints:
            url = endpoint.get("url", "")
            if url and url.startswith("http"):
                parsed = urlparse(url)
                base = f"{parsed.scheme}://{parsed.netloc}"
                urls.append(base)
        
        # Return most common base URL
        if urls:
            from collections import Counter
            most_common = Counter(urls).most_common(1)
            return most_common[0][0] if most_common else None
        
        return None