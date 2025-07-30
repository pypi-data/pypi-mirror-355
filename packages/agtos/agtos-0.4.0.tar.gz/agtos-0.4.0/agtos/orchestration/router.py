"""Intelligent agent routing for workflow orchestration.

AI_CONTEXT:
    This module implements intelligent agent selection based on:
    - Agent capabilities
    - Past performance
    - Cost optimization
    - Context requirements
    
    It's the brain that decides which agent should handle each task.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from ..agents import BaseAgent, AgentCapability, AgentRegistry

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes tasks to the most appropriate agents.
    
    AI_CONTEXT:
        The router is key to agtOS's value proposition. It knows:
        - Claude excels at reasoning and architecture
        - Codex is great for quick scripts and automation
        - Cursor shines at multi-file editing
        - Local models are free but less capable
        
        It makes intelligent decisions to optimize for quality,
        speed, and cost based on the task and context.
    """
    
    def __init__(self, registry: AgentRegistry):
        """Initialize the router with agent registry.
        
        Args:
            registry: Agent registry to use for selection
        """
        self.registry = registry
        self.routing_history = defaultdict(list)
        
    def select_agent(
        self,
        capability: AgentCapability,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAgent]:
        """Select the best agent for a capability.
        
        Args:
            capability: Required capability
            context: Selection context including preferences
            
        Returns:
            Selected agent or None
        """
        context = context or {}
        
        # Check for preferred agent
        if context.get("prefer"):
            preferred = self.registry.get_agent(context["prefer"])
            if preferred and preferred.supports_capability(capability):
                logger.info(f"Using preferred agent: {preferred.name}")
                return preferred
        
        # Get all agents that support the capability
        candidates = self.registry.find_agents_by_capability(capability)
        if not candidates:
            logger.warning(f"No agents found for capability: {capability.value}")
            return None
        
        # Score each candidate
        scores = self._score_agents(candidates, capability, context)
        
        # Apply fallback ordering if specified
        if context.get("fallback"):
            scores = self._apply_fallback_ordering(scores, context["fallback"])
        
        # Select highest scoring agent
        best_agent_name = max(scores, key=scores.get)
        selected = self.registry.get_agent(best_agent_name)
        
        # Record routing decision
        self._record_routing(capability, selected, context)
        
        logger.info(
            f"Selected agent '{selected.name}' for capability '{capability.value}' "
            f"(score: {scores[best_agent_name]:.1f})"
        )
        
        return selected
    
    def _score_agents(
        self,
        candidates: List[BaseAgent],
        capability: AgentCapability,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Score agents based on multiple factors.
        
        Scoring factors:
        - Base capability score (0-100)
        - Performance history (-20 to +20)
        - Context modifiers (varies)
        - Cost considerations (0-50)
        """
        scores = {}
        
        for agent in candidates:
            score = 0.0
            
            # Base capability score (0-10 -> 0-100)
            capability_score = agent.get_capability_score(capability)
            score += capability_score * 10
            
            # Performance history
            history_score = self._get_performance_score(agent.name, capability)
            score += history_score
            
            # Context-based modifiers
            score += self._apply_context_modifiers(agent, context)
            
            # Special capability bonuses
            score += self._get_capability_bonuses(agent, capability)
            
            scores[agent.name] = score
            
        return scores
    
    def _get_performance_score(
        self,
        agent_name: str,
        capability: AgentCapability
    ) -> float:
        """Calculate performance score from routing history.
        
        Returns:
            Score adjustment from -20 to +20
        """
        history = self.routing_history.get(agent_name, [])
        if not history:
            return 0.0
        
        # Filter by capability
        relevant = [h for h in history[-20:] if h["capability"] == capability]
        if not relevant:
            return 0.0
        
        # Calculate success rate
        successes = sum(1 for h in relevant if h.get("success", False))
        success_rate = successes / len(relevant)
        
        # Convert to score adjustment
        # 70% success = 0, 90% = +20, 50% = -20
        return (success_rate - 0.7) * 100
    
    def _apply_context_modifiers(
        self,
        agent: BaseAgent,
        context: Dict[str, Any]
    ) -> float:
        """Apply context-based score modifiers.
        
        Returns:
            Score adjustment based on context
        """
        modifier = 0.0
        
        # Local-only requirement
        if context.get("local_only"):
            if agent.config.metadata.get("is_local"):
                modifier += 100  # Strong preference
            else:
                modifier -= 1000  # Effectively disqualify
        
        # Cost optimization
        if context.get("optimize_cost"):
            if agent.config.metadata.get("is_free"):
                modifier += 50
            else:
                # Penalize based on cost
                cost_per_1k = agent.config.metadata.get("cost_per_1k_tokens", 0.01)
                modifier -= cost_per_1k * 100
        
        # Speed optimization
        if context.get("optimize_speed"):
            speed_score = agent.config.metadata.get("speed_score", 5)
            modifier += (speed_score - 5) * 5
        
        # Quality optimization
        if context.get("optimize_quality"):
            quality_score = agent.config.metadata.get("quality_score", 5)
            modifier += (quality_score - 5) * 10
        
        return modifier
    
    def _get_capability_bonuses(
        self,
        agent: BaseAgent,
        capability: AgentCapability
    ) -> float:
        """Apply special bonuses for known agent strengths.
        
        AI_CONTEXT:
            This encodes our knowledge about what each agent is
            particularly good at. For example:
            - Claude gets bonus for reasoning and architecture
            - Cursor gets bonus for multi-file editing
            - Codex gets bonus for terminal tasks
        """
        bonus = 0.0
        
        # Agent-specific bonuses
        agent_bonuses = {
            "claude": {
                AgentCapability.REASONING: 20,
                AgentCapability.CODE_REVIEW: 15,
                AgentCapability.DOCUMENTATION: 15,
            },
            "codex": {
                AgentCapability.TERMINAL_TASKS: 20,
                AgentCapability.SCRIPTING: 20,
                AgentCapability.AUTOMATION: 15,
            },
            "cursor": {
                AgentCapability.MULTI_FILE_EDIT: 25,
                AgentCapability.CODE_GENERATION: 10,
            },
            "local/codellama": {
                AgentCapability.CODE_GENERATION: 5,
                # Bonus for being free
                AgentCapability.SCRIPTING: 10,
            }
        }
        
        agent_name = agent.name.lower()
        if agent_name in agent_bonuses:
            bonus += agent_bonuses[agent_name].get(capability, 0)
        
        return bonus
    
    def _apply_fallback_ordering(
        self,
        scores: Dict[str, float],
        fallback_order: List[str]
    ) -> Dict[str, float]:
        """Adjust scores based on fallback preference order.
        
        Args:
            scores: Current agent scores
            fallback_order: Ordered list of fallback agents
            
        Returns:
            Adjusted scores
        """
        adjusted = scores.copy()
        
        # Give bonus points based on position in fallback list
        for i, agent_name in enumerate(fallback_order):
            if agent_name in adjusted:
                # Earlier in list = higher bonus
                bonus = (len(fallback_order) - i) * 10
                adjusted[agent_name] += bonus
        
        return adjusted
    
    def _record_routing(
        self,
        capability: AgentCapability,
        agent: BaseAgent,
        context: Dict[str, Any]
    ) -> None:
        """Record routing decision for learning.
        
        Args:
            capability: Requested capability
            agent: Selected agent
            context: Selection context
        """
        self.routing_history[agent.name].append({
            "capability": capability,
            "context": context.copy(),
            "timestamp": datetime.now().isoformat(),
            # Success will be updated later by feedback
            "success": None
        })
        
        # Keep history size manageable
        if len(self.routing_history[agent.name]) > 100:
            self.routing_history[agent.name] = self.routing_history[agent.name][-100:]
    
    def record_feedback(
        self,
        agent_name: str,
        success: bool,
        duration: Optional[float] = None
    ) -> None:
        """Record execution feedback for learning.
        
        Args:
            agent_name: Name of agent that executed
            success: Whether execution was successful
            duration: Execution duration in seconds
        """
        if agent_name in self.routing_history:
            history = self.routing_history[agent_name]
            if history:
                # Update the most recent routing decision
                history[-1]["success"] = success
                if duration:
                    history[-1]["duration"] = duration
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics.
        
        Returns:
            Dictionary of routing statistics
        """
        stats = {}
        
        for agent_name, history in self.routing_history.items():
            total = len(history)
            if total == 0:
                continue
                
            successes = sum(1 for h in history if h.get("success") is True)
            failures = sum(1 for h in history if h.get("success") is False)
            pending = total - successes - failures
            
            # Group by capability
            by_capability = defaultdict(lambda: {"total": 0, "success": 0})
            for h in history:
                cap = h["capability"]
                by_capability[cap.value]["total"] += 1
                if h.get("success"):
                    by_capability[cap.value]["success"] += 1
            
            stats[agent_name] = {
                "total_routings": total,
                "successes": successes,
                "failures": failures,
                "pending": pending,
                "success_rate": successes / (successes + failures) if (successes + failures) > 0 else 0,
                "by_capability": dict(by_capability)
            }
        
        return stats