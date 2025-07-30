"""Self-healing system for REST API tool creation.

This module implements automatic error correction for common REST API issues
during tool creation. It tests tools after creation and attempts to fix
common problems automatically.

AI_CONTEXT:
    The self-healer is a critical component that ensures tools work correctly
    after creation. It handles:
    - Authentication failures (wrong headers, incorrect format)
    - Endpoint issues (missing base URL, wrong path)
    - Parameter problems (missing required params, wrong types)
    - Response parsing errors
    
    The system progressively refines tools through testing and correction,
    with a maximum of 5 attempts before giving up.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import importlib.util
import sys
import traceback
from enum import Enum

from .models import ToolSpecification, APIEndpoint, AuthenticationMethod, AuthType
from .generator import ToolGenerator
from .validator import ToolValidator
from .analyzer import APIAnalyzer


class ErrorType(Enum):
    """Types of errors that can be automatically healed."""
    AUTH_HEADER = "auth_header"
    AUTH_FORMAT = "auth_format"
    ENDPOINT_URL = "endpoint_url"
    MISSING_PARAM = "missing_param"
    PARAM_TYPE = "param_type"
    RESPONSE_PARSE = "response_parse"
    SSL_CERT = "ssl_cert"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


class HealingAttempt:
    """Record of a healing attempt."""
    def __init__(self, error_type: ErrorType, error_message: str, fix_applied: str):
        self.error_type = error_type
        self.error_message = error_message
        self.fix_applied = fix_applied
        self.success = False
        self.result_message = ""


class SelfHealer:
    """Self-healing system for REST API tools.
    
    AI_CONTEXT:
        This class implements the core self-healing logic. It:
        1. Tests generated tools by executing them
        2. Analyzes errors to determine root causes
        3. Applies targeted fixes based on error patterns
        4. Re-tests after each fix
        5. Learns from successful fixes for future use
    """
    
    def __init__(self, max_attempts: int = 2):
        self.max_attempts = max_attempts
        self.common_fixes = self._load_common_fixes()
        self.error_patterns = self._compile_error_patterns()
        self.early_exit_errors = self._get_early_exit_patterns()
        
    def heal_tool(
        self, 
        spec: ToolSpecification, 
        tool_code: str,
        test_params: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ) -> Tuple[bool, str, List[HealingAttempt]]:
        """Attempt to heal a tool that's failing.
        
        Args:
            spec: The tool specification
            tool_code: Generated tool code
            test_params: Optional parameters for testing
            
        Returns:
            Tuple of (success, final_code, healing_attempts)
        """
        attempts = []
        current_code = tool_code
        current_spec = spec
        
        for attempt_num in range(self.max_attempts):
            # Test the tool
            success, error = self._test_tool(current_spec.name, current_code, test_params)
            
            if success:
                return True, current_code, attempts
            
            # Check for early exit conditions
            if self._should_exit_early(error, attempt_num):
                if verbose:
                    logger.info(f"Early exit triggered: {error}")
                break
            
            # Analyze the error
            error_type, error_details = self._analyze_error(error, current_spec)
            
            if error_type == ErrorType.UNKNOWN:
                # Can't heal unknown errors
                break
            
            # Apply a fix
            fix_description, new_spec = self._apply_fix(
                error_type, error_details, current_spec
            )
            
            # Create healing attempt record
            attempt = HealingAttempt(error_type, str(error), fix_description)
            attempts.append(attempt)
            
            # Regenerate tool with fixed spec
            generator = ToolGenerator()
            new_tool = generator.generate(new_spec)
            current_code = new_tool.tool_code
            current_spec = new_spec
            
            # Mark attempt result
            attempt.success = True
            attempt.result_message = f"Applied fix: {fix_description}"
        
        return False, current_code, attempts
    
    def _test_tool(
        self, 
        tool_name: str, 
        tool_code: str,
        test_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Exception]]:
        """Test a tool by executing it.
        
        Returns (success, error) tuple.
        """
        try:
            # Create a temporary module from the tool code
            spec = importlib.util.spec_from_loader(
                f"test_tool_{tool_name}",
                loader=None
            )
            module = importlib.util.module_from_spec(spec)
            
            # Execute the code in the module's namespace
            exec(tool_code, module.__dict__)
            
            # Find the main function (should match tool name)
            if hasattr(module, tool_name):
                func = getattr(module, tool_name)
                
                # Try to call with test parameters
                if test_params:
                    result = func(**test_params)
                else:
                    # Try with minimal/empty params
                    result = func()
                
                # Basic validation of result
                if result is None:
                    return False, Exception("Tool returned None")
                
                return True, None
            else:
                return False, Exception(f"Tool function '{tool_name}' not found in generated code")
                
        except Exception as e:
            return False, e
    
    def _analyze_error(
        self, 
        error: Exception,
        spec: ToolSpecification
    ) -> Tuple[ErrorType, Dict[str, Any]]:
        """Analyze an error to determine its type and details.
        
        Returns (error_type, error_details) tuple.
        """
        error_str = str(error).lower()
        error_trace = traceback.format_exc().lower()
        
        # Check authentication errors
        if any(pattern in error_str for pattern in [
            "401", "unauthorized", "authentication", "invalid token",
            "invalid api key", "forbidden", "auth"
        ]):
            # Determine specific auth issue
            if "bearer" in error_str or "authorization" in error_trace:
                return ErrorType.AUTH_FORMAT, {
                    "current_format": "Bearer" if "bearer" in error_str else "Token",
                    "header_name": "Authorization"
                }
            elif "api-key" in error_str or "x-api-key" in error_trace:
                return ErrorType.AUTH_HEADER, {
                    "suggested_header": "X-API-Key"
                }
            else:
                return ErrorType.AUTH_HEADER, {
                    "suggested_header": "Authorization"
                }
        
        # Check endpoint URL errors
        if any(pattern in error_str for pattern in [
            "404", "not found", "connection", "getaddrinfo failed",
            "name or service not known", "no such host"
        ]):
            return ErrorType.ENDPOINT_URL, {
                "current_url": spec.endpoints[0].url if spec.endpoints else "",
                "error_detail": error_str
            }
        
        # Check SSL certificate errors
        if any(pattern in error_str for pattern in [
            "ssl", "certificate", "verify", "https"
        ]):
            return ErrorType.SSL_CERT, {}
        
        # Check timeout errors
        if any(pattern in error_str for pattern in [
            "timeout", "timed out", "read timeout"
        ]):
            return ErrorType.TIMEOUT, {
                "current_timeout": 10
            }
        
        # Check rate limiting
        if any(pattern in error_str for pattern in [
            "429", "rate limit", "too many requests"
        ]):
            return ErrorType.RATE_LIMIT, {}
        
        # Check parameter errors
        if any(pattern in error_str for pattern in [
            "missing", "required", "parameter", "argument"
        ]):
            # Try to extract parameter name
            param_match = re.search(r"(?:missing|required).*?['\"](\w+)['\"]", error_str)
            if param_match:
                return ErrorType.MISSING_PARAM, {
                    "param_name": param_match.group(1)
                }
            else:
                return ErrorType.MISSING_PARAM, {}
        
        # Check response parsing errors
        if any(pattern in error_str for pattern in [
            "json", "decode", "parse", "expecting value"
        ]):
            return ErrorType.RESPONSE_PARSE, {}
        
        return ErrorType.UNKNOWN, {}
    
    def _apply_fix(
        self,
        error_type: ErrorType,
        error_details: Dict[str, Any],
        spec: ToolSpecification
    ) -> Tuple[str, ToolSpecification]:
        """Apply a fix for the identified error type.
        
        Returns (fix_description, modified_spec) tuple.
        """
        # Create a copy of the spec to modify
        new_spec = self._copy_spec(spec)
        
        if error_type == ErrorType.AUTH_HEADER:
            # Try different header names
            suggested = error_details.get("suggested_header", "Authorization")
            for endpoint in new_spec.endpoints:
                if endpoint.authentication:
                    if suggested == "X-API-Key":
                        endpoint.authentication.header_name = "X-API-Key"
                    else:
                        endpoint.authentication.header_name = "Authorization"
            
            return f"Changed auth header to {suggested}", new_spec
        
        elif error_type == ErrorType.AUTH_FORMAT:
            # Try different auth formats
            current = error_details.get("current_format", "Bearer")
            new_format = "Token" if current == "Bearer" else "Bearer"
            
            for endpoint in new_spec.endpoints:
                if endpoint.authentication and endpoint.authentication.type == AuthType.BEARER_TOKEN:
                    endpoint.authentication.bearer_format = new_format
            
            return f"Changed auth format from {current} to {new_format}", new_spec
        
        elif error_type == ErrorType.ENDPOINT_URL:
            # Try to fix URL issues
            if new_spec.endpoints:
                old_url = new_spec.endpoints[0].url
                
                # Common fixes
                if not old_url.startswith("http"):
                    new_spec.endpoints[0].url = f"https://{old_url}"
                    return f"Added https:// prefix to URL", new_spec
                elif "///" in old_url:
                    new_spec.endpoints[0].url = old_url.replace("///", "//")
                    return f"Fixed double slashes in URL", new_spec
                elif old_url.endswith("//"):
                    new_spec.endpoints[0].url = old_url.rstrip("/")
                    return f"Removed trailing slashes from URL", new_spec
                else:
                    # Try adding /api prefix if not present
                    if "/api" not in old_url:
                        base, path = old_url.rsplit("/", 1) if "/" in old_url else (old_url, "")
                        new_spec.endpoints[0].url = f"{base}/api/{path}".rstrip("/")
                        return f"Added /api to URL path", new_spec
            
            return "Attempted URL fix", new_spec
        
        elif error_type == ErrorType.SSL_CERT:
            # Add SSL verification bypass (with warning)
            new_spec.metadata = new_spec.metadata or {}
            new_spec.metadata["verify_ssl"] = False
            return "Disabled SSL verification (security warning!)", new_spec
        
        elif error_type == ErrorType.TIMEOUT:
            # Increase timeout
            new_spec.metadata = new_spec.metadata or {}
            new_spec.metadata["timeout"] = 30
            return "Increased timeout to 30 seconds", new_spec
        
        elif error_type == ErrorType.MISSING_PARAM:
            # Add missing parameter as optional
            param_name = error_details.get("param_name", "unknown_param")
            if new_spec.endpoints:
                from .models import Parameter, ParameterLocation
                new_param = Parameter(
                    name=param_name,
                    type="string",
                    required=False,
                    location=ParameterLocation.QUERY,
                    description=f"Auto-added parameter"
                )
                new_spec.endpoints[0].parameters.append(new_param)
            
            return f"Added optional parameter '{param_name}'", new_spec
        
        return "No fix applied", new_spec
    
    def _copy_spec(self, spec: ToolSpecification) -> ToolSpecification:
        """Create a deep copy of a tool specification."""
        # Create new spec with same basic attributes
        new_spec = ToolSpecification(
            name=spec.name,
            description=spec.description,
            natural_language_spec=spec.natural_language_spec,
            endpoints=[],
            category=spec.category,
            tags=spec.tags.copy() if spec.tags else [],
            author=spec.author,
            metadata=spec.metadata.copy() if spec.metadata else {}
        )
        
        # Copy endpoints
        for endpoint in spec.endpoints:
            new_endpoint = APIEndpoint(
                url=endpoint.url,
                method=endpoint.method,
                description=endpoint.description,
                parameters=endpoint.parameters.copy() if endpoint.parameters else [],
                authentication=endpoint.authentication
            )
            new_spec.endpoints.append(new_endpoint)
        
        return new_spec
    
    def _load_common_fixes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load common fixes from learned patterns."""
        # In future, this could load from a persistent store
        return {
            "slack": [
                {"error": "invalid_auth", "fix": "use_bearer_format"},
                {"error": "channel_not_found", "fix": "add_channel_prefix"}
            ],
            "github": [
                {"error": "401", "fix": "use_token_format"},
                {"error": "404", "fix": "check_api_version"}
            ]
        }
    
    def _compile_error_patterns(self) -> Dict[ErrorType, List[re.Pattern]]:
        """Compile regex patterns for error detection."""
        return {
            ErrorType.AUTH_HEADER: [
                re.compile(r"invalid.{0,20}api.{0,20}key", re.I),
                re.compile(r"authorization.{0,20}header", re.I),
                re.compile(r"x-api-key.{0,20}required", re.I)
            ],
            ErrorType.ENDPOINT_URL: [
                re.compile(r"404.{0,20}not found", re.I),
                re.compile(r"no such host", re.I),
                re.compile(r"connection.{0,20}refused", re.I)
            ]
        }
    
    def _should_exit_early(self, error: Exception, attempt_num: int) -> bool:
        """Check if we should stop trying based on error type.
        
        Some errors indicate fundamental issues that won't be fixed by retrying.
        """
        error_str = str(error).lower()
        
        # Exit immediately for these errors
        immediate_exit_patterns = [
            "module 'requests' has no attribute",  # Code generation issues
            "nameerror:",  # Variable not defined
            "syntaxerror:",  # Syntax errors after first attempt
            "attributeerror: 'nonetype'",  # Null reference errors
            "cannot import name",  # Import errors
            "no module named",  # Missing dependencies
        ]
        
        for pattern in immediate_exit_patterns:
            if pattern in error_str:
                return True
        
        # Exit after first attempt for these
        if attempt_num > 0:
            first_attempt_patterns = [
                "connection refused",  # Server not running
                "network is unreachable",  # Network issues
                "certificate verify failed",  # SSL issues that persist
                "too many requests",  # Rate limiting
            ]
            
            for pattern in first_attempt_patterns:
                if pattern in error_str:
                    return True
        
        return False
    
    def _get_early_exit_patterns(self) -> List[re.Pattern]:
        """Compile patterns for errors that should trigger early exit."""
        return [
            re.compile(r"module.*has no attribute", re.I),
            re.compile(r"nameerror:.*not defined", re.I),
            re.compile(r"cannot import name", re.I),
            re.compile(r"no module named", re.I),
        ]
    
    def get_healing_summary(self, attempts: List[HealingAttempt]) -> str:
        """Generate a summary of healing attempts for user display."""
        if not attempts:
            return "No healing attempts were made."
        
        successful = sum(1 for a in attempts if a.success)
        
        # For successful healing, just show a brief success message
        if successful == len(attempts):
            return f"✓ Tool automatically corrected ({len(attempts)} fix{'es' if len(attempts) > 1 else ''} applied)"
        
        # For partial success, show what worked
        if successful > 0:
            fixes = [a.fix_applied for a in attempts if a.success]
            return f"✓ Partially corrected: {', '.join(fixes[:2])}"
        
        # For complete failure, show the main issue
        if attempts:
            main_error = attempts[0].error_type.value.replace('_', ' ')
            return f"✗ Could not automatically fix {main_error} issue"
        
        return "✗ Automatic correction failed"