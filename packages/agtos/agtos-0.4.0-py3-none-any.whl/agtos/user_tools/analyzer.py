"""Natural language API analyzer.

This module analyzes natural language descriptions to extract API specifications.

AI_CONTEXT:
    The analyzer is responsible for understanding user intent from descriptions like:
    - "I need to post messages to api.company.com/messages"
    - "Get user data from https://api.service.com/users/{id}"
    - "Update products at our API using PUT requests"
    
    It extracts:
    - Base URLs and endpoints
    - HTTP methods
    - Parameters (path, query, body)
    - Authentication requirements
    - Response expectations
"""

import re
import logging
from typing import List, Optional, Dict, Tuple
from urllib.parse import urlparse, parse_qs

from .models import (
    APIEndpoint, 
    HTTPMethod, 
    Parameter,
    ParameterLocation,
    AuthenticationMethod,
    AuthType,
    ToolSpecification
)

logger = logging.getLogger(__name__)


class APIAnalyzer:
    """Analyzes natural language to extract API specifications.
    
    AI_CONTEXT: This is the brain that understands what the user wants.
    It uses patterns and heuristics to extract structured API information
    from free-form descriptions.
    """
    
    # Patterns for extracting API information
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"|\\^`\[\]]+|'  # URLs with protocol
        r'(?:api\.|/api/)[^\s<>"|\\^`\[\]]+|'  # API subdomain or path
        r'[a-zA-Z0-9][a-zA-Z0-9\-]*(?:\.[a-zA-Z0-9][a-zA-Z0-9\-]*)+(?:/[^\s<>"|\\^`\[\]]*)?'  # Domain names with paths
    )
    
    METHOD_PATTERNS = {
        HTTPMethod.GET: r'\b(get|fetch|retrieve|read|list|show)\b',
        HTTPMethod.POST: r'\b(post|create|send|submit|add)\b',
        HTTPMethod.PUT: r'\b(put|update|modify|edit)\b',
        HTTPMethod.DELETE: r'\b(delete|remove|destroy)\b',
        HTTPMethod.PATCH: r'\b(patch|partial|update partially)\b'
    }
    
    AUTH_PATTERNS = {
        AuthType.BEARER: r'\b(bearer|token|jwt|access token)\b',
        AuthType.API_KEY: r'\b(api[- ]?key|key|apikey)\b',
        AuthType.BASIC: r'\b(basic auth|username|password)\b',
    }
    
    def analyze(self, description: str, name: str = None) -> ToolSpecification:
        """Analyze natural language description to extract API specification.
        
        Args:
            description: Natural language description of the API
            name: Optional tool name (will be inferred if not provided)
            
        Returns:
            ToolSpecification with extracted information
        """
        logger.info(f"Analyzing description: {description[:100]}...")
        
        # Extract endpoints
        endpoints = self._extract_endpoints(description)
        
        # Infer tool name if not provided
        if not name:
            name = self._infer_tool_name(description, endpoints)
        
        # Extract authentication
        auth = self._extract_authentication(description)
        
        # Apply auth to all endpoints
        for endpoint in endpoints:
            if not endpoint.authentication:
                endpoint.authentication = auth
        
        # Generate a better description that preserves user intent
        tool_description = self._create_user_friendly_description(description, endpoints)
        
        return ToolSpecification(
            name=name,
            description=tool_description,
            natural_language_spec=description,
            endpoints=endpoints,
            tags=self._extract_tags(description)
        )
    
    def _extract_endpoints(self, description: str) -> List[APIEndpoint]:
        """Extract API endpoints from description."""
        endpoints = []
        
        # Find URLs in the description
        urls = self.URL_PATTERN.findall(description)
        
        # Filter out partial matches and clean up URLs
        cleaned_urls = []
        for url in urls:
            # Remove trailing words that might have been included
            # Look for common API path patterns
            if ' ' in url:
                url = url.split(' ')[0]
            
            # Remove common trailing words that get caught in the pattern
            for word in ['using', 'with', 'including', 'and', 'or', 'to', 'from']:
                if url.endswith(word):
                    url = url[:-len(word)].rstrip('/')
            
            # Only add if it looks like a valid URL/domain
            if '.' in url and len(url) > 5:
                cleaned_urls.append(url)
        
        urls = cleaned_urls
        
        if not urls:
            # Try to construct from context
            urls = self._infer_urls(description)
        
        for url in urls:
            # Extract method
            method = self._extract_method(description, url)
            
            # Extract parameters
            parameters = self._extract_parameters(description, url)
            
            # Create endpoint
            endpoint = APIEndpoint(
                url=self._normalize_url(url),
                method=method,
                description=self._extract_endpoint_description(description, url),
                parameters=parameters
            )
            
            endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_method(self, description: str, url: str) -> HTTPMethod:
        """Extract HTTP method from description context."""
        description_lower = description.lower()
        
        # Check for explicit method mentions
        for method, pattern in self.METHOD_PATTERNS.items():
            if re.search(pattern, description_lower):
                return method
        
        # Default based on context
        if '{' in url or 'id' in url.lower():
            return HTTPMethod.GET  # Likely fetching specific resource
        
        return HTTPMethod.POST  # Default for APIs
    
    def _extract_parameters(self, description: str, url: str) -> List[Parameter]:
        """Extract parameters from description and URL."""
        parameters = []
        
        # Extract path parameters from URL
        path_params = re.findall(r'\{([^}]+)\}', url)
        for param in path_params:
            # Improve parameter naming based on context
            param_name = param
            param_desc = f"Path parameter {param}"
            
            # Special handling for common API patterns
            url_lower = url.lower()
            if "pokemon" in url_lower and param in ["name", "id"]:
                # Pokemon API: always use pokemon_name for consistency
                param_name = "pokemon_name" if param == "name" else "pokemon_id"
                param_desc = "Name or ID of the Pokemon"
            elif "weather" in url_lower and param in ["city", "location", "name"]:
                # Weather API: standardize on location
                param_name = "location"
                param_desc = "City name or location for weather data"
            elif "user" in url_lower and param in ["id", "user_id", "userId"]:
                # User APIs: standardize on user_id
                param_name = "user_id"
                param_desc = "User identifier"
            elif param in ["id", "ID", "Id"]:
                # Generic ID parameters: add context
                if "product" in url_lower:
                    param_name = "product_id"
                    param_desc = "Product identifier"
                elif "order" in url_lower:
                    param_name = "order_id"
                    param_desc = "Order identifier"
            
            parameters.append(Parameter(
                name=param_name,
                type="string",
                location=ParameterLocation.PATH,
                required=True,
                description=param_desc
            ))
        
        # First, look for explicitly named parameters like "X parameter" or "parameter X"
        # This takes priority over general pattern matching
        explicit_param_patterns = [
            r'\b(\w+)\s+parameter\b',  # "ids parameter"
            r'\bparameter\s+(\w+)\b',   # "parameter ids"
            r'\b(\w+)\s+param\b',       # "ids param"
            r'\bparam\s+(\w+)\b',       # "param ids"
            r'\b(\w+)\s+as\s+a?\s*parameter\b',  # "ids as a parameter"
            r'\bparameter\s+called\s+(\w+)\b',   # "parameter called ids"
            r'\bparameter\s+named\s+(\w+)\b',    # "parameter named ids"
            r'\b(\w+)\s+query\s+parameter\b',    # "ids query parameter"
            r'\bquery\s+parameter\s+(\w+)\b',    # "query parameter ids"
        ]
        
        explicitly_named_params = {}  # Changed to dict to store additional info
        for pattern in explicit_param_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if match and match.lower() not in {'the', 'a', 'an', 'this', 'that', 'with', 'and', 'or', 'for', 'query', 'body'}:
                    param_lower = match.lower()
                    # Check if it's specifically mentioned as a query parameter
                    if 'query' in pattern:
                        explicitly_named_params[param_lower] = 'query'
                    else:
                        explicitly_named_params[param_lower] = None
        
        # Extract mentioned fields from description
        # Look for patterns like "with title and content" or "including name, email"
        # Also handle "with param_name (description) and param_name2 (description)"
        field_patterns = [
            r'with\s+parameters?\s+([^.]+?)(?:\.|$|\s+using|\s+with|\s*,?\s*returns?)',
            r'with\s+(?:the\s+)?([^.]+?)(?:\.|$|\s+using|\s+with|\s*,?\s*returns?)',
            r'including\s+([^.]+?)(?:\.|$)',
            r'fields?:?\s*([^.]+?)(?:\.|$)',
            r'parameters?:?\s*([^.]+?)(?:\.|$)'
        ]
        
        for pattern in field_patterns:
            matches = re.findall(pattern, description.lower())
            for match in matches:
                # Stop at certain keywords that indicate auth/config rather than parameters
                # Only apply stop words if they appear as separate words, not parts of parameters
                stop_patterns = [
                    (r'\s+using\s+', 'using'),
                    (r'\s+with\s+(?:bearer|api|auth)', 'with'),
                    (r'\s+(?:bearer|api)\s+(?:token|key)', 'token/key'),
                    (r',?\s*returns?\s+', 'returns')
                ]
                
                for pattern, desc in stop_patterns:
                    if re.search(pattern, ' ' + match + ' '):
                        match = re.split(pattern, match)[0]
                        break
                
                # First, extract parameters with parenthetical descriptions
                # Pattern: param_name (description) [and/,] param_name2 (description)
                param_with_desc_pattern = r'(\w+)\s*\([^)]+\)'
                params_with_desc = re.findall(param_with_desc_pattern, match)
                
                if params_with_desc:
                    # We found parameters with descriptions in parentheses
                    # Extract each parameter and its description
                    param_entries = re.findall(r'(\w+)\s*\(([^)]+)\)', match)
                    for param_name, param_desc in param_entries:
                        param_location = (
                            ParameterLocation.BODY 
                            if self._extract_method(description, url) in [HTTPMethod.POST, HTTPMethod.PUT]
                            else ParameterLocation.QUERY
                        )
                        # Avoid duplicates
                        param_names = {p.name for p in parameters}
                        if param_name not in param_names:
                            parameters.append(Parameter(
                                name=param_name,
                                type="string",
                                location=param_location,
                                required=False,
                                description=param_desc.strip()
                            ))
                else:
                    # Fallback to original logic for simpler patterns
                    # Split by common separators
                    fields = re.split(r'[,;&]|\s+and\s+', match)
                    for field in fields:
                        field = field.strip()
                        # Clean up field name - preserve the original for better analysis
                        if field and len(field) < 50:
                            param_location = (
                                ParameterLocation.BODY 
                                if self._extract_method(description, url) in [HTTPMethod.POST, HTTPMethod.PUT]
                                else ParameterLocation.QUERY
                            )
                            # Avoid duplicates
                            param_names = {p.name for p in parameters}
                            
                            # Parse "param_name for description" pattern
                            param_name = field
                            param_desc = None
                            for_match = re.match(r'^(\w+)\s+for\s+(.+)$', field)
                            if for_match:
                                param_name = for_match.group(1)
                                param_desc = for_match.group(2)
                            else:
                                # Handle "param_name for" (without description)
                                for_match = re.match(r'^(\w+)\s+for\s*$', field)
                                if for_match:
                                    param_name = for_match.group(1)
                            
                            # Keep original name but ensure it's a valid identifier
                            # Don't replace hyphens yet - let the generator handle that
                            clean_name = param_name.strip()
                            # Skip if it doesn't look like a parameter name
                            # Also skip common words that shouldn't be parameters
                            skip_words = {'parameters', 'parameter', 'params', 'param', 'fields', 'field', 
                                         'and', 'or', 'for', 'with', 'using', 'from', 'to', 'as', 'query', 'body'}
                            if (clean_name and 
                                clean_name.replace('_', '').replace('-', '').isalnum() and
                                clean_name.lower() not in skip_words):  # Allow single character params like 'q'
                                if clean_name not in param_names:
                                    param = Parameter(
                                        name=clean_name,
                                        type="string",
                                        location=param_location,
                                        required=False
                                    )
                                    if param_desc:
                                        param.description = param_desc
                                    parameters.append(param)
        
        # Add any explicitly named parameters that weren't already found
        param_names = {p.name.lower() for p in parameters}
        for explicit_param, location_hint in explicitly_named_params.items():
            if explicit_param not in param_names:
                # Determine parameter location
                if location_hint == 'query':
                    param_location = ParameterLocation.QUERY
                else:
                    param_location = (
                        ParameterLocation.BODY 
                        if self._extract_method(description, url) in [HTTPMethod.POST, HTTPMethod.PUT]
                        else ParameterLocation.QUERY
                    )
                parameters.append(Parameter(
                    name=explicit_param,
                    type="string",
                    location=param_location,
                    required=False,
                    description=f"Parameter {explicit_param}"
                ))
        
        return parameters
    
    def _extract_authentication(self, description: str) -> Optional[AuthenticationMethod]:
        """Extract authentication method from description."""
        description_lower = description.lower()
        
        for auth_type, pattern in self.AUTH_PATTERNS.items():
            if re.search(pattern, description_lower):
                # Extract specific details
                if auth_type == AuthType.BEARER:
                    return AuthenticationMethod(
                        type=AuthType.BEARER,
                        location="header",
                        key_name="Authorization",
                        value_prefix="Bearer "
                    )
                elif auth_type == AuthType.API_KEY:
                    # Check if header or query
                    if 'header' in description_lower:
                        location = "header"
                        key_name = "X-API-Key"
                    elif 'query' in description_lower or 'url' in description_lower or 'parameter' in description_lower:
                        location = "query"
                        # Try to find the key parameter name
                        key_match = re.search(r'(\w+)\s+(?:for|as|is)\s+(?:the\s+)?api\s*key', description_lower)
                        if key_match:
                            key_name = key_match.group(1)
                        else:
                            key_name = "api_key"
                    else:
                        location = "header"  # Default
                        key_name = "X-API-Key"
                    
                    # Generate credentials variable name based on URL
                    credentials_var = "API_KEY"
                    urls = re.findall(r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', description)
                    if urls:
                        domain_parts = urls[0].split('.')
                        service_name = domain_parts[-2] if len(domain_parts) > 1 and domain_parts[-2] != 'api' else domain_parts[0]
                        credentials_var = f"{service_name.upper()}_API_KEY"
                    
                    return AuthenticationMethod(
                        type=AuthType.API_KEY,
                        location=location,
                        key_name=key_name,
                        credentials_var=credentials_var
                    )
        
        return None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it's valid."""
        if not url.startswith(('http://', 'https://')):
            # Assume HTTPS
            url = f"https://{url}"
        
        # Don't remove trailing slashes if there are path params
        if '{' not in url:
            url = url.rstrip('/')
        
        return url
    
    def _infer_tool_name(self, description: str, endpoints: List[APIEndpoint]) -> str:
        """Infer a tool name from the description."""
        # Try to extract service name from URL
        if endpoints:
            parsed = urlparse(endpoints[0].url)
            domain_parts = parsed.netloc.split('.')
            if len(domain_parts) > 1:
                # Get the main domain name
                name = domain_parts[-2] if domain_parts[-2] != 'api' else domain_parts[0]
                return f"{name}_tool"
        
        # Extract from description
        words = description.lower().split()
        for word in ['api', 'service', 'platform', 'system']:
            if word in words:
                idx = words.index(word)
                if idx > 0:
                    return f"{words[idx-1]}_{word}"
        
        return "custom_api_tool"
    
    def _generate_description(self, endpoints: List[APIEndpoint]) -> str:
        """Generate a concise description from endpoints."""
        if not endpoints:
            return "Custom API tool"
        
        methods = list(set(ep.method.value for ep in endpoints))
        urls = list(set(urlparse(ep.url).netloc for ep in endpoints))
        
        return f"Tool for {', '.join(methods)} operations on {', '.join(urls)}"
    
    def _create_user_friendly_description(self, original_desc: str, endpoints: List[APIEndpoint]) -> str:
        """Create a user-friendly description that preserves intent."""
        desc_lower = original_desc.lower()
        
        # Extract the primary action/purpose
        action_phrases = [
            (r'get\s+(\w+(?:\s+\w+)?)', 'retrieve {}'),
            (r'fetch\s+(\w+(?:\s+\w+)?)', 'fetch {}'),
            (r'post\s+(\w+(?:\s+\w+)?)', 'create {}'),
            (r'send\s+(\w+(?:\s+\w+)?)', 'send {}'),
            (r'update\s+(\w+(?:\s+\w+)?)', 'update {}'),
            (r'delete\s+(\w+(?:\s+\w+)?)', 'delete {}'),
            (r'check\s+(\w+(?:\s+\w+)?)', 'check {}')
        ]
        
        # Look for specific purposes in the description
        for pattern, template in action_phrases:
            match = re.search(pattern, desc_lower)
            if match:
                target = match.group(1).strip()
                # Clean up common words and phrases
                skip_words = {'to', 'from', 'at', 'the', 'a', 'an', 'request', 'response'}
                
                # Split target into words and filter out skip words
                words = [w for w in target.split() if w not in skip_words]
                
                # If we have meaningful words left, use them
                if words:
                    cleaned_target = ' '.join(words)
                    return template.format(cleaned_target)
                # Otherwise continue to next pattern
                continue
        
        # Look for specific API purposes
        if 'price' in desc_lower or 'pricing' in desc_lower:
            return 'retrieve cryptocurrency prices'
        elif 'weather' in desc_lower:
            return 'get weather information'
        elif 'message' in desc_lower or 'notification' in desc_lower:
            return 'send messages or notifications'
        elif 'user' in desc_lower and 'data' in desc_lower:
            return 'manage user data'
        elif 'product' in desc_lower:
            return 'manage products'
        elif 'crypto' in desc_lower or 'coin' in desc_lower:
            return 'interact with cryptocurrency services'
        elif 'stock' in desc_lower or 'market' in desc_lower:
            return 'access stock market data'
        elif 'payment' in desc_lower or 'transaction' in desc_lower:
            return 'process payments or transactions'
        
        # Try to extract meaningful nouns from the description
        # Look for patterns like "X API", "X service", "X data"
        noun_patterns = [
            r'(\w+)\s+api\b',
            r'(\w+)\s+service\b',
            r'(\w+)\s+data\b',
            r'(\w+)\s+information\b',
            r'api\.(\w+)\.',
            r'(\w+)\.com',
            r'(\w+)\.io',
        ]
        
        for pattern in noun_patterns:
            if match := re.search(pattern, desc_lower):
                service_name = match.group(1)
                if service_name not in {'the', 'a', 'an', 'this', 'that', 'request', 'response'}:
                    # Determine action based on context
                    if any(word in desc_lower for word in ['get', 'fetch', 'retrieve', 'read']):
                        return f'retrieve {service_name} data'
                    elif any(word in desc_lower for word in ['post', 'send', 'create', 'submit']):
                        return f'send data to {service_name}'
                    elif any(word in desc_lower for word in ['update', 'modify', 'change']):
                        return f'update {service_name} data'
                    else:
                        return f'interact with {service_name}'
        
        # Fallback to a cleaner version using endpoints
        if endpoints:
            method = endpoints[0].method.value.lower()
            domain = urlparse(endpoints[0].url).netloc
            # Extract service name from domain
            service_parts = domain.split('.')
            service = None
            
            # Try to find the most meaningful part of the domain
            for part in service_parts:
                if part not in {'www', 'api', 'com', 'io', 'org', 'net', 'co'}:
                    service = part
                    break
            
            if not service:
                service = 'the API'
            
            action_map = {
                'get': 'retrieve data from',
                'post': 'send data to',
                'put': 'update data in',
                'delete': 'remove data from',
                'patch': 'modify data in'
            }
            action = action_map.get(method, 'interact with')
            return f"{action} {service}"
        
        return "interact with the API"
    
    def _extract_tags(self, description: str) -> List[str]:
        """Extract relevant tags from description."""
        tags = ["custom", "user-generated"]
        
        # Add method tags
        description_lower = description.lower()
        for method, pattern in self.METHOD_PATTERNS.items():
            if re.search(pattern, description_lower):
                tags.append(method.value.lower())
        
        return tags
    
    def _infer_urls(self, description: str) -> List[str]:
        """Try to infer URLs from description when none are explicitly provided."""
        # This is a fallback for descriptions like "our company API"
        # In real implementation, this might prompt the user
        return []
    
    def _extract_endpoint_description(self, description: str, url: str) -> str:
        """Extract description specific to an endpoint."""
        # Find sentence containing the URL
        sentences = description.split('.')
        for sentence in sentences:
            if url in sentence or urlparse(url).path in sentence:
                return sentence.strip()
        
        return f"API endpoint at {url}"