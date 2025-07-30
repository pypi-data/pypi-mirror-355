"""GraphQL Schema Parser for agtOS.

This parser handles GraphQL schema discovery through:
- Introspection queries to GraphQL endpoints
- Parsing schema files (SDL format)
- Extracting queries, mutations, subscriptions
- Handling types, fields, arguments
- Building query/mutation templates
"""

import json
import logging
import re
import requests
from typing import Dict, Any, List, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


# Standard GraphQL introspection query
INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


class GraphQLParser:
    """Parser for GraphQL schemas."""
    
    def __init__(self):
        self.schema = None
        self.type_map = {}
        self.query_type = None
        self.mutation_type = None
        self.subscription_type = None
    
    def parse(self, content: str, is_url: bool = False, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Parse GraphQL schema from introspection or SDL.
        
        Args:
            content: URL to GraphQL endpoint or schema SDL string
            is_url: Whether content is a URL (True) or schema string (False)
            headers: Optional headers for the request (e.g., authorization)
            
        Returns:
            Dictionary with parsed GraphQL information
        """
        try:
            if is_url:
                # Perform introspection query
                return self._introspect_endpoint(content, headers)
            else:
                # Parse SDL schema
                return self._parse_sdl(content)
                
        except Exception as e:
            logger.error(f"GraphQL parser error: {e}")
            return {
                "success": False,
                "error": str(e),
                "endpoints": []
            }
    
    def _introspect_endpoint(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform introspection query on GraphQL endpoint."""
        if headers is None:
            headers = {}
        
        # Ensure content-type for GraphQL
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("Accept", "application/json")
        
        # Prepare introspection request
        payload = {
            "query": INTROSPECTION_QUERY,
            "variables": {}
        }
        
        try:
            # Try POST first (most common)
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 405:
                # Method not allowed, try GET
                response = requests.get(
                    url,
                    params={"query": INTROSPECTION_QUERY},
                    headers=headers,
                    timeout=10
                )
            
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                # Check if introspection is disabled
                error_messages = [e.get("message", "") for e in data["errors"]]
                if any("introspection" in msg.lower() for msg in error_messages):
                    return {
                        "success": False,
                        "error": "Introspection is disabled on this GraphQL endpoint",
                        "endpoints": [],
                        "introspection_disabled": True
                    }
                else:
                    return {
                        "success": False,
                        "error": f"GraphQL errors: {'; '.join(error_messages)}",
                        "endpoints": []
                    }
            
            if "data" not in data or "__schema" not in data["data"]:
                return {
                    "success": False,
                    "error": "Invalid introspection response",
                    "endpoints": []
                }
            
            # Parse the introspection result
            return self._parse_introspection(data["data"]["__schema"], url)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to introspect GraphQL endpoint: {e}")
            return {
                "success": False,
                "error": f"Failed to connect to GraphQL endpoint: {str(e)}",
                "endpoints": []
            }
    
    def _parse_sdl(self, sdl: str) -> Dict[str, Any]:
        """Parse GraphQL SDL (Schema Definition Language).
        
        This is a simplified parser for common patterns.
        For production use, consider using graphql-core library.
        """
        result = {
            "success": True,
            "name": "GraphQL Schema",
            "description": "Parsed from SDL",
            "endpoints": [],
            "types": {},
            "scalars": set(["String", "Int", "Float", "Boolean", "ID"])
        }
        
        # Extract type definitions
        type_pattern = r'type\s+(\w+)\s*(?:implements\s+[^{]+)?\s*{([^}]+)}'
        for match in re.finditer(type_pattern, sdl, re.MULTILINE | re.DOTALL):
            type_name = match.group(1)
            fields_block = match.group(2)
            
            fields = self._parse_sdl_fields(fields_block)
            result["types"][type_name] = {
                "name": type_name,
                "kind": "OBJECT",
                "fields": fields
            }
            
            # Check if it's a root type
            if type_name in ["Query", "Mutation", "Subscription"]:
                for field_name, field_info in fields.items():
                    result["endpoints"].append({
                        "name": field_name,
                        "type": type_name.lower(),  # query, mutation, subscription
                        "description": field_info.get("description", ""),
                        "args": field_info.get("args", []),
                        "return_type": field_info.get("type", "Unknown")
                    })
        
        # Extract input types
        input_pattern = r'input\s+(\w+)\s*{([^}]+)}'
        for match in re.finditer(input_pattern, sdl, re.MULTILINE | re.DOTALL):
            type_name = match.group(1)
            fields_block = match.group(2)
            
            fields = self._parse_sdl_fields(fields_block)
            result["types"][type_name] = {
                "name": type_name,
                "kind": "INPUT_OBJECT",
                "inputFields": fields
            }
        
        # Extract enums
        enum_pattern = r'enum\s+(\w+)\s*{([^}]+)}'
        for match in re.finditer(enum_pattern, sdl, re.MULTILINE | re.DOTALL):
            enum_name = match.group(1)
            values_block = match.group(2)
            
            values = [v.strip() for v in values_block.strip().split('\n') if v.strip()]
            result["types"][enum_name] = {
                "name": enum_name,
                "kind": "ENUM",
                "enumValues": [{"name": v} for v in values]
            }
        
        # Extract scalar definitions
        scalar_pattern = r'scalar\s+(\w+)'
        for match in re.finditer(scalar_pattern, sdl):
            result["scalars"].add(match.group(1))
        
        return result
    
    def _parse_sdl_fields(self, fields_block: str) -> Dict[str, Any]:
        """Parse fields from SDL field block."""
        fields = {}
        
        # Match field definitions: fieldName(args): ReturnType
        field_pattern = r'(\w+)\s*(?:\(([^)]*)\))?\s*:\s*([^\n]+)'
        
        for match in re.finditer(field_pattern, fields_block):
            field_name = match.group(1)
            args_str = match.group(2) or ""
            return_type = match.group(3).strip()
            
            field_info = {
                "name": field_name,
                "type": return_type,
                "args": []
            }
            
            # Parse arguments if present
            if args_str:
                arg_pattern = r'(\w+)\s*:\s*([^,\n]+)'
                for arg_match in re.finditer(arg_pattern, args_str):
                    arg_name = arg_match.group(1)
                    arg_type = arg_match.group(2).strip()
                    field_info["args"].append({
                        "name": arg_name,
                        "type": arg_type
                    })
            
            fields[field_name] = field_info
        
        return fields
    
    def _parse_introspection(self, schema_data: Dict[str, Any], endpoint_url: str) -> Dict[str, Any]:
        """Parse introspection query result."""
        self.schema = schema_data
        
        # Build type map
        for type_data in schema_data.get("types", []):
            self.type_map[type_data["name"]] = type_data
        
        # Get root types
        query_type_name = schema_data.get("queryType", {}).get("name") if schema_data.get("queryType") else None
        mutation_type_name = schema_data.get("mutationType", {}).get("name") if schema_data.get("mutationType") else None
        subscription_type_name = schema_data.get("subscriptionType", {}).get("name") if schema_data.get("subscriptionType") else None
        
        self.query_type = self.type_map.get(query_type_name) if query_type_name else None
        self.mutation_type = self.type_map.get(mutation_type_name) if mutation_type_name else None
        self.subscription_type = self.type_map.get(subscription_type_name) if subscription_type_name else None
        
        result = {
            "success": True,
            "name": "GraphQL API",
            "description": f"GraphQL schema from {endpoint_url}",
            "base_url": endpoint_url,
            "endpoints": [],
            "types": {},
            "statistics": {
                "total_types": len(self.type_map),
                "queries": 0,
                "mutations": 0,
                "subscriptions": 0
            }
        }
        
        # Extract queries
        if self.query_type:
            queries = self._extract_operations(self.query_type, "query")
            result["endpoints"].extend(queries)
            result["statistics"]["queries"] = len(queries)
        
        # Extract mutations
        if self.mutation_type:
            mutations = self._extract_operations(self.mutation_type, "mutation")
            result["endpoints"].extend(mutations)
            result["statistics"]["mutations"] = len(mutations)
        
        # Extract subscriptions
        if self.subscription_type:
            subscriptions = self._extract_operations(self.subscription_type, "subscription")
            result["endpoints"].extend(subscriptions)
            result["statistics"]["subscriptions"] = len(subscriptions)
        
        # Include important custom types
        custom_types = self._extract_custom_types()
        result["types"] = custom_types
        
        # Generate tool suggestions
        result["suggested_tools"] = self._suggest_tools(result["endpoints"])
        
        return result
    
    def _extract_operations(self, root_type: Dict[str, Any], operation_type: str) -> List[Dict[str, Any]]:
        """Extract operations (queries/mutations/subscriptions) from root type."""
        operations = []
        
        for field in root_type.get("fields", []):
            # Skip deprecated fields by default
            if field.get("isDeprecated", False):
                continue
            
            # Skip introspection fields
            if field["name"].startswith("__"):
                continue
            
            operation = {
                "name": field["name"],
                "type": operation_type,
                "description": field.get("description", ""),
                "args": [],
                "return_type": self._format_type(field["type"]),
                "return_type_details": field["type"],
                "query_template": None
            }
            
            # Extract arguments
            for arg in field.get("args", []):
                arg_info = {
                    "name": arg["name"],
                    "type": self._format_type(arg["type"]),
                    "type_details": arg["type"],
                    "description": arg.get("description", ""),
                    "default_value": arg.get("defaultValue"),
                    "required": self._is_required_type(arg["type"])
                }
                operation["args"].append(arg_info)
            
            # Generate query template
            operation["query_template"] = self._generate_query_template(operation)
            
            operations.append(operation)
        
        return operations
    
    def _format_type(self, type_ref: Dict[str, Any]) -> str:
        """Format GraphQL type reference to human-readable string."""
        if type_ref["kind"] == "NON_NULL":
            return f"{self._format_type(type_ref['ofType'])}!"
        elif type_ref["kind"] == "LIST":
            return f"[{self._format_type(type_ref['ofType'])}]"
        else:
            return type_ref.get("name", "Unknown")
    
    def _is_required_type(self, type_ref: Dict[str, Any]) -> bool:
        """Check if a type is required (NON_NULL)."""
        return type_ref.get("kind") == "NON_NULL"
    
    def _extract_custom_types(self) -> Dict[str, Any]:
        """Extract important custom types (excluding built-ins)."""
        custom_types = {}
        
        # Built-in types to exclude
        builtin_prefixes = ["__", "String", "Int", "Float", "Boolean", "ID"]
        
        for type_name, type_data in self.type_map.items():
            # Skip built-in types
            if any(type_name.startswith(prefix) for prefix in builtin_prefixes):
                continue
            
            # Skip root types
            if type_name in [self.query_type.get("name") if self.query_type else None,
                           self.mutation_type.get("name") if self.mutation_type else None,
                           self.subscription_type.get("name") if self.subscription_type else None]:
                continue
            
            # Include objects, input objects, and enums
            if type_data["kind"] in ["OBJECT", "INPUT_OBJECT", "ENUM", "INTERFACE", "UNION"]:
                custom_types[type_name] = {
                    "name": type_name,
                    "kind": type_data["kind"],
                    "description": type_data.get("description", "")
                }
                
                # Add fields for objects
                if type_data["kind"] == "OBJECT" and "fields" in type_data:
                    custom_types[type_name]["fields"] = [
                        {
                            "name": f["name"],
                            "type": self._format_type(f["type"]),
                            "description": f.get("description", "")
                        }
                        for f in type_data["fields"]
                        if not f["name"].startswith("__")
                    ]
                
                # Add input fields for input objects
                elif type_data["kind"] == "INPUT_OBJECT" and "inputFields" in type_data:
                    custom_types[type_name]["inputFields"] = [
                        {
                            "name": f["name"],
                            "type": self._format_type(f["type"]),
                            "description": f.get("description", "")
                        }
                        for f in type_data["inputFields"]
                    ]
                
                # Add enum values
                elif type_data["kind"] == "ENUM" and "enumValues" in type_data:
                    custom_types[type_name]["values"] = [
                        v["name"] for v in type_data["enumValues"]
                        if not v.get("isDeprecated", False)
                    ]
        
        return custom_types
    
    def _generate_query_template(self, operation: Dict[str, Any]) -> str:
        """Generate a template query/mutation for the operation."""
        op_type = operation["type"]
        op_name = operation["name"]
        
        # Build arguments string
        args_str = ""
        variables_str = ""
        
        if operation["args"]:
            arg_parts = []
            var_parts = []
            
            for arg in operation["args"]:
                arg_name = arg["name"]
                arg_type = arg["type"]
                
                # Add to operation arguments
                arg_parts.append(f"{arg_name}: ${arg_name}")
                
                # Add to variables declaration
                var_parts.append(f"${arg_name}: {arg_type}")
            
            args_str = f"({', '.join(arg_parts)})"
            variables_str = f"({', '.join(var_parts)})"
        
        # Build the template
        # Capitalize first letter while preserving the rest of the name
        operation_name = op_name[0].upper() + op_name[1:] if op_name else op_name
        
        if op_type == "query":
            template = f"""query {operation_name}{variables_str} {{
  {op_name}{args_str} {{
    # Add fields to select here
    __typename
  }}
}}"""
        elif op_type == "mutation":
            template = f"""mutation {operation_name}{variables_str} {{
  {op_name}{args_str} {{
    # Add fields to return here
    __typename
  }}
}}"""
        else:  # subscription
            template = f"""subscription {operation_name}{variables_str} {{
  {op_name}{args_str} {{
    # Add fields to subscribe to here
    __typename
  }}
}}"""
        
        return template
    
    def _suggest_tools(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate tool suggestions based on discovered operations."""
        suggestions = []
        
        # Group by operation type
        queries = [ep for ep in endpoints if ep.get("type") == "query"]
        mutations = [ep for ep in endpoints if ep.get("type") == "mutation"]
        subscriptions = [ep for ep in endpoints if ep.get("type") == "subscription"]
        
        # Suggest a comprehensive GraphQL tool if there are enough operations
        if len(endpoints) >= 5:
            suggestions.append({
                "tool_name": "graphql_api",
                "description": "Comprehensive GraphQL API client",
                "operations_count": len(endpoints),
                "operation_breakdown": {
                    "queries": len(queries),
                    "mutations": len(mutations),
                    "subscriptions": len(subscriptions)
                }
            })
        
        # Group by operation prefix (e.g., getUser, getUserById -> user operations)
        operation_groups = {}
        
        for endpoint in endpoints:
            name = endpoint["name"]
            
            # Extract resource name
            # Common patterns: getUser, createUser, users, user
            resource = None
            
            # Pattern 1: verbNoun (e.g., getUser)
            verb_noun_match = re.match(r'(get|create|update|delete|list)([A-Z]\w+)', name)
            if verb_noun_match:
                resource = verb_noun_match.group(2).lower()
            # Pattern 2: plural or singular noun
            elif name.endswith('s') and len(name) > 2:
                resource = name[:-1]  # Remove 's' for plural
            else:
                resource = name
            
            if resource not in operation_groups:
                operation_groups[resource] = []
            operation_groups[resource].append(endpoint)
        
        # Create suggestions for each group
        for resource, operations in operation_groups.items():
            if len(operations) >= 2:  # Only suggest if there are multiple related operations
                op_types = set(op["type"] for op in operations)
                
                suggestion = {
                    "tool_name": f"graphql_{resource}",
                    "description": f"GraphQL operations for {resource}",
                    "operations_count": len(operations),
                    "operation_types": list(op_types),
                    "sample_operations": [op["name"] for op in operations[:3]]
                }
                suggestions.append(suggestion)
        
        return suggestions[:5]  # Limit to top 5 suggestions