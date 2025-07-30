"""Workflow recording and replay system for agtos.

This package provides secure recording of tool executions and replay functionality
with parameter substitution and credential management.

AI_CONTEXT: The workflow system allows users to record sequences of tool
executions and replay them later with different parameters. Security is
paramount - all sensitive data is automatically redacted before saving.
"""

from .recorder import WorkflowRecorder, Workflow, ToolExecution, SecurityRedactor
from .replay import WorkflowPlayer, WorkflowStep, ParameterSubstitutor
from .library import WorkflowLibrary, WorkflowMetadata, get_library
from .analyzer import WorkflowAnalyzer, WorkflowDependency, WorkflowAnalysis
from .integration import WorkflowIntegration, get_integration

__all__ = [
    "WorkflowRecorder",
    "WorkflowPlayer", 
    "Workflow",
    "ToolExecution",
    "WorkflowStep",
    "SecurityRedactor",
    "ParameterSubstitutor",
    "WorkflowLibrary",
    "WorkflowMetadata",
    "get_library",
    "WorkflowAnalyzer",
    "WorkflowDependency",
    "WorkflowAnalysis",
    "WorkflowIntegration",
    "get_integration"
]