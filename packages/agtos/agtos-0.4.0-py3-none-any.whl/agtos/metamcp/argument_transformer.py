"""Argument transformation and validation for Meta-MCP tools.

AI_CONTEXT:
    This module provides centralized argument handling for all tool types,
    addressing issue #90. It transforms MCP-format arguments into the
    appropriate format for each tool type (CLI, REST, MCP, Plugin) and
    validates them against tool schemas.
    
    Key features:
    - Type conversion based on JSON schema
    - Required vs optional argument validation
    - Complex type handling (arrays, objects)
    - Clear error messages for validation failures
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from .types import ToolSpec

logger = logging.getLogger(__name__)


class ArgumentType(Enum):
    """Types of arguments we handle."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


@dataclass
class ArgumentValidationError:
    """Details about an argument validation error."""
    argument_name: str
    expected_type: str
    actual_value: Any
    message: str


class ArgumentTransformer:
    """Transforms and validates tool arguments based on schemas.
    
    AI_CONTEXT:
        This is the core class that solves issue #90. It takes MCP-format
        arguments and transforms them based on the tool's input schema,
        ensuring proper types and validation.
    """
    
    def __init__(self):
        """Initialize the argument transformer."""
        self.type_converters = {
            ArgumentType.STRING: self._convert_to_string,
            ArgumentType.NUMBER: self._convert_to_number,
            ArgumentType.INTEGER: self._convert_to_integer,
            ArgumentType.BOOLEAN: self._convert_to_boolean,
            ArgumentType.ARRAY: self._convert_to_array,
            ArgumentType.OBJECT: self._convert_to_object,
        }
    
    def transform_arguments(
        self,
        tool_spec: ToolSpec,
        raw_arguments: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[ArgumentValidationError]]:
        """Transform arguments based on tool schema.
        
        Args:
            tool_spec: Tool specification with input schema
            raw_arguments: Raw arguments from MCP request
            
        Returns:
            Tuple of (transformed_arguments, validation_errors)
        """
        schema = tool_spec.inputSchema or {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        transformed = {}
        errors = []
        
        # Validate required arguments
        for req_arg in required:
            if req_arg not in raw_arguments:
                errors.append(ArgumentValidationError(
                    argument_name=req_arg,
                    expected_type=properties.get(req_arg, {}).get("type", "any"),
                    actual_value=None,
                    message=f"Required argument '{req_arg}' is missing"
                ))
        
        # Transform each argument
        for arg_name, arg_value in raw_arguments.items():
            if arg_name not in properties:
                # Unknown argument - pass through as-is
                logger.debug(f"Unknown argument '{arg_name}' for tool {tool_spec.name}")
                transformed[arg_name] = arg_value
                continue
            
            arg_schema = properties[arg_name]
            result, error = self._transform_argument(arg_name, arg_value, arg_schema)
            
            if error:
                errors.append(error)
            else:
                transformed[arg_name] = result
        
        return transformed, errors
    
    def _transform_argument(
        self,
        name: str,
        value: Any,
        schema: Dict[str, Any]
    ) -> Tuple[Any, Optional[ArgumentValidationError]]:
        """Transform a single argument based on its schema.
        
        Args:
            name: Argument name
            value: Raw argument value
            schema: JSON schema for this argument
            
        Returns:
            Tuple of (transformed_value, error)
        """
        # Handle null values
        if value is None:
            if schema.get("nullable", False) or "null" in schema.get("type", []):
                return None, None
            else:
                return None, ArgumentValidationError(
                    argument_name=name,
                    expected_type=schema.get("type", "any"),
                    actual_value=value,
                    message=f"Argument '{name}' cannot be null"
                )
        
        # Get the expected type(s)
        expected_types = schema.get("type", "string")
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        
        # Try each possible type
        for type_name in expected_types:
            try:
                arg_type = ArgumentType(type_name)
                converter = self.type_converters.get(arg_type)
                if converter:
                    return converter(value, schema), None
            except (ValueError, TypeError) as e:
                continue
        
        # No successful conversion
        return value, ArgumentValidationError(
            argument_name=name,
            expected_type=" or ".join(expected_types),
            actual_value=value,
            message=f"Cannot convert '{name}' to {'/'.join(expected_types)}"
        )
    
    def _convert_to_string(self, value: Any, schema: Dict[str, Any]) -> str:
        """Convert value to string."""
        if isinstance(value, str):
            return value
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        else:
            return str(value)
    
    def _convert_to_number(self, value: Any, schema: Dict[str, Any]) -> float:
        """Convert value to number."""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return float(value)
        else:
            raise ValueError(f"Cannot convert {type(value)} to number")
    
    def _convert_to_integer(self, value: Any, schema: Dict[str, Any]) -> int:
        """Convert value to integer."""
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            if value.is_integer():
                return int(value)
            else:
                raise ValueError(f"Float {value} cannot be converted to integer")
        elif isinstance(value, str):
            return int(value)
        else:
            raise ValueError(f"Cannot convert {type(value)} to integer")
    
    def _convert_to_boolean(self, value: Any, schema: Dict[str, Any]) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            elif value.lower() in ("false", "0", "no", "off"):
                return False
            else:
                raise ValueError(f"Cannot convert string '{value}' to boolean")
        elif isinstance(value, (int, float)):
            return bool(value)
        else:
            raise ValueError(f"Cannot convert {type(value)} to boolean")
    
    def _convert_to_array(self, value: Any, schema: Dict[str, Any]) -> List[Any]:
        """Convert value to array."""
        if isinstance(value, list):
            # Validate items if schema provided
            items_schema = schema.get("items", {})
            if items_schema:
                result = []
                for item in value:
                    transformed, error = self._transform_argument(
                        f"array_item",
                        item,
                        items_schema
                    )
                    if error:
                        logger.warning(f"Array item validation error: {error.message}")
                    result.append(transformed if not error else item)
                return result
            return value
        elif isinstance(value, str):
            # Try to parse JSON array
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Treat comma-separated string as array
            return [v.strip() for v in value.split(",")]
        else:
            # Single value becomes single-item array
            return [value]
    
    def _convert_to_object(self, value: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert value to object."""
        if isinstance(value, dict):
            # Validate properties if schema provided
            properties = schema.get("properties", {})
            if properties:
                result = {}
                for key, val in value.items():
                    if key in properties:
                        transformed, error = self._transform_argument(
                            key,
                            val,
                            properties[key]
                        )
                        if error:
                            logger.warning(f"Object property validation error: {error.message}")
                        result[key] = transformed if not error else val
                    else:
                        result[key] = val
                return result
            return value
        elif isinstance(value, str):
            # Try to parse JSON object
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
            raise ValueError(f"Cannot convert string to object: {value}")
        else:
            raise ValueError(f"Cannot convert {type(value)} to object")
    
    def format_for_cli(
        self,
        tool_name: str,
        transformed_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format transformed arguments for CLI execution.
        
        AI_CONTEXT:
            This method takes validated/transformed arguments and formats
            them specifically for CLI tools, handling flags, positional
            arguments, etc.
        
        Args:
            tool_name: Name of the CLI tool
            transformed_args: Already transformed and validated arguments
            
        Returns:
            Dictionary with CLI-specific formatting
        """
        # Extract special CLI arguments
        command = transformed_args.pop("command", None)
        subcommand = transformed_args.pop("subcommand", None)
        arguments = transformed_args.pop("arguments", [])
        extra_args = transformed_args.pop("extra_args", [])
        
        # Format remaining arguments as flags
        flags = {}
        for key, value in transformed_args.items():
            if isinstance(value, bool):
                if value:
                    flags[f"flag_{key}"] = True
            else:
                flags[f"flag_{key}"] = value
        
        result = {}
        if command:
            result["command"] = command
        if subcommand:
            result["subcommand"] = subcommand
        if arguments:
            result["arguments"] = arguments
        if extra_args:
            result["extra_args"] = extra_args
        
        result.update(flags)
        return result
    
    def format_for_rest(
        self,
        endpoint: str,
        method: str,
        transformed_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format transformed arguments for REST API execution.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            transformed_args: Already transformed and validated arguments
            
        Returns:
            Dictionary with REST-specific formatting
        """
        # Separate path params, query params, headers, and body
        result = {
            "path_params": {},
            "query_params": {},
            "headers": {},
            "body": None
        }
        
        # Extract path parameters from endpoint
        import re
        path_param_pattern = re.compile(r'\{(\w+)\}')
        path_params = path_param_pattern.findall(endpoint)
        
        for param in path_params:
            if param in transformed_args:
                result["path_params"][param] = transformed_args.pop(param)
        
        # Extract known headers
        header_keys = ["authorization", "content-type", "accept", "user-agent"]
        for key in list(transformed_args.keys()):
            if key.lower() in header_keys or key.lower().startswith("x-"):
                result["headers"][key] = transformed_args.pop(key)
        
        # For GET/DELETE, remaining args are query params
        if method.upper() in ["GET", "DELETE"]:
            result["query_params"] = transformed_args
        else:
            # For POST/PUT/PATCH, args become body
            if transformed_args:
                result["body"] = transformed_args
        
        return result