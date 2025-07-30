"""Base agent class for all AI agents in agtOS.

AI_CONTEXT:
    This module defines the abstract base class that all agents must implement.
    It provides:
    - Lifecycle hooks (initialize, health_check, shutdown)
    - Capability declaration
    - Execution interface
    - Cost tracking
    - Context management
    
    The design allows for different agent types (MCP, CLI, API, local) while
    providing a consistent interface for the orchestrator.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle status."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentCapability(Enum):
    """Standard capability types that agents can provide."""
    # Core capabilities
    REASONING = "reasoning"
    CODE_GENERATION = "code-generation"
    CODE_REVIEW = "code-review"
    CODE_ANALYSIS = "code-analysis"
    
    # Specialized capabilities
    MULTI_FILE_EDIT = "multi-file-edit"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    
    # Domain-specific
    AWS_CODE = "aws-code"
    CLOUD_INFRASTRUCTURE = "cloud-infrastructure"
    SECURITY_ANALYSIS = "security-analysis"
    PERFORMANCE_ANALYSIS = "performance-analysis"
    
    # Tool-specific
    TOOL_EXECUTION = "tool-execution"
    API_INTERACTION = "api-interaction"
    FILE_OPERATIONS = "file-operations"
    WEB_AUTOMATION = "web-automation"
    TERMINAL_TASKS = "terminal-tasks"
    SCRIPTING = "scripting"
    AUTOMATION = "automation"
    LINTING = "linting"
    FORMATTING = "formatting"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    type: str  # 'mcp', 'cli', 'api', 'local'
    description: str
    version: Optional[str] = None
    endpoint: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, int]] = None  # capability -> score (0-10)
    metadata: Optional[Dict[str, Any]] = None
    

@dataclass
class ExecutionResult:
    """Result from agent execution."""
    success: bool
    content: Any
    agent: str
    duration: float
    cost: float = 0.0
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Abstract base class for all agents in agtOS.
    
    AI_CONTEXT:
        All agents (Claude, Codex, Cursor, local models) inherit from this
        class. It provides:
        - Consistent interface for the orchestrator
        - Lifecycle management
        - Capability reporting
        - Context handling
        - Cost tracking
        
        The existing MCP server code will be refactored into ClaudeAgent,
        which inherits from this class.
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = config
        self.status = AgentStatus.UNINITIALIZED
        self._context: Dict[str, Any] = {}
        self._total_cost = 0.0
        self._total_tokens = 0
        self._execution_count = 0
        self._start_time = datetime.now()
        
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name
    
    @property
    def capabilities(self) -> Dict[AgentCapability, int]:
        """Get agent capabilities with scores."""
        cap_dict = {}
        if self.config.capabilities:
            for cap_str, score in self.config.capabilities.items():
                try:
                    cap_enum = AgentCapability(cap_str)
                    cap_dict[cap_enum] = score
                except ValueError:
                    logger.warning(f"Unknown capability: {cap_str}")
        return cap_dict
    
    def get_capability_score(self, capability: AgentCapability) -> int:
        """Get score for a specific capability (0-10)."""
        return self.capabilities.get(capability, 0)
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent connection and resources.
        
        This method should:
        - Establish connections (MCP, API, etc.)
        - Verify authentication
        - Load any required resources
        - Set status to READY when complete
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the agent is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ExecutionResult:
        """Execute a task with the agent.
        
        Args:
            prompt: The task/prompt to execute
            context: Optional context from previous steps
            **kwargs: Agent-specific parameters
            
        Returns:
            ExecutionResult with success status and content
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent.
        
        This method should:
        - Close connections
        - Save state if needed
        - Release resources
        - Set status to SHUTDOWN
        """
        pass
    
    # ========================================================================
    # Common functionality for all agents
    # ========================================================================
    
    def update_context(self, key: str, value: Any) -> None:
        """Update agent context for future executions."""
        self._context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from agent context."""
        return self._context.get(key, default)
    
    def clear_context(self) -> None:
        """Clear all context."""
        self._context.clear()
    
    def record_execution(
        self,
        duration: float,
        cost: float = 0.0,
        tokens: Optional[int] = None
    ) -> None:
        """Record execution metrics."""
        self._execution_count += 1
        self._total_cost += cost
        if tokens:
            self._total_tokens += tokens
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        uptime = (datetime.now() - self._start_time).total_seconds()
        return {
            "name": self.name,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "execution_count": self._execution_count,
            "total_cost": self._total_cost,
            "total_tokens": self._total_tokens,
            "average_cost": self._total_cost / max(1, self._execution_count),
            "capabilities": {
                cap.value: score 
                for cap, score in self.capabilities.items()
            }
        }
    
    def supports_capability(
        self,
        capability: AgentCapability,
        min_score: int = 5
    ) -> bool:
        """Check if agent supports a capability with minimum score."""
        return self.get_capability_score(capability) >= min_score
    
    def get_best_capabilities(self, top_n: int = 3) -> List[AgentCapability]:
        """Get the agent's strongest capabilities."""
        sorted_caps = sorted(
            self.capabilities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [cap for cap, _ in sorted_caps[:top_n]]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', status={self.status.value})"