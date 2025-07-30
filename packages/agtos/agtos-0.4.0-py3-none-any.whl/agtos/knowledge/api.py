"""API Knowledge Acquisition Module.

This module provides AI-First capabilities for discovering and understanding REST APIs
through multiple methods including OpenAPI specs, documentation parsing, and endpoint testing.

Key Features:
- Automatic OpenAPI/Swagger specification discovery
- Documentation parsing for API pattern extraction  
- Postman collection analysis
- API endpoint testing and validation
- Intelligent caching with TTL support

AI Context:
The APIKnowledge class is designed to help AI assistants understand how to interact
with REST APIs by automatically discovering endpoints, authentication methods, and
data schemas. It provides multiple discovery strategies to maximize the chances of
understanding an API even when formal specifications are not available.

Example Usage:
    >>> api_knowledge = APIKnowledge()
    >>> # Discover API from OpenAPI spec
    >>> knowledge = api_knowledge.discover_api_from_docs("https://api.example.com")
    >>> # Test specific endpoint
    >>> result = api_knowledge.test_api_endpoint("https://api.example.com/users")
"""
import requests
import json
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..knowledge_store import get_knowledge_store

logger = logging.getLogger(__name__)


class APIKnowledge:
    """Acquire knowledge about REST APIs through multiple discovery methods.
    
    This class provides comprehensive API discovery capabilities including:
    - OpenAPI/Swagger spec fetching and parsing
    - Documentation scraping and pattern extraction
    - Postman collection analysis
    - Live endpoint testing
    
    All discovered knowledge is cached with configurable TTL to improve performance
    and reduce redundant API calls.
    """
    
    def __init__(self):
        self.store = get_knowledge_store()
    
    def fetch_documentation(self, url: str) -> Optional[str]:
        """Fetch documentation content from URL.
        
        Args:
            url: URL to fetch documentation from
            
        Returns:
            Documentation content as string or None
        """
        try:
            headers = {
                "User-Agent": "agtOS/1.0 (API Discovery Bot)",
                "Accept": "text/html,application/json,text/plain"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to fetch documentation from {url}: {e}")
            return None
    
    def fetch_openapi_spec(self, url: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch OpenAPI/Swagger specification from URL.
        
        Attempts to discover OpenAPI specs at common endpoints. Supports both
        authenticated and unauthenticated APIs.
        
        Args:
            url: Base URL of the API
            api_key: Optional API key for authenticated endpoints
            
        Returns:
            Parsed OpenAPI specification dict or None if not found
        """
        # Common OpenAPI spec paths
        spec_paths = [
            "/openapi.json",
            "/swagger.json", 
            "/api/openapi.json",
            "/api/swagger.json",
            "/v1/openapi.json",
            "/v2/openapi.json",
            "/v3/openapi.json",
            "/docs/openapi.json",
            "/api-docs",
            "/api/docs"
        ]
        
        base_url = url.rstrip('/')
        
        headers = {"Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        for path in spec_paths:
            try:
                response = requests.get(
                    f"{base_url}{path}",
                    timeout=5,
                    headers=headers
                )
                if response.status_code == 200:
                    return response.json()
            except:
                continue
        
        return None
    
    def parse_openapi_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAPI spec to extract useful information.
        
        Extracts key API information including endpoints, authentication methods,
        and schemas from an OpenAPI specification.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Structured knowledge dict with endpoints, auth methods, etc.
        """
        # Build knowledge structure
        knowledge = self._extract_basic_info(spec)
        knowledge["base_url"] = self._extract_base_url(spec)
        knowledge["auth_methods"] = self._extract_auth_methods(spec)
        knowledge["endpoints"] = self._extract_endpoints(spec)
        
        return knowledge
    
    def _extract_basic_info(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic API information from spec.
        
        Args:
            spec: OpenAPI specification
            
        Returns:
            Dict with title, version, description
        """
        info = spec.get("info", {})
        return {
            "title": info.get("title", "Unknown API"),
            "version": info.get("version", ""),
            "description": info.get("description", ""),
            "base_url": "",
            "auth_methods": [],
            "endpoints": []
        }
    
    def _extract_base_url(self, spec: Dict[str, Any]) -> str:
        """Extract base URL from servers section.
        
        Args:
            spec: OpenAPI specification
            
        Returns:
            Base URL string
        """
        if "servers" in spec and spec["servers"]:
            return spec["servers"][0].get("url", "")
        return ""
    
    def _extract_auth_methods(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract authentication methods from spec.
        
        Args:
            spec: OpenAPI specification
            
        Returns:
            List of auth method definitions
        """
        auth_methods = []
        
        if "components" in spec and "securitySchemes" in spec["components"]:
            for name, scheme in spec["components"]["securitySchemes"].items():
                auth_method = self._parse_auth_scheme(name, scheme)
                if auth_method:
                    auth_methods.append(auth_method)
        
        return auth_methods
    
    def _parse_auth_scheme(self, name: str, scheme: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single authentication scheme.
        
        Args:
            name: Scheme name
            scheme: Scheme definition
            
        Returns:
            Auth method dict or None
        """
        auth_type = scheme.get("type", "")
        
        if auth_type == "apiKey":
            return {
                "type": "api_key",
                "name": name,
                "in": scheme.get("in", "header"),
                "key_name": scheme.get("name", "")
            }
        elif auth_type == "http":
            return {
                "type": "http",
                "scheme": scheme.get("scheme", "bearer")
            }
        elif auth_type == "oauth2":
            return {
                "type": "oauth2",
                "flows": list(scheme.get("flows", {}).keys())
            }
        
        return None
    
    def _extract_endpoints(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all endpoints from paths section.
        
        Args:
            spec: OpenAPI specification
            
        Returns:
            List of endpoint definitions
        """
        endpoints = []
        
        if "paths" in spec:
            for path, methods in spec["paths"].items():
                for method, details in methods.items():
                    if method in ["get", "post", "put", "patch", "delete"]:
                        endpoint = self._parse_endpoint_details(path, method, details)
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_endpoint_details(self, path: str, method: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Parse details for a single endpoint.
        
        Args:
            path: Endpoint path
            method: HTTP method
            details: Endpoint details from spec
            
        Returns:
            Endpoint definition dict
        """
        endpoint = {
            "path": path,
            "method": method.upper(),
            "summary": details.get("summary", ""),
            "description": details.get("description", ""),
            "operation_id": details.get("operationId", ""),
            "parameters": self._extract_endpoint_parameters(details),
            "request_body": self._extract_request_body(details),
            "responses": {}
        }
        
        return endpoint
    
    def _extract_endpoint_parameters(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameters for an endpoint.
        
        Args:
            details: Endpoint details
            
        Returns:
            List of parameter definitions
        """
        parameters = []
        
        if "parameters" in details:
            for param in details["parameters"]:
                parameters.append({
                    "name": param.get("name", ""),
                    "in": param.get("in", ""),
                    "required": param.get("required", False),
                    "description": param.get("description", ""),
                    "type": param.get("schema", {}).get("type", "string")
                })
        
        return parameters
    
    def _extract_request_body(self, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body schema for an endpoint.
        
        Args:
            details: Endpoint details
            
        Returns:
            Request body definition or None
        """
        if "requestBody" in details:
            content = details["requestBody"].get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                return {
                    "required": details["requestBody"].get("required", False),
                    "schema": schema
                }
        
        return None
    
    def discover_api_from_docs(self, url: str, docs_url: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Try to discover API information from documentation.
        
        Attempts multiple discovery strategies:
        1. Check cache for previously discovered knowledge
        2. Try to fetch OpenAPI specification
        3. Parse documentation page for API patterns
        
        Args:
            url: Base URL of the API
            docs_url: Optional documentation URL to parse
            use_cache: Whether to use cached results
            
        Returns:
            API knowledge dict with discovery method and extracted information
        """
        # Initialize knowledge structure
        knowledge = {
            "url": url,
            "discovered": False,
            "method": "none"
        }
        
        # Check cache first
        if use_cache:
            cached = self._check_api_cache(url)
            if cached:
                return cached
        
        # Try OpenAPI discovery
        openapi_knowledge = self._try_openapi_discovery(url)
        if openapi_knowledge:
            return openapi_knowledge
        
        # Try documentation parsing
        if docs_url:
            docs_knowledge = self._parse_documentation_page(docs_url, knowledge)
            if docs_knowledge["discovered"]:
                self._store_api_knowledge(url, docs_knowledge, "docs_parsing")
                return docs_knowledge
        
        return knowledge
    
    def _check_api_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if API knowledge exists in cache.
        
        Args:
            url: API base URL
            
        Returns:
            Cached knowledge dict or None
        """
        cached = self.store.retrieve("api", url)
        if cached:
            return cached["data"]
        return None
    
    def _try_openapi_discovery(self, url: str) -> Optional[Dict[str, Any]]:
        """Try to discover API via OpenAPI specification.
        
        Args:
            url: API base URL
            
        Returns:
            API knowledge dict if discovered, None otherwise
        """
        spec = self.fetch_openapi_spec(url)
        if spec:
            knowledge = {
                "url": url,
                "discovered": True,
                "method": "openapi"
            }
            knowledge.update(self.parse_openapi_spec(spec))
            
            # Store in cache
            self._store_api_knowledge(url, knowledge, "openapi_spec")
            return knowledge
        
        return None
    
    def _parse_documentation_page(self, docs_url: str, base_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Parse documentation page for API patterns.
        
        Args:
            docs_url: Documentation URL
            base_knowledge: Base knowledge dict to update
            
        Returns:
            Updated knowledge dict
        """
        knowledge = base_knowledge.copy()
        
        try:
            response = requests.get(docs_url, timeout=5)
            if response.status_code == 200:
                text = response.text
                
                # Extract API endpoints
                endpoints = self._extract_api_patterns(text)
                if endpoints:
                    knowledge["endpoints"] = list(set(endpoints))[:20]
                    knowledge["discovered"] = True
                    knowledge["method"] = "docs_parsing"
                
                # Check for authentication requirements
                if "api key" in text.lower() or "authorization" in text.lower():
                    knowledge["auth_required"] = True
        except Exception:
            # Silently ignore parsing errors
            pass
        
        return knowledge
    
    def _extract_api_patterns(self, text: str) -> List[str]:
        """Extract API endpoint patterns from text.
        
        Args:
            text: HTML or text content to parse
            
        Returns:
            List of discovered endpoint paths
        """
        endpoint_patterns = [
            r'(?:GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\{\}:-]+)',
            r'"(?:GET|POST|PUT|PATCH|DELETE)"\s*:\s*"(/[\w/\{\}:-]+)"',
            r'`(?:GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\{\}:-]+)`'
        ]
        
        endpoints = []
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, text)
            endpoints.extend(matches)
        
        return endpoints
    
    def _store_api_knowledge(self, url: str, knowledge: Dict[str, Any], source: str) -> None:
        """Store API knowledge in cache.
        
        Args:
            url: API base URL
            knowledge: Knowledge dict to store
            source: Discovery source (openapi_spec, docs_parsing)
        """
        self.store.store(
            type="api",
            name=url,
            data=knowledge,
            source=source,
            ttl_hours=168  # 1 week for API specs
        )
    
    def discover_api_from_package(self, package_name: str) -> Dict[str, Any]:
        """Discover API information from package documentation.
        
        Attempts to find API documentation from package registries like PyPI.
        
        Args:
            package_name: Name of the package to search
            
        Returns:
            Dict containing package info and discovered APIs
        """
        knowledge = {
            "package": package_name,
            "apis": [],
            "discovered": False
        }
        
        # Try to find package info from PyPI
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{package_name}/json",
                timeout=10
            )
            if response.status_code == 200:
                pkg_data = response.json()
                info = pkg_data.get("info", {})
                
                # Extract relevant information
                knowledge["description"] = info.get("summary", "")
                knowledge["version"] = info.get("version", "")
                knowledge["home_page"] = info.get("home_page", "")
                knowledge["docs_url"] = info.get("docs_url") or info.get("project_urls", {}).get("Documentation", "")
                
                # Look for API endpoints in description/docs
                if knowledge["docs_url"]:
                    api_info = self.discover_api_from_docs("", knowledge["docs_url"])
                    if api_info["discovered"]:
                        knowledge["apis"].append(api_info)
                        knowledge["discovered"] = True
        except:
            pass
        
        return knowledge
    
    def analyze_postman_collection(self, collection_path: Path) -> Dict[str, Any]:
        """Extract API knowledge from Postman collection.
        
        Parses Postman collection files to extract endpoint definitions,
        authentication methods, and environment variables.
        
        Args:
            collection_path: Path to Postman collection JSON file
            
        Returns:
            Structured API knowledge extracted from collection
        """
        with open(collection_path, 'r') as f:
            collection = json.load(f)
        
        knowledge = {
            "name": collection.get("info", {}).get("name", "Unknown API"),
            "description": collection.get("info", {}).get("description", ""),
            "endpoints": [],
            "auth_methods": [],
            "variables": {}
        }
        
        # Extract variables
        for var in collection.get("variable", []):
            knowledge["variables"][var["key"]] = var.get("value", "")
        
        # Extract auth
        if "auth" in collection:
            auth = collection["auth"]
            knowledge["auth_methods"].append({
                "type": auth.get("type", "unknown"),
                "details": auth
            })
        
        # Extract endpoints from items
        def extract_requests(items, parent_path=""):
            for item in items:
                if "request" in item:
                    request = item["request"]
                    endpoint = {
                        "name": item.get("name", ""),
                        "method": request.get("method", "GET"),
                        "url": request.get("url", {}).get("raw", ""),
                        "description": request.get("description", ""),
                        "headers": request.get("header", []),
                        "body": request.get("body", {})
                    }
                    knowledge["endpoints"].append(endpoint)
                
                # Recurse into folders
                if "item" in item:
                    extract_requests(item["item"], f"{parent_path}/{item.get('name', '')}")
        
        extract_requests(collection.get("item", []))
        
        return knowledge
    
    def test_api_endpoint(self, 
                         url: str, 
                         method: str = "GET",
                         headers: Optional[Dict[str, str]] = None,
                         timeout: int = 5) -> Dict[str, Any]:
        """Test an API endpoint to gather response information.
        
        Makes a live request to an API endpoint to validate accessibility
        and gather response metadata.
        
        AI_CONTEXT: Performs live API endpoint testing for discovery.
        Makes real HTTP requests to validate endpoints and capture metadata
        (status codes, headers, response samples). Handles failures gracefully.
        
        Args:
            url: Full URL of the endpoint to test
            method: HTTP method to use (default: GET)
            headers: Optional headers to include
            timeout: Request timeout in seconds
            
        Returns:
            Dict with endpoint test results including status, headers, and sample response
        """
        result = self._initialize_test_result(url, method)
        
        try:
            response = self._make_test_request(method, url, headers, timeout)
            
            if response is not None:
                self._process_test_response(response, result)
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _initialize_test_result(self, url: str, method: str) -> Dict[str, Any]:
        """Initialize the result dictionary for endpoint testing.
        
        Args:
            url: Endpoint URL
            method: HTTP method
            
        Returns:
            Initial result dictionary
        """
        return {
            "url": url,
            "method": method,
            "accessible": False,
            "status_code": None,
            "headers": {},
            "response_sample": None,
            "error": None
        }
    
    def _make_test_request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]], 
        timeout: int
    ) -> Optional[requests.Response]:
        """Make the HTTP request for testing.
        
        Args:
            method: HTTP method
            url: Endpoint URL
            headers: Optional request headers
            timeout: Request timeout
            
        Returns:
            Response object or None if request fails
        """
        return requests.request(
            method=method,
            url=url,
            headers=headers or {},
            timeout=timeout
        )
    
    def _process_test_response(
        self, 
        response: requests.Response, 
        result: Dict[str, Any]
    ) -> None:
        """Process the response and update result dictionary.
        
        Args:
            response: HTTP response object
            result: Result dictionary to update
        """
        result["accessible"] = True
        result["status_code"] = response.status_code
        result["headers"] = dict(response.headers)
        
        # Extract JSON sample if applicable
        result["response_sample"] = self._extract_json_sample(response)
    
    def _extract_json_sample(self, response: requests.Response) -> Optional[Any]:
        """Extract JSON sample from response if applicable.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed JSON data or None
        """
        if "application/json" in response.headers.get("Content-Type", ""):
            try:
                return response.json()
            except Exception:
                pass
        return None