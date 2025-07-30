"""GraphQL-specific tool generator for agtOS.

This generator creates tools that build and execute GraphQL queries/mutations.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from textwrap import dedent, indent

logger = logging.getLogger(__name__)


class GraphQLToolGenerator:
    """Generates GraphQL-specific tool code."""
    
    def generate_graphql_tool(self, 
                            tool_name: str,
                            endpoint_url: str,
                            operations: List[Dict[str, Any]],
                            auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete GraphQL tool.
        
        Args:
            tool_name: Name for the tool
            endpoint_url: GraphQL endpoint URL
            operations: List of GraphQL operations from discovery
            auth_config: Optional authentication configuration
            
        Returns:
            Dict with tool_code and mcp_schema
        """
        # Generate imports
        imports = self._generate_imports()
        
        # Generate methods for each operation
        methods = []
        mcp_methods = {}
        
        for op in operations:
            method_code = self._generate_operation_method(op)
            methods.append(method_code)
            
            # Create MCP schema entry
            mcp_methods[op["name"]] = self._generate_mcp_schema_for_operation(op)
        
        # Generate class definition with methods
        class_def = self._generate_class(tool_name, endpoint_url, auth_config, methods)
        
        # Combine all code
        tool_code = f"""{imports}

{class_def}

def get_tools():
    \"\"\"Return tool instance for Meta-MCP.\"\"\"
    return {tool_name}()

def get_tool_schemas():
    \"\"\"Return MCP schemas for all methods.\"\"\"
    return {json.dumps(mcp_methods, indent=4)}
"""
        
        return {
            "tool_code": tool_code,
            "mcp_schema": mcp_methods
        }
    
    def _generate_imports(self) -> str:
        """Generate import statements."""
        return dedent("""
        import os
        import json
        import logging
        from typing import Dict, Any, Optional, List
        import requests
        from requests.exceptions import RequestException
        from agtos.utils.errors import ToolExecutionError
        
        logger = logging.getLogger(__name__)
        """).strip()
    
    def _generate_class(self, tool_name: str, endpoint_url: str, auth_config: Optional[Dict[str, Any]], methods: List[str]) -> str:
        """Generate class definition."""
        class_name = self._to_class_name(tool_name)
        
        auth_init = ""
        if auth_config:
            if auth_config.get("type") == "bearer":
                auth_init = '''
        # Setup authentication
        token = os.environ.get("GRAPHQL_API_TOKEN")
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        '''
            elif auth_config.get("type") == "api_key":
                key_name = auth_config.get("key_name", "X-API-Key")
                auth_init = f'''
        # Setup authentication
        api_key = os.environ.get("GRAPHQL_API_KEY")
        if api_key:
            self.headers["{key_name}"] = api_key
        '''
        
        # Format the class template
        class_code = f"""class {class_name}:
    \"\"\"GraphQL API client for {endpoint_url}.\"\"\"
    
    def __init__(self):
        self.endpoint = "{endpoint_url}"
        self.session = requests.Session()
        self.headers = {{
            "Content-Type": "application/json",
            "Accept": "application/json"
        }}{auth_init}
    
    def _execute_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"Execute a GraphQL query/mutation.\"\"\"
        payload = {{
            "query": query,
            "variables": variables or {{}}
        }}
        
        try:
            response = self.session.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                error_messages = [e.get("message", str(e)) for e in result["errors"]]
                raise ToolExecutionError(
                    "{tool_name}",
                    f"GraphQL errors: {{'; '.join(error_messages)}}"
                )
            
            return result.get("data", {{}})
            
        except RequestException as e:
            logger.error(f"GraphQL request failed: {{e}}")
            raise ToolExecutionError("{tool_name}", f"Request failed: {{str(e)}}")
        except Exception as e:
            logger.error(f"Unexpected error: {{e}}")
            raise ToolExecutionError("{tool_name}", f"Error: {{str(e)}}")
    
    def _build_fields_selection(self, fields: Optional[List[str]], return_type: str) -> str:
        \"\"\"Build GraphQL fields selection.\"\"\"
        if fields:
            return "\\n                ".join(fields)
        else:
            # Default to common fields
            return \"\"\"__typename
        id
        name
        description
        createdAt
        updatedAt\"\"\"
"""
        
        # Add methods to class
        methods_indented = []
        for method in methods:
            # Indent each line of the method by 4 spaces
            lines = method.strip().split('\n')
            indented_lines = ['    ' + line if line.strip() else line for line in lines]
            methods_indented.append('\n'.join(indented_lines))
        
        # Add methods to class code
        class_code = class_code.rstrip() + '\n\n' + '\n\n'.join(methods_indented)
        
        return class_code
    
    def _generate_operation_method(self, operation: Dict[str, Any]) -> str:
        """Generate method for a GraphQL operation."""
        method_name = self._to_method_name(operation["name"])
        op_type = operation.get("type", "query")
        
        # Generate parameter list
        params = ["self"]
        param_docs = []
        
        for arg in operation.get("args", []):
            param_name = self._sanitize_param_name(arg["name"])
            param_type = self._graphql_to_python_type(arg["type"])
            
            if arg.get("required", False):
                params.append(f"{param_name}: {param_type}")
            else:
                default = arg.get("default_value", "None")
                params.append(f"{param_name}: Optional[{param_type}] = {default}")
            
            param_docs.append(f"        {param_name}: {arg.get('description', 'No description')}")
        
        # Add fields parameter for selecting return fields
        params.append("fields: Optional[List[str]] = None")
        param_docs.append("        fields: List of fields to return (defaults to all scalar fields)")
        
        params_str = ", ".join(params)
        
        # Generate variables dict
        variables_lines = []
        for arg in operation.get("args", []):
            param_name = self._sanitize_param_name(arg["name"])
            if arg.get("required", False):
                variables_lines.append(f'            "{arg["name"]}": {param_name},')
            else:
                variables_lines.append(f'            "{arg["name"]}": {param_name} if {param_name} is not None else None,')
        
        variables_code = ""
        if variables_lines:
            variables_code = f"""
        # Build variables
        variables = {{
{chr(10).join(variables_lines)}
        }}
        # Remove None values
        variables = {{k: v for k, v in variables.items() if v is not None}}
        """
        
        # Capitalize first letter while preserving the rest
        operation_name = operation['name'][0].upper() + operation['name'][1:] if operation['name'] else operation['name']
        
        # Generate the method
        method_template = dedent(f"""
def {method_name}({params_str}) -> Dict[str, Any]:
    \"\"\"{operation.get('description', f'Execute {operation["name"]} {op_type}.')}
    
    Args:
{chr(10).join(param_docs)}
        
    Returns:
        GraphQL response data
    \"\"\"  
{variables_code}
    
    # Build query
    fields_selection = self._build_fields_selection(fields, "{operation.get('return_type', 'Unknown')}")
    
    query = f\"\"\"
    {op_type} {operation_name}({', '.join(f'${arg["name"]}: {arg["type"]}' for arg in operation.get("args", []))}) {{
        {operation['name']}({', '.join(f'{arg["name"]}: ${arg["name"]}' for arg in operation.get("args", []))}) {{
            {{fields_selection}}
        }}
    }}
    \"\"\"
    
    return self._execute_graphql(query, variables)
        """)
        
        return method_template
    
    def _generate_mcp_schema_for_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MCP schema for a GraphQL operation."""
        schema = {
            "description": operation.get("description", f"Execute {operation['name']} GraphQL {operation.get('type', 'query')}"),
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Add parameters from GraphQL args
        for arg in operation.get("args", []):
            param_name = self._sanitize_param_name(arg["name"])
            param_schema = {
                "type": self._graphql_to_json_schema_type(arg["type"]),
                "description": arg.get("description", "")
            }
            
            if "default_value" in arg and arg["default_value"] is not None:
                param_schema["default"] = arg["default_value"]
            
            schema["schema"]["properties"][param_name] = param_schema
            
            if arg.get("required", False):
                schema["schema"]["required"].append(param_name)
        
        # Add fields parameter
        schema["schema"]["properties"]["fields"] = {
            "type": "array",
            "items": {"type": "string"},
            "description": "Fields to return in the response"
        }
        
        return schema
    
    def _to_class_name(self, tool_name: str) -> str:
        """Convert tool name to class name."""
        parts = tool_name.split('_')
        return ''.join(part.capitalize() for part in parts)
    
    def _to_method_name(self, operation_name: str) -> str:
        """Convert GraphQL operation name to Python method name."""
        # camelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', operation_name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return name
    
    def _sanitize_param_name(self, name: str) -> str:
        """Sanitize parameter name for Python."""
        # Replace invalid characters
        name = name.replace('-', '_').replace(' ', '_')
        
        # Handle Python keywords
        if name in ['class', 'def', 'return', 'type', 'id', 'from', 'import']:
            name = f"{name}_param"
        
        return name
    
    def _graphql_to_python_type(self, graphql_type: str) -> str:
        """Convert GraphQL type to Python type annotation."""
        # Remove ! (non-null) for Python types
        type_str = graphql_type.replace('!', '')
        
        # Handle lists
        if type_str.startswith('[') and type_str.endswith(']'):
            inner_type = type_str[1:-1]
            return f"List[{self._graphql_to_python_type(inner_type)}]"
        
        # Map scalar types
        type_mapping = {
            'String': 'str',
            'Int': 'int',
            'Float': 'float',
            'Boolean': 'bool',
            'ID': 'str'
        }
        
        return type_mapping.get(type_str, 'Dict[str, Any]')
    
    def _graphql_to_json_schema_type(self, graphql_type: str) -> str:
        """Convert GraphQL type to JSON Schema type."""
        # Remove ! (non-null)
        type_str = graphql_type.replace('!', '')
        
        # Handle lists
        if type_str.startswith('[') and type_str.endswith(']'):
            return "array"
        
        # Map scalar types
        type_mapping = {
            'String': 'string',
            'Int': 'integer',
            'Float': 'number',
            'Boolean': 'boolean',
            'ID': 'string'
        }
        
        return type_mapping.get(type_str, 'object')