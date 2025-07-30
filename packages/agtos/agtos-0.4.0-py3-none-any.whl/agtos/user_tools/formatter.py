"""Format tool creation results for better user experience.

This module provides formatting utilities to present tool creation results
in a user-friendly way without technical details or awkward line breaks.

AI_CONTEXT:
    The formatter transforms raw tool creation results into readable messages
    that focus on what the user needs to know, hiding implementation details
    and presenting errors in a helpful way.
"""

from typing import Dict, Any, List, Optional
import textwrap


class ToolCreationFormatter:
    """Formats tool creation results for user presentation."""
    
    def __init__(self):
        self.max_width = 80  # Maximum line width for output
    
    def format_success(self, result: Dict[str, Any]) -> str:
        """Format a successful tool creation result.
        
        Args:
            result: Raw result from tool creation
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        # Success header
        tool_name = result.get("tool_name", "Unknown")
        lines.append(f"✅ I've successfully created the '{tool_name}' tool!")
        lines.append("")
        
        # Simple description of what it does
        if desc := result.get("description"):
            lines.append(f"This tool will {desc.lower()}.")
            lines.append("")
        
        # Validation warnings (if any)
        if warnings := result.get("validation_warnings"):
            if warnings:  # Only show if there are actual warnings
                lines.append("⚠️  Warnings:")
                for warning in warnings[:3]:  # Limit to 3 warnings
                    lines.append(f"  • {self._simplify_warning(warning)}")
                if len(warnings) > 3:
                    lines.append(f"  • ...and {len(warnings) - 3} more")
                lines.append("")
        
        # Hot reload status (if present)
        if hot_reload_status := result.get("hot_reload_status"):
            if "successfully" in hot_reload_status.lower():
                lines.append("✨ The tool is now available for use!")
            else:
                # Don't mention technical details about hot reload
                pass
        
        lines.append("")
        
        # Usage instructions - keep it simple
        lines.append("🚀 Ready to use!")
        usage_hint = self._get_usage_hint(result)
        # Avoid redundancy if usage hint already mentions the tool
        if tool_name.lower() in usage_hint.lower():
            lines.append(f"I can now {usage_hint}.")
        else:
            lines.append(f"I can now use the '{tool_name}' tool to {usage_hint}.")
        
        # Add healing summary if present
        if healing_summary := result.get("healing_summary"):
            lines.append("")
            lines.append(healing_summary)
        elif healing_note := result.get("healing_note"):
            lines.append("")
            lines.append(f"⚠️  {healing_note}")
        
        return "\n".join(lines)
    
    def format_tool_info(self, info: Dict[str, Any]) -> str:
        """Format tool information for display.
        
        Args:
            info: Tool information from inspector
            
        Returns:
            Formatted tool information
        """
        lines = []
        
        # Header
        tool_name = info.get("tool_name", "Unknown")
        source = info.get("source", "unknown")
        source_emoji = {
            "user": "👤",
            "plugin": "🔌",
            "builtin": "🏗️",
            "mcp": "🌐"
        }.get(source, "❓")
        
        lines.append(f"{source_emoji} Tool: {tool_name}")
        lines.append(f"📍 Source: {source}")
        
        # Version info for user tools
        if source == "user" and "version" in info:
            lines.append(f"📦 Version: {info['version']}")
            if versions := info.get("versions"):
                lines.append(f"   Available versions: {versions['total']}")
        
        # Description
        if desc := info.get("description"):
            lines.append("")
            lines.append(f"📝 Description: {desc}")
        
        # Parameters
        if params := info.get("parameters"):
            lines.append("")
            lines.append("📋 Parameters:")
            for param in params:
                required = "*" if param.get("required") else ""
                param_type = param.get("type", "string")
                lines.append(f"  • {param['name']}{required} ({param_type})")
                if param_desc := param.get("description"):
                    wrapped = textwrap.wrap(param_desc, width=self.max_width - 6)
                    for line in wrapped:
                        lines.append(f"      {line}")
        
        # Endpoints for user tools
        if endpoints := info.get("endpoints"):
            lines.append("")
            lines.append("🔌 API Endpoints:")
            for ep in endpoints:
                method = ep.get("method", "GET")
                url = ep.get("url", "Unknown")
                lines.append(f"  • {method} {url}")
                
                # Show parameters
                if ep_params := ep.get("parameters"):
                    for param in ep_params:
                        required = "*" if param.get("required") else ""
                        lines.append(f"    - {param['name']}{required} ({param.get('location', 'query')})")
                
                # Show auth
                if auth := ep.get("authentication"):
                    lines.append(f"    🔐 Auth: {auth['type']} in {auth['location']}")
        
        # Usage stats if available
        if usage := info.get("usage"):
            if usage.get("total_calls", 0) > 0:
                lines.append("")
                lines.append("📊 Usage Statistics:")
                lines.append(f"  • Total calls: {usage['total_calls']}")
                lines.append(f"  • Success rate: {100 - usage.get('error_rate', 0):.1f}%")
                if last_used := usage.get("last_used"):
                    lines.append(f"  • Last used: {last_used}")
        
        # Debug info if requested
        if debug := info.get("debug"):
            lines.append("")
            lines.append("🐛 Debug Information:")
            for key, value in debug.items():
                lines.append(f"  • {key}: {value}")
        
        return "\n".join(lines)
    
    def format_error(self, result: Dict[str, Any]) -> str:
        """Format an error result in a helpful way.
        
        Args:
            result: Raw error result
            
        Returns:
            User-friendly error message
        """
        lines = []
        
        # Error header
        lines.append("❌ Tool creation failed")
        lines.append("")
        
        # Determine error type and provide helpful message
        if syntax_errors := result.get("syntax_errors"):
            lines.append("🔧 The generated code has syntax issues:")
            for error in syntax_errors[:2]:
                lines.append(f"  • {self._simplify_syntax_error(error)}")
            lines.append("")
            lines.append("💡 This usually happens when:")
            lines.append("  • Parameter names contain special characters (use underscores instead of hyphens)")
            lines.append("  • The API description was ambiguous")
            lines.append("")
            lines.append("Try providing a clearer description or use the clarification process.")
            
        elif security_errors := result.get("security_errors"):
            lines.append("🛡️  Security concerns detected:")
            for error in security_errors:
                lines.append(f"  • {error}")
            lines.append("")
            lines.append("For security reasons, we cannot create tools that perform these operations.")
            
        else:
            # Generic error
            error_msg = result.get("error", "Unknown error occurred")
            lines.append(f"❗ Error: {self._simplify_error_message(error_msg)}")
            lines.append("")
            
            # Provide helpful suggestions based on error
            if "analyze" in error_msg.lower() or "parse" in error_msg.lower():
                lines.append("💡 Suggestions:")
                lines.append("  • Try providing a more specific API description")
                lines.append("  • Include the full API endpoint URL")
                lines.append("  • Specify the HTTP method (GET, POST, etc.)")
                lines.append("  • Use the clarification process for complex APIs")
            
        return "\n".join(lines)
    
    def format_clarification_needed(self, intent: str) -> str:
        """Format a message indicating clarification is needed.
        
        Args:
            intent: The user's original intent
            
        Returns:
            Message suggesting clarification
        """
        lines = [
            "🤔 I need more information to create this tool properly.",
            "",
            f"You want to: {intent}",
            "",
            "To create the best tool for you, I'll need to know:",
            "  • Which service/API you want to use",
            "  • The specific endpoint or functionality",
            "  • Any authentication requirements",
            "",
            "Would you like me to start the clarification process to gather this information?"
        ]
        
        return "\n".join(lines)
    
    def _simplify_warning(self, warning: str) -> str:
        """Simplify a validation warning for users."""
        # Remove technical jargon
        replacements = {
            "Import error": "Missing dependency",
            "ModuleNotFoundError": "Required package not found",
            "SyntaxError": "Code formatting issue",
            "validation": "check"
        }
        
        simplified = warning
        for old, new in replacements.items():
            simplified = simplified.replace(old, new)
        
        return simplified
    
    def _simplify_syntax_error(self, error: str) -> str:
        """Simplify a syntax error message."""
        # Extract the key issue
        if "invalid syntax" in error.lower():
            if "line" in error:
                # Try to extract line number
                import re
                if match := re.search(r'line (\d+)', error):
                    line_num = match.group(1)
                    return f"Invalid code syntax at line {line_num}"
            return "Invalid code syntax detected"
        
        # Handle common cases
        if "identifier" in error:
            return "Invalid character in parameter or function name (avoid hyphens, use underscores)"
        
        return error[:100] + "..." if len(error) > 100 else error
    
    def _simplify_error_message(self, error: str) -> str:
        """Simplify a generic error message."""
        # Remove stack traces
        if "\n" in error:
            error = error.split("\n")[0]
        
        # Remove module paths
        import re
        error = re.sub(r'[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+\.', '', error)
        
        # Simplify common errors
        replacements = {
            "KeyError": "Missing required information",
            "ValueError": "Invalid value provided",
            "TypeError": "Incorrect data type",
            "AttributeError": "Missing attribute"
        }
        
        for old, new in replacements.items():
            if old in error:
                return new + ": " + error.split(":")[-1].strip()
        
        return error[:150] + "..." if len(error) > 150 else error
    
    def _get_usage_hint(self, result: Dict[str, Any]) -> str:
        """Generate a usage hint based on the tool configuration."""
        desc = result.get("description", "")
        
        # If we have a good description, just use it
        if desc and not desc.startswith("Tool for"):
            return desc.lower()
        
        # Otherwise, create a simple action phrase
        tool_name = result.get("tool_name", "the tool")
        desc_lower = desc.lower()
        
        if "post" in desc_lower or "send" in desc_lower:
            return "send data"
        elif "get" in desc_lower or "fetch" in desc_lower or "retrieve" in desc_lower:
            return "retrieve information"
        elif "update" in desc_lower or "put" in desc_lower:
            return "update data"
        elif "delete" in desc_lower or "remove" in desc_lower:
            return "delete data"
        else:
            return "interact with the API"
    
    def format_edit_success(self, result: Dict[str, Any]) -> str:
        """Format a successful tool edit result.
        
        Args:
            result: Edit result with changes summary
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        # Success header
        tool_name = result.get("tool_name", "Unknown")
        lines.append(f"✅ Successfully modified tool: {tool_name}")
        lines.append("")
        
        # Show what changed
        if changes := result.get("changes_applied", []):
            lines.append("📝 Changes Applied:")
            for change in changes:
                change_type = change.get("type", "unknown")
                
                if change_type == "endpoint_url":
                    lines.append(f"  • Endpoint URL changed")
                    lines.append(f"    From: {change.get('from', 'N/A')}")
                    lines.append(f"    To: {change.get('to', 'N/A')}")
                
                elif change_type == "api_version":
                    lines.append(f"  • {change.get('description', 'API version updated')}")
                
                elif change_type == "parameter_rename":
                    lines.append(f"  • Parameter renamed: '{change.get('from')}' → '{change.get('to')}'")
                
                elif change_type == "new_parameter":
                    lines.append(f"  • Added parameter: '{change.get('name')}' ({change.get('details', 'parameter')})")
                
                elif change_type == "authentication":
                    lines.append(f"  • Authentication changed")
                    lines.append(f"    From: {change.get('from', 'none')}")
                    lines.append(f"    To: {change.get('to', 'none')}")
                
                elif change_type == "provider":
                    lines.append(f"  • {change.get('description', 'Provider changed')}")
            
            lines.append("")
            lines.append(f"Total changes: {result.get('total_changes', len(changes))}")
        
        lines.append("")
        lines.append("🔄 The tool has been updated and hot-reloaded.")
        lines.append("✨ Changes are immediately available - no restart needed!")
        
        return "\n".join(lines)
    
    def format_tool_summary(self, summary: Dict[str, Any]) -> str:
        """Format a tool summary without showing code.
        
        Args:
            summary: Tool summary data
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        # Header
        tool_name = summary.get("name", "Unknown")
        lines.append(f"🔧 Tool: {tool_name}")
        lines.append("")
        
        # Description
        if desc := summary.get("description"):
            lines.append(f"📝 Description: {desc}")
            lines.append("")
        
        # Created date
        if created := summary.get("created"):
            # Format ISO date nicely
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
                lines.append(f"📅 Created: {formatted_date}")
            except:
                lines.append(f"📅 Created: {created}")
            lines.append("")
        
        # Endpoints
        if endpoints := summary.get("endpoints", []):
            lines.append("🔌 API Endpoints:")
            for i, ep in enumerate(endpoints, 1):
                method = ep.get("method", "GET")
                url = ep.get("url", "Unknown URL")
                desc = ep.get("description", "")
                
                lines.append(f"\n  {i}. {method} {url}")
                if desc:
                    lines.append(f"     Purpose: {desc}")
                
                # Authentication
                if auth := ep.get("authentication"):
                    auth_type = auth.get("type", "unknown")
                    auth_location = auth.get("location", "header")
                    lines.append(f"     🔐 Auth: {auth_type} (in {auth_location})")
                
                # Parameters
                if params := ep.get("parameters", []):
                    lines.append("     📋 Parameters:")
                    for param in params:
                        param_name = param.get("name", "unknown")
                        param_type = param.get("type", "string")
                        required = "required" if param.get("required", False) else "optional"
                        param_desc = param.get("description", "")
                        
                        lines.append(f"        • {param_name} ({param_type}, {required})")
                        if param_desc:
                            lines.append(f"          {param_desc}")
        
        lines.append("")
        lines.append("💡 This tool is ready to use in your workflows.")
        
        return "\n".join(lines)
    
    def format_delete_confirmation(self, result: Dict[str, Any]) -> str:
        """Format a tool deletion confirmation.
        
        Args:
            result: Deletion result
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        tool_name = result.get("deleted_tool", "Unknown")
        description = result.get("description", "No description")
        
        lines.append(f"🗑️  Tool '{tool_name}' has been deleted")
        lines.append("")
        lines.append(f"The following tool was removed:")
        lines.append(f"  • Name: {tool_name}")
        lines.append(f"  • Description: {description}")
        lines.append("")
        lines.append("✅ The tool and its metadata have been permanently removed.")
        lines.append("🔄 Hot reload triggered - the tool is no longer available.")
        
        return "\n".join(lines)
    
    def format_version_info(self, version_data: Dict[str, Any]) -> str:
        """Format version history information.
        
        Args:
            version_data: Version history data
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        tool_name = version_data.get("tool_name", "Unknown")
        active_version = version_data.get("active_version", "None")
        versions = version_data.get("versions", [])
        
        lines.append(f"📦 Version History: {tool_name}")
        lines.append("")
        lines.append(f"🎯 Active Version: {active_version}")
        lines.append("")
        lines.append("📋 Available Versions:")
        lines.append("")
        
        for v_info in versions:
            version = v_info.get("version", "Unknown")
            created = v_info.get("created_at", "Unknown")
            is_active = v_info.get("is_active", False)
            has_breaking = v_info.get("breaking_changes", False)
            
            # Format version line
            version_line = f"  • {version}"
            if is_active:
                version_line += " ⭐ (active)"
            if has_breaking:
                version_line += " ⚠️  (breaking changes)"
            
            lines.append(version_line)
            
            # Format date nicely
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
                lines.append(f"    Created: {formatted_date}")
            except:
                lines.append(f"    Created: {created}")
            
            lines.append("")
        
        lines.append(f"Total versions: {version_data.get('total_versions', 0)}")
        
        return "\n".join(lines)
    
    def format_update_available(self, recommendation: Any) -> str:
        """Format update available notification.
        
        Args:
            recommendation: UpdateRecommendation object
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        # Header with priority emoji
        priority_emojis = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "📦",
            "low": "💡"
        }
        emoji = priority_emojis.get(recommendation.priority.value, "📦")
        
        lines.append(f"{emoji} Update Available: {recommendation.tool_name}")
        lines.append("")
        lines.append(f"Current: {recommendation.current_version} → Available: {recommendation.recommended_version}")
        lines.append("")
        
        # Reasons for update
        if recommendation.reasons:
            lines.append("📝 Why update:")
            for reason in recommendation.reasons:
                lines.append(f"  • {reason}")
            lines.append("")
        
        # Benefits
        if recommendation.benefits:
            lines.append("✨ Benefits:")
            for benefit in recommendation.benefits:
                lines.append(f"  • {benefit}")
            lines.append("")
        
        # Impact and risk
        lines.append("📊 Impact Analysis:")
        lines.append(f"  • Affected workflows: {len(recommendation.affected_workflows)}")
        lines.append(f"  • Risk level: {recommendation.risk_assessment}")
        lines.append(f"  • Estimated effort: {recommendation.estimated_effort}")
        lines.append(f"  • Auto-updatable: {'Yes ✅' if recommendation.auto_updatable else 'No ❌'}")
        
        if recommendation.breaking_changes:
            lines.append("  • ⚠️  Contains breaking changes")
        
        lines.append("")
        
        # Update command
        if recommendation.auto_updatable:
            lines.append("💡 To update automatically:")
            lines.append(f"☐ Run: tool_creator_upgrade with tool_name='{recommendation.tool_name}'")
        else:
            lines.append("💡 To review and update:")
            lines.append(f"☐ Run: tool_creator_migrate with tool_name='{recommendation.tool_name}' and target_version='{recommendation.recommended_version}'")
        
        return "\n".join(lines)
    
    def format_migration_plan(self, plan: Any) -> str:
        """Format a migration plan for user review.
        
        Args:
            plan: MigrationPlan object
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        lines.append(f"🔄 Migration Plan: {plan.tool_name}")
        lines.append(f"   {plan.from_version} → {plan.to_version}")
        lines.append("")
        
        # Summary
        lines.append("📊 Summary:")
        lines.append(f"  • Risk level: {plan.risk_level}")
        lines.append(f"  • Estimated time: {plan.estimated_duration}")
        lines.append(f"  • Files affected: {len(plan.affected_files)}")
        lines.append(f"  • Can rollback: {'Yes ✅' if plan.rollback_available else 'No ❌'}")
        lines.append("")
        
        # Migration steps
        lines.append("📋 Migration Steps:")
        for i, step in enumerate(plan.steps, 1):
            step_emoji = {
                "automatic": "🤖",
                "manual": "👤",
                "confirmation": "✅"
            }.get(step.step_type, "📌")
            
            lines.append(f"  {i}. {step_emoji} {step.description}")
            
            if step.instructions:
                lines.append(f"     Instructions: {step.instructions}")
            
            if step.step_type == "automatic":
                lines.append("     (This will be done automatically)")
        
        lines.append("")
        
        # Affected files
        if plan.affected_files:
            lines.append("📁 Affected Files:")
            for file_path in plan.affected_files[:5]:  # Show first 5
                lines.append(f"  • {file_path}")
            if len(plan.affected_files) > 5:
                lines.append(f"  • ...and {len(plan.affected_files) - 5} more")
            lines.append("")
        
        # Next steps
        lines.append("💡 Next Steps:")
        if plan.risk_level == "low" and all(s.step_type == "automatic" for s in plan.steps):
            lines.append("  This migration can be applied automatically.")
            lines.append(f"  ☐ Run: tool_creator_migrate with apply_automatic=true")
        else:
            lines.append("  Review the migration plan above.")
            lines.append("  Some steps require manual intervention.")
            lines.append(f"  ☐ Run: tool_creator_migrate to start interactive migration")
        
        return "\n".join(lines)
    
    def format_upgrade_success(self, result: Dict[str, Any]) -> str:
        """Format successful upgrade result.
        
        Args:
            result: Upgrade result data
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        tool_name = result.get("tool_name", "Unknown")
        from_version = result.get("from_version", "Unknown")
        to_version = result.get("to_version", "Unknown")
        
        lines.append(f"✅ Successfully upgraded {tool_name}!")
        lines.append("")
        lines.append(f"📦 Version: {from_version} → {to_version}")
        lines.append("")
        
        if result.get("automatic"):
            lines.append("🤖 Automatic upgrade completed:")
            lines.append("  • Tool code updated")
            lines.append("  • Version activated")
            lines.append("  • Hot reload triggered")
        
        lines.append("")
        lines.append("✨ The upgraded tool is now active and ready to use!")
        
        return "\n".join(lines)
    
    def format_migration_complete(self, result: Dict[str, Any]) -> str:
        """Format migration completion result.
        
        Args:
            result: Migration result data
            
        Returns:
            User-friendly formatted string
        """
        lines = []
        
        tool_name = result.get("tool_name", "Unknown")
        from_version = result.get("from_version", "Unknown")
        to_version = result.get("to_version", "Unknown")
        files_migrated = result.get("files_migrated", 0)
        changes_made = result.get("changes_made", 0)
        
        lines.append(f"✅ Migration completed successfully!")
        lines.append("")
        lines.append(f"🔧 Tool: {tool_name}")
        lines.append(f"📦 Version: {from_version} → {to_version}")
        lines.append("")
        lines.append("📊 Migration Summary:")
        lines.append(f"  • Files migrated: {files_migrated}")
        lines.append(f"  • Changes applied: {changes_made}")
        lines.append(f"  • Backups created: Yes ✅")
        lines.append("")
        lines.append("✨ The new version is now active!")
        lines.append("")
        lines.append("💡 Next steps:")
        lines.append("  • Test your workflows to ensure they work correctly")
        lines.append("  • Review the backups if you need to rollback")
        lines.append("  • Delete backups once you're confident everything works")
        
        return "\n".join(lines)


def should_use_clarification(description: str) -> bool:
    """Determine if clarification should be used based on the description.
    
    Args:
        description: The API description provided by the user
        
    Returns:
        True if clarification is recommended
    """
    # Check for vague descriptions
    vague_indicators = [
        "i want to",
        "i need to",
        "help me",
        "can you",
        "how do i",
        "create a tool",
        "make a tool"
    ]
    
    desc_lower = description.lower()
    
    # Check if description is too vague
    if any(indicator in desc_lower for indicator in vague_indicators):
        return True
    
    # Check if description lacks key API details
    has_url = any(x in desc_lower for x in ["http://", "https://", ".com", ".io", ".org", "api."])
    has_method = any(x in desc_lower for x in ["get", "post", "put", "delete", "patch"])
    
    # If missing both URL and method, probably needs clarification
    if not has_url and not has_method:
        return True
    
    # Check if description is very short (likely incomplete)
    if len(description.split()) < 5:
        return True
    
    return False