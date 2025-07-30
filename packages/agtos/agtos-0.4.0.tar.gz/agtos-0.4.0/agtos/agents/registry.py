"""Agent registry for discovering and managing AI agents.

AI_CONTEXT:
    This module implements the agent discovery and management system.
    It handles:
    - Auto-discovery of installed agents
    - Agent registration and lifecycle
    - Capability tracking
    - Agent selection based on requirements
    - Performance tracking
    
    The registry is the central component that enables multi-agent
    orchestration in agtOS.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Any
import json
import yaml

from .base import BaseAgent, AgentCapability, AgentStatus, AgentConfig, ExecutionResult

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for all AI agents in agtOS.
    
    AI_CONTEXT:
        The registry manages the lifecycle of all agents and provides
        the orchestrator with agent discovery and selection capabilities.
        
        Key responsibilities:
        - Discover available agents (Claude, Codex, Cursor, etc.)
        - Initialize and health check agents
        - Track agent capabilities and performance
        - Provide agent selection based on requirements
        - Handle agent failures and recovery
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the agent registry.
        
        Args:
            config_path: Path to agents configuration file
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
        self.performance_history = defaultdict(list)
        self.config_path = config_path or Path.home() / ".agtos" / "agents.yaml"
        self._initialized = False
        
        # Register built-in agent types
        self._register_builtin_agents()
    
    def _register_builtin_agents(self) -> None:
        """Register built-in agent types."""
        # Import here to avoid circular imports
        from .claude import ClaudeAgent
        
        self.agent_classes["claude"] = ClaudeAgent
        # Future agents will be registered here:
        # self.agent_classes["codex"] = CodexAgent
        # self.agent_classes["cursor"] = CursorAgent
        # self.agent_classes["ollama"] = OllamaAgent
    
    async def initialize(self) -> None:
        """Initialize the registry and discover agents."""
        if self._initialized:
            return
            
        logger.info("Initializing agent registry...")
        
        # Load configuration
        config = await self._load_config()
        
        # Discover and initialize agents
        await self._discover_agents(config)
        
        # Health check all agents
        await self._health_check_all()
        
        self._initialized = True
        logger.info(f"Agent registry initialized with {len(self.agents)} agents")
    
    async def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from file."""
        if not self.config_path.exists():
            logger.info(f"No config file found at {self.config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_path) as f:
                if self.config_path.suffix == '.yaml':
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default agent configuration."""
        return {
            "agents": [
                {
                    "name": "claude",
                    "type": "claude",
                    "description": "Claude via MCP protocol",
                    "enabled": True,
                    "capabilities": {
                        "reasoning": 10,
                        "code-generation": 8,
                        "code-review": 9,
                        "documentation": 9,
                        "debugging": 8,
                        "multi-file-edit": 3
                    }
                }
                # Future agents:
                # {
                #     "name": "codex",
                #     "type": "codex",
                #     "description": "OpenAI Codex for quick implementation",
                #     "enabled": True,
                #     "capabilities": {
                #         "code-generation": 9,
                #         "terminal-tasks": 10,
                #         "scripting": 10,
                #         "automation": 9
                #     }
                # }
            ]
        }
    
    async def _discover_agents(self, config: Dict[str, Any]) -> None:
        """Discover and initialize configured agents."""
        agent_configs = config.get("agents", [])
        
        for agent_cfg in agent_configs:
            if not agent_cfg.get("enabled", True):
                continue
                
            agent_type = agent_cfg.get("type")
            if agent_type not in self.agent_classes:
                logger.warning(f"Unknown agent type: {agent_type}")
                continue
            
            try:
                # Create agent config
                agent_config = AgentConfig(
                    name=agent_cfg["name"],
                    type=agent_type,
                    description=agent_cfg.get("description", ""),
                    version=agent_cfg.get("version"),
                    endpoint=agent_cfg.get("endpoint"),
                    auth=agent_cfg.get("auth"),
                    capabilities=agent_cfg.get("capabilities", {}),
                    metadata=agent_cfg.get("metadata", {})
                )
                
                # Instantiate agent
                agent_class = self.agent_classes[agent_type]
                agent = agent_class(agent_config)
                
                # Initialize agent
                await agent.initialize()
                
                # Register agent
                self.agents[agent.name] = agent
                logger.info(f"Registered agent: {agent.name} ({agent_type})")
                
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_cfg['name']}: {e}")
    
    async def _health_check_all(self) -> None:
        """Health check all registered agents."""
        for name, agent in self.agents.items():
            try:
                if await agent.health_check():
                    agent.status = AgentStatus.READY
                    logger.info(f"Agent {name} is healthy")
                else:
                    agent.status = AgentStatus.ERROR
                    logger.warning(f"Agent {name} failed health check")
            except Exception as e:
                agent.status = AgentStatus.ERROR
                logger.error(f"Health check failed for {name}: {e}")
    
    # ========================================================================
    # Agent Selection and Execution
    # ========================================================================
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get a specific agent by name."""
        return self.agents.get(name)
    
    def get_available_agents(self) -> List[BaseAgent]:
        """Get all available (ready) agents."""
        return [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.READY
        ]
    
    def find_agents_by_capability(
        self,
        capability: AgentCapability,
        min_score: int = 5
    ) -> List[BaseAgent]:
        """Find agents that support a capability with minimum score."""
        matching_agents = []
        for agent in self.get_available_agents():
            if agent.supports_capability(capability, min_score):
                matching_agents.append(agent)
        
        # Sort by capability score
        matching_agents.sort(
            key=lambda a: a.get_capability_score(capability),
            reverse=True
        )
        
        return matching_agents
    
    def select_best_agent(
        self,
        capability: AgentCapability,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAgent]:
        """Select the best agent for a capability.
        
        AI_CONTEXT:
            This method implements intelligent agent selection based on:
            - Capability scores
            - Past performance
            - Current availability
            - Context requirements (e.g., prefer local for privacy)
            - Cost considerations
        """
        candidates = self.find_agents_by_capability(capability)
        if not candidates:
            return None
        
        # Score each candidate
        scores = {}
        for agent in candidates:
            score = 0.0
            
            # Base capability score (0-10 -> 0-100)
            score += agent.get_capability_score(capability) * 10
            
            # Performance history bonus (-20 to +20)
            perf_modifier = self._get_performance_modifier(agent.name, capability)
            score += perf_modifier
            
            # Context-based modifiers
            if context:
                # Prefer local agents for privacy
                if context.get("local_only") and agent.config.metadata.get("is_local"):
                    score += 50
                
                # Cost considerations
                if context.get("optimize_cost") and agent.config.metadata.get("is_free"):
                    score += 30
                
                # Speed requirements
                if context.get("optimize_speed"):
                    speed_score = agent.config.metadata.get("speed_score", 5)
                    score += speed_score * 2
            
            scores[agent.name] = score
        
        # Return highest scoring agent
        best_agent_name = max(scores, key=scores.get)
        return self.get_agent(best_agent_name)
    
    def _get_performance_modifier(
        self,
        agent_name: str,
        capability: AgentCapability
    ) -> float:
        """Calculate performance modifier based on history."""
        history = self.performance_history.get(agent_name, [])
        if not history:
            return 0.0
        
        # Filter by capability
        relevant = [h for h in history if h.get("capability") == capability]
        if not relevant:
            return 0.0
        
        # Calculate success rate (last 10 executions)
        recent = relevant[-10:]
        successes = sum(1 for h in recent if h.get("success", False))
        success_rate = successes / len(recent)
        
        # Convert to modifier (-20 to +20)
        # 70% success rate = 0 modifier
        return (success_rate - 0.7) * 100
    
    async def execute_with_best_agent(
        self,
        capability: AgentCapability,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        fallback_agents: Optional[List[str]] = None
    ) -> ExecutionResult:
        """Execute a task with the best available agent.
        
        Args:
            capability: Required capability
            prompt: Task prompt
            context: Execution context
            fallback_agents: Ordered list of fallback agent names
            
        Returns:
            ExecutionResult from successful execution
            
        Raises:
            RuntimeError: If no agents available or all fail
        """
        # Select primary agent
        primary_agent = self._select_primary_agent(capability, context)
        
        # Build list of agents to try
        agents_to_try = self._build_agent_execution_list(
            primary_agent, fallback_agents
        )
        
        # Execute with agents
        return await self._execute_with_agent_list(
            agents_to_try, capability, prompt, context
        )
    
    def _select_primary_agent(
        self,
        capability: AgentCapability,
        context: Optional[Dict[str, Any]]
    ) -> BaseAgent:
        """Select the primary agent for execution.
        
        Args:
            capability: Required capability
            context: Execution context
            
        Returns:
            Selected agent
            
        Raises:
            RuntimeError: If no agents available
        """
        agent = self.select_best_agent(capability, context)
        if not agent:
            raise RuntimeError(
                f"No agents available for capability: {capability.value}"
            )
        return agent
    
    def _build_agent_execution_list(
        self,
        primary_agent: BaseAgent,
        fallback_agent_names: Optional[List[str]]
    ) -> List[BaseAgent]:
        """Build ordered list of agents to try.
        
        Args:
            primary_agent: Primary agent to try first
            fallback_agent_names: Names of fallback agents
            
        Returns:
            List of agents in execution order
        """
        agents_to_try = [primary_agent]
        
        if fallback_agent_names:
            for name in fallback_agent_names:
                fallback = self.get_agent(name)
                if fallback and fallback.status == AgentStatus.READY:
                    agents_to_try.append(fallback)
                    
        return agents_to_try
    
    async def _execute_with_agent_list(
        self,
        agents: List[BaseAgent],
        capability: AgentCapability,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> ExecutionResult:
        """Execute task with ordered list of agents.
        
        Args:
            agents: Ordered list of agents to try
            capability: Required capability
            prompt: Task prompt
            context: Execution context
            
        Returns:
            ExecutionResult from successful execution
            
        Raises:
            RuntimeError: If all agents fail
        """
        last_error = None
        
        for agent in agents:
            result = await self._try_agent_execution(
                agent, capability, prompt, context
            )
            
            if result.success:
                return result
            else:
                last_error = result.error
                logger.warning(f"Agent {agent.name} failed: {result.error}")
        
        # All agents failed
        raise RuntimeError(
            f"All agents failed. Last error: {last_error}\n"
            f"Tried agents: {[a.name for a in agents]}"
        )
    
    async def _try_agent_execution(
        self,
        agent: BaseAgent,
        capability: AgentCapability,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> ExecutionResult:
        """Try executing task with a single agent.
        
        Args:
            agent: Agent to execute with
            capability: Required capability
            prompt: Task prompt
            context: Execution context
            
        Returns:
            ExecutionResult (may indicate failure)
        """
        try:
            logger.info(f"Executing with agent: {agent.name}")
            agent.status = AgentStatus.BUSY
            
            result = await agent.execute(prompt, context)
            
            if result.success:
                # Record success
                self._record_execution(
                    agent.name,
                    capability,
                    success=True,
                    duration=result.duration
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Agent {agent.name} raised exception: {e}")
            return ExecutionResult(
                success=False,
                content="",
                error=str(e),
                agent=agent.name,
                duration=0.0
            )
        finally:
            if agent.status == AgentStatus.BUSY:
                agent.status = AgentStatus.READY
    
    def _record_execution(
        self,
        agent_name: str,
        capability: AgentCapability,
        success: bool,
        duration: float
    ) -> None:
        """Record execution in performance history."""
        self.performance_history[agent_name].append({
            "capability": capability,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100 executions per agent
        if len(self.performance_history[agent_name]) > 100:
            self.performance_history[agent_name] = self.performance_history[agent_name][-100:]
    
    # ========================================================================
    # Registry Management
    # ========================================================================
    
    async def add_agent(self, agent: BaseAgent) -> None:
        """Add a new agent to the registry."""
        await agent.initialize()
        self.agents[agent.name] = agent
        logger.info(f"Added agent: {agent.name}")
    
    async def remove_agent(self, name: str) -> None:
        """Remove an agent from the registry."""
        if name in self.agents:
            agent = self.agents[name]
            await agent.shutdown()
            del self.agents[name]
            logger.info(f"Removed agent: {name}")
    
    async def shutdown(self) -> None:
        """Shutdown all agents and cleanup."""
        logger.info("Shutting down agent registry...")
        
        # Shutdown all agents
        shutdown_tasks = []
        for agent in self.agents.values():
            shutdown_tasks.append(agent.shutdown())
        
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.agents.clear()
        self._initialized = False
        logger.info("Agent registry shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_agents": len(self.agents),
            "ready_agents": len(self.get_available_agents()),
            "agents": {
                name: agent.get_stats()
                for name, agent in self.agents.items()
            },
            "performance_summary": self._get_performance_summary()
        }
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all agents."""
        summary = {}
        for agent_name, history in self.performance_history.items():
            if history:
                total = len(history)
                successes = sum(1 for h in history if h.get("success", False))
                avg_duration = sum(h.get("duration", 0) for h in history) / total
                
                summary[agent_name] = {
                    "total_executions": total,
                    "success_rate": successes / total,
                    "average_duration": avg_duration
                }
        return summary