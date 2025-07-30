"""Operation manager for tracking system operations and costs.

This module provides centralized tracking of all operations in agtOS including:
- AI agent operations (with cost tracking)
- System processes (npm, git, etc.)
- Tool executions
- Background tasks

AI_CONTEXT:
    The operation manager maintains a real-time view of what the system is doing.
    It tracks operation lifecycle (started, running, completed, failed) and
    calculates costs for AI operations based on token usage.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from .utils import get_logger
from .config import get_config_dir

logger = get_logger(__name__)


class OperationType(Enum):
    """Types of operations that can be tracked."""
    AI_AGENT = "ai_agent"
    SYSTEM_PROCESS = "system_process"
    TOOL_EXECUTION = "tool_execution"
    BACKGROUND_TASK = "background_task"
    NETWORK_REQUEST = "network_request"
    FILE_OPERATION = "file_operation"


class OperationStatus(Enum):
    """Status of an operation."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Operation:
    """Represents a tracked operation."""
    id: str
    type: OperationType
    name: str
    description: str
    status: OperationStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    progress: Optional[float] = None  # 0.0 to 1.0
    cost: Optional[float] = None  # In USD
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "progress": self.progress,
            "cost": self.cost,
            "metadata": self.metadata,
            "error": self.error
        }


class CostCalculator:
    """Calculates costs for AI operations."""
    
    # Token costs per 1M tokens (input/output)
    PRICING = {
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }
    
    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage."""
        pricing = cls.PRICING.get(model.lower())
        if not pricing:
            return 0.0
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)


class OperationManager:
    """Manages and tracks all system operations.
    
    AI_CONTEXT:
        This is a singleton that tracks all operations across the system.
        It provides real-time status updates and historical data for the dashboard.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the operation manager."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.operations: Dict[str, Operation] = {}
        self.completed_operations: List[Operation] = []
        self.operation_counter = 0
        self.total_cost = 0.0
        self.cost_by_agent: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._listeners: List[Callable] = []
        
        # Load session data
        self._load_session_data()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _load_session_data(self):
        """Load session data from disk."""
        session_file = get_config_dir() / "operation_session.json"
        if session_file.exists():
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    self.total_cost = data.get("total_cost", 0.0)
                    self.cost_by_agent = data.get("cost_by_agent", {})
            except Exception as e:
                logger.warning(f"Failed to load session data: {e}")
    
    def _save_session_data(self):
        """Save session data to disk."""
        session_file = get_config_dir() / "operation_session.json"
        try:
            session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(session_file, 'w') as f:
                json.dump({
                    "total_cost": self.total_cost,
                    "cost_by_agent": self.cost_by_agent,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    def _start_cleanup_thread(self):
        """Start thread to clean up old completed operations."""
        def cleanup():
            while True:
                time.sleep(60)  # Check every minute
                with self._lock:
                    # Keep only last 100 completed operations
                    if len(self.completed_operations) > 100:
                        self.completed_operations = self.completed_operations[-100:]
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def start_operation(
        self,
        type: OperationType,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start tracking a new operation."""
        with self._lock:
            self.operation_counter += 1
            op_id = f"op_{self.operation_counter}_{int(time.time() * 1000)}"
            
            operation = Operation(
                id=op_id,
                type=type,
                name=name,
                description=description,
                status=OperationStatus.RUNNING,
                start_time=time.time(),
                metadata=metadata or {}
            )
            
            self.operations[op_id] = operation
            self._notify_listeners()
            
            logger.debug(f"Started operation {op_id}: {name}")
            return op_id
    
    def update_progress(self, operation_id: str, progress: float, message: Optional[str] = None):
        """Update operation progress."""
        with self._lock:
            if operation_id in self.operations:
                self.operations[operation_id].progress = max(0.0, min(1.0, progress))
                if message:
                    self.operations[operation_id].description = message
                self._notify_listeners()
    
    def complete_operation(
        self,
        operation_id: str,
        cost: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Mark an operation as completed."""
        with self._lock:
            if operation_id in self.operations:
                op = self.operations[operation_id]
                op.status = OperationStatus.COMPLETED
                op.end_time = time.time()
                op.duration = op.end_time - op.start_time
                op.progress = 1.0
                
                if cost is not None:
                    op.cost = cost
                    self.total_cost += cost
                    
                    # Track cost by agent
                    agent_name = op.metadata.get("agent", "unknown")
                    self.cost_by_agent[agent_name] = self.cost_by_agent.get(agent_name, 0.0) + cost
                
                if metadata:
                    op.metadata.update(metadata)
                
                # Move to completed
                self.completed_operations.append(op)
                del self.operations[operation_id]
                
                self._save_session_data()
                self._notify_listeners()
                
                logger.debug(f"Completed operation {operation_id}: {op.name} (cost: ${cost or 0:.4f})")
    
    def fail_operation(self, operation_id: str, error: str):
        """Mark an operation as failed."""
        with self._lock:
            if operation_id in self.operations:
                op = self.operations[operation_id]
                op.status = OperationStatus.FAILED
                op.end_time = time.time()
                op.duration = op.end_time - op.start_time
                op.error = error
                
                # Move to completed
                self.completed_operations.append(op)
                del self.operations[operation_id]
                
                self._notify_listeners()
                
                logger.error(f"Failed operation {operation_id}: {op.name} - {error}")
    
    def get_active_operations(self) -> List[Operation]:
        """Get all active operations."""
        with self._lock:
            return list(self.operations.values())
    
    def get_recent_operations(self, limit: int = 20) -> List[Operation]:
        """Get recent completed operations."""
        with self._lock:
            return self.completed_operations[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get operation statistics."""
        with self._lock:
            active_count = len(self.operations)
            completed_count = len(self.completed_operations)
            
            # Calculate average duration
            durations = [op.duration for op in self.completed_operations if op.duration]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Count by type
            type_counts = {}
            for op in self.completed_operations:
                type_counts[op.type.value] = type_counts.get(op.type.value, 0) + 1
            
            return {
                "active_count": active_count,
                "completed_count": completed_count,
                "total_cost": self.total_cost,
                "cost_by_agent": self.cost_by_agent,
                "average_duration": avg_duration,
                "operations_by_type": type_counts
            }
    
    def track_ai_operation(
        self,
        agent: str,
        task: str,
        model: Optional[str] = None
    ) -> str:
        """Convenience method to track AI agent operations."""
        return self.start_operation(
            type=OperationType.AI_AGENT,
            name=f"{agent}: {task}",
            description=f"{agent} is {task}",
            metadata={
                "agent": agent,
                "model": model,
                "task": task
            }
        )
    
    def complete_ai_operation(
        self,
        operation_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str
    ):
        """Complete an AI operation with token usage."""
        cost = CostCalculator.calculate_cost(model, input_tokens, output_tokens)
        self.complete_operation(
            operation_id,
            cost=cost,
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        )
    
    def track_system_process(self, process: str, command: str) -> str:
        """Track a system process execution."""
        return self.start_operation(
            type=OperationType.SYSTEM_PROCESS,
            name=process,
            description=f"Running: {command}",
            metadata={
                "process": process,
                "command": command
            }
        )
    
    def add_listener(self, callback: Callable):
        """Add a listener for operation updates."""
        with self._lock:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """Remove a listener."""
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
    
    def _notify_listeners(self):
        """Notify all listeners of changes."""
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")
    
    def reset_session(self):
        """Reset session costs and statistics."""
        with self._lock:
            self.total_cost = 0.0
            self.cost_by_agent = {}
            self.completed_operations = []
            self._save_session_data()
            self._notify_listeners()


# Global instance
_operation_manager = None


def get_operation_manager() -> OperationManager:
    """Get the global operation manager instance."""
    global _operation_manager
    if _operation_manager is None:
        _operation_manager = OperationManager()
    return _operation_manager