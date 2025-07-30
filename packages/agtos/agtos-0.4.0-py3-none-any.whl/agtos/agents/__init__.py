"""Multi-agent orchestration system for agtOS.

AI_CONTEXT:
    This package implements the core multi-agent functionality that transforms
    agtos from a single-agent MCP server to a full agent operating system.
    
    Key components:
    - BaseAgent: Abstract base class for all agents
    - AgentRegistry: Discovers and manages multiple AI agents
    - Agent implementations: Claude, Codex, Cursor, local models, etc.
    
    The existing Meta-MCP server becomes the universal tool layer that
    provides tools to ALL agents, not just Claude.
"""

from .base import BaseAgent, AgentCapability, AgentStatus, AgentConfig, ExecutionResult
from .registry import AgentRegistry
from .claude import ClaudeAgent
from .codex import CodexAgent
from .tool_agent import ToolAgent

__all__ = [
    'BaseAgent',
    'AgentCapability', 
    'AgentStatus',
    'AgentConfig',
    'ExecutionResult',
    'AgentRegistry',
    'ClaudeAgent',
    'CodexAgent',
    'ToolAgent'
]