"""Smart update notifications for agtOS tools.

Provides intelligent update recommendations based on usage patterns,
risk assessment, and dependency analysis.

AI_CONTEXT:
    This makes updates less scary by being smart about when and how to
    recommend them. It considers usage patterns, breaking changes, security
    fixes, and dependency counts to prioritize and recommend updates at
    the right time with the right level of urgency.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .version_manager import VersionManager, Version
from .dependency_tracker import DependencyTracker


class UpdatePriority(Enum):
    """Update priority levels."""
    CRITICAL = "critical"  # Security fixes
    HIGH = "high"        # Important bug fixes
    MEDIUM = "medium"    # New features, minor fixes
    LOW = "low"          # Optional improvements


@dataclass
class UpdateRecommendation:
    """A recommendation for updating a tool."""
    tool_name: str
    current_version: str
    recommended_version: str
    latest_version: str
    priority: UpdatePriority
    reasons: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    auto_updatable: bool = False
    affected_workflows: List[str] = field(default_factory=list)
    risk_assessment: str = "low"
    estimated_effort: str = "< 1 minute"
    benefits: List[str] = field(default_factory=list)
    last_used: Optional[str] = None
    usage_frequency: str = "low"  # low, medium, high


class UpdateNotifier:
    """Provides smart update notifications and recommendations.
    
    AI_CONTEXT:
        This class analyzes the entire tool ecosystem to provide intelligent
        update recommendations. It considers many factors including security,
        usage patterns, dependencies, and breaking changes to help users
        make informed decisions about when and how to update their tools.
    """
    
    def __init__(self, version_manager: VersionManager,
                 dependency_tracker: DependencyTracker):
        """Initialize update notifier.
        
        Args:
            version_manager: Version manager instance
            dependency_tracker: Dependency tracker instance
        """
        self.version_manager = version_manager
        self.dependency_tracker = dependency_tracker
        self.tools_dir = version_manager.tools_dir
        self.config_file = self.tools_dir / "update_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load update notification configuration."""
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        else:
            return {
                "auto_update": {
                    "enabled": True,
                    "patch_only": True,
                    "require_confirmation": True
                },
                "notifications": {
                    "security_updates": "immediate",
                    "breaking_changes": "weekly",
                    "feature_updates": "weekly"
                },
                "ignored_updates": {},
                "update_history": []
            }
    
    def _save_config(self):
        """Save update configuration."""
        self.config_file.write_text(json.dumps(self.config, indent=2))
    
    def check_updates(self) -> List[UpdateRecommendation]:
        """Check for available updates and generate recommendations.
        
        Returns:
            List of update recommendations sorted by priority
        """
        recommendations = []
        
        # Get all tools with their active versions
        tools = self.version_manager.list_all_tools()
        
        for tool_name, active_version, total_versions in tools:
            if active_version == "none":
                continue
            
            # Get available versions
            versions = self.version_manager.get_available_versions(tool_name)
            if not versions or versions[0] == active_version:
                continue  # Already on latest
            
            # Create recommendation
            rec = self._analyze_update(tool_name, active_version, versions[0])
            if rec:
                recommendations.append(rec)
        
        # Sort by priority
        priority_order = {
            UpdatePriority.CRITICAL: 0,
            UpdatePriority.HIGH: 1,
            UpdatePriority.MEDIUM: 2,
            UpdatePriority.LOW: 3
        }
        
        recommendations.sort(key=lambda r: (priority_order[r.priority], r.tool_name))
        
        return recommendations
    
    def calculate_update_priority(self, tool_name: str, 
                                current_version: str, 
                                latest_version: str) -> UpdatePriority:
        """Calculate update priority based on multiple factors.
        
        Args:
            tool_name: Name of the tool
            current_version: Current version
            latest_version: Latest available version
            
        Returns:
            Update priority level
        """
        current_v = Version.parse(current_version)
        latest_v = Version.parse(latest_version)
        
        # Get metadata for both versions
        current_meta = self.version_manager.get_version_metadata(tool_name, current_version)
        latest_meta = self.version_manager.get_version_metadata(tool_name, latest_version)
        
        if not current_meta or not latest_meta:
            return UpdatePriority.LOW
        
        # Check for security fixes
        changelog = latest_meta.get("changelog", "")
        if any(word in changelog.lower() for word in ["security", "vulnerability", "cve"]):
            return UpdatePriority.CRITICAL
        
        # Check version difference
        if latest_v.major > current_v.major:
            # Major version change - check usage
            deps = self.dependency_tracker.get_dependents(tool_name, current_version)
            if len(deps) > 5:
                return UpdatePriority.MEDIUM  # Many dependents, be careful
            else:
                return UpdatePriority.HIGH  # Few dependents, good to update
        
        if latest_v.minor > current_v.minor:
            # Minor version - new features
            return UpdatePriority.MEDIUM
        
        if latest_v.patch > current_v.patch:
            # Patch version - bug fixes
            if "fix" in changelog.lower() or "bug" in changelog.lower():
                return UpdatePriority.HIGH
            else:
                return UpdatePriority.LOW
        
        return UpdatePriority.LOW
    
    def should_auto_update(self, tool_name: str, 
                         from_version: str, to_version: str) -> bool:
        """Determine if an update can be applied automatically.
        
        Args:
            tool_name: Name of the tool
            from_version: Current version
            to_version: Target version
            
        Returns:
            True if update can be automatic
        """
        if not self.config["auto_update"]["enabled"]:
            return False
        
        from_v = Version.parse(from_version)
        to_v = Version.parse(to_version)
        
        # Only auto-update patches if configured
        if self.config["auto_update"]["patch_only"]:
            if from_v.major != to_v.major or from_v.minor != to_v.minor:
                return False
        
        # Check for breaking changes
        impact = self.dependency_tracker.analyze_upgrade_impact(
            tool_name, from_version, to_version, self.version_manager
        )
        
        if impact.breaking_changes:
            return False
        
        # Check risk level
        if impact.estimated_risk != "low":
            return False
        
        return True
    
    def generate_update_summary(self) -> str:
        """Generate human-readable update summary.
        
        Returns:
            Markdown formatted update summary
        """
        recommendations = self.check_updates()
        
        if not recommendations:
            return "# All tools are up to date! 🎉\n\nNo updates are available at this time."
        
        summary = ["# Tool Update Summary", ""]
        
        # Group by priority
        by_priority = {}
        for rec in recommendations:
            if rec.priority not in by_priority:
                by_priority[rec.priority] = []
            by_priority[rec.priority].append(rec)
        
        # Critical updates
        if UpdatePriority.CRITICAL in by_priority:
            summary.extend([
                "## 🚨 Critical Updates (Security)",
                "",
                "These updates contain security fixes and should be applied immediately:",
                ""
            ])
            for rec in by_priority[UpdatePriority.CRITICAL]:
                summary.append(self._format_recommendation(rec))
            summary.append("")
        
        # High priority updates
        if UpdatePriority.HIGH in by_priority:
            summary.extend([
                "## ⚠️  High Priority Updates",
                "",
                "These updates contain important bug fixes:",
                ""
            ])
            for rec in by_priority[UpdatePriority.HIGH]:
                summary.append(self._format_recommendation(rec))
            summary.append("")
        
        # Medium priority updates
        if UpdatePriority.MEDIUM in by_priority:
            summary.extend([
                "## 📦 Feature Updates",
                "",
                "New features and improvements are available:",
                ""
            ])
            for rec in by_priority[UpdatePriority.MEDIUM]:
                summary.append(self._format_recommendation(rec))
            summary.append("")
        
        # Low priority updates
        if UpdatePriority.LOW in by_priority:
            summary.extend([
                "## 💡 Optional Updates",
                "",
                "Minor improvements available when convenient:",
                ""
            ])
            for rec in by_priority[UpdatePriority.LOW]:
                summary.append(self._format_recommendation(rec))
            summary.append("")
        
        # Add quick actions
        summary.extend([
            "## Quick Actions",
            "",
            "- Update all (safe): `agtos update --safe`",
            "- Update specific tool: `agtos update <tool_name>`",
            "- Review changes: `agtos changelog <tool_name>`",
            "- Ignore update: `agtos ignore-update <tool_name> <version>`"
        ])
        
        return "\n".join(summary)
    
    def get_update_for_tool(self, tool_name: str) -> Optional[UpdateRecommendation]:
        """Get update recommendation for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Update recommendation or None
        """
        active_version = self.version_manager.get_active_version(tool_name)
        if not active_version:
            return None
        
        versions = self.version_manager.get_available_versions(tool_name)
        if not versions or versions[0] == active_version:
            return None
        
        return self._analyze_update(tool_name, active_version, versions[0])
    
    def ignore_update(self, tool_name: str, version: str):
        """Ignore a specific update.
        
        Args:
            tool_name: Name of the tool
            version: Version to ignore
        """
        if tool_name not in self.config["ignored_updates"]:
            self.config["ignored_updates"][tool_name] = []
        
        if version not in self.config["ignored_updates"][tool_name]:
            self.config["ignored_updates"][tool_name].append(version)
            self._save_config()
    
    def _analyze_update(self, tool_name: str, current_version: str, 
                       target_version: str) -> Optional[UpdateRecommendation]:
        """Analyze a potential update and create recommendation."""
        # Check if ignored
        ignored = self.config["ignored_updates"].get(tool_name, [])
        if target_version in ignored:
            return None
        
        # Get impact analysis
        impact = self.dependency_tracker.analyze_upgrade_impact(
            tool_name, current_version, target_version, self.version_manager
        )
        
        # Calculate priority
        priority = self.calculate_update_priority(tool_name, current_version, target_version)
        
        # Get usage statistics
        usage_stats = self._get_usage_statistics(tool_name, current_version)
        
        # Create recommendation
        rec = UpdateRecommendation(
            tool_name=tool_name,
            current_version=current_version,
            recommended_version=target_version,
            latest_version=target_version,
            priority=priority,
            breaking_changes=bool(impact.breaking_changes),
            auto_updatable=impact.auto_migratable and self.should_auto_update(
                tool_name, current_version, target_version
            ),
            affected_workflows=impact.affected_workflows,
            risk_assessment=impact.estimated_risk,
            last_used=usage_stats.get("last_used"),
            usage_frequency=usage_stats.get("frequency", "low")
        )
        
        # Add reasons
        current_v = Version.parse(current_version)
        target_v = Version.parse(target_version)
        
        if target_v.major > current_v.major:
            rec.reasons.append("Major version with new features")
        elif target_v.minor > current_v.minor:
            rec.reasons.append("New features available")
        elif target_v.patch > current_v.patch:
            rec.reasons.append("Bug fixes available")
        
        # Check changelog for specific improvements
        target_meta = self.version_manager.get_version_metadata(tool_name, target_version)
        if target_meta:
            changelog = target_meta.get("changelog", "")
            if "performance" in changelog.lower():
                rec.benefits.append("Performance improvements")
            if "fix" in changelog.lower():
                rec.benefits.append("Bug fixes")
            if "feature" in changelog.lower():
                rec.benefits.append("New features")
        
        # Estimate effort
        if rec.breaking_changes and not rec.auto_updatable:
            rec.estimated_effort = f"{len(impact.affected_workflows) * 5} minutes"
        elif rec.breaking_changes and rec.auto_updatable:
            rec.estimated_effort = "2-3 minutes"
        else:
            rec.estimated_effort = "< 1 minute"
        
        return rec
    
    def _get_usage_statistics(self, tool_name: str, version: str) -> Dict[str, Any]:
        """Get usage statistics for a tool."""
        stats = self.dependency_tracker.get_parameter_usage_stats(tool_name, version)
        deps = self.dependency_tracker.get_dependents(tool_name, version)
        
        # Calculate last used
        last_used = None
        for dep in deps:
            if dep.last_used:
                dep_time = datetime.fromisoformat(dep.last_used.replace('Z', '+00:00'))
                if not last_used or dep_time > last_used:
                    last_used = dep_time
        
        # Calculate frequency
        if not last_used:
            frequency = "never"
        else:
            days_ago = (datetime.now() - last_used.replace(tzinfo=None)).days
            if days_ago < 1:
                frequency = "high"
            elif days_ago < 7:
                frequency = "medium"
            else:
                frequency = "low"
        
        return {
            "last_used": last_used.isoformat() if last_used else None,
            "frequency": frequency,
            "total_usage": sum(stats.values()),
            "dependent_count": len(deps)
        }
    
    def _format_recommendation(self, rec: UpdateRecommendation) -> str:
        """Format a recommendation for display."""
        lines = [f"### {rec.tool_name}: {rec.current_version} → {rec.recommended_version}"]
        
        # Add emoji based on auto-updatable
        if rec.auto_updatable:
            lines[0] += " ✅"
        elif rec.breaking_changes:
            lines[0] += " ⚠️"
        
        lines.append("")
        
        # Reasons
        if rec.reasons:
            lines.append("**Why update:**")
            for reason in rec.reasons:
                lines.append(f"- {reason}")
            lines.append("")
        
        # Benefits
        if rec.benefits:
            lines.append("**Benefits:**")
            for benefit in rec.benefits:
                lines.append(f"- {benefit}")
            lines.append("")
        
        # Impact
        lines.append(f"**Impact:** {len(rec.affected_workflows)} workflows affected")
        lines.append(f"**Risk:** {rec.risk_assessment}")
        lines.append(f"**Effort:** {rec.estimated_effort}")
        lines.append(f"**Usage:** {rec.usage_frequency} (last used: {rec.last_used or 'never'})")
        
        # Update command
        if rec.auto_updatable:
            lines.append(f"\n```\nagtos update {rec.tool_name} --auto\n```")
        else:
            lines.append(f"\n```\nagtos update {rec.tool_name}\n```")
        
        lines.append("")
        return "\n".join(lines)