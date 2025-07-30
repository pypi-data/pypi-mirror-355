"""API Discovery Tools for agtOS.

These tools are designed to be called by agents (like Claude) after they find
API documentation through web search. The tools specialize in parsing various
documentation formats and extracting actionable API specifications.
"""

import re
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urljoin

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
from agtos.user_tools.tool_creator.parsers import PostmanParser, GraphQLParser, InsomniaParser, HARParser

logger = logging.getLogger(__name__)


def discover_api_from_url(url: str, focus: Optional[str] = None) -> Dict[str, Any]:
    """Discover and analyze API from documentation URL or local file.
    
    This is designed to be called after an agent finds API documentation.
    It will attempt to extract API specifications in multiple ways:
    1. Check for OpenAPI/Swagger spec (from URL or local file)
    2. Check for Postman collection format
    3. Parse HTML documentation for patterns
    4. Extract from README or markdown
    5. Look for example code
    
    Args:
        url: URL of API documentation or file path (supports:
             - file:///path/to/openapi.json
             - /path/to/openapi.json
             - /path/to/collection.postman_collection.json)
        focus: Optional focus area (e.g., "weather endpoints", "user management")
        
    Returns:
        Detailed API analysis with endpoints, auth, and confidence scores
    """
    try:
        api_knowledge = APIKnowledge()
        
        # Check if this is a file path
        is_file_path = (
            url.startswith('file://') or 
            url.startswith('/') or 
            url.startswith('./') or
            url.startswith('../') or
            ':' in url and '://' not in url  # Windows path like C:\path\to\file
        )
        
        if is_file_path:
            # Handle file path
            import os
            from pathlib import Path
            
            # Clean up file path
            if url.startswith('file://'):
                file_path = url[7:]  # Remove file:// prefix
            else:
                file_path = url
            
            file_path = os.path.expanduser(file_path)  # Expand ~ to home directory
            file_path = os.path.abspath(file_path)  # Convert to absolute path
            
            results = {
                "success": False,
                "base_url": "local_file",
                "documentation_url": file_path,
                "discovery_methods": [],
                "endpoints": [],
                "authentication": None,
                "confidence_score": 0,
                "suggested_tools": []
            }
            
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"❌ File not found: {file_path}"
                }
            
            # Read and parse the file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to parse as JSON (OpenAPI/Swagger or Postman)
                try:
                    json_content = json.loads(content)
                    
                    # Check if it's a Postman collection
                    if "info" in json_content and "item" in json_content and "schema.getpostman.com" in json_content.get("info", {}).get("schema", ""):
                        # It's a Postman collection
                        results["discovery_methods"].append("postman_collection_file")
                        parser = PostmanParser()
                        parsed = parser.parse(content)
                        
                        if parsed.get("success"):
                            results["base_url"] = parsed.get("base_url", "https://api.example.com")
                            results["endpoints"] = _convert_postman_endpoints(parsed.get("endpoints", []))
                            results["authentication"] = parsed.get("authentication")
                            results["confidence_score"] = 0.90  # High confidence with Postman collections
                            results["postman_version"] = parsed.get("version", "unknown")
                            results["variables"] = parsed.get("variables", {})
                            results["statistics"] = parsed.get("statistics", {})  # Include statistics
                            
                            # Generate tool suggestions
                            results["suggested_tools"] = _suggest_tools_from_endpoints(
                                results["endpoints"],
                                results["base_url"],
                                focus
                            )
                            
                            results["success"] = True
                            results["message"] = f"✅ Loaded Postman collection! Discovered {len(results['endpoints'])} endpoints."
                        else:
                            results["message"] = f"❌ Failed to parse Postman collection: {parsed.get('error', 'Unknown error')}"
                    
                    # Check if it's an Insomnia collection
                    elif isinstance(json_content, list) and any(
                        isinstance(item, dict) and item.get("_type") in ["workspace", "request", "environment"]
                        for item in json_content
                    ):
                        # It's an Insomnia collection
                        results["discovery_methods"].append("insomnia_collection_file")
                        parser = InsomniaParser()
                        parsed = parser.parse(content)
                        
                        if parsed.get("success"):
                            results["base_url"] = parsed.get("base_url", "https://api.example.com")
                            results["endpoints"] = _convert_insomnia_endpoints(parsed.get("endpoints", []))
                            results["authentication"] = parsed.get("authentication")
                            results["confidence_score"] = 0.90  # High confidence with Insomnia collections
                            results["insomnia_version"] = parsed.get("version", "v4")
                            results["variables"] = parsed.get("variables", {})
                            results["statistics"] = parsed.get("statistics", {})  # Include statistics
                            
                            # Generate tool suggestions
                            results["suggested_tools"] = _suggest_tools_from_endpoints(
                                results["endpoints"],
                                results["base_url"],
                                focus
                            )
                            
                            results["success"] = True
                            results["message"] = f"✅ Loaded Insomnia collection! Discovered {len(results['endpoints'])} endpoints."
                        else:
                            results["message"] = f"❌ Failed to parse Insomnia collection: {parsed.get('error', 'Unknown error')}"
                    
                    # Check if it's a HAR file
                    elif "log" in json_content and "entries" in json_content.get("log", {}):
                        # It's a HAR file
                        results["discovery_methods"].append("har_file")
                        parser = HARParser()
                        parsed = parser.parse(content)
                        
                        if parsed.get("success"):
                            results["base_url"] = parsed.get("base_url", "https://api.example.com")
                            results["endpoints"] = _convert_har_endpoints(parsed.get("endpoints", []))
                            results["authentication"] = parsed.get("authentication")
                            results["confidence_score"] = 0.85  # Good confidence with HAR files
                            results["har_version"] = parsed.get("version", "1.2")
                            results["statistics"] = parsed.get("statistics", {})
                            results["creator"] = parsed.get("creator", "Unknown")
                            
                            # Generate tool suggestions
                            results["suggested_tools"] = _suggest_tools_from_endpoints(
                                results["endpoints"],
                                results["base_url"],
                                focus
                            )
                            
                            results["success"] = True
                            results["message"] = f"✅ Loaded HAR file! Discovered {len(results['endpoints'])} unique API endpoints from {results['statistics'].get('api_entries', 0)} API calls."
                        else:
                            results["message"] = f"❌ Failed to parse HAR file: {parsed.get('error', 'Unknown error')}"
                    
                    # Check if it's a GraphQL introspection result
                    elif "__schema" in json_content.get("data", {}):
                        # It's a GraphQL introspection result
                        results["discovery_methods"].append("graphql_introspection_file")
                        parser = GraphQLParser()
                        # Pass the schema data directly
                        parsed = parser._parse_introspection(
                            json_content["data"]["__schema"], 
                            "https://api.example.com/graphql"
                        )
                        
                        if parsed.get("success"):
                            results["base_url"] = parsed.get("base_url", "https://api.example.com/graphql")
                            results["endpoints"] = _convert_graphql_endpoints(parsed.get("endpoints", []))
                            results["authentication"] = None  # GraphQL auth is typically in headers
                            results["confidence_score"] = 0.95  # High confidence with introspection
                            results["graphql_types"] = parsed.get("types", {})
                            
                            # Generate tool suggestions
                            results["suggested_tools"] = parsed.get("suggested_tools", [])
                            
                            results["success"] = True
                            results["message"] = f"✅ Loaded GraphQL schema! Found {len(results['endpoints'])} operations."
                        else:
                            results["message"] = f"❌ Failed to parse GraphQL schema: {parsed.get('error', 'Unknown error')}"
                    
                    # Verify it's actually an OpenAPI/Swagger spec
                    elif any(key in json_content for key in ['openapi', 'swagger', 'paths']):
                        results["discovery_methods"].append("openapi_spec_file")
                        parsed = api_knowledge.parse_openapi_spec(json_content)
                        
                        # Extract base URL from spec if available
                        if parsed.get("base_url"):
                            results["base_url"] = parsed["base_url"]
                        elif "servers" in json_content and json_content["servers"]:
                            results["base_url"] = json_content["servers"][0].get("url", "https://api.example.com")
                        else:
                            results["base_url"] = "https://api.example.com"
                        
                        results["endpoints"] = parsed.get("endpoints", [])
                        results["authentication"] = parsed.get("auth_methods", [])
                        results["confidence_score"] = 0.95  # High confidence with OpenAPI
                        results["openapi_version"] = json_content.get("openapi", json_content.get("swagger", "unknown"))
                        
                        # Generate tool suggestions
                        results["suggested_tools"] = _suggest_tools_from_endpoints(
                            parsed.get("endpoints", []), 
                            results["base_url"],
                            focus
                        )
                        
                        results["success"] = True
                        results["message"] = f"✅ Loaded OpenAPI spec from file! Discovered {len(results['endpoints'])} endpoints."
                    else:
                        # Not an OpenAPI spec, treat as documentation
                        results["discovery_methods"].append("documentation_file")
                        extracted = _extract_api_patterns_from_docs(content, "https://api.example.com")
                        
                        results["endpoints"] = extracted["endpoints"]
                        results["authentication"] = extracted["authentication"]
                        results["confidence_score"] = extracted["confidence"]
                        results["base_url"] = "https://api.example.com"  # Default for file-based docs
                        
                        if results["endpoints"]:
                            results["success"] = True
                            results["message"] = f"📄 Extracted {len(results['endpoints'])} endpoints from file."
                        else:
                            results["message"] = "⚠️ Could not extract API patterns from file."
                            
                except json.JSONDecodeError:
                    # Not JSON, might be GraphQL SDL or documentation text
                    # Check if it's GraphQL SDL
                    if any(keyword in content for keyword in ['type Query', 'type Mutation', 'schema {', 'type ', 'input ', 'enum ']):
                        results["discovery_methods"].append("graphql_sdl_file")
                        parser = GraphQLParser()
                        parsed = parser.parse(content, is_url=False)
                        
                        if parsed.get("success"):
                            results["base_url"] = "https://api.example.com/graphql"
                            results["endpoints"] = _convert_graphql_endpoints(parsed.get("endpoints", []))
                            results["authentication"] = None
                            results["confidence_score"] = 0.90
                            results["graphql_types"] = parsed.get("types", {})
                            
                            # Generate tool suggestions
                            results["suggested_tools"] = _suggest_graphql_tools(parsed.get("endpoints", []))
                            
                            results["success"] = True
                            results["message"] = f"✅ Parsed GraphQL SDL! Found {len(results['endpoints'])} operations."
                        else:
                            # Not GraphQL SDL, treat as documentation text
                            results["discovery_methods"].append("documentation_file")
                            extracted = _extract_api_patterns_from_docs(content, "https://api.example.com")
                    
                            results["endpoints"] = extracted["endpoints"]
                            results["authentication"] = extracted["authentication"]
                            results["confidence_score"] = extracted["confidence"]
                            results["base_url"] = "https://api.example.com"  # Default for file-based docs
                            
                            # Generate tool suggestions
                            results["suggested_tools"] = _suggest_tools_from_endpoints(
                                extracted["endpoints"],
                                results["base_url"],
                                focus
                            )
                            
                            if results["endpoints"]:
                                results["success"] = True
                                results["message"] = f"📄 Extracted {len(results['endpoints'])} endpoints from documentation file."
                            else:
                                results["message"] = "⚠️ Found documentation but couldn't extract clear API patterns."
                        
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"❌ Error reading file: {str(e)}"
                }
                
        else:
            # Handle URL (existing logic)
            base_url = '/'.join(url.split('/')[:3])
            
            results = {
                "success": False,
                "base_url": base_url,
                "documentation_url": url,
                "discovery_methods": [],
                "endpoints": [],
                "authentication": None,
                "confidence_score": 0,
                "suggested_tools": []
            }
            
            # Method 1: Try to find OpenAPI/Swagger spec
            logger.info(f"Attempting OpenAPI discovery for {base_url}")
            openapi_spec = api_knowledge.fetch_openapi_spec(base_url)
            
            if openapi_spec:
                results["discovery_methods"].append("openapi_spec")
                parsed = api_knowledge.parse_openapi_spec(openapi_spec)
                
                results["endpoints"] = parsed.get("endpoints", [])
                results["authentication"] = parsed.get("auth_methods", [])
                results["confidence_score"] = 0.95  # High confidence with OpenAPI
                results["openapi_version"] = openapi_spec.get("openapi", openapi_spec.get("swagger", "unknown"))
                
                # Generate tool suggestions
                results["suggested_tools"] = _suggest_tools_from_endpoints(
                    parsed.get("endpoints", []), 
                    base_url,
                    focus
                )
                
                results["success"] = True
                results["message"] = f"✅ Found OpenAPI spec! Discovered {len(results['endpoints'])} endpoints."
                
            # Method 2: Check if it's a GraphQL endpoint
            elif url.endswith('/graphql') or '/graphql' in url:
                logger.info(f"Detected potential GraphQL endpoint: {url}")
                parser = GraphQLParser()
                
                # Try introspection
                parsed = parser.parse(url, is_url=True)
                
                if parsed.get("success"):
                    results["discovery_methods"].append("graphql_introspection")
                    results["endpoints"] = _convert_graphql_endpoints(parsed.get("endpoints", []))
                    results["authentication"] = None  # GraphQL typically uses header auth
                    results["confidence_score"] = 0.95
                    results["graphql_types"] = parsed.get("types", {})
                    results["suggested_tools"] = parsed.get("suggested_tools", [])
                    
                    results["success"] = True
                    results["message"] = f"✅ GraphQL endpoint discovered! Found {parsed['statistics']['queries']} queries, {parsed['statistics']['mutations']} mutations."
                elif parsed.get("introspection_disabled"):
                    results["message"] = "⚠️ GraphQL endpoint found but introspection is disabled. Provide schema file instead."
                    results["recommendations"] = [
                        "📝 Download the GraphQL schema SDL file from your API provider",
                        "🔍 Look for developer documentation with example queries",
                        "📧 Contact the API provider for schema access"
                    ]
                else:
                    results["message"] = f"❌ GraphQL introspection failed: {parsed.get('error', 'Unknown error')}"
            
            else:
                # Method 3: Try to parse HTML documentation
                logger.info(f"No OpenAPI spec found, attempting HTML parsing for {url}")
                doc_content = api_knowledge.fetch_documentation(url)
                
                if doc_content:
                    results["discovery_methods"].append("documentation_parsing")
                    
                    # Extract API patterns from documentation
                    extracted = _extract_api_patterns_from_docs(doc_content, base_url)
                    
                    results["endpoints"] = extracted["endpoints"]
                    results["authentication"] = extracted["authentication"]
                    results["confidence_score"] = extracted["confidence"]
                    
                    # Generate tool suggestions
                    results["suggested_tools"] = _suggest_tools_from_endpoints(
                        extracted["endpoints"],
                        base_url,
                        focus
                    )
                    
                    if results["endpoints"]:
                        results["success"] = True
                        results["message"] = f"📄 Extracted {len(results['endpoints'])} endpoints from documentation."
                    else:
                        results["message"] = "⚠️ Found documentation but couldn't extract clear API patterns."
                else:
                    results["message"] = "❌ Could not fetch documentation content."
        
        # Add recommendations (only if not already set)
        if "recommendations" not in results:
            results["recommendations"] = _generate_recommendations(results)
        
        return results
        
    except Exception as e:
        import traceback
        logger.error(f"API discovery error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Discovery failed: {str(e)}"
        }


def _convert_postman_endpoints(postman_endpoints: List[Dict]) -> List[Dict[str, Any]]:
    """Convert Postman endpoints to our standard format."""
    converted = []
    
    for ep in postman_endpoints:
        endpoint = {
            "url": ep.get("url", ""),
            "method": ep.get("method", "GET"),
            "description": ep.get("description", ep.get("name", "")),
            "parameters": []
        }
        
        # Add path parameters
        if "path_params" in ep:
            for param in ep["path_params"]:
                endpoint["parameters"].append({
                    "name": param.get("name", ""),
                    "in": "path",
                    "required": True,
                    "type": "string",
                    "description": param.get("description", "")
                })
        
        # Add query parameters  
        if "query_params" in ep:
            for param in ep["query_params"]:
                endpoint["parameters"].append({
                    "name": param.get("name", ""),
                    "in": "query",
                    "required": False,
                    "type": "string",
                    "description": param.get("description", ""),
                    "default": param.get("value", "")
                })
        
        # Add headers as parameters
        if "headers" in ep:
            for key, value in ep["headers"].items():
                if key.lower() not in ["content-type", "accept", "authorization"]:
                    endpoint["parameters"].append({
                        "name": key,
                        "in": "header",
                        "required": False,
                        "type": "string",
                        "default": value
                    })
        
        # Add body schema if present
        if "body" in ep:
            body = ep["body"]
            if body.get("mode") == "raw" and body.get("content"):
                endpoint["request_body"] = {
                    "content_type": body.get("content_type", "application/json"),
                    "example": body.get("content", "")
                }
            elif body.get("mode") in ["urlencoded", "formdata"] and body.get("content"):
                endpoint["request_body"] = {
                    "content_type": body.get("content_type", "application/x-www-form-urlencoded"),
                    "properties": body.get("content", {})
                }
        
        # Add authentication info
        if "authentication" in ep and ep["authentication"]:
            endpoint["security"] = [ep["authentication"]]
        
        # Add examples if available
        if "examples" in ep:
            endpoint["examples"] = ep["examples"]
        
        converted.append(endpoint)
    
    return converted


def _convert_insomnia_endpoints(insomnia_endpoints: List[Dict]) -> List[Dict[str, Any]]:
    """Convert Insomnia endpoints to our standard format."""
    converted = []
    
    for ep in insomnia_endpoints:
        endpoint = {
            "url": ep.get("url", ""),
            "method": ep.get("method", "GET"),
            "description": ep.get("description", ep.get("name", "")),
            "parameters": []
        }
        
        # Add path parameters
        if "path_params" in ep:
            for param in ep["path_params"]:
                endpoint["parameters"].append({
                    "name": param.get("name", ""),
                    "in": "path",
                    "required": True,
                    "type": "string",
                    "description": param.get("description", "")
                })
        
        # Add query parameters  
        if "query_params" in ep:
            for param in ep["query_params"]:
                endpoint["parameters"].append({
                    "name": param.get("name", ""),
                    "in": "query",
                    "required": False,
                    "type": "string",
                    "description": param.get("description", ""),
                    "default": param.get("value", "")
                })
        
        # Add headers as parameters
        if "headers" in ep:
            for key, value in ep["headers"].items():
                if key.lower() not in ["content-type", "accept", "authorization"]:
                    endpoint["parameters"].append({
                        "name": key,
                        "in": "header",
                        "required": False,
                        "type": "string",
                        "default": value
                    })
        
        # Add body schema if present
        if "body" in ep:
            body = ep["body"]
            if body.get("mode") == "raw" and body.get("content"):
                endpoint["request_body"] = {
                    "content_type": body.get("content_type", "application/json"),
                    "example": body.get("content", "")
                }
            elif body.get("mode") in ["urlencoded", "formdata"] and body.get("content"):
                endpoint["request_body"] = {
                    "content_type": body.get("content_type", "application/x-www-form-urlencoded"),
                    "properties": body.get("content", {})
                }
            elif body.get("mode") == "graphql" and body.get("query"):
                endpoint["request_body"] = {
                    "content_type": "application/graphql",
                    "query": body.get("query", "")
                }
        
        # Add authentication info
        if "authentication" in ep and ep["authentication"]:
            endpoint["security"] = [ep["authentication"]]
        
        # Add Insomnia-specific metadata
        if "folder_path" in ep and ep["folder_path"]:
            endpoint["tags"] = [ep["folder_path"]]
        
        converted.append(endpoint)
    
    return converted


def _convert_har_endpoints(har_endpoints: List[Dict]) -> List[Dict[str, Any]]:
    """Convert HAR endpoints to our standard format."""
    converted = []
    
    for ep in har_endpoints:
        endpoint = {
            "url": ep.get("url", ""),
            "method": ep.get("method", "GET"),
            "description": ep.get("description", ""),
            "parameters": []
        }
        
        # Add path parameters
        if "path_params" in ep:
            for param in ep["path_params"]:
                endpoint["parameters"].append({
                    "name": param.get("name", ""),
                    "in": "path",
                    "required": True,
                    "type": "string",
                    "description": param.get("description", "")
                })
        
        # Add query parameters  
        if "query_params" in ep:
            for param in ep["query_params"]:
                endpoint["parameters"].append({
                    "name": param.get("name", ""),
                    "in": "query",
                    "required": param.get("required", False),
                    "type": "string",
                    "description": param.get("description", ""),
                    "values": param.get("values", [])  # HAR parser provides example values
                })
        
        # Add headers as parameters (excluding auth headers)
        if "headers" in ep:
            for key, value in ep["headers"].items():
                if key.lower() not in ["content-type", "accept", "authorization"]:
                    endpoint["parameters"].append({
                        "name": key,
                        "in": "header",
                        "required": False,
                        "type": "string",
                        "default": value
                    })
        
        # Add body schema if present
        if "body" in ep and ep["body"]:
            body = ep["body"]
            endpoint["request_body"] = {
                "content_type": body.get("mimeType", "application/json"),
                "schema": body.get("properties", {}),
                "examples": body.get("examples", [])
            }
        
        # Add authentication info
        if "authentication" in ep and ep["authentication"]:
            endpoint["security"] = [ep["authentication"]]
        
        # Add response examples
        if "examples" in ep and ep["examples"]:
            endpoint["examples"] = ep["examples"]
            
        # Add timing information (unique to HAR)
        if "average_response_time" in ep.get("examples", {}):
            endpoint["performance"] = {
                "average_response_time": ep["examples"]["average_response_time"]
            }
        
        converted.append(endpoint)
    
    return converted


def _extract_api_patterns_from_docs(content: str, base_url: str) -> Dict[str, Any]:
    """Extract API patterns from HTML/text documentation.
    
    Looks for:
    - Code blocks with curl examples
    - URL patterns like /api/v1/resource
    - HTTP method mentions (GET, POST, etc.)
    - Parameter documentation
    - Authentication headers
    """
    extracted = {
        "endpoints": [],
        "authentication": None,
        "confidence": 0
    }
    
    # Look for code blocks (markdown or HTML)
    code_blocks = re.findall(r'```[\s\S]*?```|<code>[\s\S]*?</code>|<pre>[\s\S]*?</pre>', content, re.IGNORECASE)
    
    endpoints_found = {}
    auth_methods = set()
    
    for block in code_blocks:
        # Clean up the block
        block_clean = re.sub(r'```|</?code>|</?pre>', '', block)
        
        # Look for curl commands
        curl_match = re.search(r'curl\s+(?:-[A-Z]\s+\w+\s+)*([\'"]?)([^\'"\s]+)\1', block_clean)
        if curl_match:
            url_part = curl_match.group(2)
            
            # Extract method
            method_match = re.search(r'-X\s+(\w+)', block_clean)
            method = method_match.group(1) if method_match else "GET"
            
            # Build full URL
            if url_part.startswith('http'):
                endpoint_url = url_part
            elif url_part.startswith('/'):
                endpoint_url = base_url + url_part
            else:
                endpoint_url = urljoin(base_url + '/', url_part)
            
            # Extract headers for auth
            header_matches = re.findall(r'-H\s+[\'"]([^:]+):\s*([^\'"]*)[\'"]]', block_clean)
            for header_name, header_value in header_matches:
                if 'authorization' in header_name.lower():
                    if 'bearer' in header_value.lower():
                        auth_methods.add('bearer')
                    elif 'basic' in header_value.lower():
                        auth_methods.add('basic')
                elif 'api-key' in header_name.lower() or 'x-api-key' in header_name.lower():
                    auth_methods.add('api_key')
            
            # Extract path parameters
            path_params = re.findall(r'\{([^}]+)\}|:(\w+)', url_part)
            parameters = []
            for param in path_params:
                param_name = param[0] or param[1]
                parameters.append({
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "type": "string"
                })
            
            # Store endpoint
            endpoint_key = f"{method} {urlparse(endpoint_url).path}"
            if endpoint_key not in endpoints_found:
                endpoints_found[endpoint_key] = {
                    "url": endpoint_url,
                    "method": method,
                    "parameters": parameters,
                    "examples": [block_clean]
                }
            else:
                endpoints_found[endpoint_key]["examples"].append(block_clean)
    
    # Also look for endpoint patterns in text
    # Pattern: GET /api/v1/users
    endpoint_patterns = re.findall(r'\b(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)', content)
    for method, path in endpoint_patterns:
        endpoint_key = f"{method} {path}"
        if endpoint_key not in endpoints_found:
            endpoints_found[endpoint_key] = {
                "url": urljoin(base_url + '/', path.lstrip('/')),
                "method": method,
                "parameters": _extract_path_params(path),
                "examples": []
            }
    
    # Convert to endpoint list
    extracted["endpoints"] = list(endpoints_found.values())
    
    # Determine authentication
    if 'bearer' in auth_methods:
        extracted["authentication"] = {
            "type": "bearer",
            "description": "Bearer token authentication"
        }
    elif 'api_key' in auth_methods:
        extracted["authentication"] = {
            "type": "api_key",
            "description": "API key authentication"
        }
    elif 'basic' in auth_methods:
        extracted["authentication"] = {
            "type": "basic",
            "description": "Basic authentication"
        }
    
    # Calculate confidence score
    confidence = 0
    if extracted["endpoints"]:
        confidence += 0.3
    if len(extracted["endpoints"]) > 3:
        confidence += 0.2
    if any(ep.get("examples") for ep in extracted["endpoints"]):
        confidence += 0.3
    if extracted["authentication"]:
        confidence += 0.2
    
    extracted["confidence"] = min(confidence, 0.85)  # Cap at 0.85 since it's not OpenAPI
    
    return extracted


def _extract_path_params(path: str) -> List[Dict[str, Any]]:
    """Extract parameters from URL path."""
    params = []
    
    # {param} style
    for match in re.finditer(r'\{([^}]+)\}', path):
        params.append({
            "name": match.group(1),
            "in": "path",
            "required": True,
            "type": "string"
        })
    
    # :param style
    for match in re.finditer(r':(\w+)', path):
        params.append({
            "name": match.group(1),
            "in": "path", 
            "required": True,
            "type": "string"
        })
    
    return params


def _suggest_tools_from_endpoints(endpoints: List[Dict], base_url: str, focus: Optional[str]) -> List[Dict[str, Any]]:
    """Generate tool suggestions from discovered endpoints."""
    suggestions = []
    
    # Group endpoints by resource
    resource_groups = {}
    for endpoint in endpoints:
        # Handle both "url" (from doc parsing) and "path" (from OpenAPI)
        endpoint_path = endpoint.get("path", "")
        if not endpoint_path and "url" in endpoint:
            endpoint_path = urlparse(endpoint.get("url", "")).path
        
        # Extract resource name (e.g., /api/v1/users -> users)
        parts = [p for p in endpoint_path.split('/') if p and not p.startswith('v')]
        resource = parts[0] if parts else "api"
        
        if resource not in resource_groups:
            resource_groups[resource] = []
        resource_groups[resource].append(endpoint)
    
    # Create suggestions for each resource group
    for resource, group_endpoints in resource_groups.items():
        # Skip if not relevant to focus
        if focus and focus.lower() not in resource.lower():
            continue
        
        methods = {ep.get("method", "GET") for ep in group_endpoints}
        
        suggestion = {
            "tool_name": f"{urlparse(base_url).netloc.replace('.', '_')}_{resource}",
            "description": f"Interact with {resource} endpoints",
            "endpoints": len(group_endpoints),
            "methods": list(methods),
            "sample_endpoint": group_endpoints[0] if group_endpoints else None
        }
        
        suggestions.append(suggestion)
    
    return suggestions[:5]  # Limit to top 5 suggestions


def _generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on discovery results."""
    recommendations = []
    
    if results.get("success"):
        if results.get("confidence_score", 0) > 0.9:
            recommendations.append("✅ High confidence discovery - tools can be created automatically")
        else:
            recommendations.append("⚠️ Medium confidence - review extracted endpoints before creating tools")
        
        if results.get("authentication"):
            # Handle both dict (from doc parsing) and list (from OpenAPI)
            auth = results["authentication"]
            if isinstance(auth, list) and auth:
                # Get auth types from list
                auth_types = [a.get("type", "unknown") for a in auth]
                auth_type = auth_types[0] if auth_types else "unknown"
            elif isinstance(auth, dict):
                auth_type = auth.get("type", "unknown")
            else:
                auth_type = "unknown"
            recommendations.append(f"🔐 Prepare {auth_type} credentials before creating tools")
        
        if results.get("suggested_tools"):
            recommendations.append(f"🛠️ Consider creating {len(results['suggested_tools'])} specialized tools")
    else:
        recommendations.append("❌ Automatic discovery failed - try providing specific endpoint examples")
        recommendations.append("💡 Look for API reference or developer documentation pages")
    
    return recommendations


def create_tool_from_discovery(
    discovery_results: Dict[str, Any],
    tool_name: str,
    endpoints_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a tool from discovery results.
    
    Args:
        discovery_results: Results from discover_api_from_url
        tool_name: Name for the new tool
        endpoints_filter: Optional list of endpoint patterns to include
        
    Returns:
        Tool creation result
    """
    if not discovery_results.get("success"):
        return {
            "success": False,
            "message": "Cannot create tool from failed discovery"
        }
    
    # Filter endpoints if requested
    endpoints = discovery_results.get("endpoints", [])
    if endpoints_filter:
        filtered = []
        for endpoint in endpoints:
            # Handle both "url" (from doc parsing) and "path" (from OpenAPI)
            if "path" in endpoint:
                path = endpoint["path"]
            elif "url" in endpoint:
                path = urlparse(endpoint["url"]).path
            else:
                continue
            
            if any(pattern in path for pattern in endpoints_filter):
                filtered.append(endpoint)
        endpoints = filtered
    
    if not endpoints:
        return {
            "success": False,
            "message": "No endpoints match the filter criteria"
        }
    
    # Build natural language description
    base_url = discovery_results.get("base_url", "")
    methods = {ep.get("method", "GET") for ep in endpoints}
    
    description = f"Access {base_url} API with {', '.join(methods)} methods"
    if endpoints_filter:
        description += f" for {', '.join(endpoints_filter)}"
    
    # Add authentication info
    if discovery_results.get("authentication"):
        # Handle both dict (from doc parsing) and list (from OpenAPI)
        auth = discovery_results["authentication"]
        if isinstance(auth, list) and auth:
            auth_type = auth[0].get("type", "unknown")
        elif isinstance(auth, dict):
            auth_type = auth.get("type", "unknown")
        else:
            auth_type = "unknown"
        description += f" using {auth_type} authentication"
    
    # Check if this is GraphQL (all endpoints are POST to /graphql)
    is_graphql = all(
        ep.get("method") == "POST" and 
        (ep.get("path", "").startswith("/graphql") or ep.get("operation_type") in ["query", "mutation", "subscription"])
        for ep in endpoints
    )
    
    if is_graphql:
        # Use GraphQL-specific generator
        from agtos.user_tools.tool_creator.generators import GraphQLToolGenerator
        
        generator = GraphQLToolGenerator()
        result = generator.generate_graphql_tool(
            tool_name=tool_name,
            endpoint_url=base_url,
            operations=endpoints,
            auth_config=discovery_results.get("authentication")
        )
        
        # Save the generated tool
        import os
        from pathlib import Path
        
        # Ensure user_tools directory exists
        user_tools_dir = Path.home() / ".agtos" / "user_tools"
        user_tools_dir.mkdir(parents=True, exist_ok=True)
        
        # Write tool file
        tool_file = user_tools_dir / f"{tool_name}.py"
        tool_file.write_text(result["tool_code"])
        
        return {
            "success": True,
            "message": f"✅ Created GraphQL tool '{tool_name}' with {len(endpoints)} operations!",
            "file_path": str(tool_file),
            "operations": [ep.get("name", ep.get("path", "unknown")) for ep in endpoints]
        }
    else:
        # Use standard REST API tool creation
        from agtos.plugins.tool_creator import create_tool_from_description
        
        # For now, we'll just pass the description and name
        # TODO: Consider enhancing create_tool_from_description to accept metadata
        return create_tool_from_description(
            description=description,
            name=tool_name
        )


def _convert_graphql_endpoints(graphql_operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert GraphQL operations to our standard endpoint format."""
    converted = []
    
    for op in graphql_operations:
        endpoint = {
            "name": op["name"],  # Keep the original operation name
            "path": f"/graphql#{op['name']}",  # Use fragment to distinguish operations
            "method": "POST",  # GraphQL always uses POST
            "description": op.get("description", op.get("name", "")),
            "operation_type": op.get("type", "query"),  # query, mutation, subscription
            "parameters": [],
            "graphql_template": op.get("query_template", ""),
            "args": op.get("args", []),  # Keep original args for generator
            "return_type": op.get("return_type", "Unknown")
        }
        
        # Convert GraphQL args to parameters
        for arg in op.get("args", []):
            param = {
                "name": arg["name"],
                "in": "variable",  # GraphQL variables
                "required": arg.get("required", False),
                "type": arg.get("type", "string"),
                "description": arg.get("description", "")
            }
            if "default_value" in arg and arg["default_value"] is not None:
                param["default"] = arg["default_value"]
            endpoint["parameters"].append(param)
        
        # Add return type info
        endpoint["return_type"] = op.get("return_type", "Unknown")
        
        converted.append(endpoint)
    
    return converted


def _suggest_graphql_tools(operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate tool suggestions for GraphQL operations."""
    # Group by operation type
    queries = [op for op in operations if op.get("type") == "query"]
    mutations = [op for op in operations if op.get("type") == "mutation"]
    subscriptions = [op for op in operations if op.get("type") == "subscription"]
    
    suggestions = []
    
    # Suggest a comprehensive GraphQL tool
    if len(operations) > 5:
        suggestions.append({
            "tool_name": "graphql_api",
            "description": "Comprehensive GraphQL API client",
            "operations_count": len(operations),
            "operation_breakdown": {
                "queries": len(queries),
                "mutations": len(mutations),
                "subscriptions": len(subscriptions)
            }
        })
    
    # Suggest resource-specific tools
    resource_ops = {}
    for op in operations:
        # Extract resource from operation name
        name = op.get("name", "")
        # Common patterns: getUser, users, createPost, etc.
        resource = None
        if name.startswith(("get", "list", "create", "update", "delete")):
            # Remove verb prefix
            resource = name[3:] if name.startswith("get") else name[4:] if name.startswith("list") else name[6:]
            resource = resource[0].lower() + resource[1:] if resource else None
        elif name.endswith("s"):
            resource = name[:-1]
        else:
            resource = name
        
        if resource:
            if resource not in resource_ops:
                resource_ops[resource] = []
            resource_ops[resource].append(op)
    
    # Create suggestions for resources with multiple operations
    for resource, ops in resource_ops.items():
        if len(ops) >= 2:
            suggestions.append({
                "tool_name": f"graphql_{resource}",
                "description": f"GraphQL operations for {resource}",
                "operations": [op["name"] for op in ops],
                "operation_types": list(set(op.get("type", "query") for op in ops))
            })
    
    return suggestions[:5]  # Limit suggestions


# Plugin interface for Meta-MCP
def get_api_discovery_tools():
    """Return API discovery tools for the Meta-MCP plugin system."""
    return {
        "tool_creator_discover": {
            "description": "Discover API specifications from documentation URL or local API specification file (OpenAPI/Swagger, Postman Collection, Insomnia Collection, or HAR file)",
            "schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of API documentation or path to local file (supports: OpenAPI/Swagger JSON/YAML, Postman Collection v2.1, Insomnia Collection v4, HAR 1.2 files, GraphQL endpoint URL, GraphQL SDL/introspection file, file:///path/to/spec.json or just /path/to/spec.json)"
                    },
                    "focus": {
                        "type": "string", 
                        "description": "Optional focus area (e.g., 'weather', 'user management', 'authentication')"
                    }
                },
                "required": ["url"]
            },
            "func": discover_api_from_url
        },
        "tool_creator_from_discovery": {
            "description": "Create a tool from API discovery results",
            "schema": {
                "type": "object",
                "properties": {
                    "discovery_results": {
                        "type": "object",
                        "description": "Results from tool_creator_discover"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Name for the new tool"
                    },
                    "endpoints_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional endpoint patterns to include"
                    }
                },
                "required": ["discovery_results", "tool_name"]
            },
            "func": create_tool_from_discovery
        }
    }