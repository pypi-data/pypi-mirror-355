"""HAR (HTTP Archive) Parser for agtOS.

This parser handles HAR 1.2 format files which are JSON-formatted logs of browser network traffic.
It intelligently filters API calls from static assets and extracts:
- API endpoints with methods, URLs, headers, body
- Authentication patterns (Bearer, API key, cookies)
- Request/response patterns for API discovery
- Groups similar endpoints (e.g., /users/1, /users/2 → /users/{id})
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs, urljoin
from collections import defaultdict
import mimetypes

logger = logging.getLogger(__name__)


class HARParser:
    """Parser for HAR (HTTP Archive) format files."""
    
    # Content types that indicate API responses
    API_CONTENT_TYPES = {
        'application/json',
        'application/xml',
        'text/xml',
        'application/graphql',
        'application/x-www-form-urlencoded',
        'multipart/form-data',
        'text/plain',  # Some APIs return plain text
        'application/vnd.api+json',  # JSON API
        'application/hal+json',  # HAL JSON
        'application/ld+json',  # JSON-LD
    }
    
    # URL patterns to exclude (analytics, tracking, static assets)
    EXCLUDE_PATTERNS = [
        r'/\.well-known/',
        r'/favicon\.',
        r'google-analytics\.com',
        r'googletagmanager\.com',
        r'doubleclick\.net',
        r'facebook\.com/tr',
        r'segment\.io',
        r'mixpanel\.com',
        r'amplitude\.com',
        r'sentry\.io',
        r'bugsnag\.com',
        r'cdn\.',
        r'cloudfront\.net',
        r'amazonaws\.com/static',
        r'/static/',
        r'/assets/',
        r'/dist/',
        r'/build/',
        r'\.chunk\.',
        r'\.bundle\.',
    ]
    
    # File extensions to exclude
    STATIC_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp',
        '.css', '.scss', '.sass', '.less',
        '.js', '.mjs', '.map', '.ts',
        '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.mp4', '.webm', '.mp3', '.wav',
        '.pdf', '.zip', '.tar', '.gz',
    }
    
    # Common API path patterns
    API_PATH_PATTERNS = [
        r'/api/',
        r'/v\d+/',
        r'/graphql',
        r'/rest/',
        r'/services/',
        r'/endpoints/',
    ]
    
    def __init__(self):
        self.auth_methods = set()
        self.base_urls = defaultdict(int)
        self.endpoint_groups = defaultdict(list)
        
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse HAR file and extract API information.
        
        Args:
            content: JSON string containing HAR data
            
        Returns:
            Dictionary with parsed API information
        """
        try:
            har_data = json.loads(content)
            
            # Verify it's a HAR file
            if not self._is_har_file(har_data):
                return {
                    "success": False,
                    "error": "Not a valid HAR file",
                    "endpoints": []
                }
            
            # Extract log entries
            entries = har_data.get("log", {}).get("entries", [])
            
            if not entries:
                return {
                    "success": False,
                    "error": "No entries found in HAR file",
                    "endpoints": []
                }
            
            # Process entries
            api_entries = self._filter_api_entries(entries)
            
            if not api_entries:
                return {
                    "success": False,
                    "error": "No API calls found in HAR file",
                    "endpoints": [],
                    "statistics": {
                        "total_entries": len(entries),
                        "filtered_entries": 0
                    }
                }
            
            # Extract endpoints
            endpoints = self._extract_endpoints(api_entries)
            
            # Group similar endpoints
            grouped_endpoints = self._group_similar_endpoints(endpoints)
            
            # Determine base URL
            base_url = self._determine_base_url()
            
            # Extract authentication
            authentication = self._extract_authentication()
            
            result = {
                "success": True,
                "base_url": base_url,
                "endpoints": grouped_endpoints,
                "authentication": authentication,
                "statistics": {
                    "total_entries": len(entries),
                    "api_entries": len(api_entries),
                    "unique_endpoints": len(grouped_endpoints),
                    "auth_methods": list(self.auth_methods)
                },
                "version": har_data.get("log", {}).get("version", "1.2"),
                "creator": har_data.get("log", {}).get("creator", {}).get("name", "Unknown"),
                "pages": self._extract_page_info(har_data)
            }
            
            return result
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON: {str(e)}",
                "endpoints": []
            }
        except Exception as e:
            logger.error(f"Error parsing HAR file: {str(e)}")
            return {
                "success": False,
                "error": f"Parse error: {str(e)}",
                "endpoints": []
            }
    
    def _is_har_file(self, data: Dict[str, Any]) -> bool:
        """Check if data is a valid HAR file."""
        return (
            isinstance(data, dict) and
            "log" in data and
            isinstance(data["log"], dict) and
            "entries" in data["log"]
        )
    
    def _filter_api_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter HAR entries to find API calls."""
        api_entries = []
        
        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})
            
            url = request.get("url", "")
            if not url:
                continue
            
            # Skip if matches exclusion patterns
            if self._should_exclude_url(url):
                continue
            
            # Check response content type
            content_type = self._get_response_content_type(response)
            
            # Include if:
            # 1. Has API-like content type
            # 2. Has API path pattern
            # 3. Has interesting status code (not just 200/304 for static assets)
            # 4. Has request body (likely API call)
            
            is_api_content = any(api_type in content_type for api_type in self.API_CONTENT_TYPES)
            has_api_path = any(re.search(pattern, url, re.IGNORECASE) for pattern in self.API_PATH_PATTERNS)
            has_body = request.get("postData", {}).get("text")
            interesting_status = response.get("status", 0) not in [0, 204, 304]  # 0 = no response
            
            if is_api_content or has_api_path or (has_body and interesting_status):
                # Track base URLs
                parsed = urlparse(url)
                base = f"{parsed.scheme}://{parsed.netloc}"
                self.base_urls[base] += 1
                
                api_entries.append(entry)
        
        return api_entries
    
    def _should_exclude_url(self, url: str) -> bool:
        """Check if URL should be excluded."""
        # Check static file extensions
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in self.STATIC_EXTENSIONS:
            if path.endswith(ext):
                return True
        
        # Check exclusion patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def _get_response_content_type(self, response: Dict[str, Any]) -> str:
        """Extract content type from response headers."""
        headers = response.get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "content-type":
                return header.get("value", "").lower()
        return ""
    
    def _extract_endpoints(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract endpoint information from HAR entries."""
        endpoints = []
        
        for entry in entries:
            request = entry.get("request", {})
            response = entry.get("response", {})
            
            endpoint = {
                "url": request.get("url", ""),
                "method": request.get("method", "GET"),
                "headers": self._extract_headers(request),
                "query_params": self._extract_query_params(request),
                "path_params": [],  # Will be inferred during grouping
                "body": self._extract_body(request),
                "response": {
                    "status": response.get("status", 0),
                    "content_type": self._get_response_content_type(response),
                    "example": self._extract_response_content(response)
                },
                "timing": self._extract_timing(entry),
                "authentication": self._extract_auth_from_request(request)
            }
            
            endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_headers(self, request: Dict[str, Any]) -> Dict[str, str]:
        """Extract relevant headers from request."""
        headers = {}
        exclude_headers = {
            'host', 'user-agent', 'accept', 'accept-encoding', 
            'accept-language', 'connection', 'referer', 'origin',
            'cache-control', 'pragma', 'sec-fetch-dest', 'sec-fetch-mode',
            'sec-fetch-site', 'sec-ch-ua', 'dnt', 'upgrade-insecure-requests'
        }
        
        for header in request.get("headers", []):
            name = header.get("name", "").lower()
            value = header.get("value", "")
            
            if name not in exclude_headers and value:
                headers[header.get("name", "")] = value
        
        return headers
    
    def _extract_query_params(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract query parameters from request."""
        params = []
        
        for param in request.get("queryString", []):
            params.append({
                "name": param.get("name", ""),
                "value": param.get("value", ""),
                "description": ""  # Will be inferred from usage
            })
        
        return params
    
    def _extract_body(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body information."""
        post_data = request.get("postData", {})
        
        if not post_data:
            return None
        
        body_info = {
            "mimeType": post_data.get("mimeType", ""),
            "text": post_data.get("text", ""),
            "params": []
        }
        
        # For form data, extract parameters
        if "application/x-www-form-urlencoded" in body_info["mimeType"]:
            for param in post_data.get("params", []):
                body_info["params"].append({
                    "name": param.get("name", ""),
                    "value": param.get("value", "")
                })
        
        return body_info
    
    def _extract_response_content(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract response content if available."""
        content = response.get("content", {})
        
        if content.get("text"):
            # Limit size to prevent huge responses
            text = content["text"][:1000]
            
            # Try to parse as JSON for better formatting
            if "json" in self._get_response_content_type(response):
                try:
                    parsed = json.loads(text)
                    return json.dumps(parsed, indent=2)
                except:
                    pass
            
            return text
        
        return None
    
    def _extract_timing(self, entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract timing information."""
        timings = entry.get("timings", {})
        
        return {
            "wait": timings.get("wait", 0),
            "receive": timings.get("receive", 0),
            "total": entry.get("time", 0)
        }
    
    def _extract_auth_from_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract authentication information from request."""
        headers = request.get("headers", [])
        cookies = request.get("cookies", [])
        
        # Track all auth methods in this request (don't return early)
        request_auth = None
        
        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")
            
            # Bearer token
            if name == "authorization" and value.startswith("Bearer "):
                self.auth_methods.add("bearer")
                if not request_auth:  # Use first auth found
                    request_auth = {
                        "type": "bearer",
                        "header": "Authorization",
                        "prefix": "Bearer"
                    }
            
            # Basic auth
            elif name == "authorization" and value.startswith("Basic "):
                self.auth_methods.add("basic")
                if not request_auth:
                    request_auth = {
                        "type": "basic",
                        "header": "Authorization"
                    }
            
            # API key in header
            elif name in ["x-api-key", "api-key", "apikey", "x-auth-token"]:
                self.auth_methods.add("api_key")
                if not request_auth:
                    request_auth = {
                        "type": "api_key",
                        "header": header.get("name", ""),
                        "location": "header"
                    }
        
        # Check for auth cookies
        auth_cookies = ["session", "token", "auth", "jwt", "sid", "ssid"]
        for cookie in cookies:
            cookie_name = cookie.get("name", "").lower()
            # Check if cookie name contains auth-related terms or ends with _token
            if any(auth in cookie_name for auth in auth_cookies) or cookie_name.endswith("_token"):
                self.auth_methods.add("cookie")
                if not request_auth:
                    request_auth = {
                        "type": "cookie",
                        "cookie_name": cookie.get("name", "")
                    }
        
        # Check query parameters for API key
        for param in request.get("queryString", []):
            param_name = param.get("name", "").lower()
            if param_name in ["api_key", "apikey", "key", "token"]:
                self.auth_methods.add("api_key")
                if not request_auth:
                    request_auth = {
                        "type": "api_key",
                        "parameter": param.get("name", ""),
                        "location": "query"
                    }
        
        return request_auth
    
    def _group_similar_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group similar endpoints and extract patterns."""
        # Group by method and path pattern
        groups = defaultdict(list)
        
        for endpoint in endpoints:
            url = endpoint["url"]
            method = endpoint["method"]
            
            # Extract path
            parsed = urlparse(url)
            path = parsed.path
            
            # Normalize path by replacing IDs with placeholders
            pattern = self._normalize_path(path)
            
            key = f"{method} {pattern}"
            groups[key].append(endpoint)
        
        # Convert groups to endpoints with patterns
        grouped = []
        
        for key, group in groups.items():
            method, pattern = key.split(" ", 1)
            
            # Extract common elements from group
            merged = self._merge_endpoint_group(group, method, pattern)
            grouped.append(merged)
        
        return grouped
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing variable parts with placeholders."""
        # Split path into segments
        segments = path.split('/')
        normalized_segments = []
        
        for segment in segments:
            if not segment:  # Empty segment
                normalized_segments.append(segment)
                continue
                
            # Skip common API path segments
            if segment.lower() in ['api', 'v1', 'v2', 'v3', 'graphql', 'rest']:
                normalized_segments.append(segment)
                continue
                
            # Check for ID patterns
            if re.match(r'^\d+$', segment):  # Pure numeric
                normalized_segments.append('{id}')
            elif re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', segment):  # UUID
                normalized_segments.append('{uuid}')
            elif re.match(r'^[a-f0-9]{24}$', segment):  # MongoDB ObjectId
                normalized_segments.append('{objectId}')
            elif re.match(r'^(users?|orders?|products?|items?|posts?|comments?|reviews?)$', segment):  # Resource names
                normalized_segments.append(segment)
            elif len(segment) > 5 and re.match(r'^[a-zA-Z0-9_-]+$', segment):  # Likely an ID
                # But preserve certain keywords
                if segment.lower() in ['health', 'status', 'info', 'version', 'search', 'filter', 'export', 'import']:
                    normalized_segments.append(segment)
                else:
                    normalized_segments.append('{id}')
            else:
                normalized_segments.append(segment)
        
        return '/'.join(normalized_segments)
    
    def _merge_endpoint_group(self, group: List[Dict[str, Any]], method: str, pattern: str) -> Dict[str, Any]:
        """Merge a group of similar endpoints into one pattern."""
        # Use the first endpoint as base
        base = group[0]
        
        # Collect all query parameters
        all_params = defaultdict(set)
        for endpoint in group:
            for param in endpoint.get("query_params", []):
                all_params[param["name"]].add(param.get("value", ""))
        
        # Extract path parameters from pattern
        path_params = []
        for match in re.finditer(r'\{([^}]+)\}', pattern):
            param_name = match.group(1)
            path_params.append({
                "name": param_name,
                "description": f"Path parameter: {param_name}",
                "required": True
            })
        
        # Collect all headers (excluding auth)
        all_headers = {}
        auth_info = None
        
        for endpoint in group:
            headers = endpoint.get("headers", {})
            auth = endpoint.get("authentication")
            
            if auth and not auth_info:
                auth_info = auth
            
            for name, value in headers.items():
                if name.lower() not in ["authorization", "x-api-key", "api-key"]:
                    all_headers[name] = value
        
        # Determine body schema from examples
        body_schema = None
        body_examples = []
        
        for endpoint in group:
            body = endpoint.get("body")
            if body and body.get("text"):
                body_examples.append(body["text"])
        
        if body_examples:
            body_schema = self._infer_body_schema(body_examples, base.get("body", {}).get("mimeType", ""))
        
        # Get response examples
        response_examples = []
        for endpoint in group:
            resp = endpoint.get("response", {})
            if resp.get("example"):
                response_examples.append(resp["example"])
        
        # Calculate average response time
        avg_time = sum(ep.get("timing", {}).get("total", 0) for ep in group) / len(group)
        
        result = {
            "url": pattern,
            "method": method,
            "description": f"{method} {pattern}",
            "path_params": path_params,
            "query_params": [
                {
                    "name": name,
                    "values": list(values),
                    "required": len(values) == len(group)  # Required if in all requests
                }
                for name, values in all_params.items()
            ],
            "headers": all_headers,
            "authentication": auth_info,
            "body": body_schema,
            "examples": {
                "count": len(group),
                "response_examples": response_examples[:3],  # Limit examples
                "average_response_time": avg_time
            }
        }
        
        return result
    
    def _infer_body_schema(self, examples: List[str], mime_type: str) -> Dict[str, Any]:
        """Infer body schema from examples."""
        schema = {
            "mimeType": mime_type,
            "properties": {}
        }
        
        if "json" in mime_type:
            # Try to parse JSON examples
            parsed_examples = []
            for example in examples:
                try:
                    parsed = json.loads(example)
                    parsed_examples.append(parsed)
                except:
                    continue
            
            if parsed_examples:
                # Extract common properties
                schema["properties"] = self._extract_json_schema(parsed_examples)
                schema["examples"] = parsed_examples[:2]  # Keep a couple examples
        
        elif "form" in mime_type:
            # Parse form data
            form_fields = defaultdict(set)
            for example in examples:
                params = parse_qs(example)
                for key, values in params.items():
                    form_fields[key].update(values)
            
            schema["properties"] = {
                field: {
                    "type": "string",
                    "examples": list(values)[:3]
                }
                for field, values in form_fields.items()
            }
        
        return schema
    
    def _extract_json_schema(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract JSON schema from examples."""
        if not examples:
            return {}
        
        # Simple schema extraction - just get all keys and types
        schema = {}
        
        for example in examples:
            if isinstance(example, dict):
                for key, value in example.items():
                    if key not in schema:
                        schema[key] = {
                            "type": type(value).__name__,
                            "examples": []
                        }
                    if len(schema[key]["examples"]) < 3:
                        schema[key]["examples"].append(value)
        
        return schema
    
    def _determine_base_url(self) -> str:
        """Determine the most likely base URL from collected URLs."""
        if not self.base_urls:
            return "https://api.example.com"
        
        # Return the most frequent base URL
        return max(self.base_urls.items(), key=lambda x: x[1])[0]
    
    def _extract_authentication(self) -> Optional[Dict[str, Any]]:
        """Extract the most likely authentication method."""
        if not self.auth_methods:
            return None
        
        # Prioritize auth methods
        priority = ["bearer", "api_key", "basic", "cookie"]
        
        for method in priority:
            if method in self.auth_methods:
                if method == "bearer":
                    return {
                        "type": "bearer",
                        "description": "Bearer token authentication in Authorization header"
                    }
                elif method == "api_key":
                    return {
                        "type": "api_key",
                        "description": "API key authentication (check headers or query parameters)"
                    }
                elif method == "basic":
                    return {
                        "type": "basic",
                        "description": "HTTP Basic authentication"
                    }
                elif method == "cookie":
                    return {
                        "type": "cookie",
                        "description": "Cookie-based session authentication"
                    }
        
        return None
    
    def _extract_page_info(self, har_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract page information if available."""
        pages = har_data.get("log", {}).get("pages", [])
        
        return [
            {
                "id": page.get("id", ""),
                "title": page.get("title", ""),
                "timestamp": page.get("startedDateTime", "")
            }
            for page in pages
        ]