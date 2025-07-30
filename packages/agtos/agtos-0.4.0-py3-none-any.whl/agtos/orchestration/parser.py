"""Workflow definition parser for multi-agent orchestration.

AI_CONTEXT:
    This module parses workflow definitions from YAML files.
    It supports various workflow formats:
    - Explicit agent assignment
    - Capability-based routing
    - Hybrid approaches with preferences
    
    The parser enables users to define complex multi-agent
    workflows in a simple, readable format.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Union

from .engine import WorkflowDefinition, WorkflowStep

logger = logging.getLogger(__name__)


class WorkflowParser:
    """Parses workflow definitions from YAML format.
    
    AI_CONTEXT:
        The parser supports flexible workflow definitions that align
        with the vision documents. Users can specify:
        - Exact agents: agent: claude
        - Capabilities: capability: reasoning
        - Preferences: prefer: claude, fallback: [codex, cursor]
        - Requirements: require: codewhisperer (for AWS tasks)
    """
    
    def parse_file(self, file_path: Union[str, Path]) -> WorkflowDefinition:
        """Parse workflow from YAML file.
        
        Args:
            file_path: Path to YAML workflow file
            
        Returns:
            Parsed workflow definition
            
        Raises:
            ValueError: If workflow format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        with open(file_path) as f:
            data = yaml.safe_load(f)
        
        return self.parse_dict(data)
    
    def parse_dict(self, data: Dict[str, Any]) -> WorkflowDefinition:
        """Parse workflow from dictionary.
        
        Args:
            data: Workflow data as dictionary
            
        Returns:
            Parsed workflow definition
        """
        # Validate required fields
        if "name" not in data:
            raise ValueError("Workflow must have a 'name' field")
        if "steps" not in data:
            raise ValueError("Workflow must have 'steps' field")
        
        # Parse steps
        steps = []
        for i, step_data in enumerate(data["steps"]):
            step = self._parse_step(step_data, i)
            steps.append(step)
        
        # Create workflow definition
        return WorkflowDefinition(
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            parameters=data.get("parameters", {}),
            metadata=data.get("metadata", {})
        )
    
    def _parse_step(self, step_data: Dict[str, Any], index: int) -> WorkflowStep:
        """Parse a single workflow step.
        
        Args:
            step_data: Step data dictionary
            index: Step index (for default naming)
            
        Returns:
            Parsed workflow step
        """
        # Handle different step formats
        if isinstance(step_data, str):
            # Simple format: just a prompt
            return WorkflowStep(
                name=f"step_{index + 1}",
                prompt=step_data
            )
        
        # Full format with all options
        name = step_data.get("name", f"step_{index + 1}")
        
        # Prompt is required
        if "prompt" not in step_data:
            raise ValueError(f"Step '{name}' must have a 'prompt' field")
        
        return WorkflowStep(
            name=name,
            prompt=step_data["prompt"],
            agent=step_data.get("agent"),
            capability=step_data.get("capability"),
            prefer=step_data.get("prefer"),
            require=step_data.get("require"),
            fallback=step_data.get("fallback", []),
            parallel=step_data.get("parallel", False),
            condition=step_data.get("condition"),
            timeout=step_data.get("timeout"),
            metadata=step_data.get("metadata", {})
        )
    
    def parse_yaml_string(self, yaml_content: str) -> WorkflowDefinition:
        """Parse workflow from YAML string.
        
        Args:
            yaml_content: YAML content as string
            
        Returns:
            Parsed workflow definition
        """
        data = yaml.safe_load(yaml_content)
        return self.parse_dict(data)


def create_example_workflows() -> Dict[str, str]:
    """Create example workflow YAML strings.
    
    Returns:
        Dictionary of example workflows
    """
    examples = {}
    
    # Add each example workflow
    examples["explicit_agents"] = _create_explicit_agents_example()
    examples["capability_based"] = _create_capability_based_example()
    examples["hybrid_fallbacks"] = _create_hybrid_fallbacks_example()
    examples["cost_optimized"] = _create_cost_optimized_example()
    examples["parallel_execution"] = _create_parallel_execution_example()
    
    return examples


def _create_explicit_agents_example() -> str:
    """Create example showing explicit agent selection."""
    return """
name: refactor-codebase
description: Comprehensive refactoring with explicit agent selection
steps:
  - name: analyze
    agent: claude
    prompt: "Analyze this legacy code and suggest refactoring strategies"
  
  - name: implement
    agent: cursor
    prompt: "Implement the refactoring across all files"
    
  - name: test
    agent: codex
    prompt: "Write comprehensive tests for the refactored code"
    
  - name: review
    agent: claude
    prompt: "Review all changes and test coverage"
"""


def _create_capability_based_example() -> str:
    """Create example showing capability-based routing."""
    return """
name: debug-production-issue
description: Debug using best agents for each capability
steps:
  - name: analyze_logs
    capability: reasoning
    prompt: "Analyze these production logs and identify the root cause"
  
  - name: find_code
    capability: code-analysis
    prompt: "Find the problematic code based on the analysis"
    
  - name: implement_fix
    capability: code-generation
    prefer: codex
    prompt: "Implement a fix for the identified issue"
    
  - name: test_fix
    capability: testing
    prompt: "Write tests to verify the fix works"
"""


def _create_hybrid_fallbacks_example() -> str:
    """Create example showing hybrid approach with fallbacks."""
    return """
name: aws-deployment
description: Deploy to AWS with specialized agents
steps:
  - name: design_architecture
    capability: architecture
    prefer: claude
    fallback: [gemini, gpt4]
    prompt: "Design the AWS architecture for this application"
    
  - name: implement_infrastructure
    capability: aws-code
    require: codewhisperer  # Must use AWS specialist
    prompt: "Implement the infrastructure as code"
    
  - name: create_scripts
    capability: scripting
    fallback: [codex, claude, cursor]
    prompt: "Create deployment and monitoring scripts"
    
  - name: security_review
    capability: security-analysis
    prompt: "Review the deployment for security best practices"
"""


def _create_cost_optimized_example() -> str:
    """Create example showing cost-optimized workflow."""
    return """
name: cost-optimized-development
description: Prefer free local models when possible
metadata:
  optimization: cost
steps:
  - name: initial_design
    capability: reasoning
    fallback: [local/llama3, local/mistral, claude]
    prompt: "Design the feature architecture"
    
  - name: implement_code
    capability: code-generation
    fallback: [local/codellama, codex]
    prompt: "Implement the designed feature"
    
  - name: run_tests
    agent: local/pytest  # Always use local tool
    prompt: "Run the test suite"
    
  - name: final_review
    capability: code-review
    require_quality: high  # May force cloud agent
    prompt: "Perform thorough code review"
"""


def _create_parallel_execution_example() -> str:
    """Create example showing parallel task execution."""
    return """
name: multi-task-processing
description: Execute multiple tasks in parallel
steps:
  - name: analyze_requirements
    agent: claude
    prompt: "Analyze the feature requirements"
    
  - name: frontend_implementation
    agent: cursor
    prompt: "Implement the frontend components"
    parallel: true  # Run next step in parallel
    
  - name: backend_implementation
    agent: codex
    prompt: "Implement the backend API"
    
  - name: integration
    agent: claude
    prompt: "Review and integrate frontend and backend"
    condition: "frontend_implementation.success and backend_implementation.success"
"""