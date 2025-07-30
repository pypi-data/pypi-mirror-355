"""Tool code generator for natural language specifications.

This module generates Python code for tools based on analyzed API specifications.

AI_CONTEXT:
    The generator creates working Python code that:
    - Implements the MCP tool interface
    - Handles API requests with proper error handling
    - Manages authentication securely
    - Validates parameters
    - Returns properly formatted responses
    
    The generated tools are immediately usable through Meta-MCP.
"""

import json
import logging
from typing import Dict, Any, List
from textwrap import dedent, indent

from .models import (
    ToolSpecification,
    APIEndpoint,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    AuthType,
    GeneratedTool
)

logger = logging.getLogger(__name__)


class ToolGenerator:
    """Generates tool code from specifications.
    
    AI_CONTEXT: This is where the magic happens - turning user intent
    into working code. The generator creates clean, readable Python code
    that follows agtOS conventions.
    """
    
    def generate(self, spec: ToolSpecification) -> GeneratedTool:
        """Generate a complete tool from specification.
        
        Args:
            spec: The analyzed tool specification
            
        Returns:
            GeneratedTool with code and MCP schema
        """
        logger.info(f"Generating tool: {spec.name}")
        
        # Generate the Python code
        tool_code = self._generate_tool_code(spec)
        
        # Generate MCP schema
        mcp_schema = self._generate_mcp_schema(spec)
        
        return GeneratedTool(
            spec=spec,
            tool_code=tool_code,
            mcp_schema=mcp_schema
        )
    
    def _generate_tool_code(self, spec: ToolSpecification) -> str:
        """Generate the complete Python tool code."""
        # Generate imports
        imports = self._generate_imports(spec)
        
        # Generate class definition
        class_def = self._generate_class(spec)
        
        # Generate methods for each endpoint
        methods = []
        for endpoint in spec.endpoints:
            method = self._generate_endpoint_method(endpoint, spec.name)
            methods.append(method)
        
        # Combine everything
        code = f"{imports}\n\n{class_def}\n"
        for method in methods:
            code += f"\n{indent(method, '    ')}\n"
        
        # Add registration code
        code += self._generate_registration(spec)
        
        return code
    
    def _generate_imports(self, spec: ToolSpecification) -> str:
        """Generate import statements."""
        imports = [
            "import os",
            "import json",
            "import logging",
            "from typing import Dict, Any, Optional",
            "import requests",
            "from requests.exceptions import RequestException",
            "",
            "from agtos.errors import ToolExecutionError"
        ]
        
        return "\n".join(imports)
    
    def _generate_class(self, spec: ToolSpecification) -> str:
        """Generate class definition."""
        return dedent(f'''
        logger = logging.getLogger(__name__)
        
        
        class {self._to_class_name(spec.name)}:
            """Generated tool: {spec.description}
            
            Generated from: {spec.natural_language_spec}
            """
            
            def __init__(self):
                self.name = "{spec.name}"
                self.description = "{spec.description}"
                self._session = requests.Session()
        ''').strip()
    
    def _generate_endpoint_method(self, endpoint: APIEndpoint, tool_name: str) -> str:
        """Generate method for a specific endpoint."""
        method_name = self._generate_method_name(endpoint)
        
        # Generate parameter list
        params = self._generate_parameter_list(endpoint.parameters)
        
        # Generate docstring
        docstring = self._generate_method_docstring(endpoint)
        
        # Generate authentication
        auth_code = self._generate_auth_code(endpoint.authentication)
        
        # Generate request code
        request_code = self._generate_request_code(endpoint)
        
        # Strip any existing indentation first, then indent properly
        auth_code_lines = auth_code.strip().split('\n')
        auth_code_indented = '\n'.join('        ' + line if line.strip() else '' for line in auth_code_lines)
        
        request_code_lines = request_code.strip().split('\n')
        request_code_indented = '\n'.join('        ' + line if line.strip() else '' for line in request_code_lines)
        
        method = f'''def {method_name}({params}) -> Dict[str, Any]:
    """{docstring}"""
    try:
        # Prepare authentication
{auth_code_indented}
        
        # Prepare request
{request_code_indented}
        
        # Execute request
        response = self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data
        )
        
        # Check response
        response.raise_for_status()
        
        # Return result
        if response.content:
            return response.json()
        else:
            return {{"status": "success", "code": response.status_code}}
            
    except RequestException as e:
        logger.error(f"API request failed: {{e}}")
        raise ToolExecutionError(self.name, f"Failed to {endpoint.description}: {{str(e)}}")
    except Exception as e:
        logger.error(f"Unexpected error: {{e}}")
        raise ToolExecutionError(self.name, f"Error in {method_name}: {{str(e)}}")
'''
        
        return method
    
    def _generate_parameter_list(self, parameters: List[Parameter]) -> str:
        """Generate method parameter list."""
        params = ["self"]
        
        # Add required parameters first
        for param in parameters:
            if param.required:
                sanitized_name = self._sanitize_param_name(param.name)
                param_def = f"{sanitized_name}: {self._python_type(param.type)}"
                params.append(param_def)
        
        # Add optional parameters
        for param in parameters:
            if not param.required:
                sanitized_name = self._sanitize_param_name(param.name)
                default = self._get_default_value(param.type)
                param_def = f"{sanitized_name}: Optional[{self._python_type(param.type)}] = {default}"
                params.append(param_def)
        
        # Always add kwargs for flexibility
        params.append("**kwargs")
        
        return ", ".join(params)
    
    def _generate_auth_code(self, auth) -> str:
        """Generate authentication code."""
        if not auth:
            return "headers = {}"
        
        if auth.type == AuthType.BEARER:
            return dedent(f'''
            token = os.environ.get("{auth.credentials_var or 'API_TOKEN'}")
            if not token:
                raise ToolExecutionError(self.name, "Missing authentication token")
            headers = {{"{auth.key_name}": f"{auth.value_prefix}{{token}}"}}
            ''').strip()
        
        elif auth.type == AuthType.API_KEY:
            env_var = auth.credentials_var or 'API_KEY'
            if auth.location == "query":
                # For query parameter auth, we'll add it to params in _generate_request_code
                # Don't require env var if the parameter can be passed directly
                return dedent(f'''
                api_key = os.environ.get("{env_var}")
                headers = {{}}
                ''').strip()
            else:
                return dedent(f'''
                api_key = os.environ.get("{env_var}")
                if not api_key:
                    raise ToolExecutionError(self.name, "Missing API key (set {env_var} environment variable)")
                headers = {{"{auth.key_name}": api_key}}
                ''').strip()
        
        return "headers = {}"
    
    def _generate_request_code(self, endpoint: APIEndpoint) -> str:
        """Generate request preparation code."""
        lines = []
        
        # Create mapping of original to sanitized names
        param_mapping = {}
        for param in endpoint.parameters:
            sanitized = self._sanitize_param_name(param.name)
            if sanitized != param.name:
                param_mapping[param.name] = sanitized
        
        # Method and URL
        lines.append(f'method = "{endpoint.method.value}"')
        
        # Handle URL with path parameters
        if any(p.location == ParameterLocation.PATH for p in endpoint.parameters):
            url_template = endpoint.url
            format_args = []
            for param in endpoint.parameters:
                if param.location == ParameterLocation.PATH:
                    sanitized_name = self._sanitize_param_name(param.name)
                    format_args.append(f"{param.name}={sanitized_name}")
            
            lines.append(f'url = f"{url_template}"')
        else:
            lines.append(f'url = "{endpoint.url}"')
        
        # Query parameters
        query_params = [p for p in endpoint.parameters if p.location == ParameterLocation.QUERY]
        if query_params or (endpoint.authentication and endpoint.authentication.location == "query"):
            lines.append("params = {}")
            
            # Handle authentication parameters - prefer passed values over environment
            auth_param_handled = False
            
            for param in query_params:
                sanitized_name = self._sanitize_param_name(param.name)
                
                # Check if this is the auth key parameter
                if (endpoint.authentication and 
                    endpoint.authentication.location == "query" and 
                    param.name == endpoint.authentication.key_name):
                    # For auth parameters, use passed value if provided, otherwise fall back to env var
                    lines.append(f'if {sanitized_name} is not None:')
                    lines.append(f'    params["{param.name}"] = {sanitized_name}')
                    lines.append(f'else:')
                    lines.append(f'    if api_key:')
                    lines.append(f'        params["{param.name}"] = api_key')
                    lines.append(f'    else:')
                    lines.append(f'        raise ToolExecutionError(self.name, "Missing {param.name} parameter and no {endpoint.authentication.credentials_var or "API_KEY"} environment variable set")')
                    auth_param_handled = True
                else:
                    # Regular parameters
                    if param.required:
                        lines.append(f'params["{param.name}"] = {sanitized_name}')
                    else:
                        lines.append(f'if {sanitized_name} is not None:')
                        lines.append(f'    params["{param.name}"] = {sanitized_name}')
            
            # If auth key wasn't in parameters list, add it from env var
            if endpoint.authentication and endpoint.authentication.location == "query" and not auth_param_handled:
                lines.append(f'params["{endpoint.authentication.key_name}"] = api_key')
        else:
            lines.append("params = None")
        
        # Body parameters
        body_params = [p for p in endpoint.parameters if p.location == ParameterLocation.BODY]
        if body_params:
            lines.append("json_data = {}")
            for param in body_params:
                sanitized_name = self._sanitize_param_name(param.name)
                if param.required:
                    lines.append(f'json_data["{param.name}"] = {sanitized_name}')
                else:
                    lines.append(f'if {sanitized_name} is not None:')
                    lines.append(f'    json_data["{param.name}"] = {sanitized_name}')
        else:
            lines.append("json_data = None")
        
        return "\n".join(lines)
    
    def _generate_mcp_schema(self, spec: ToolSpecification) -> Dict[str, Any]:
        """Generate MCP-compatible tool schema."""
        tools = []
        
        for endpoint in spec.endpoints:
            # Generate parameter schema
            properties = {}
            required = []
            
            for param in endpoint.parameters:
                # Use sanitized parameter name to match Python code
                sanitized_name = self._sanitize_param_name(param.name)
                properties[sanitized_name] = {
                    "type": param.type,
                    "description": param.description or f"{param.name} parameter"
                }
                if param.required:
                    required.append(sanitized_name)
            
            # Clean up the tool name for MCP schema
            method_name = self._generate_method_name(endpoint)
            tool_name = f"{spec.name}_{method_name}"
            
            tool_schema = {
                "name": tool_name,
                "description": endpoint.description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            
            tools.append(tool_schema)
        
        return {"tools": tools}
    
    def _generate_method_name(self, endpoint: APIEndpoint) -> str:
        """Generate a method name from endpoint."""
        # Extract meaningful parts from URL
        from urllib.parse import urlparse
        parsed = urlparse(endpoint.url)
        
        # Get path parts, removing empty ones and parameters
        path_parts = [p for p in parsed.path.split('/') if p and '{' not in p]
        
        # If we have path parts, use the last meaningful one
        if path_parts:
            # Clean up any special characters
            path_name = path_parts[-1].replace('.', '_').replace('-', '_')
        else:
            # Use domain if no path
            domain_parts = parsed.netloc.split('.')
            path_name = domain_parts[0] if domain_parts else 'api'
        
        method_prefix = endpoint.method.value.lower()
        
        return f"{method_prefix}_{path_name}"
    
    def _generate_method_docstring(self, endpoint: APIEndpoint) -> str:
        """Generate method docstring."""
        lines = [endpoint.description]
        
        if endpoint.parameters:
            lines.append("")
            lines.append("Args:")
            for param in endpoint.parameters:
                desc = param.description or f"{param.name} value"
                lines.append(f"    {param.name}: {desc}")
        
        lines.append("")
        lines.append("Returns:")
        lines.append("    API response as dictionary")
        
        return "\\n".join(lines)
    
    def _generate_registration(self, spec: ToolSpecification) -> str:
        """Generate tool registration code."""
        class_name = self._to_class_name(spec.name)
        
        return dedent(f'''
        
        # Tool registration
        TOOL_INSTANCE = {class_name}()
        
        def get_tool_info():
            """Get tool information for Meta-MCP registration."""
            return {{
                "name": "{spec.name}",
                "description": "{spec.description}",
                "instance": TOOL_INSTANCE
            }}
        ''').strip()
    
    def _to_class_name(self, name: str) -> str:
        """Convert tool name to class name."""
        parts = name.replace('-', '_').split('_')
        return ''.join(p.capitalize() for p in parts)
    
    def _sanitize_param_name(self, name: str) -> str:
        """Sanitize parameter name for use as Python identifier.
        
        Args:
            name: Original parameter name
            
        Returns:
            Valid Python identifier
        """
        # Replace hyphens and other invalid characters with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'param_' + sanitized
        
        # Ensure it's not a Python keyword
        import keyword
        if keyword.iskeyword(sanitized):
            sanitized = sanitized + '_param'
        
        return sanitized or 'param'
    
    def _python_type(self, param_type: str) -> str:
        """Convert parameter type to Python type."""
        type_map = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "object": "Dict[str, Any]",
            "array": "List[Any]"
        }
        return type_map.get(param_type, "Any")
    
    def _get_default_value(self, param_type: str) -> str:
        """Get default value for parameter type."""
        defaults = {
            "string": "None",
            "number": "None",
            "integer": "None", 
            "boolean": "False",
            "object": "None",
            "array": "None"
        }
        return defaults.get(param_type, "None")