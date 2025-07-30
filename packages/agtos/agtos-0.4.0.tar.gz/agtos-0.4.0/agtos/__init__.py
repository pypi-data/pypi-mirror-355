"""agtOS - Agent Operating System for AI orchestration.

A multi-agent orchestration platform that enables developers to seamlessly 
coordinate multiple AI agents (Claude, Codex, Cursor, local models) through 
a unified interface. Built on Meta-MCP for universal tool access.

AI_CONTEXT:
    agtOS has evolved from a simple MCP server to a full agent operating
    system. Key components:
    - Multi-agent orchestration with intelligent routing
    - Meta-MCP server providing tools to ALL agents
    - Workflow engine for complex multi-step operations
    - Support for Claude, Codex, Cursor, and local models
    - "Docker for AI agents" - simple, powerful, essential
"""

__version__ = "0.3.6"
__author__ = "William Attaway"

# Public API
from .project_store import ProjectStore
from .providers import get_provider, list_available_providers

# Multi-agent components
from .agents import (
    BaseAgent,
    AgentCapability,
    AgentStatus,
    AgentRegistry,
    ClaudeAgent
)

from .orchestration import (
    OrchestrationEngine,
    WorkflowDefinition,
    WorkflowStep,
    StepResult,
    WorkflowParser,
    AgentRouter,
    WorkflowContext
)

__all__ = [
    # Original API
    "ProjectStore",
    "get_provider", 
    "list_available_providers",
    "__version__",
    
    # Agent components
    "BaseAgent",
    "AgentCapability",
    "AgentStatus", 
    "AgentRegistry",
    "ClaudeAgent",
    
    # Orchestration components
    "OrchestrationEngine",
    "WorkflowDefinition",
    "WorkflowStep",
    "StepResult",
    "WorkflowParser",
    "AgentRouter",
    "WorkflowContext"
]