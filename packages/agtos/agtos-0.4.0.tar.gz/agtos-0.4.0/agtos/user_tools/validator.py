"""Tool validation for generated tools.

This module validates that generated tools work correctly before registration.

AI_CONTEXT:
    Validation is critical for user trust. We need to ensure that:
    - Generated code is syntactically correct
    - The tool can be imported without errors
    - Basic functionality works (at least structurally)
    - Security checks pass (no dangerous operations)
    - The tool integrates properly with Meta-MCP
"""

import ast
import sys
import logging
import tempfile
import importlib.util
from typing import List, Optional, Tuple
from pathlib import Path

from .models import GeneratedTool

logger = logging.getLogger(__name__)


class ToolValidator:
    """Validates generated tools for safety and correctness.
    
    AI_CONTEXT: This ensures we don't register broken or dangerous tools.
    Validation includes syntax checking, import testing, and basic
    security scanning.
    """
    
    # Dangerous operations we don't allow in generated code
    DANGEROUS_IMPORTS = {
        'subprocess', 'os.system', 'eval', 'exec', 
        '__import__', 'compile', 'open'
    }
    
    # Required imports for a valid tool
    REQUIRED_IMPORTS = {
        'requests',  # For API calls
        'agtos.errors'  # For proper error handling
    }
    
    def validate(self, tool: GeneratedTool) -> Tuple[bool, List[str]]:
        """Validate a generated tool.
        
        Args:
            tool: The generated tool to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Syntax validation
        syntax_valid, syntax_errors = self._validate_syntax(tool.tool_code)
        if not syntax_valid:
            errors.extend(syntax_errors)
            return False, errors
        
        # Security validation
        security_valid, security_errors = self._validate_security(tool.tool_code)
        if not security_valid:
            errors.extend(security_errors)
            return False, errors
        
        # Structure validation
        structure_valid, structure_errors = self._validate_structure(tool.tool_code)
        if not structure_valid:
            errors.extend(structure_errors)
        
        # Import validation (if no critical errors)
        if not errors:
            import_valid, import_errors = self._validate_import(tool)
            if not import_valid:
                errors.extend(import_errors)
        
        # Update tool validation status
        if errors:
            tool.validation_status = "failed"
            tool.validation_errors = errors
        else:
            tool.validation_status = "passed"
            tool.validation_errors = []
        
        return len(errors) == 0, errors
    
    def _validate_syntax(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            return False, [f"Syntax error at line {e.lineno}: {e.msg}"]
        except Exception as e:
            return False, [f"Failed to parse code: {str(e)}"]
    
    def _validate_security(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code for security issues."""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            # Check for dangerous imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_IMPORTS:
                            errors.append(
                                f"Dangerous import detected: {alias.name}"
                            )
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.DANGEROUS_IMPORTS:
                        errors.append(
                            f"Dangerous import detected: {node.module}"
                        )
                
                # Check for dangerous function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile']:
                            errors.append(
                                f"Dangerous function call: {node.func.id}"
                            )
        
        except Exception as e:
            errors.append(f"Security validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_structure(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code structure and requirements."""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            # Check for required imports
            found_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        found_imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        found_imports.add(node.module)
            
            # Check if we have at least some required imports
            if not any(imp in str(found_imports) for imp in ['requests', 'agtos']):
                errors.append(
                    "Missing required imports for API tool functionality"
                )
            
            # Check for class definition
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            if not classes:
                errors.append("No class definition found in generated code")
            
            # Check for get_tool_info function
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            if not any(f.name == 'get_tool_info' for f in functions):
                errors.append("Missing get_tool_info() function for registration")
        
        except Exception as e:
            errors.append(f"Structure validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_import(self, tool: GeneratedTool) -> Tuple[bool, List[str]]:
        """Validate that the tool can be imported and instantiated.
        
        AI_CONTEXT: Tests if generated code can be loaded as a Python module
        and has the required structure. Uses temporary file and isolated
        module loading to avoid conflicts.
        """
        errors = []
        temp_path = None
        module_name = None
        
        try:
            # Write tool code to temporary file
            temp_path = self._write_tool_to_temp_file(tool)
            
            # Create and load module
            module, module_name = self._create_module_from_file(
                tool.specification.name, temp_path
            )
            
            if module:
                # Validate module structure
                module_errors = self._validate_module_structure(module)
                errors.extend(module_errors)
            else:
                errors.append("Failed to create module from generated code")
        
        except ImportError as e:
            errors.append(f"Import error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        finally:
            # Clean up resources
            self._cleanup_temp_resources(temp_path, module_name)
        
        return len(errors) == 0, errors
    
    def _write_tool_to_temp_file(self, tool: GeneratedTool) -> str:
        """Write tool code to a temporary file.
        
        Args:
            tool: The generated tool
            
        Returns:
            Path to the temporary file
        """
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(tool.tool_code)
            return f.name
    
    def _create_module_from_file(
        self, 
        tool_name: str, 
        file_path: str
    ) -> Tuple[Optional[object], Optional[str]]:
        """Create and load a module from file.
        
        Args:
            tool_name: Name of the tool
            file_path: Path to the Python file
            
        Returns:
            Tuple of (module object, module name) or (None, None) on failure
        """
        module_name = f"user_tool_{tool_name}"
        
        # Create module spec
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        
        if not spec or not spec.loader:
            return None, None
        
        # Create module and add to sys.modules
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        
        try:
            # Execute the module
            spec.loader.exec_module(module)
            return module, module_name
        except Exception:
            # Clean up on failure
            if module_name in sys.modules:
                del sys.modules[module_name]
            raise
    
    def _validate_module_structure(self, module: object) -> List[str]:
        """Validate the structure of an imported module.
        
        Args:
            module: The imported module
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for get_tool_info function
        if not hasattr(module, 'get_tool_info'):
            errors.append("Module missing get_tool_info() function")
            return errors
        
        # Validate tool info structure
        try:
            tool_info = module.get_tool_info()
            
            if not isinstance(tool_info, dict):
                errors.append("get_tool_info() must return a dictionary")
            elif 'instance' not in tool_info:
                errors.append("get_tool_info() must include 'instance' key")
        except Exception as e:
            errors.append(f"Error calling get_tool_info(): {str(e)}")
        
        return errors
    
    def _cleanup_temp_resources(
        self, 
        temp_path: Optional[str], 
        module_name: Optional[str]
    ) -> None:
        """Clean up temporary file and module registration.
        
        Args:
            temp_path: Path to temporary file
            module_name: Name of module in sys.modules
        """
        # Clean up temp file
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        
        # Clean up sys.modules
        if module_name and module_name in sys.modules:
            del sys.modules[module_name]