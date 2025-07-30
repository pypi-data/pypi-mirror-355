"""Workflow recording system for agtos.

This module provides secure recording of tool executions into replayable workflows.
All sensitive data is automatically redacted before saving.

AI_CONTEXT: This is the core workflow recording system. It hooks into tool
executions, records parameters and results, and saves them as YAML workflows.
Security is paramount - all credentials and sensitive data are automatically
detected and redacted. Users must review workflows before saving.
"""
import re
import json
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

from ..config import get_config_dir
from ..utils import get_logger
from .integration import get_integration, track_workflow_save

logger = get_logger(__name__)


class SensitiveDataType(Enum):
    """Types of sensitive data to redact."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    SECRET = "secret"
    CREDENTIAL = "credential"
    PRIVATE_KEY = "private_key"
    CONNECTION_STRING = "connection_string"
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"


@dataclass
class ToolExecution:
    """Record of a single tool execution.
    
    AI_CONTEXT: Captures all details of a tool execution including timing,
    parameters, results, and any errors. Used to build replayable workflows.
    """
    tool_name: str
    tool_type: str  # 'cli', 'rest', 'plugin', 'mcp'
    timestamp: float
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """A recorded workflow of tool executions.
    
    AI_CONTEXT: Represents a complete workflow with metadata and a sequence
    of tool executions. Can be serialized to YAML for persistence.
    """
    name: str
    description: str
    created_at: datetime
    executions: List[ToolExecution] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)  # Workflow-level params
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"


class SecurityRedactor:
    """Handles redaction of sensitive data from workflows.
    
    AI_CONTEXT: This class is critical for security. It uses multiple strategies
    to detect and redact sensitive information including pattern matching,
    key name analysis, and value heuristics. Always err on the side of caution.
    """
    
    # Patterns for detecting sensitive data
    PATTERNS = {
        SensitiveDataType.API_KEY: [
            r'[a-zA-Z0-9]{32,}',  # Long alphanumeric strings
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI style
            r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',  # UUIDs
        ],
        SensitiveDataType.EMAIL: [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ],
        SensitiveDataType.PHONE: [
            r'\+?1?\d{10,14}',
            r'\(\d{3}\)\s*\d{3}-\d{4}'
        ],
        SensitiveDataType.CREDIT_CARD: [
            r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}'
        ],
        SensitiveDataType.SSN: [
            r'\d{3}-\d{2}-\d{4}'
        ]
    }
    
    # Key names that likely contain sensitive data
    SENSITIVE_KEY_PATTERNS = [
        r'.*password.*',
        r'.*secret.*',
        r'.*key.*',
        r'.*token.*',
        r'.*credential.*',
        r'.*auth.*',
        r'.*private.*',
        r'.*connection.*string.*',
        r'.*conn.*str.*',
    ]
    
    def __init__(self):
        """Initialize the security redactor."""
        self.compiled_patterns = {}
        for data_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[data_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        self.sensitive_key_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.SENSITIVE_KEY_PATTERNS
        ]
    
    def redact(self, data: Any, path: str = "") -> Any:
        """Recursively redact sensitive data.
        
        Args:
            data: Data to redact (can be dict, list, or primitive)
            path: Current path in the data structure (for key analysis)
            
        Returns:
            Redacted copy of the data
            
        AI_CONTEXT: This method recursively walks through data structures,
        checking both keys and values for sensitive information. The path
        parameter helps identify sensitive keys like 'api_key' or 'password'.
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if self._is_sensitive_key(key):
                    result[key] = "[REDACTED]"
                else:
                    result[key] = self.redact(value, new_path)
            return result
            
        elif isinstance(data, list):
            return [self.redact(item, f"{path}[{i}]") for i, item in enumerate(data)]
            
        elif isinstance(data, str):
            return self._redact_string(data, path)
            
        else:
            return data
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name suggests sensitive data."""
        key_lower = key.lower()
        return any(pattern.match(key_lower) for pattern in self.sensitive_key_patterns)
    
    def _redact_string(self, value: str, path: str) -> str:
        """Redact sensitive patterns from a string."""
        # Skip if already redacted
        if value == "[REDACTED]":
            return value
            
        # Check against all patterns
        for data_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(value):
                    # For partial redaction, show some context
                    if data_type == SensitiveDataType.EMAIL:
                        # Show domain for emails
                        match = pattern.search(value)
                        if match:
                            email = match.group()
                            domain = email.split('@')[1] if '@' in email else ''
                            return value.replace(email, f"[REDACTED_EMAIL@{domain}]")
                    else:
                        # Full redaction for other types
                        return "[REDACTED]"
        
        return value
    
    def get_redacted_summary(self, workflow: Workflow) -> Dict[str, Any]:
        """Generate a summary of what was redacted.
        
        AI_CONTEXT: Provides transparency about what was redacted so users
        can verify the workflow is still useful while being secure.
        """
        summary = {
            "total_redactions": 0,
            "redacted_fields": [],
            "redaction_types": {}
        }
        
        # Count redactions in workflow
        for execution in workflow.executions:
            redacted_params = self.redact(execution.parameters)
            summary["total_redactions"] += self._count_redactions(
                execution.parameters, redacted_params
            )
        
        return summary
    
    def _count_redactions(self, original: Any, redacted: Any, path: str = "") -> int:
        """Count number of redactions between original and redacted data."""
        if isinstance(original, dict) and isinstance(redacted, dict):
            count = 0
            for key in original:
                new_path = f"{path}.{key}" if path else key
                if key in redacted:
                    if redacted[key] == "[REDACTED]" and original[key] != "[REDACTED]":
                        count += 1
                    else:
                        count += self._count_redactions(
                            original[key], redacted[key], new_path
                        )
            return count
        elif isinstance(original, list) and isinstance(redacted, list):
            return sum(
                self._count_redactions(o, r, f"{path}[{i}]")
                for i, (o, r) in enumerate(zip(original, redacted))
            )
        else:
            return 1 if redacted == "[REDACTED]" and original != "[REDACTED]" else 0


class WorkflowRecorder:
    """Records tool executions into replayable workflows.
    
    AI_CONTEXT: Main interface for workflow recording. Maintains recording state,
    captures tool executions, and saves workflows with security redaction.
    Integrates with the Meta-MCP server to intercept tool calls.
    """
    
    def __init__(self, workflow_dir: Optional[Path] = None):
        """Initialize workflow recorder.
        
        Args:
            workflow_dir: Directory to store workflows (default: ~/.agtos/workflows)
        """
        self.workflow_dir = workflow_dir or (get_config_dir() / "workflows")
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        
        self.redactor = SecurityRedactor()
        self.current_workflow: Optional[Workflow] = None
        self.recording = False
        self._execution_stack: List[float] = []  # For tracking nested executions
    
    def start_recording(self, name: str, description: str = "") -> None:
        """Start recording a new workflow.
        
        Args:
            name: Name for the workflow
            description: Human-readable description
            
        AI_CONTEXT: Creates a new workflow and sets recording flag. All subsequent
        tool executions will be captured until stop_recording is called.
        """
        if self.recording:
            raise RuntimeError("Already recording a workflow")
        
        self.current_workflow = Workflow(
            name=name,
            description=description,
            created_at=datetime.now()
        )
        self.recording = True
        logger.info(f"Started recording workflow: {name}")
    
    def stop_recording(self, save: bool = True, review: bool = True) -> Optional[Path]:
        """Stop recording and optionally save the workflow.
        
        Args:
            save: Whether to save the workflow
            review: Whether to show review before saving
            
        Returns:
            Path to saved workflow file if saved, None otherwise
            
        AI_CONTEXT: Stops recording, optionally shows a security review of what
        will be saved, and saves the workflow as YAML. Review is critical for
        security - users must see what data will be persisted.
        """
        if not self.recording:
            raise RuntimeError("Not currently recording")
        
        self.recording = False
        workflow = self.current_workflow
        self.current_workflow = None
        
        if not workflow or not workflow.executions:
            logger.warning("No executions recorded")
            return None
        
        # Redact sensitive data
        workflow = self._redact_workflow(workflow)
        
        if review:
            if not self._review_workflow(workflow):
                logger.info("Workflow review cancelled")
                return None
        
        if save:
            return self._save_workflow(workflow)
        
        return None
    
    def record_execution(self, tool_name: str, tool_type: str, 
                        parameters: Dict[str, Any]) -> str:
        """Record the start of a tool execution.
        
        Args:
            tool_name: Name of the tool being executed
            tool_type: Type of tool (cli, rest, plugin, mcp)
            parameters: Parameters passed to the tool
            
        Returns:
            Execution ID for tracking
            
        AI_CONTEXT: Called before tool execution. Returns an ID that must be
        passed to record_result to complete the execution record.
        """
        if not self.recording or not self.current_workflow:
            return ""
        
        execution = ToolExecution(
            tool_name=tool_name,
            tool_type=tool_type,
            timestamp=time.time(),
            parameters=parameters.copy()  # Copy to avoid mutations
        )
        
        self.current_workflow.executions.append(execution)
        self._execution_stack.append(execution.timestamp)
        
        # Track tool usage in real-time during recording
        integration = get_integration()
        integration.track_tool_execution(
            tool_name=tool_name,
            tool_type=tool_type,
            parameters=parameters,
            result=None  # Will be updated in record_result
        )
        
        return str(execution.timestamp)
    
    def record_result(self, execution_id: str, result: Any = None, 
                     error: Optional[str] = None) -> None:
        """Record the result of a tool execution.
        
        Args:
            execution_id: ID from record_execution
            result: Result of the execution
            error: Error message if execution failed
            
        AI_CONTEXT: Completes an execution record with results or error.
        Calculates execution duration and stores all relevant data.
        """
        if not self.recording or not self.current_workflow:
            return
        
        try:
            timestamp = float(execution_id)
        except ValueError:
            logger.error(f"Invalid execution ID: {execution_id}")
            return
        
        # Find the execution
        for execution in reversed(self.current_workflow.executions):
            if execution.timestamp == timestamp:
                execution.duration = time.time() - timestamp
                execution.result = result
                execution.error = error
                
                # Remove from stack
                if timestamp in self._execution_stack:
                    self._execution_stack.remove(timestamp)
                break
    
    def _redact_workflow(self, workflow: Workflow) -> Workflow:
        """Redact sensitive data from workflow."""
        # Create a deep copy to avoid modifying original
        import copy
        redacted = copy.deepcopy(workflow)
        
        # Redact each execution
        for execution in redacted.executions:
            execution.parameters = self.redactor.redact(execution.parameters)
            if execution.result:
                execution.result = self.redactor.redact(execution.result)
        
        # Redact workflow-level parameters
        redacted.parameters = self.redactor.redact(redacted.parameters)
        
        return redacted
    
    def _review_workflow(self, workflow: Workflow) -> bool:
        """Show workflow review and get user confirmation.
        
        AI_CONTEXT: Shows the user exactly what will be saved, highlighting
        any redactions. User must confirm to proceed with saving.
        """
        import typer
        
        typer.echo("\n📋 Workflow Review")
        typer.echo("=" * 50)
        typer.echo(f"Name: {workflow.name}")
        typer.echo(f"Description: {workflow.description}")
        typer.echo(f"Steps: {len(workflow.executions)}")
        
        # Show redaction summary
        summary = self.redactor.get_redacted_summary(workflow)
        if summary["total_redactions"] > 0:
            typer.echo(f"\n🔐 Security: {summary['total_redactions']} sensitive values redacted")
        
        # Show execution summary
        typer.echo("\n📝 Execution Summary:")
        for i, execution in enumerate(workflow.executions, 1):
            typer.echo(f"\n{i}. {execution.tool_name} ({execution.tool_type})")
            
            # Show parameters (already redacted)
            if execution.parameters:
                typer.echo("   Parameters:")
                for key, value in execution.parameters.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."
                    typer.echo(f"     {key}: {value_str}")
            
            if execution.error:
                typer.echo(f"   ❌ Error: {execution.error}")
            elif execution.duration:
                typer.echo(f"   ✅ Duration: {execution.duration:.2f}s")
        
        typer.echo("\n" + "=" * 50)
        return typer.confirm("Save this workflow?", default=True)
    
    @track_workflow_save
    def _save_workflow(self, workflow: Workflow) -> Path:
        """Save workflow to YAML file."""
        # Generate filename
        safe_name = re.sub(r'[^\w\s-]', '', workflow.name.lower())
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        timestamp = workflow.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.yml"
        
        filepath = self.workflow_dir / filename
        
        # Convert to dict for YAML serialization
        workflow_dict = {
            "version": workflow.version,
            "name": workflow.name,
            "description": workflow.description,
            "created_at": workflow.created_at.isoformat(),
            "parameters": workflow.parameters,
            "metadata": workflow.metadata,
            "executions": [
                {
                    "tool_name": e.tool_name,
                    "tool_type": e.tool_type,
                    "parameters": e.parameters,
                    "result": e.result,
                    "error": e.error,
                    "duration": e.duration,
                    "metadata": e.metadata
                }
                for e in workflow.executions
            ]
        }
        
        with open(filepath, 'w') as f:
            yaml.dump(workflow_dict, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Workflow saved to: {filepath}")
        return filepath
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all saved workflows.
        
        Returns:
            List of workflow summaries
            
        AI_CONTEXT: Scans the workflow directory and returns summary information
        about each workflow without loading full content.
        """
        workflows = []
        
        for filepath in self.workflow_dir.glob("*.yml"):
            try:
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
                
                workflows.append({
                    "name": data.get("name", filepath.stem),
                    "description": data.get("description", ""),
                    "created_at": data.get("created_at", ""),
                    "steps": len(data.get("executions", [])),
                    "filepath": str(filepath)
                })
            except Exception as e:
                logger.error(f"Error reading workflow {filepath}: {e}")
        
        return sorted(workflows, key=lambda w: w["created_at"], reverse=True)