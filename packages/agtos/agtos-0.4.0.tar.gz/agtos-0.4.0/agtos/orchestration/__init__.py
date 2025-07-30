"""Multi-agent workflow orchestration engine.

AI_CONTEXT:
    This package implements the orchestration layer for agtOS that
    coordinates multiple AI agents to complete complex workflows.
    
    It builds on top of the existing workflow recording/replay system
    but adds multi-agent capabilities:
    - Agent selection based on capabilities
    - Context sharing between agents
    - Parallel and sequential execution
    - Intelligent routing decisions
    
    The existing workflows/ package handles tool recording/replay,
    while this package handles agent orchestration.
"""

from .engine import OrchestrationEngine, WorkflowDefinition, WorkflowStep, StepResult
from .parser import WorkflowParser
from .router import AgentRouter
from .context import WorkflowContext

__all__ = [
    'OrchestrationEngine',
    'WorkflowDefinition',
    'WorkflowStep',
    'StepResult',
    'WorkflowParser',
    'AgentRouter',
    'WorkflowContext'
]