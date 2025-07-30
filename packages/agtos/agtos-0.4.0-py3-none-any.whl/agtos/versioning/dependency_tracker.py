"""Dependency tracking for tools and workflows.

Tracks which workflows use which tools, parameter usage patterns,
and analyzes upgrade impacts.

AI_CONTEXT:
    This is crucial for safe updates. It tracks every tool usage in workflows,
    which parameters are actually used, and can predict the impact of changes.
    This enables intelligent update recommendations and migration planning.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class DependencyInfo:
    """Information about a tool dependency."""
    tool_name: str
    version: str
    used_by: str  # workflow or tool name
    usage_type: str  # 'workflow' or 'tool'
    parameters_used: List[str] = field(default_factory=list)
    last_used: Optional[str] = None
    usage_count: int = 0


@dataclass 
class UpgradeImpact:
    """Analysis of upgrade impact."""
    affected_workflows: List[str]
    affected_tools: List[str]
    breaking_changes: List[Dict[str, Any]]
    parameter_conflicts: List[Dict[str, Any]]
    estimated_risk: str  # 'low', 'medium', 'high'
    auto_migratable: bool
    manual_steps_required: List[str]


class DependencyTracker:
    """Tracks and analyzes dependencies between tools and workflows.
    
    AI_CONTEXT:
        This class maintains a comprehensive index of all tool usage across
        workflows. It tracks not just which tools are used, but HOW they're
        used - which parameters, how often, and in what context. This enables
        intelligent decision-making about updates and migrations.
    """
    
    def __init__(self, tools_dir: Path):
        """Initialize dependency tracker.
        
        Args:
            tools_dir: Base directory for user tools
        """
        self.tools_dir = Path(tools_dir)
        self.index_file = self.tools_dir / "dependency_index.json"
        self.dependency_index = self._load_dependency_index()
    
    def _load_dependency_index(self) -> Dict[str, Any]:
        """Load the dependency index from disk."""
        if self.index_file.exists():
            return json.loads(self.index_file.read_text())
        else:
            return {
                "active_versions": {},
                "dependencies": {},
                "parameter_usage": {},
                "workflow_tools": {},
                "tool_dependencies": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_dependency_index(self):
        """Save the dependency index to disk."""
        self.dependency_index["last_updated"] = datetime.now().isoformat()
        self.index_file.write_text(json.dumps(self.dependency_index, indent=2))
    
    def track_usage(self, context_name: str, context_type: str,
                   tool_name: str, version: str, 
                   parameters_used: List[str]):
        """Track tool usage within a workflow or another tool.
        
        Args:
            context_name: Name of workflow or tool using this tool
            context_type: 'workflow' or 'tool'
            tool_name: Name of the tool being used
            version: Version of the tool
            parameters_used: List of parameter names that were used
        """
        # Create tool entry if it doesn't exist
        if tool_name not in self.dependency_index["dependencies"]:
            self.dependency_index["dependencies"][tool_name] = {}
        
        if version not in self.dependency_index["dependencies"][tool_name]:
            self.dependency_index["dependencies"][tool_name][version] = {
                "used_by": [],
                "total_usage_count": 0,
                "parameter_stats": {}
            }
        
        tool_deps = self.dependency_index["dependencies"][tool_name][version]
        
        # Track usage context
        usage_key = f"{context_type}:{context_name}"
        existing_usage = next(
            (u for u in tool_deps["used_by"] if u["context"] == usage_key),
            None
        )
        
        if existing_usage:
            existing_usage["usage_count"] += 1
            existing_usage["last_used"] = datetime.now().isoformat()
            # Merge parameters
            existing_params = set(existing_usage.get("parameters", []))
            existing_params.update(parameters_used)
            existing_usage["parameters"] = list(existing_params)
        else:
            tool_deps["used_by"].append({
                "context": usage_key,
                "context_type": context_type,
                "context_name": context_name,
                "parameters": parameters_used,
                "usage_count": 1,
                "first_used": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            })
        
        # Update parameter statistics
        tool_deps["total_usage_count"] += 1
        for param in parameters_used:
            if param not in tool_deps["parameter_stats"]:
                tool_deps["parameter_stats"][param] = 0
            tool_deps["parameter_stats"][param] += 1
        
        # Update reverse mapping for workflows
        if context_type == "workflow":
            if context_name not in self.dependency_index["workflow_tools"]:
                self.dependency_index["workflow_tools"][context_name] = []
            
            tool_ref = f"{tool_name}@{version}"
            if tool_ref not in self.dependency_index["workflow_tools"][context_name]:
                self.dependency_index["workflow_tools"][context_name].append(tool_ref)
        
        self._save_dependency_index()
    
    def get_dependents(self, tool_name: str, version: Optional[str] = None) -> List[DependencyInfo]:
        """Get all workflows/tools that depend on this tool.
        
        Args:
            tool_name: Name of the tool
            version: Optional specific version (None for all versions)
            
        Returns:
            List of dependency information
        """
        dependents = []
        
        if tool_name not in self.dependency_index["dependencies"]:
            return dependents
        
        tool_deps = self.dependency_index["dependencies"][tool_name]
        versions_to_check = [version] if version else tool_deps.keys()
        
        for v in versions_to_check:
            if v not in tool_deps:
                continue
                
            for usage in tool_deps[v]["used_by"]:
                dependents.append(DependencyInfo(
                    tool_name=tool_name,
                    version=v,
                    used_by=usage["context_name"],
                    usage_type=usage["context_type"],
                    parameters_used=usage["parameters"],
                    last_used=usage["last_used"],
                    usage_count=usage["usage_count"]
                ))
        
        return dependents
    
    def analyze_upgrade_impact(self, tool_name: str, 
                             from_version: str, to_version: str,
                             version_manager: Any) -> UpgradeImpact:
        """Analyze the impact of upgrading a tool version.
        
        Args:
            tool_name: Name of the tool
            from_version: Current version
            to_version: Target version
            version_manager: VersionManager instance for metadata
            
        Returns:
            UpgradeImpact analysis
        """
        # Get metadata for both versions
        from_metadata = version_manager.get_version_metadata(tool_name, from_version)
        to_metadata = version_manager.get_version_metadata(tool_name, to_version)
        
        if not from_metadata or not to_metadata:
            raise ValueError("Cannot find metadata for versions")
        
        # Find all dependents of current version
        dependents = self.get_dependents(tool_name, from_version)
        affected_workflows = [d.used_by for d in dependents if d.usage_type == "workflow"]
        affected_tools = [d.used_by for d in dependents if d.usage_type == "tool"]
        
        # Analyze breaking changes
        breaking_changes = self._analyze_breaking_changes(from_metadata, to_metadata)
        
        # Check parameter conflicts
        parameter_conflicts = self._check_parameter_conflicts(
            dependents, from_metadata, to_metadata
        )
        
        # Estimate risk
        risk = self._estimate_upgrade_risk(
            breaking_changes, parameter_conflicts, len(dependents)
        )
        
        # Determine if auto-migratable
        auto_migratable = all(
            change.get("migration") == "automatic" 
            for change in breaking_changes
        )
        
        # Collect manual steps
        manual_steps = [
            change.get("instructions", "Manual migration required")
            for change in breaking_changes
            if change.get("migration") == "manual"
        ]
        
        return UpgradeImpact(
            affected_workflows=affected_workflows,
            affected_tools=affected_tools,
            breaking_changes=breaking_changes,
            parameter_conflicts=parameter_conflicts,
            estimated_risk=risk,
            auto_migratable=auto_migratable,
            manual_steps_required=manual_steps
        )
    
    def find_unused_parameters(self, tool_name: str, version: Optional[str] = None) -> List[str]:
        """Find parameters that are never used in any workflow.
        
        Args:
            tool_name: Name of the tool
            version: Optional specific version
            
        Returns:
            List of unused parameter names
        """
        # Get tool metadata to find all parameters
        from .version_manager import VersionManager
        vm = VersionManager(self.tools_dir)
        
        if version:
            metadata = vm.get_version_metadata(tool_name, version)
            versions = [version]
        else:
            # Check active version
            version = vm.get_active_version(tool_name)
            if not version:
                return []
            metadata = vm.get_version_metadata(tool_name, version)
            versions = [version]
        
        if not metadata:
            return []
        
        # Extract all parameter names from specification
        all_params = set()
        spec = metadata.get("specification", {})
        for endpoint in spec.get("endpoints", []):
            for param in endpoint.get("parameters", []):
                all_params.add(param["name"])
        
        # Find which parameters are used
        used_params = set()
        for v in versions:
            if (tool_name in self.dependency_index["dependencies"] and
                v in self.dependency_index["dependencies"][tool_name]):
                param_stats = self.dependency_index["dependencies"][tool_name][v]["parameter_stats"]
                used_params.update(param_stats.keys())
        
        # Return unused parameters
        return list(all_params - used_params)
    
    def get_parameter_usage_stats(self, tool_name: str, version: str) -> Dict[str, int]:
        """Get usage statistics for each parameter.
        
        Args:
            tool_name: Name of the tool
            version: Version of the tool
            
        Returns:
            Dict mapping parameter names to usage counts
        """
        if (tool_name not in self.dependency_index["dependencies"] or
            version not in self.dependency_index["dependencies"][tool_name]):
            return {}
        
        return self.dependency_index["dependencies"][tool_name][version]["parameter_stats"].copy()
    
    def find_tools_by_workflow(self, workflow_name: str) -> List[str]:
        """Find all tools used by a workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            List of tool references (name@version)
        """
        return self.dependency_index["workflow_tools"].get(workflow_name, [])
    
    def generate_dependency_graph(self) -> Dict[str, Any]:
        """Generate a dependency graph for visualization.
        
        Returns:
            Graph structure suitable for visualization
        """
        nodes = []
        edges = []
        
        # Add tool nodes
        for tool_name, versions in self.dependency_index["dependencies"].items():
            for version, data in versions.items():
                node_id = f"{tool_name}@{version}"
                nodes.append({
                    "id": node_id,
                    "type": "tool",
                    "name": tool_name,
                    "version": version,
                    "usage_count": data["total_usage_count"]
                })
        
        # Add workflow nodes and edges
        for workflow_name, tools in self.dependency_index["workflow_tools"].items():
            nodes.append({
                "id": f"workflow:{workflow_name}",
                "type": "workflow",
                "name": workflow_name
            })
            
            for tool_ref in tools:
                edges.append({
                    "from": f"workflow:{workflow_name}",
                    "to": tool_ref,
                    "type": "uses"
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "generated_at": datetime.now().isoformat()
        }
    
    def _analyze_breaking_changes(self, from_metadata: Dict[str, Any], 
                                to_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze breaking changes between versions."""
        breaking_changes = []
        
        # Check for documented breaking changes
        if "breaking_changes" in to_metadata:
            version_changes = to_metadata["breaking_changes"]
            for version, changes in version_changes.items():
                breaking_changes.extend(changes)
        
        # Auto-detect some breaking changes
        from_spec = from_metadata.get("specification", {})
        to_spec = to_metadata.get("specification", {})
        
        # Check for removed parameters
        from_params = self._extract_all_parameters(from_spec)
        to_params = self._extract_all_parameters(to_spec)
        
        removed_params = from_params - to_params
        for param in removed_params:
            breaking_changes.append({
                "type": "parameter_removed",
                "parameter": param,
                "migration": "manual",
                "instructions": f"Parameter '{param}' has been removed"
            })
        
        # Check for authentication changes
        from_auth = self._extract_auth_type(from_spec)
        to_auth = self._extract_auth_type(to_spec)
        
        if from_auth != to_auth:
            breaking_changes.append({
                "type": "auth_change",
                "from": from_auth,
                "to": to_auth,
                "migration": "manual",
                "instructions": "Authentication method has changed"
            })
        
        return breaking_changes
    
    def _check_parameter_conflicts(self, dependents: List[DependencyInfo],
                                 from_metadata: Dict[str, Any],
                                 to_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for parameter usage conflicts."""
        conflicts = []
        
        to_spec = to_metadata.get("specification", {})
        to_params = self._extract_all_parameters(to_spec)
        
        # Check if any used parameters are missing in new version
        for dep in dependents:
            for param in dep.parameters_used:
                if param not in to_params:
                    conflicts.append({
                        "type": "missing_parameter",
                        "parameter": param,
                        "used_by": dep.used_by,
                        "usage_type": dep.usage_type
                    })
        
        return conflicts
    
    def _estimate_upgrade_risk(self, breaking_changes: List[Dict[str, Any]],
                             parameter_conflicts: List[Dict[str, Any]],
                             dependent_count: int) -> str:
        """Estimate the risk level of an upgrade."""
        # High risk if any manual breaking changes or many dependents
        if any(c.get("migration") == "manual" for c in breaking_changes):
            return "high"
        
        if parameter_conflicts or dependent_count > 10:
            return "medium"
        
        if breaking_changes or dependent_count > 5:
            return "medium"
        
        return "low"
    
    def _extract_all_parameters(self, spec: Dict[str, Any]) -> Set[str]:
        """Extract all parameter names from a specification."""
        params = set()
        for endpoint in spec.get("endpoints", []):
            for param in endpoint.get("parameters", []):
                params.add(param["name"])
        return params
    
    def _extract_auth_type(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract authentication type from specification."""
        for endpoint in spec.get("endpoints", []):
            if auth := endpoint.get("authentication"):
                return auth.get("type", "unknown")
        return None