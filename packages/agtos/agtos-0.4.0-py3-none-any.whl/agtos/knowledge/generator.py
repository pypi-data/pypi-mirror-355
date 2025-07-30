"""Plugin code generation from discovered knowledge.

This module generates plugin code based on discovered CLI and API knowledge.
It transforms structured knowledge into executable Python plugins.

The AI-First approach means:
1. Knowledge-driven code generation
2. Self-documenting output with embedded discovery metadata
3. Adaptive patterns based on discovered capabilities
4. Safe execution wrappers for all generated functions
"""
import json
import re
from typing import Dict, Any, List, Tuple


class PluginGenerator:
    """Generate plugin code with acquired knowledge.
    
    This class contains static methods to generate different types of plugins
    based on discovered knowledge about CLIs and APIs.
    """
    
    @staticmethod
    def generate_cli_plugin(service: str, knowledge: Dict[str, Any]) -> str:
        """Generate a CLI plugin with discovered knowledge.
        
        Args:
            service: Name of the CLI service/tool
            knowledge: Discovered CLI knowledge including:
                - available: Whether CLI is available
                - subcommands: List of discovered subcommands
                - global_flags: List of global flags
                - patterns: Patterns including CRUD operations and auth requirements
                - examples: Example commands discovered
                
        Returns:
            Generated Python plugin code as a string
        """
        # Generate plugin components
        header = _generate_plugin_header(service, knowledge)
        imports = _generate_imports()
        safe_execute = _generate_safe_execute_decorator()
        cli_info = _generate_cli_info_comments(service, knowledge)
        
        # Generate functions and tools
        functions = []
        tools = {}
        
        # Add CRUD operation functions
        crud_functions, crud_tools = _generate_crud_functions(service, knowledge)
        functions.extend(crud_functions)
        tools.update(crud_tools)
        
        # Add example function if examples exist
        if knowledge.get("examples"):
            example_func = _generate_example_function(service, knowledge)
            functions.append(example_func)
        
        # Build final plugin
        return _assemble_plugin_content(
            header, imports, safe_execute, cli_info, functions, tools
        )
    
    @staticmethod
    def generate_api_plugin(service: str, knowledge: Dict[str, Any]) -> str:
        """Generate an API plugin with discovered knowledge.
        
        Args:
            service: Name of the API service
            knowledge: Discovered API knowledge including:
                - title: API title
                - version: API version
                - description: API description
                - base_url: Base URL for the API
                - auth_methods: List of authentication methods
                - endpoints: List of discovered endpoints
                
        Returns:
            Generated Python plugin code as a string
        """
        # Generate each component
        header = PluginGenerator._generate_api_header(service, knowledge)
        imports = PluginGenerator._generate_api_imports()
        safe_execute = PluginGenerator._generate_safe_execute_decorator()
        config = PluginGenerator._generate_api_config(service, knowledge)
        get_headers = PluginGenerator._generate_auth_function(service, knowledge)
        
        # Generate endpoint functions and tools
        functions = []
        tools = {}
        if knowledge.get("endpoints"):
            for endpoint in knowledge["endpoints"][:10]:  # Limit to 10 most important
                func_code, tool_def = PluginGenerator._generate_endpoint_function(
                    service, endpoint
                )
                if func_code:
                    functions.append(func_code)
                    tools.update(tool_def)
        
        # Assemble final plugin
        plugin_content = header + imports + safe_execute + config + get_headers
        plugin_content += "\n".join(functions)
        plugin_content += PluginGenerator._generate_tools_export(tools)
        
        return plugin_content
    
    @staticmethod
    def _generate_api_header(service: str, knowledge: Dict[str, Any]) -> str:
        """Generate plugin header documentation."""
        header = f'"""Plugin for {service} REST API integration.\n'
        header += 'Auto-generated with discovered knowledge.\n\n'
        header += f'API: {knowledge.get("title", f"{service} API")}\n'
        header += f'Version: {knowledge.get("version", "")}\n'
        header += f'{knowledge.get("description", "")}\n'
        header += '"""\n'
        return header
    
    @staticmethod
    def _generate_api_imports() -> str:
        """Generate standard imports for API plugin."""
        return '''import requests
import os
from typing import Dict, Any, List, Optional

'''
    
    @staticmethod
    def _generate_safe_execute_decorator() -> str:
        """Generate safe execution decorator."""
        return '''def safe_execute(func):
    """Decorator for safe execution."""
    def wrapper(*args, **kwargs):
        try:
            return {"success": True, "data": func(*args, **kwargs)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return wrapper

'''
    
    @staticmethod
    def _generate_api_config(service: str, knowledge: Dict[str, Any]) -> str:
        """Generate API configuration constants."""
        default_base_url = f"https://api.{service}.com"
        base_url = knowledge.get("base_url", default_base_url)
        
        config = f'''# API Configuration
BASE_URL = "{base_url}"
API_KEY_ENV = "{service.upper()}_API_KEY"

# Discovered Authentication: {knowledge.get("auth_methods", [])}

'''
        return config
    
    @staticmethod
    def _generate_auth_function(service: str, knowledge: Dict[str, Any]) -> str:
        """Generate authentication headers function."""
        # Determine auth code based on discovered auth
        auth_code = 'headers["Authorization"] = f"Bearer {api_key}"'
        if knowledge.get("auth_methods"):
            auth = knowledge["auth_methods"][0]
            if auth["type"] == "api_key":
                if auth.get("in") == "header":
                    auth_code = f'headers["{auth.get("key_name", "X-API-Key")}"] = api_key'
                elif auth.get("in") == "query":
                    auth_code = '# API key goes in query parameters'
        
        get_headers = f'''def get_headers() -> Dict[str, str]:
    """Get authorization headers."""
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise ValueError(f"{{API_KEY_ENV}} not found in environment")
    
    headers = {{"Content-Type": "application/json"}}
    
    # Add auth based on discovered method
    {auth_code}
    
    return headers

'''
        return get_headers
    
    @staticmethod
    def _generate_endpoint_function(service: str, endpoint: Dict[str, Any]) -> tuple:
        """Generate function for a single endpoint.
        
        Returns:
            Tuple of (function_code, tool_definition)
        """
        # Create function name
        func_name = PluginGenerator._create_function_name(endpoint)
        
        # Build function signature
        func_signature, params = PluginGenerator._build_function_signature(
            func_name, endpoint
        )
        
        # Build function body
        function_code = PluginGenerator._build_function_body(
            func_signature, endpoint
        )
        
        # Build tool definition
        tool_def = PluginGenerator._build_tool_definition(
            service, func_name, endpoint, params
        )
        
        return function_code, tool_def
    
    @staticmethod
    def _create_function_name(endpoint: Dict[str, Any]) -> str:
        """Create a valid Python function name from endpoint."""
        if endpoint.get("operation_id"):
            func_name = endpoint["operation_id"]
        else:
            path = endpoint['path'].replace('/', '_').replace('{', '').replace('}', '')
            func_name = f"{endpoint['method'].lower()}_{path.strip('_')}"
        
        # Ensure valid Python identifier
        func_name = re.sub(r'[^a-zA-Z0-9_]', '_', func_name)
        return func_name
    
    @staticmethod
    def _build_function_signature(func_name: str, endpoint: Dict[str, Any]) -> tuple:
        """Build function signature and return params list."""
        params = [p for p in endpoint.get("parameters", []) if p.get("required")]
        optional_params = [p for p in endpoint.get("parameters", []) if not p.get("required")]
        
        param_list = []
        for p in params:
            param_list.append(f"{p['name']}: str")
        for p in optional_params:
            param_list.append(f"{p['name']}: Optional[str] = None")
        if endpoint.get("request_body"):
            param_list.append("body: Optional[Dict[str, Any]] = None")
        
        func_signature = f"def {func_name}(" + ", ".join(param_list) + ")"
        return func_signature, params
    
    @staticmethod
    def _build_function_body(func_signature: str, endpoint: Dict[str, Any]) -> str:
        """Build complete function body with request logic."""
        function_code = f'''
@safe_execute
{func_signature}:
    """{endpoint.get('summary', 'API endpoint')}
    
    {endpoint.get('description', '')}
    """
    url = f"{{BASE_URL}}{endpoint['path']}"
    headers = get_headers()
    
'''
        
        # Add request method specific logic
        request_code = PluginGenerator._generate_request_code(endpoint)
        function_code += request_code
        
        # Add response handling
        function_code += '''    
    response.raise_for_status()
    return response.json() if response.content else {"status": "success"}
'''
        
        return function_code
    
    @staticmethod
    def _generate_request_code(endpoint: Dict[str, Any]) -> str:
        """Generate HTTP request code based on method and parameters."""
        method = endpoint['method']
        
        if method == 'GET' and endpoint.get('parameters'):
            code = '    params = {}\n'
            for p in endpoint['parameters']:
                if p['in'] == 'query':
                    if p['required']:
                        code += f'    params["{p["name"]}"] = {p["name"]}\n'
                    else:
                        code += f'    if {p["name"]}:\n        params["{p["name"]}"] = {p["name"]}\n'
            code += '    response = requests.get(url, headers=headers, params=params)\n'
            return code
        elif method in ['POST', 'PUT', 'PATCH']:
            return f'    response = requests.{method.lower()}(url, headers=headers, json=body)\n'
        elif method == 'DELETE':
            return '    response = requests.delete(url, headers=headers)\n'
        else:
            return f'    response = requests.{method.lower()}(url, headers=headers)\n'
    
    @staticmethod
    def _build_tool_definition(service: str, func_name: str, 
                               endpoint: Dict[str, Any], params: list) -> Dict[str, Any]:
        """Build tool definition for TOOLS export."""
        tool_def = {
            f"{service}.{func_name}": {
                "version": "1.0",
                "description": endpoint.get("summary", f"{endpoint['method']} {endpoint['path']}"),
                "schema": {
                    "type": "object",
                    "properties": {
                        p["name"]: {
                            "type": "string",
                            "description": p.get("description", "")
                        } for p in params
                    },
                    "required": [p["name"] for p in params]
                },
                "func": func_name
            }
        }
        return tool_def
    
    @staticmethod
    def _generate_tools_export(tools: Dict[str, Any]) -> str:
        """Generate TOOLS dictionary export."""
        tools_json = json.dumps(tools, indent=4)
        tools_export = "\n\n# Auto-generated TOOLS\nTOOLS = " + tools_json
        # Fix function references (remove quotes)
        tools_export = tools_export.replace('"func": "', '"func": ')
        return tools_export


# ========================================================================
# Helper Functions for generate_cli_plugin
# ========================================================================

def _generate_plugin_header(service: str, knowledge: Dict[str, Any]) -> str:
    """Generate the plugin header docstring.
    
    Args:
        service: Service name
        knowledge: Discovered knowledge
        
    Returns:
        Header string
    """
    header = f'"""Plugin for {service} CLI integration.\nAuto-generated with discovered knowledge.\n\n'
    header += f"Subcommands: {', '.join(knowledge.get('subcommands', [])[:5])}\n"
    header += '"""\n'
    return header


def _generate_imports() -> str:
    """Generate standard imports for CLI plugin.
    
    Returns:
        Import statements
    """
    return '''import subprocess
import os
import json
from typing import Dict, Any, List

'''


def _generate_safe_execute_decorator() -> str:
    """Generate the safe_execute decorator code.
    
    Returns:
        Decorator function code
    """
    return '''def safe_execute(func):
    """Decorator for safe execution."""
    def wrapper(*args, **kwargs):
        try:
            return {"success": True, "data": func(*args, **kwargs)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return wrapper

'''


def _generate_cli_info_comments(service: str, knowledge: Dict[str, Any]) -> str:
    """Generate CLI information comments.
    
    Args:
        service: Service name
        knowledge: Discovered knowledge
        
    Returns:
        Comments string
    """
    return f'''# Discovered CLI Information:
# Available: {knowledge.get("available", False)}
# Subcommands: {knowledge.get("subcommands", [])[:10]}
# Global Flags: {knowledge.get("global_flags", [])[:10]}
# Auth Required: {knowledge.get("patterns", {}).get("auth_required", False)}

'''


def _generate_crud_functions(
    service: str, 
    knowledge: Dict[str, Any]
) -> Tuple[List[str], Dict[str, Any]]:
    """Generate functions for CRUD operations.
    
    Args:
        service: Service name
        knowledge: Discovered knowledge
        
    Returns:
        Tuple of (function_list, tools_dict)
    """
    functions = []
    tools = {}
    
    if "patterns" not in knowledge or not knowledge["patterns"]["crud_operations"]:
        return functions, tools
    
    for op in knowledge["patterns"]["crud_operations"]:
        func_name = f"{op['operation']}_{op['command'].replace('-', '_')}"
        
        # Generate function code
        function_code = _generate_crud_function_code(service, op, func_name)
        functions.append(function_code)
        
        # Generate tool definition
        tool_def = _generate_crud_tool_definition(service, op, func_name)
        tools.update(tool_def)
    
    return functions, tools


def _generate_crud_function_code(service: str, op: Dict[str, Any], func_name: str) -> str:
    """Generate code for a single CRUD function.
    
    Args:
        service: Service name
        op: Operation details
        func_name: Function name
        
    Returns:
        Function code string
    """
    return f'''
@safe_execute
def {func_name}(**kwargs):
    """Execute {service} {op['command']} command."""
    cmd = ["{service}", "{op['command']}"]
    
    # Add arguments from kwargs
    for key, value in kwargs.items():
        if key.startswith("flag_"):
            cmd.append(f"--{{key[5:].replace('_', '-')}}")
            if value is not True:  # For boolean flags
                cmd.append(str(value))
        else:
            cmd.append(str(value))
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {{result.stderr}}")
    
    # Try to parse JSON output
    try:
        return json.loads(result.stdout)
    except:
        return result.stdout
'''


def _generate_crud_tool_definition(
    service: str, 
    op: Dict[str, Any], 
    func_name: str
) -> Dict[str, Any]:
    """Generate tool definition for a CRUD operation.
    
    Args:
        service: Service name
        op: Operation details
        func_name: Function name
        
    Returns:
        Tool definition dict
    """
    return {
        f"{service}.{func_name}": {
            "version": "1.0",
            "description": f"Execute {service} {op['command']} command",
            "schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": True
            },
            "func": func_name
        }
    }


def _generate_example_function(service: str, knowledge: Dict[str, Any]) -> str:
    """Generate example function code.
    
    Args:
        service: Service name
        knowledge: Discovered knowledge with examples
        
    Returns:
        Example function code
    """
    example_func = f'''
@safe_execute
def run_example():
    """Run an example {service} command."""
    # Example commands discovered:
'''
    for example in knowledge["examples"]:
        example_func += f'    # {example}\n'
    
    example_func += f'''    
    # Running first example
    cmd = "{knowledge["examples"][0] if knowledge["examples"] else service + ' --help'}".split()
    result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ)
    return result.stdout
'''
    return example_func


def _assemble_plugin_content(
    header: str,
    imports: str,
    safe_execute: str,
    cli_info: str,
    functions: List[str],
    tools: Dict[str, Any]
) -> str:
    """Assemble all plugin components into final content.
    
    Args:
        header: Plugin header
        imports: Import statements
        safe_execute: Decorator code
        cli_info: CLI info comments
        functions: List of function codes
        tools: Tools dictionary
        
    Returns:
        Complete plugin code
    """
    plugin_content = header + imports + safe_execute + cli_info
    plugin_content += "\n".join(functions)
    plugin_content += "\n\n# Auto-generated TOOLS\nTOOLS = " + json.dumps(tools, indent=4)
    plugin_content = plugin_content.replace('"func": "', '"func": ')
    
    return plugin_content