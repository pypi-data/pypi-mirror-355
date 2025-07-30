"""Progressive error disclosure for tool creation.

This module implements a user-friendly error handling system that shows
natural language errors by default, with technical details available on request.

AI_CONTEXT:
    Progressive disclosure ensures users aren't overwhelmed with technical
    error messages. The system:
    - Shows friendly, actionable error messages by default
    - Stores full technical details for debugging
    - Provides suggestions for common problems
    - Learns from error patterns to improve suggestions
"""

import json
import re
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum

from agtos.utils import get_logger

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    VALIDATION = "validation"
    SYNTAX = "syntax"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorContext:
    """Context for an error with progressive detail levels."""
    
    def __init__(
        self,
        category: ErrorCategory,
        user_message: str,
        technical_details: str,
        suggestions: List[str],
        error_code: Optional[str] = None
    ):
        self.category = category
        self.user_message = user_message
        self.technical_details = technical_details
        self.suggestions = suggestions
        self.error_code = error_code
        self.timestamp = datetime.now()
        self.id = f"err_{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{category.value}"
    
    def to_dict(self, include_technical: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with optional technical details."""
        result = {
            "id": self.id,
            "category": self.category.value,
            "message": self.user_message,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.error_code:
            result["error_code"] = self.error_code
        
        if include_technical:
            result["technical_details"] = self.technical_details
        
        return result


class ProgressiveErrorHandler:
    """Handle errors with progressive disclosure.
    
    AI_CONTEXT:
        This class manages error presentation in a user-friendly way.
        It categorizes errors, provides helpful suggestions, and stores
        technical details for later retrieval if needed.
    """
    
    def __init__(self):
        self.error_log_dir = Path.home() / ".agtos" / "error_logs"
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        self.error_patterns = self._load_error_patterns()
        self.suggestion_db = self._load_suggestion_database()
    
    def handle_error(
        self, 
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Handle an error and return user-friendly context.
        
        Args:
            error: The exception that occurred
            context: Additional context about what was happening
            
        Returns:
            ErrorContext with progressive detail levels
        """
        # Get full technical details
        technical_details = self._get_technical_details(error)
        
        # Categorize the error
        category = self._categorize_error(error, technical_details)
        
        # Generate user-friendly message
        user_message = self._generate_user_message(error, category, context)
        
        # Get suggestions
        suggestions = self._get_suggestions(error, category, context)
        
        # Create error context
        error_context = ErrorContext(
            category=category,
            user_message=user_message,
            technical_details=technical_details,
            suggestions=suggestions,
            error_code=self._get_error_code(error)
        )
        
        # Log the error
        self._log_error(error_context, context)
        
        return error_context
    
    def get_error_details(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full technical details for a specific error.
        
        Args:
            error_id: The error ID to look up
            
        Returns:
            Full error details including technical information
        """
        error_file = self.error_log_dir / f"{error_id}.json"
        
        if error_file.exists():
            try:
                return json.loads(error_file.read_text())
            except Exception as e:
                logger.error(f"Failed to load error details for {error_id}: {e}")
        
        return None
    
    def format_error_response(
        self, 
        error_context: ErrorContext,
        show_technical: bool = False
    ) -> str:
        """Format an error for display to the user.
        
        Args:
            error_context: The error context
            show_technical: Whether to include technical details
            
        Returns:
            Formatted error message
        """
        parts = []
        
        # Main message
        parts.append(f"❌ {error_context.user_message}")
        
        # Suggestions
        if error_context.suggestions:
            parts.append("\n💡 Suggestions:")
            for i, suggestion in enumerate(error_context.suggestions, 1):
                parts.append(f"   {i}. {suggestion}")
        
        # Error ID for reference
        parts.append(f"\n🔍 Error ID: {error_context.id}")
        
        # Technical details if requested
        if show_technical:
            parts.append("\n📋 Technical Details:")
            parts.append(error_context.technical_details)
        else:
            parts.append("\n💬 For technical details, use: tool_creator_error_details")
        
        return "\n".join(parts)
    
    def _categorize_error(self, error: Exception, technical_details: str) -> ErrorCategory:
        """Categorize an error based on its type and content."""
        error_str = str(error).lower()
        tech_lower = technical_details.lower()
        
        # Check for authentication errors
        if any(keyword in error_str or keyword in tech_lower for keyword in [
            "401", "403", "unauthorized", "forbidden", "authentication",
            "invalid token", "invalid api key", "credentials"
        ]):
            return ErrorCategory.AUTHENTICATION
        
        # Check for network errors
        if any(keyword in error_str or keyword in tech_lower for keyword in [
            "connection", "timeout", "refused", "unreachable",
            "dns", "getaddrinfo", "network", "socket"
        ]):
            return ErrorCategory.NETWORK
        
        # Check for validation errors
        if any(keyword in error_str or keyword in tech_lower for keyword in [
            "validation", "invalid", "missing required", "schema",
            "type error", "value error"
        ]):
            return ErrorCategory.VALIDATION
        
        # Check for syntax errors
        if isinstance(error, SyntaxError) or any(keyword in tech_lower for keyword in [
            "syntaxerror", "indentation", "unexpected token", "parse error"
        ]):
            return ErrorCategory.SYNTAX
        
        # Check for permission errors
        if any(keyword in error_str or keyword in tech_lower for keyword in [
            "permission", "access denied", "forbidden", "read-only"
        ]):
            return ErrorCategory.PERMISSION
        
        # Check for configuration errors
        if any(keyword in error_str or keyword in tech_lower for keyword in [
            "config", "missing file", "not found", "environment"
        ]):
            return ErrorCategory.CONFIGURATION
        
        return ErrorCategory.UNKNOWN
    
    def _generate_user_message(
        self, 
        error: Exception, 
        category: ErrorCategory,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a user-friendly error message."""
        error_str = str(error)
        
        if category == ErrorCategory.AUTHENTICATION:
            if "bearer" in error_str.lower():
                return "The API rejected your authentication token. The token might be expired or incorrect."
            elif "api key" in error_str.lower() or "api-key" in error_str.lower():
                return "The API key was not accepted. Please check that it's correct and active."
            else:
                return "Authentication failed. Please verify your credentials."
        
        elif category == ErrorCategory.NETWORK:
            if "timeout" in error_str.lower():
                return "The request timed out. The API might be slow or unreachable."
            elif "connection refused" in error_str.lower():
                return "Could not connect to the API. The server might be down or the URL might be wrong."
            elif "dns" in error_str.lower() or "getaddrinfo" in error_str.lower():
                return "Could not find the API server. Please check the URL is correct."
            else:
                return "Network error occurred while trying to reach the API."
        
        elif category == ErrorCategory.VALIDATION:
            if "missing required" in error_str.lower():
                return "Some required information is missing from your request."
            elif "invalid" in error_str.lower():
                return "The provided information doesn't match what the API expects."
            else:
                return "The tool configuration has validation errors."
        
        elif category == ErrorCategory.SYNTAX:
            return "There's a problem with the generated code syntax."
        
        elif category == ErrorCategory.PERMISSION:
            return "You don't have permission to perform this action."
        
        elif category == ErrorCategory.CONFIGURATION:
            return "There's a configuration issue preventing the tool from working."
        
        else:
            # Try to extract a meaningful message
            if len(error_str) < 100:
                return f"An error occurred: {error_str}"
            else:
                return "An unexpected error occurred while creating the tool."
    
    def _get_suggestions(
        self, 
        error: Exception, 
        category: ErrorCategory,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get suggestions for fixing the error."""
        suggestions = []
        error_str = str(error).lower()
        
        if category == ErrorCategory.AUTHENTICATION:
            suggestions.extend([
                "Double-check your API credentials",
                "Ensure the token/key hasn't expired",
                "Verify you're using the correct authentication method (Bearer token vs API key)"
            ])
            
            if "bearer" in error_str and "api key" in error_str:
                suggestions.append("Try switching between Bearer token and API key authentication")
        
        elif category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check if the API URL is correct",
                "Verify your internet connection",
                "Try again in a few moments if the service might be temporarily down"
            ])
            
            if context and "url" in context:
                url = context["url"]
                if not url.startswith("http"):
                    suggestions.insert(0, "Add 'https://' to the beginning of your URL")
        
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Review the API documentation for required parameters",
                "Check that all parameter names are spelled correctly",
                "Ensure parameter values are in the correct format"
            ])
        
        elif category == ErrorCategory.SYNTAX:
            suggestions.extend([
                "This might be a bug in the tool generator",
                "Try simplifying your API description",
                "Report this issue with the error ID"
            ])
        
        elif category == ErrorCategory.PERMISSION:
            suggestions.extend([
                "Check if your API plan includes this feature",
                "Verify your account has the necessary permissions",
                "Contact the API provider for access"
            ])
        
        elif category == ErrorCategory.CONFIGURATION:
            suggestions.extend([
                "Run 'agtos doctor' to check your setup",
                "Ensure all required files are in place",
                "Check environment variables if the API requires them"
            ])
        
        # Add context-specific suggestions
        if context:
            if "tool_name" in context:
                suggestions.append(f"Try 'tool_creator_summary {context['tool_name']}' to see current configuration")
            
            if "retry_count" in context and context["retry_count"] > 2:
                suggestions.append("Consider using 'tool_creator_clarify' for guided tool creation")
        
        # Limit suggestions
        return suggestions[:4]
    
    def _get_technical_details(self, error: Exception) -> str:
        """Get full technical details of an error."""
        parts = []
        
        # Exception type and message
        parts.append(f"Exception Type: {type(error).__name__}")
        parts.append(f"Message: {str(error)}")
        
        # Full traceback
        parts.append("\nTraceback:")
        parts.append(traceback.format_exc())
        
        # Exception attributes
        if hasattr(error, "__dict__"):
            attrs = {k: v for k, v in error.__dict__.items() if not k.startswith("_")}
            if attrs:
                parts.append("\nException Attributes:")
                parts.append(json.dumps(attrs, indent=2, default=str))
        
        return "\n".join(parts)
    
    def _get_error_code(self, error: Exception) -> Optional[str]:
        """Extract error code if available."""
        # Try common attributes
        for attr in ["code", "status_code", "error_code", "errno"]:
            if hasattr(error, attr):
                return str(getattr(error, attr))
        
        # Try to extract from message
        error_str = str(error)
        if match := re.search(r"\b(\d{3})\b", error_str):
            return match.group(1)
        
        return None
    
    def _log_error(self, error_context: ErrorContext, context: Optional[Dict[str, Any]]):
        """Log error details for later retrieval."""
        log_entry = {
            "error": error_context.to_dict(include_technical=True),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to file
        error_file = self.error_log_dir / f"{error_context.id}.json"
        error_file.write_text(json.dumps(log_entry, indent=2))
        
        # Also log to standard logger
        logger.error(f"Tool creation error: {error_context.user_message} (ID: {error_context.id})")
    
    def _load_error_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load known error patterns for better categorization."""
        # In future, this could load from a persistent store
        return {
            "authentication": [
                {"pattern": r"401.*unauthorized", "category": "token_expired"},
                {"pattern": r"invalid.*api.*key", "category": "wrong_key"},
                {"pattern": r"forbidden.*403", "category": "insufficient_permissions"}
            ],
            "network": [
                {"pattern": r"timeout.*exceeded", "category": "slow_api"},
                {"pattern": r"connection.*refused", "category": "server_down"},
                {"pattern": r"name.*resolution.*failed", "category": "wrong_url"}
            ]
        }
    
    def _load_suggestion_database(self) -> Dict[str, List[str]]:
        """Load suggestion database for common errors."""
        # In future, this could be enhanced with ML-based suggestions
        return {
            "token_expired": [
                "Generate a new API token from the provider's dashboard",
                "Check if the token has an expiration date"
            ],
            "wrong_url": [
                "Verify the API domain (e.g., api.example.com vs example.com/api)",
                "Check if the API requires a specific version in the URL"
            ]
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors for analysis."""
        errors = []
        
        # Get all error files
        error_files = sorted(
            self.error_log_dir.glob("err_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        for error_file in error_files:
            try:
                error_data = json.loads(error_file.read_text())
                errors.append({
                    "id": error_file.stem,
                    "category": error_data["error"]["category"],
                    "message": error_data["error"]["message"],
                    "timestamp": error_data["error"]["timestamp"]
                })
            except Exception as e:
                logger.error(f"Failed to load error file {error_file}: {e}")
        
        return errors


