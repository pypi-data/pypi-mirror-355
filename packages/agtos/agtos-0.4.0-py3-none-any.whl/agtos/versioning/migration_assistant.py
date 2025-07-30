"""Migration assistance for tool version upgrades.

Helps users migrate between tool versions, especially when there are
breaking changes.

AI_CONTEXT:
    This is where the magic happens for smooth upgrades. It can automatically
    migrate simple changes (like parameter renames) and guide users through
    complex migrations interactively. It generates migration scripts and
    validates that workflows will work with new versions.
"""

import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .version_manager import VersionManager, Version
from .dependency_tracker import DependencyTracker, UpgradeImpact


@dataclass
class MigrationStep:
    """A single step in a migration plan."""
    step_type: str  # 'automatic', 'manual', 'confirmation'
    description: str
    action: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None
    can_rollback: bool = True


@dataclass
class MigrationPlan:
    """Complete migration plan for a tool upgrade."""
    tool_name: str
    from_version: str
    to_version: str
    affected_files: List[Path] = field(default_factory=list)
    steps: List[MigrationStep] = field(default_factory=list)
    estimated_duration: str = "< 1 minute"
    risk_level: str = "low"
    rollback_available: bool = True


class MigrationAssistant:
    """Assists with migrating tools between versions.
    
    AI_CONTEXT:
        This class handles the complex task of migrating workflows when tools
        have breaking changes. It can perform automatic migrations for simple
        changes and guide users through manual steps when needed. It also
        validates migrations before applying them.
    """
    
    def __init__(self, version_manager: VersionManager, 
                 dependency_tracker: DependencyTracker):
        """Initialize migration assistant.
        
        Args:
            version_manager: Version manager instance
            dependency_tracker: Dependency tracker instance
        """
        self.version_manager = version_manager
        self.dependency_tracker = dependency_tracker
        self.tools_dir = version_manager.tools_dir
    
    def create_migration_plan(self, tool_name: str, 
                            target_version: str,
                            current_version: Optional[str] = None) -> MigrationPlan:
        """Create a migration plan for upgrading a tool.
        
        Args:
            tool_name: Name of the tool
            target_version: Target version to migrate to
            current_version: Current version (auto-detected if None)
            
        Returns:
            MigrationPlan with all necessary steps
        """
        # Get current version if not provided
        if not current_version:
            current_version = self.version_manager.get_active_version(tool_name)
            if not current_version:
                raise ValueError(f"No active version found for {tool_name}")
        
        # Get upgrade impact analysis
        impact = self.dependency_tracker.analyze_upgrade_impact(
            tool_name, current_version, target_version, self.version_manager
        )
        
        # Create plan
        plan = MigrationPlan(
            tool_name=tool_name,
            from_version=current_version,
            to_version=target_version,
            risk_level=impact.estimated_risk
        )
        
        # Find affected files
        plan.affected_files = self._find_affected_files(tool_name, impact)
        
        # Add migration steps based on breaking changes
        for change in impact.breaking_changes:
            if change.get("migration") == "automatic":
                plan.steps.append(MigrationStep(
                    step_type="automatic",
                    description=self._describe_change(change),
                    action=change,
                    can_rollback=True
                ))
            else:
                plan.steps.append(MigrationStep(
                    step_type="manual",
                    description=self._describe_change(change),
                    instructions=change.get("instructions", "Manual migration required"),
                    can_rollback=False
                ))
        
        # Add validation step
        plan.steps.append(MigrationStep(
            step_type="automatic",
            description="Validate migrated workflows",
            action={"type": "validate"},
            can_rollback=False
        ))
        
        # Add activation step
        plan.steps.append(MigrationStep(
            step_type="confirmation",
            description=f"Activate {tool_name} version {target_version}",
            action={"type": "activate_version"},
            can_rollback=True
        ))
        
        # Estimate duration
        auto_steps = sum(1 for s in plan.steps if s.step_type == "automatic")
        manual_steps = sum(1 for s in plan.steps if s.step_type == "manual")
        
        if manual_steps > 0:
            plan.estimated_duration = f"{manual_steps * 5} - {manual_steps * 10} minutes"
        else:
            plan.estimated_duration = f"< {auto_steps} minute(s)"
        
        return plan
    
    def generate_migration_script(self, plan: MigrationPlan) -> str:
        """Generate an automated migration script.
        
        Args:
            plan: Migration plan
            
        Returns:
            Python script that performs the migration
        """
        script_lines = [
            "#!/usr/bin/env python3",
            '"""',
            f"Auto-generated migration script for {plan.tool_name}",
            f"Migrating from {plan.from_version} to {plan.to_version}",
            f"Generated at: {datetime.now().isoformat()}",
            '"""',
            "",
            "import json",
            "import yaml", 
            "from pathlib import Path",
            "",
            "# Migration configuration",
            f"TOOL_NAME = '{plan.tool_name}'",
            f"FROM_VERSION = '{plan.from_version}'",
            f"TO_VERSION = '{plan.to_version}'",
            "",
            "# Files to migrate",
            "FILES_TO_MIGRATE = [",
        ]
        
        for file_path in plan.affected_files:
            script_lines.append(f"    Path('{file_path}'),")
        
        script_lines.extend([
            "]",
            "",
            "def migrate_file(file_path):",
            "    '''Migrate a single file.'''",
            "    print(f'Migrating {file_path}...')",
            "    ",
            "    # Read file",
            "    if file_path.suffix == '.yaml':",
            "        with open(file_path, 'r') as f:",
            "            content = yaml.safe_load(f)",
            "    else:",
            "        with open(file_path, 'r') as f:",
            "            content = json.load(f)",
            "    ",
            "    # Apply migrations",
            "    modified = False",
        ])
        
        # Add migration logic for each automatic step
        for step in plan.steps:
            if step.step_type == "automatic" and step.action:
                script_lines.extend(self._generate_migration_code(step.action))
        
        script_lines.extend([
            "    ",
            "    # Save if modified",
            "    if modified:",
            "        # Backup original",
            "        backup_path = file_path.with_suffix(file_path.suffix + '.backup')",
            "        file_path.rename(backup_path)",
            "        ",
            "        # Write migrated content",
            "        if file_path.suffix == '.yaml':",
            "            with open(file_path, 'w') as f:",
            "                yaml.dump(content, f, default_flow_style=False)",
            "        else:",
            "            with open(file_path, 'w') as f:",
            "                json.dump(content, f, indent=2)",
            "        ",
            "        print(f'  ✓ Migrated successfully (backup: {backup_path})')",
            "    else:",
            "        print('  - No changes needed')",
            "",
            "if __name__ == '__main__':",
            "    print(f'Starting migration of {TOOL_NAME} from {FROM_VERSION} to {TO_VERSION}')",
            "    print()",
            "    ",
            "    for file_path in FILES_TO_MIGRATE:",
            "        if file_path.exists():",
            "            migrate_file(file_path)",
            "        else:",
            "            print(f'Warning: {file_path} not found')",
            "    ",
            "    print()",
            "    print('Migration complete!')",
            "    print('Please review the changes and test your workflows.')",
        ])
        
        return "\n".join(script_lines)
    
    def apply_automatic_migrations(self, tool_name: str, 
                                 workflow_file: Path) -> Tuple[bool, List[str]]:
        """Apply automatic migrations to a workflow file.
        
        Args:
            tool_name: Name of the tool being migrated
            workflow_file: Path to workflow file
            
        Returns:
            Tuple of (success, list of changes made)
        """
        changes_made = []
        
        try:
            # Read workflow file
            if workflow_file.suffix == '.yaml':
                with open(workflow_file, 'r') as f:
                    content = yaml.safe_load(f)
                    is_yaml = True
            else:
                with open(workflow_file, 'r') as f:
                    content = json.load(f)
                    is_yaml = False
            
            # Get current and target versions
            current_version = self.version_manager.get_active_version(tool_name)
            
            # Find the tool version used in this workflow
            workflow_version = self._find_tool_version_in_workflow(content, tool_name)
            if not workflow_version:
                return True, []  # Tool not used in this workflow
            
            # Get metadata for migrations
            current_meta = self.version_manager.get_version_metadata(tool_name, workflow_version)
            target_meta = self.version_manager.get_version_metadata(tool_name, current_version)
            
            if not current_meta or not target_meta:
                return False, ["Could not load tool metadata"]
            
            # Apply migrations
            modified = False
            breaking_changes = target_meta.get("breaking_changes", {})
            
            for version, version_changes in breaking_changes.items():
                for change in version_changes:
                    if change.get("migration") == "automatic":
                        if self._apply_single_migration(content, tool_name, change):
                            modified = True
                            changes_made.append(self._describe_change(change))
            
            # Save if modified
            if modified:
                # Backup original
                backup_path = workflow_file.with_suffix(workflow_file.suffix + '.backup')
                workflow_file.rename(backup_path)
                
                # Write migrated content
                if is_yaml:
                    with open(workflow_file, 'w') as f:
                        yaml.dump(content, f, default_flow_style=False)
                else:
                    with open(workflow_file, 'w') as f:
                        json.dump(content, f, indent=2)
                
                changes_made.append(f"Backup saved to {backup_path}")
            
            return True, changes_made
            
        except Exception as e:
            return False, [f"Error during migration: {str(e)}"]
    
    def interactive_migration(self, tool_name: str, target_version: str):
        """Guide user through interactive migration process.
        
        Args:
            tool_name: Name of the tool
            target_version: Target version
        """
        # This would be called by the TUI or CLI to provide an interactive
        # migration experience. For now, we'll return the structured data
        # that the UI can use.
        
        plan = self.create_migration_plan(tool_name, target_version)
        
        return {
            "plan": plan,
            "steps": [
                {
                    "type": step.step_type,
                    "description": step.description,
                    "instructions": step.instructions,
                    "can_skip": step.step_type == "manual",
                    "can_rollback": step.can_rollback
                }
                for step in plan.steps
            ],
            "summary": {
                "total_steps": len(plan.steps),
                "automatic_steps": sum(1 for s in plan.steps if s.step_type == "automatic"),
                "manual_steps": sum(1 for s in plan.steps if s.step_type == "manual"),
                "affected_files": len(plan.affected_files),
                "estimated_time": plan.estimated_duration,
                "risk_level": plan.risk_level
            }
        }
    
    def validate_migration(self, tool_name: str, version: str, 
                         workflow_file: Path) -> List[str]:
        """Validate that a workflow will work with new version.
        
        Args:
            tool_name: Name of the tool
            version: Target version
            workflow_file: Path to workflow file
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Read workflow
            if workflow_file.suffix == '.yaml':
                with open(workflow_file, 'r') as f:
                    workflow = yaml.safe_load(f)
            else:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
            
            # Get tool metadata
            metadata = self.version_manager.get_version_metadata(tool_name, version)
            if not metadata:
                errors.append(f"Cannot find metadata for {tool_name}@{version}")
                return errors
            
            # Extract available parameters from new version
            available_params = set()
            spec = metadata.get("specification", {})
            for endpoint in spec.get("endpoints", []):
                for param in endpoint.get("parameters", []):
                    available_params.add(param["name"])
            
            # Check each step in workflow
            for step in workflow.get("steps", []):
                if step.get("tool") == tool_name or step.get("tool").startswith(f"{tool_name}@"):
                    # Check parameters
                    step_params = step.get("arguments", {})
                    for param_name in step_params:
                        if param_name not in available_params:
                            errors.append(
                                f"Step '{step.get('name')}' uses parameter '{param_name}' "
                                f"which doesn't exist in {tool_name}@{version}"
                            )
            
        except Exception as e:
            errors.append(f"Error validating workflow: {str(e)}")
        
        return errors
    
    def create_migration_guide(self, tool_name: str, from_version: str,
                             to_version: str, changes: Dict[str, Any]) -> str:
        """Create a human-readable migration guide.
        
        Args:
            tool_name: Name of the tool
            from_version: Source version
            to_version: Target version  
            changes: Dictionary of changes
            
        Returns:
            Markdown migration guide
        """
        guide = [
            f"# Migration Guide: {tool_name} {from_version} → {to_version}",
            "",
            f"This guide helps you migrate from {tool_name} version {from_version} to {to_version}.",
            "",
            "## Breaking Changes",
            ""
        ]
        
        # Document each breaking change
        if "parameter_renames" in changes:
            guide.extend([
                "### Parameter Renames",
                "",
                "The following parameters have been renamed:",
                "",
                "| Old Name | New Name |",
                "|----------|----------|"
            ])
            for old, new in changes["parameter_renames"].items():
                guide.append(f"| `{old}` | `{new}` |")
            guide.extend(["", "**Migration**: These will be automatically updated in your workflows.", ""])
        
        if "endpoint_url" in changes:
            guide.extend([
                "### Endpoint Changes",
                "",
                f"The API endpoint has changed to: `{changes['endpoint_url']}`",
                "",
                "**Migration**: This will be automatically updated.",
                ""
            ])
        
        if "auth_type" in changes:
            guide.extend([
                "### Authentication Changes",
                "",
                f"Authentication has changed to: {changes['auth_type']}",
                "",
                "**Migration**: You will need to update your credentials:",
            ])
            
            if changes["auth_type"] == "bearer":
                guide.extend([
                    "1. Obtain a Bearer token from the service",
                    "2. Update your environment variable or credential store",
                    "3. The tool will automatically use the new authentication method",
                ])
            guide.append("")
        
        # Add usage examples
        guide.extend([
            "## After Migration",
            "",
            "Your workflows will be updated automatically where possible.",
            "Please test your workflows after migration to ensure they work correctly.",
            "",
            "If you encounter issues, you can roll back to the previous version:",
            "```",
            f"agtos version activate {tool_name} {from_version}",
            "```"
        ])
        
        return "\n".join(guide)
    
    def _find_affected_files(self, tool_name: str, impact: UpgradeImpact) -> List[Path]:
        """Find all files affected by a tool upgrade."""
        affected_files = []
        
        # Search for workflow files
        workflow_dirs = [
            Path.home() / ".agtos" / "workflows",
            Path.cwd() / "workflows",
            Path.cwd() / ".agtos" / "workflows"
        ]
        
        for workflow_dir in workflow_dirs:
            if workflow_dir.exists():
                for file_path in workflow_dir.rglob("*.yaml"):
                    if self._file_uses_tool(file_path, tool_name):
                        affected_files.append(file_path)
                
                for file_path in workflow_dir.rglob("*.yml"):
                    if self._file_uses_tool(file_path, tool_name):
                        affected_files.append(file_path)
        
        return affected_files
    
    def _file_uses_tool(self, file_path: Path, tool_name: str) -> bool:
        """Check if a file uses a specific tool."""
        try:
            content = file_path.read_text()
            # Look for tool references
            return (f'tool: {tool_name}' in content or 
                    f'tool: "{tool_name}"' in content or
                    f"tool: '{tool_name}'" in content or
                    f'tool: {tool_name}@' in content)
        except:
            return False
    
    def _describe_change(self, change: Dict[str, Any]) -> str:
        """Generate human-readable description of a change."""
        change_type = change.get("type", "unknown")
        
        if change_type == "parameter_rename":
            return f"Rename parameter '{change.get('from')}' to '{change.get('to')}'"
        elif change_type == "parameter_removed":
            return f"Remove parameter '{change.get('parameter')}'"
        elif change_type == "auth_change":
            return f"Change authentication from {change.get('from')} to {change.get('to')}"
        elif change_type == "endpoint_change":
            return "Update API endpoint URL"
        else:
            return change.get("description", "Apply changes")
    
    def _find_tool_version_in_workflow(self, workflow: Dict[str, Any], 
                                     tool_name: str) -> Optional[str]:
        """Find which version of a tool is used in a workflow."""
        for step in workflow.get("steps", []):
            tool_ref = step.get("tool", "")
            if tool_ref == tool_name:
                # No version specified, use active
                return self.version_manager.get_active_version(tool_name)
            elif tool_ref.startswith(f"{tool_name}@"):
                # Version specified
                return tool_ref.split("@")[1]
        return None
    
    def _apply_single_migration(self, content: Dict[str, Any], 
                              tool_name: str, change: Dict[str, Any]) -> bool:
        """Apply a single migration to workflow content."""
        modified = False
        
        if change["type"] == "parameter_rename":
            # Find and rename parameters
            for step in content.get("steps", []):
                if (step.get("tool") == tool_name or 
                    step.get("tool", "").startswith(f"{tool_name}@")):
                    
                    args = step.get("arguments", {})
                    if change["from"] in args:
                        args[change["to"]] = args.pop(change["from"])
                        modified = True
        
        return modified
    
    def _generate_migration_code(self, action: Dict[str, Any]) -> List[str]:
        """Generate Python code for a migration action."""
        code = []
        
        if action["type"] == "parameter_rename":
            code.extend([
                f"    # Rename parameter '{action['from']}' to '{action['to']}'",
                "    for step in content.get('steps', []):",
                f"        if step.get('tool') == TOOL_NAME or step.get('tool', '').startswith(f'{{TOOL_NAME}}@'):",
                "            args = step.get('arguments', {})",
                f"            if '{action['from']}' in args:",
                f"                args['{action['to']}'] = args.pop('{action['from']}')",
                "                modified = True",
            ])
        
        return code