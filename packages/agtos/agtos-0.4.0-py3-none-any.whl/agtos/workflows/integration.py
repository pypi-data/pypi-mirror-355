"""Integration between workflow system and dependency tracking.

This module provides hooks and decorators to automatically track tool usage
whenever workflows are created, saved, or executed.

AI_CONTEXT:
    This integration ensures dependency tracking happens transparently without
    changing the existing workflow API. It hooks into key workflow operations
    to maintain an accurate dependency graph for update impact analysis.
"""

import functools
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from ..utils import get_logger
from ..config import get_config_dir
from ..versioning.dependency_tracker import DependencyTracker
from ..versioning.version_manager import VersionManager
from .analyzer import WorkflowAnalyzer

logger = get_logger(__name__)


class WorkflowIntegration:
    """Manages integration between workflows and dependency tracking.
    
    AI_CONTEXT:
        Central integration point that coordinates workflow operations with
        dependency tracking. Provides decorators and hooks to ensure all
        tool usage is tracked without modifying existing workflow code.
    """
    
    _instance = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize integration if not already done."""
        if not self._initialized:
            tools_dir = get_config_dir() / "tools"
            self.dependency_tracker = DependencyTracker(tools_dir)
            self.version_manager = VersionManager(tools_dir)
            self.analyzer = WorkflowAnalyzer(
                self.dependency_tracker,
                self.version_manager
            )
            self._initialized = True
            self._hooks = {
                "workflow_saved": [],
                "workflow_executed": [],
                "tool_executed": [],
                "workflow_loaded": []
            }
    
    def register_hook(self, event: str, callback: Callable):
        """Register a callback for workflow events.
        
        Args:
            event: Event name ('workflow_saved', 'workflow_executed', etc.)
            callback: Function to call when event occurs
        """
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def _trigger_hooks(self, event: str, **kwargs):
        """Trigger all registered hooks for an event.
        
        Args:
            event: Event name
            **kwargs: Arguments to pass to callbacks
        """
        for callback in self._hooks.get(event, []):
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Hook error for {event}: {e}")
    
    def track_workflow_save(self, workflow_path: Path, workflow_data: Dict[str, Any]):
        """Track dependencies when a workflow is saved.
        
        Args:
            workflow_path: Path where workflow is saved
            workflow_data: Workflow definition data
        """
        try:
            # Analyze workflow dependencies
            analysis = self.analyzer.track_workflow_dependencies(workflow_path)
            
            # Log summary
            logger.info(
                f"Workflow '{analysis.workflow_name}' uses {analysis.unique_tools} tools "
                f"with {analysis.total_tool_calls} total calls"
            )
            
            # Trigger hooks
            self._trigger_hooks(
                "workflow_saved",
                workflow_path=workflow_path,
                analysis=analysis
            )
            
            # Check for version warnings
            if analysis.warnings:
                for warning in analysis.warnings:
                    logger.warning(f"Workflow analysis warning: {warning}")
                    
        except Exception as e:
            logger.error(f"Failed to track workflow save: {e}")
    
    def track_workflow_execution(self, workflow_name: str, workflow_version: str):
        """Track when a workflow starts execution.
        
        Args:
            workflow_name: Name of the workflow
            workflow_version: Version of the workflow
        """
        self._current_workflow = {
            "name": workflow_name,
            "version": workflow_version,
            "start_time": datetime.now().isoformat()
        }
        
        # Trigger hooks
        self._trigger_hooks(
            "workflow_executed",
            workflow_name=workflow_name,
            workflow_version=workflow_version
        )
    
    def track_tool_execution(self, tool_name: str, tool_type: str,
                           parameters: Dict[str, Any], result: Any):
        """Track individual tool execution within a workflow.
        
        Args:
            tool_name: Name of the tool
            tool_type: Type of tool ('cli', 'rest', etc.)
            parameters: Parameters passed to tool
            result: Execution result
        """
        if hasattr(self, '_current_workflow'):
            # Track in context of current workflow
            workflow = self._current_workflow
            
            # Determine tool version
            version = self.version_manager.get_active_version(tool_name)
            if not version:
                logger.warning(f"No version found for tool: {tool_name}")
                return
            
            # Track usage
            self.dependency_tracker.track_usage(
                context_name=workflow["name"],
                context_type="workflow",
                tool_name=tool_name,
                version=version,
                parameters_used=list(parameters.keys())
            )
            
            # Trigger hooks
            self._trigger_hooks(
                "tool_executed",
                workflow_name=workflow["name"],
                tool_name=tool_name,
                tool_type=tool_type,
                parameters=parameters,
                result=result
            )
    
    def check_workflow_updates(self, workflow_path: Path) -> Dict[str, Any]:
        """Check if any tools used by a workflow have updates.
        
        Args:
            workflow_path: Path to workflow YAML file
            
        Returns:
            Update information for workflow
        """
        # Analyze workflow
        analysis = self.analyzer.analyze_workflow(workflow_path)
        
        updates_available = []
        
        for dep in analysis.dependencies:
            # Get current version
            current = self.version_manager.get_active_version(dep.tool_name)
            if not current:
                continue
            
            # Check for updates
            available = self.version_manager.list_versions(dep.tool_name)
            newer_versions = [
                v for v in available
                if self._is_newer_version(v, current)
            ]
            
            if newer_versions:
                # Get latest version
                latest = max(newer_versions, key=lambda v: self._parse_version(v))
                
                # Check compatibility
                compat_check = self.analyzer.check_workflow_compatibility(
                    workflow_path, dep.tool_name, latest
                )
                
                updates_available.append({
                    "tool": dep.tool_name,
                    "current_version": current,
                    "latest_version": latest,
                    "compatible": compat_check["compatible"],
                    "compatibility_issues": compat_check.get("issues", []),
                    "usage_count": dep.usage_count,
                    "critical": dep.critical
                })
        
        return {
            "workflow": analysis.workflow_name,
            "total_dependencies": len(analysis.dependencies),
            "updates_available": len(updates_available),
            "updates": updates_available
        }
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Check if version1 is newer than version2."""
        try:
            from packaging.version import parse
            return parse(version1) > parse(version2)
        except:
            # Fallback to string comparison
            return version1 > version2
    
    def _parse_version(self, version: str):
        """Parse version for comparison."""
        try:
            from packaging.version import parse
            return parse(version)
        except:
            return version


# Global integration instance
_integration = WorkflowIntegration()


def track_workflow_save(func: Callable) -> Callable:
    """Decorator to track workflow saves.
    
    AI_CONTEXT: Apply this decorator to any function that saves workflows
    to automatically track dependencies.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Extract workflow path and data from function arguments
        # This assumes standard signature: save_workflow(path, data)
        if args:
            path = args[0] if isinstance(args[0], Path) else Path(args[0])
            data = args[1] if len(args) > 1 else kwargs.get('data', {})
            
            _integration.track_workflow_save(path, data)
        
        return result
    
    return wrapper


def track_workflow_execution(func: Callable) -> Callable:
    """Decorator to track workflow execution.
    
    AI_CONTEXT: Apply this decorator to workflow execution functions
    to track which workflows are actually used.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract workflow info from arguments
        workflow_name = kwargs.get('workflow_name', 'unknown')
        workflow_version = kwargs.get('workflow_version', '1.0.0')
        
        # Track start
        _integration.track_workflow_execution(workflow_name, workflow_version)
        
        # Execute workflow
        result = func(*args, **kwargs)
        
        return result
    
    return wrapper


def track_tool_execution(tool_type: str) -> Callable:
    """Decorator factory for tracking tool executions.
    
    Args:
        tool_type: Type of tool ('cli', 'rest', 'plugin', 'mcp')
        
    AI_CONTEXT: Apply this decorator to tool execution functions to
    automatically track parameter usage within workflows.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(tool_name: str, parameters: Dict[str, Any], *args, **kwargs):
            # Execute tool
            result = func(tool_name, parameters, *args, **kwargs)
            
            # Track execution
            _integration.track_tool_execution(
                tool_name=tool_name,
                tool_type=tool_type,
                parameters=parameters,
                result=result
            )
            
            return result
        
        return wrapper
    
    return decorator


def get_integration() -> WorkflowIntegration:
    """Get the global workflow integration instance.
    
    Returns:
        WorkflowIntegration singleton
    """
    return _integration