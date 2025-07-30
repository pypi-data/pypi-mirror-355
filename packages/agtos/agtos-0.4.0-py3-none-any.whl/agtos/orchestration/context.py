"""Workflow context management for multi-agent orchestration.

AI_CONTEXT:
    This module manages context sharing between agents in a workflow.
    Context includes:
    - Results from previous steps
    - Shared data between agents
    - Workflow parameters
    - Execution history
    
    The context enables agents to build on each other's work.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class WorkflowContext:
    """Manages context data throughout workflow execution.
    
    AI_CONTEXT:
        The context is crucial for multi-agent collaboration. It allows:
        - Claude to design something that Codex implements
        - Cursor to see what Claude analyzed
        - Agents to share data without direct communication
        - Workflows to maintain state across steps
    """
    
    def __init__(self, workflow_name: str):
        """Initialize workflow context.
        
        Args:
            workflow_name: Name of the workflow
        """
        self.workflow_name = workflow_name
        self.start_time = datetime.now()
        self._data: Dict[str, Any] = {}
        self._step_results: List[Any] = []
        self._parameters: Dict[str, Any] = {}
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update context with new data.
        
        Args:
            data: Data to merge into context
        """
        self._data.update(data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value from context or default
        """
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in context.
        
        Args:
            key: Key to set
            value: Value to store
        """
        self._data[key] = value
    
    def add_step_result(self, step_name: str, result: Any) -> None:
        """Add a step result to history.
        
        Args:
            step_name: Name of the step
            result: Result object from step execution
        """
        self._step_results.append(result)
        
        # Also store in data for easy access
        self._data[f"step_{step_name}_result"] = result
        self._data["last_step_result"] = result
    
    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get result from a specific step.
        
        Args:
            step_name: Name of the step
            
        Returns:
            Step result or None
        """
        return self._data.get(f"step_{step_name}_result")
    
    def get_last_result(self) -> Optional[Any]:
        """Get the most recent step result."""
        return self._step_results[-1] if self._step_results else None
    
    def get_recent_results(self, n: int = 5) -> List[Any]:
        """Get the N most recent step results.
        
        Args:
            n: Number of results to retrieve
            
        Returns:
            List of recent results
        """
        return self._step_results[-n:] if self._step_results else []
    
    def get_all_results(self) -> List[Any]:
        """Get all step results."""
        return self._step_results.copy()
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set workflow parameters.
        
        Args:
            parameters: Workflow parameters
        """
        self._parameters = parameters
        # Also make available in main data
        self._data["parameters"] = parameters
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a workflow parameter.
        
        Args:
            name: Parameter name
            default: Default value if not found
            
        Returns:
            Parameter value or default
        """
        return self._parameters.get(name, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary.
        
        Returns:
            Dictionary representation of context
        """
        return {
            "workflow_name": self.workflow_name,
            "start_time": self.start_time.isoformat(),
            "elapsed_time": (datetime.now() - self.start_time).total_seconds(),
            "parameters": self._parameters,
            "data": self._data,
            "step_count": len(self._step_results),
            "last_step_success": self._step_results[-1].success if self._step_results else None
        }
    
    def to_json(self) -> str:
        """Convert context to JSON string.
        
        Returns:
            JSON representation of context
        """
        # Create serializable version
        data = self.to_dict()
        
        # Convert step results to serializable format
        data["step_results"] = [
            {
                "step_name": r.step_name,
                "success": r.success,
                "agent_used": r.agent_used,
                "duration": r.duration,
                "cost": r.cost,
                "error": r.error
            }
            for r in self._step_results
        ]
        
        return json.dumps(data, indent=2)
    
    def clear(self) -> None:
        """Clear all context data."""
        self._data.clear()
        self._step_results.clear()
        self._parameters.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary.
        
        Returns:
            Summary statistics
        """
        total_steps = len(self._step_results)
        successful_steps = sum(1 for r in self._step_results if r.success)
        total_duration = sum(r.duration for r in self._step_results)
        total_cost = sum(r.cost for r in self._step_results)
        
        agents_used = {}
        for result in self._step_results:
            agent = result.agent_used
            if agent not in agents_used:
                agents_used[agent] = {"count": 0, "duration": 0, "cost": 0}
            agents_used[agent]["count"] += 1
            agents_used[agent]["duration"] += result.duration
            agents_used[agent]["cost"] += result.cost
        
        return {
            "workflow_name": self.workflow_name,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "total_duration": total_duration,
            "total_cost": total_cost,
            "agents_used": agents_used,
            "start_time": self.start_time.isoformat(),
            "elapsed_time": (datetime.now() - self.start_time).total_seconds()
        }