"""Workflow dependency analyzer for integration with version tracking.

This module analyzes workflow definitions to extract tool dependencies,
parameter usage, and version requirements for the dependency tracking system.

AI_CONTEXT:
    This analyzer bridges the workflow system and dependency tracker. It parses
    workflow YAML files to understand tool usage patterns, enabling intelligent
    update recommendations and impact analysis. Critical for maintaining
    workflow compatibility across tool updates.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from ..utils import get_logger
from ..versioning.dependency_tracker import DependencyTracker
from ..versioning.version_manager import VersionManager

logger = get_logger(__name__)


@dataclass
class WorkflowDependency:
    """Represents a tool dependency within a workflow.
    
    AI_CONTEXT: Captures detailed information about how a tool is used
    in a workflow, including which parameters and version constraints.
    """
    tool_name: str
    tool_type: str  # 'cli', 'rest', 'plugin', 'mcp'
    parameters_used: Set[str] = field(default_factory=set)
    required_version: Optional[str] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    usage_count: int = 0
    critical: bool = False  # If failure stops workflow
    

@dataclass
class WorkflowAnalysis:
    """Complete analysis of a workflow's dependencies.
    
    AI_CONTEXT: Comprehensive view of all tools and parameters used
    in a workflow, enabling dependency tracking and update impact analysis.
    """
    workflow_name: str
    workflow_version: str
    dependencies: List[WorkflowDependency]
    total_tool_calls: int
    unique_tools: int
    analysis_timestamp: str
    warnings: List[str] = field(default_factory=list)
    

class WorkflowAnalyzer:
    """Analyzes workflow definitions for dependency tracking.
    
    AI_CONTEXT:
        This analyzer examines workflow YAML files to extract all tool usage
        information. It identifies which tools are used, what parameters they
        receive, and any version constraints. This data feeds into the
        dependency tracker for comprehensive impact analysis.
    """
    
    def __init__(self, dependency_tracker: DependencyTracker,
                 version_manager: VersionManager):
        """Initialize workflow analyzer.
        
        Args:
            dependency_tracker: DependencyTracker instance
            version_manager: VersionManager instance
        """
        self.dependency_tracker = dependency_tracker
        self.version_manager = version_manager
        
    def analyze_workflow(self, workflow_path: Path) -> WorkflowAnalysis:
        """Analyze a workflow file for dependencies.
        
        Args:
            workflow_path: Path to workflow YAML file
            
        Returns:
            WorkflowAnalysis with complete dependency information
        """
        logger.info(f"Analyzing workflow: {workflow_path}")
        
        # Load workflow
        with open(workflow_path, 'r') as f:
            workflow_data = yaml.safe_load(f)
        
        workflow_name = workflow_data.get("name", workflow_path.stem)
        workflow_version = workflow_data.get("version", "1.0.0")
        
        # Extract dependencies
        dependencies = {}
        total_calls = 0
        warnings = []
        
        # Analyze pre-checks
        for check in workflow_data.get("pre_checks", []):
            self._analyze_step(check, dependencies, warnings)
            total_calls += 1
        
        # Analyze main steps
        for step in workflow_data.get("steps", []):
            self._analyze_step(step, dependencies, warnings)
            total_calls += 1
        
        # Analyze error handlers
        for handler in workflow_data.get("error_handlers", []):
            self._analyze_step(handler, dependencies, warnings)
            total_calls += 1
        
        # Analyze cleanup steps
        for cleanup in workflow_data.get("cleanup", []):
            self._analyze_step(cleanup, dependencies, warnings)
            total_calls += 1
        
        # Convert to list of WorkflowDependency objects
        dep_list = list(dependencies.values())
        
        return WorkflowAnalysis(
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            dependencies=dep_list,
            total_tool_calls=total_calls,
            unique_tools=len(dep_list),
            analysis_timestamp=datetime.now().isoformat(),
            warnings=warnings
        )
    
    def _analyze_step(self, step: Dict[str, Any], 
                     dependencies: Dict[str, WorkflowDependency],
                     warnings: List[str]):
        """Analyze a single workflow step for tool usage.
        
        Args:
            step: Step definition from workflow
            dependencies: Dict to accumulate dependencies
            warnings: List to accumulate warnings
        """
        tool_name = step.get("tool", "")
        if not tool_name:
            warnings.append(f"Step '{step.get('name', 'unnamed')}' has no tool defined")
            return
        
        # Parse tool type and name
        tool_type, clean_name = self._parse_tool_name(tool_name)
        
        # Get or create dependency entry
        dep_key = f"{tool_type}:{clean_name}"
        if dep_key not in dependencies:
            dependencies[dep_key] = WorkflowDependency(
                tool_name=clean_name,
                tool_type=tool_type,
                critical=step.get("on_error") == "stop"
            )
        
        dep = dependencies[dep_key]
        dep.usage_count += 1
        
        # Extract parameters used
        self._extract_parameters(step, dep)
        
        # Check for version constraints
        if "version" in step:
            dep.required_version = step["version"]
        elif "min_version" in step:
            dep.min_version = step["min_version"]
        elif "max_version" in step:
            dep.max_version = step["max_version"]
    
    def _parse_tool_name(self, tool_name: str) -> Tuple[str, str]:
        """Parse tool name to extract type and clean name.
        
        Args:
            tool_name: Full tool name (e.g., 'cli__git__status')
            
        Returns:
            Tuple of (tool_type, clean_name)
        """
        parts = tool_name.split("__", 1)
        
        if parts[0] in ["cli", "rest", "plugin", "mcp"]:
            return parts[0], tool_name
        else:
            # Default to plugin if no prefix
            return "plugin", tool_name
    
    def _extract_parameters(self, step: Dict[str, Any], 
                           dependency: WorkflowDependency):
        """Extract parameters used in a step.
        
        Args:
            step: Step definition
            dependency: WorkflowDependency to update
        """
        # Direct arguments
        if "arguments" in step:
            args = step["arguments"]
            if isinstance(args, dict):
                dependency.parameters_used.update(args.keys())
        
        # Named parameters
        if "parameters" in step:
            params = step["parameters"]
            if isinstance(params, dict):
                dependency.parameters_used.update(params.keys())
        
        # Environment variables (often contain parameters)
        if "env" in step:
            env = step["env"]
            if isinstance(env, dict):
                # Track env vars as special parameters
                for key in env.keys():
                    dependency.parameters_used.add(f"env:{key}")
    
    def track_workflow_dependencies(self, workflow_path: Path) -> WorkflowAnalysis:
        """Analyze workflow and update dependency tracker.
        
        Args:
            workflow_path: Path to workflow YAML file
            
        Returns:
            WorkflowAnalysis results
        """
        # Analyze workflow
        analysis = self.analyze_workflow(workflow_path)
        
        # Update dependency tracker for each tool
        for dep in analysis.dependencies:
            # Get active version if not specified
            version = dep.required_version
            if not version:
                version = self.version_manager.get_active_version(dep.tool_name)
                if not version:
                    logger.warning(f"No active version for tool: {dep.tool_name}")
                    continue
            
            # Track usage
            self.dependency_tracker.track_usage(
                context_name=analysis.workflow_name,
                context_type="workflow",
                tool_name=dep.tool_name,
                version=version,
                parameters_used=list(dep.parameters_used)
            )
        
        logger.info(f"Tracked {len(analysis.dependencies)} dependencies for {analysis.workflow_name}")
        return analysis
    
    def analyze_all_workflows(self, workflows_dir: Path) -> Dict[str, WorkflowAnalysis]:
        """Analyze all workflows in a directory.
        
        Args:
            workflows_dir: Directory containing workflow YAML files
            
        Returns:
            Dict mapping workflow names to analysis results
        """
        results = {}
        
        for yaml_file in workflows_dir.glob("*.yaml"):
            try:
                analysis = self.track_workflow_dependencies(yaml_file)
                results[analysis.workflow_name] = analysis
            except Exception as e:
                logger.error(f"Failed to analyze {yaml_file}: {e}")
        
        return results
    
    def check_workflow_compatibility(self, workflow_path: Path,
                                   tool_name: str, new_version: str) -> Dict[str, Any]:
        """Check if a workflow is compatible with a tool version.
        
        Args:
            workflow_path: Path to workflow YAML file
            tool_name: Name of tool being updated
            new_version: New version to check
            
        Returns:
            Compatibility report
        """
        # Analyze workflow
        analysis = self.analyze_workflow(workflow_path)
        
        # Find dependency for this tool
        tool_dep = None
        for dep in analysis.dependencies:
            if dep.tool_name == tool_name:
                tool_dep = dep
                break
        
        if not tool_dep:
            return {
                "compatible": True,
                "reason": "Workflow does not use this tool"
            }
        
        # Check version constraints
        issues = []
        
        if tool_dep.required_version and tool_dep.required_version != new_version:
            issues.append(f"Requires exact version {tool_dep.required_version}")
        
        if tool_dep.min_version and not self._version_gte(new_version, tool_dep.min_version):
            issues.append(f"Requires minimum version {tool_dep.min_version}")
        
        if tool_dep.max_version and not self._version_lte(new_version, tool_dep.max_version):
            issues.append(f"Requires maximum version {tool_dep.max_version}")
        
        # Check parameter compatibility
        new_metadata = self.version_manager.get_version_metadata(tool_name, new_version)
        if new_metadata:
            available_params = self._extract_tool_parameters(new_metadata)
            missing_params = tool_dep.parameters_used - available_params
            
            if missing_params:
                issues.append(f"Uses parameters not in new version: {missing_params}")
        
        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "parameters_used": list(tool_dep.parameters_used),
            "usage_count": tool_dep.usage_count,
            "critical": tool_dep.critical
        }
    
    def _extract_tool_parameters(self, metadata: Dict[str, Any]) -> Set[str]:
        """Extract available parameters from tool metadata.
        
        Args:
            metadata: Tool metadata
            
        Returns:
            Set of parameter names
        """
        params = set()
        spec = metadata.get("specification", {})
        
        for endpoint in spec.get("endpoints", []):
            for param in endpoint.get("parameters", []):
                params.add(param["name"])
        
        return params
    
    def _version_gte(self, version1: str, version2: str) -> bool:
        """Check if version1 >= version2."""
        try:
            from packaging.version import parse
            return parse(version1) >= parse(version2)
        except:
            # Fallback to string comparison
            return version1 >= version2
    
    def _version_lte(self, version1: str, version2: str) -> bool:
        """Check if version1 <= version2."""
        try:
            from packaging.version import parse
            return parse(version1) <= parse(version2)
        except:
            # Fallback to string comparison
            return version1 <= version2