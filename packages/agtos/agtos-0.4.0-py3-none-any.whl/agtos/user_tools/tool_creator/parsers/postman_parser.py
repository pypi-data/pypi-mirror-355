"""Postman Collection Parser for agtOS.

This parser handles Postman Collection format v2.1 and extracts:
- Collection metadata
- Requests with methods, URLs, headers, body, auth
- Environment variables
- Folder structure and inheritance
- Authentication inheritance
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


class PostmanParser:
    """Parser for Postman Collection format."""
    
    def __init__(self):
        self.variables = {}  # Collection/environment variables
        self.auth_hierarchy = {}  # Track auth inheritance
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse Postman collection and extract API information.
        
        Args:
            content: JSON string containing Postman collection
            
        Returns:
            Dictionary with parsed API information
        """
        try:
            collection = json.loads(content)
            
            # Verify it's a Postman collection
            if not self._is_postman_collection(collection):
                return {
                    "success": False,
                    "error": "Not a valid Postman collection",
                    "endpoints": []
                }
            
            # Extract collection info
            info = collection.get("info", {})
            result = {
                "success": True,
                "name": info.get("name", "Unknown Collection"),
                "description": info.get("description", ""),
                "version": info.get("schema", "").split("/")[-1],  # Extract version from schema URL
                "endpoints": [],
                "authentication": None,
                "base_url": None,
                "variables": {}
            }
            
            # Extract collection variables
            if "variable" in collection:
                self._extract_variables(collection["variable"])
                result["variables"] = self.variables.copy()
            
            # Extract collection-level auth
            collection_auth = None
            if "auth" in collection:
                collection_auth = self._parse_auth(collection["auth"])
                result["authentication"] = collection_auth
            
            # Process items (requests and folders)
            endpoints = []
            self._process_items(
                collection.get("item", []), 
                endpoints, 
                parent_auth=collection_auth
            )
            
            result["endpoints"] = endpoints
            
            # Try to determine base URL from endpoints
            if endpoints:
                result["base_url"] = self._infer_base_url(endpoints)
            
            # Add statistics
            result["statistics"] = {
                "total_endpoints": len(endpoints),
                "methods": list(set(ep.get("method", "GET") for ep in endpoints)),
                "auth_types": list(set(
                    ep.get("authentication", {}).get("type", "none") 
                    for ep in endpoints 
                    if ep.get("authentication")
                ))
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
            logger.error(f"Postman parser error: {e}")
            return {
                "success": False,
                "error": str(e),
                "endpoints": []
            }
    
    def _is_postman_collection(self, data: Dict) -> bool:
        """Check if data is a valid Postman collection."""
        # Check for required fields
        if "info" not in data or "item" not in data:
            return False
        
        # Check for schema (v2.0 or v2.1)
        schema = data.get("info", {}).get("schema", "")
        return "schema.getpostman.com" in schema
    
    def _extract_variables(self, variables: List[Dict]):
        """Extract collection variables."""
        for var in variables:
            if isinstance(var, dict):
                key = var.get("key", "")
                value = var.get("value", var.get("default", ""))
                if key:
                    self.variables[key] = value
    
    def _parse_auth(self, auth: Dict) -> Optional[Dict[str, Any]]:
        """Parse authentication configuration."""
        if not auth:
            return None
        
        auth_type = auth.get("type", "").lower()
        
        if auth_type == "bearer":
            bearer_config = auth.get("bearer", [])
            token = self._get_auth_value(bearer_config, "token")
            return {
                "type": "bearer",
                "token": token,
                "description": "Bearer token authentication"
            }
        
        elif auth_type == "basic":
            basic_config = auth.get("basic", [])
            username = self._get_auth_value(basic_config, "username")
            password = self._get_auth_value(basic_config, "password")
            return {
                "type": "basic",
                "username": username,
                "password": password,
                "description": "Basic authentication"
            }
        
        elif auth_type == "apikey":
            apikey_config = auth.get("apikey", [])
            key = self._get_auth_value(apikey_config, "key")
            value = self._get_auth_value(apikey_config, "value")
            location = self._get_auth_value(apikey_config, "in", "header")
            return {
                "type": "api_key",
                "key_name": key,
                "key_value": value,
                "location": location,
                "description": f"API key authentication ({location})"
            }
        
        elif auth_type == "oauth2":
            oauth2_config = auth.get("oauth2", [])
            return {
                "type": "oauth2",
                "description": "OAuth 2.0 authentication",
                "config": self._extract_oauth2_config(oauth2_config)
            }
        
        return None
    
    def _get_auth_value(self, config: List[Dict], key: str, default: str = "") -> str:
        """Extract value from auth configuration array."""
        for item in config:
            if isinstance(item, dict) and item.get("key") == key:
                return item.get("value", default)
        return default
    
    def _extract_oauth2_config(self, config: List[Dict]) -> Dict[str, Any]:
        """Extract OAuth2 configuration details."""
        oauth_config = {}
        for item in config:
            if isinstance(item, dict):
                key = item.get("key", "")
                value = item.get("value", "")
                if key and value:
                    oauth_config[key] = value
        return oauth_config
    
    def _process_items(self, items: List[Dict], endpoints: List[Dict], 
                      parent_auth: Optional[Dict] = None, parent_path: str = ""):
        """Process collection items (requests and folders)."""
        for item in items:
            if not isinstance(item, dict):
                continue
            
            # Check if it's a folder
            if "item" in item:
                # It's a folder - process recursively
                folder_name = item.get("name", "")
                folder_auth = parent_auth  # Default to parent auth
                
                # Check for folder-level auth
                if "auth" in item:
                    folder_auth = self._parse_auth(item["auth"])
                
                # Recursively process folder items
                self._process_items(
                    item["item"], 
                    endpoints, 
                    parent_auth=folder_auth,
                    parent_path=f"{parent_path}/{folder_name}" if parent_path else folder_name
                )
            
            # Check if it's a request
            elif "request" in item:
                # It's a request - extract endpoint
                endpoint = self._extract_endpoint(item, parent_auth, parent_path)
                if endpoint:
                    endpoints.append(endpoint)
    
    def _extract_endpoint(self, item: Dict, parent_auth: Optional[Dict], 
                         parent_path: str) -> Optional[Dict[str, Any]]:
        """Extract endpoint information from a request item."""
        request = item.get("request")
        if not request:
            return None
        
        endpoint = {
            "name": item.get("name", "Unknown Request"),
            "description": item.get("description", ""),
            "folder_path": parent_path
        }
        
        # Extract method
        if isinstance(request, dict):
            endpoint["method"] = request.get("method", "GET").upper()
            
            # Extract URL
            url_info = request.get("url", {})
            if isinstance(url_info, str):
                # Simple string URL
                endpoint["url"] = self._substitute_variables(url_info)
            elif isinstance(url_info, dict):
                # Complex URL object
                endpoint["url"] = self._build_url_from_object(url_info)
            
            # Extract headers
            headers = request.get("header", [])
            endpoint["headers"] = self._extract_headers(headers)
            
            # Extract authentication
            if "auth" in request:
                endpoint["authentication"] = self._parse_auth(request["auth"])
            elif parent_auth:
                endpoint["authentication"] = parent_auth
            
            # Extract body
            body = request.get("body", {})
            if body:
                endpoint["body"] = self._extract_body(body)
            
            # Extract query parameters from URL object
            if isinstance(url_info, dict) and "query" in url_info:
                endpoint["query_params"] = self._extract_query_params(url_info["query"])
            
            # Extract path parameters
            endpoint["path_params"] = self._extract_path_params(endpoint.get("url", ""))
            
            # Note pre-request scripts and tests
            if "event" in item:
                events = item["event"]
                for event in events:
                    if event.get("listen") == "prerequest":
                        endpoint["has_prerequest_script"] = True
                    elif event.get("listen") == "test":
                        endpoint["has_test_script"] = True
        
        return endpoint
    
    def _build_url_from_object(self, url_obj: Dict) -> str:
        """Build URL from Postman URL object."""
        # Try raw URL first
        if "raw" in url_obj:
            return self._substitute_variables(url_obj["raw"])
        
        # Build from components
        protocol = url_obj.get("protocol", "https")
        host = url_obj.get("host", [])
        port = url_obj.get("port", "")
        path = url_obj.get("path", [])
        
        # Handle host as array
        if isinstance(host, list):
            host = ".".join(str(h) for h in host)
        
        # Handle path as array
        if isinstance(path, list):
            path = "/".join(str(p) for p in path)
        
        # Build URL
        url = f"{protocol}://{host}"
        if port:
            url += f":{port}"
        if path:
            url += f"/{path}"
        
        return self._substitute_variables(url)
    
    def _substitute_variables(self, text: str) -> str:
        """Substitute {{variable}} with actual values."""
        if not text:
            return text
        
        # Find all variables
        pattern = r'\{\{([^}]+)\}\}'
        
        def replacer(match):
            var_name = match.group(1)
            # Check collection variables
            if var_name in self.variables:
                return str(self.variables[var_name])
            # Return placeholder for undefined variables
            return f"{{{var_name}}}"
        
        return re.sub(pattern, replacer, text)
    
    def _extract_headers(self, headers: List[Dict]) -> Dict[str, str]:
        """Extract headers from request."""
        header_dict = {}
        for header in headers:
            if isinstance(header, dict):
                key = header.get("key", "")
                value = header.get("value", "")
                if key and not header.get("disabled", False):
                    header_dict[key] = self._substitute_variables(value)
        return header_dict
    
    def _extract_body(self, body: Dict) -> Dict[str, Any]:
        """Extract request body information."""
        mode = body.get("mode", "raw")
        body_info = {"mode": mode}
        
        if mode == "raw":
            body_info["content"] = self._substitute_variables(body.get("raw", ""))
            # Try to detect content type from options
            options = body.get("options", {})
            if "raw" in options:
                body_info["content_type"] = options["raw"].get("language", "text")
        
        elif mode == "urlencoded":
            body_info["content"] = self._extract_form_data(body.get("urlencoded", []))
            body_info["content_type"] = "application/x-www-form-urlencoded"
        
        elif mode == "formdata":
            body_info["content"] = self._extract_form_data(body.get("formdata", []))
            body_info["content_type"] = "multipart/form-data"
        
        elif mode == "file":
            body_info["file_path"] = body.get("file", {}).get("src", "")
        
        elif mode == "graphql":
            body_info["query"] = body.get("graphql", {}).get("query", "")
            body_info["variables"] = body.get("graphql", {}).get("variables", "")
        
        return body_info
    
    def _extract_form_data(self, data: List[Dict]) -> Dict[str, str]:
        """Extract form data fields."""
        form_dict = {}
        for field in data:
            if isinstance(field, dict) and not field.get("disabled", False):
                key = field.get("key", "")
                value = field.get("value", "")
                if key:
                    form_dict[key] = self._substitute_variables(value)
        return form_dict
    
    def _extract_query_params(self, params: List[Dict]) -> List[Dict[str, Any]]:
        """Extract query parameters."""
        query_params = []
        for param in params:
            if isinstance(param, dict) and not param.get("disabled", False):
                query_params.append({
                    "name": param.get("key", ""),
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
        
        # Look for {param} style (already handled by variable substitution)
        # but we still want to identify them as parameters
        for match in re.finditer(r'\{([^}]+)\}', url):
            param_name = match.group(1)
            # Skip if it's a variable reference
            if not param_name.startswith("{"):
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