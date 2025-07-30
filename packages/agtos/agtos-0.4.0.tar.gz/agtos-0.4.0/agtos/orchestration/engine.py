"""Core orchestration engine for multi-agent workflows.

AI_CONTEXT:
    This module implements the main orchestration engine that executes
    multi-agent workflows. It coordinates between:
    - Agent Registry (manages available agents)
    - Meta-MCP Server (provides tools to agents)
    - Workflow definitions (what to execute)
    - Context management (sharing data between steps)
    
    The engine is the heart of agtOS's multi-agent capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from ..agents import AgentRegistry, AgentCapability, BaseAgent
from ..agents.base import ExecutionResult
from .context import WorkflowContext
from .router import AgentRouter

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Definition of a single workflow step."""
    name: str
    prompt: str
    agent: Optional[str] = None  # Explicit agent name
    capability: Optional[str] = None  # Required capability
    prefer: Optional[str] = None  # Preferred agent
    require: Optional[str] = None  # Required agent (must use)
    fallback: Optional[List[str]] = None  # Fallback agents
    parallel: bool = False  # Execute in parallel with next step
    condition: Optional[str] = None  # Conditional execution
    timeout: Optional[float] = None  # Step timeout in seconds
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StepResult:
    """Result from executing a workflow step."""
    step_name: str
    success: bool
    agent_used: str
    content: Any
    duration: float
    cost: float = 0.0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    name: str
    description: str
    steps: List[WorkflowStep]
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class OrchestrationEngine:
    """Multi-agent workflow orchestration engine.
    
    AI_CONTEXT:
        This engine executes workflows by:
        1. Parsing workflow definitions
        2. Selecting appropriate agents for each step
        3. Managing context between steps
        4. Handling failures and retries
        5. Tracking execution metrics
        
        It's designed to be flexible - workflows can specify exact agents,
        required capabilities, or let the engine choose intelligently.
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        meta_mcp_endpoint: Optional[str] = None
    ):
        """Initialize the orchestration engine.
        
        Args:
            agent_registry: Registry of available agents
            meta_mcp_endpoint: Meta-MCP server endpoint for tool access
        """
        self.registry = agent_registry
        self.router = AgentRouter(agent_registry)
        self.meta_mcp_endpoint = meta_mcp_endpoint or "http://localhost:8585"
        self.active_workflows: Dict[str, WorkflowContext] = {}
        
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> List[StepResult]:
        """Execute a complete workflow.
        
        Args:
            workflow: Workflow definition to execute
            initial_context: Initial context data
            
        Returns:
            List of step results
        """
        # Initialize context and register workflow
        context, workflow_id = self._initialize_workflow_context(
            workflow, initial_context
        )
        
        try:
            logger.info(f"Starting workflow execution: {workflow.name}")
            
            # Execute all workflow steps
            results = await self._execute_workflow_steps(workflow, context)
            
            logger.info(f"Workflow completed: {workflow.name}")
            return results
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
        finally:
            # Cleanup
            del self.active_workflows[workflow_id]
    
    def _initialize_workflow_context(
        self,
        workflow: WorkflowDefinition,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[WorkflowContext, str]:
        """Initialize workflow context and return context with workflow ID.
        
        AI_CONTEXT:
            Creates workflow context, applies initial data and parameters,
            and generates unique workflow ID for tracking.
        """
        # Create workflow context
        context = WorkflowContext(workflow.name)
        if initial_context:
            context.update(initial_context)
        
        # Set workflow parameters if present
        if workflow.parameters:
            context.set_parameters(workflow.parameters)
        
        # Store active workflow
        workflow_id = f"{workflow.name}-{datetime.now().isoformat()}"
        self.active_workflows[workflow_id] = context
        
        return context, workflow_id
    
    async def _execute_workflow_steps(
        self,
        workflow: WorkflowDefinition,
        context: WorkflowContext
    ) -> List[StepResult]:
        """Execute all workflow steps in sequence.
        
        AI_CONTEXT:
            Iterates through steps, handling conditions, execution,
            context updates, failure handling, and parallel execution.
        """
        results = []
        parallel_tasks = []
        
        for i, step in enumerate(workflow.steps):
            # Process the step
            should_continue = await self._process_workflow_step(
                step, context, results
            )
            
            if not should_continue:
                break
            
            # Handle parallel execution if needed
            parallel_task = self._check_parallel_execution(
                i, workflow.steps, step, context
            )
            if parallel_task:
                parallel_tasks.append(parallel_task)
        
        # Wait for any parallel tasks to complete
        if parallel_tasks:
            await asyncio.gather(*parallel_tasks)
        
        return results
    
    async def _process_workflow_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        results: List[StepResult]
    ) -> bool:
        """Process a single workflow step.
        
        AI_CONTEXT:
            Evaluates conditions, executes step, updates context,
            and returns whether to continue workflow execution.
        """
        # Check if step should be skipped (condition)
        if step.condition and not self._evaluate_condition(step.condition, context):
            logger.info(f"Skipping step {step.name} due to condition")
            return True  # Continue to next step
        
        # Execute step
        result = await self._execute_step(step, context)
        results.append(result)
        
        # Update context with result
        context.add_step_result(step.name, result)
        
        # Check if we should stop on failure
        if not result.success and not (step.metadata and step.metadata.get("continue_on_failure")):
            logger.error(f"Workflow failed at step: {step.name}")
            return False  # Stop workflow execution
        
        return True  # Continue to next step
    
    def _check_parallel_execution(
        self,
        current_index: int,
        workflow_steps: List[WorkflowStep],
        current_step: WorkflowStep,
        context: WorkflowContext
    ) -> Optional[asyncio.Task]:
        """Check if next step should be executed in parallel.
        
        AI_CONTEXT:
            Determines if current step is marked for parallel execution
            and creates async task for next step if applicable.
        """
        if current_step.parallel and current_index < len(workflow_steps) - 1:
            # Execute next step in parallel
            next_step = workflow_steps[current_index + 1]
            parallel_task = asyncio.create_task(
                self._execute_step(next_step, context)
            )
            return parallel_task
        
        return None
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> StepResult:
        """Execute a single workflow step.
        
        AI_CONTEXT:
            Orchestrates step execution by selecting agent, preparing prompt,
            executing task, and handling errors. Delegates to specialized
            methods for each responsibility.
        """
        start_time = datetime.now()
        
        try:
            # Select and validate agent
            agent = await self._select_and_validate_agent(step, context)
            
            # Execute the step with the selected agent
            result = await self._execute_with_agent(
                agent, step, context, start_time
            )
            
            return result
            
        except asyncio.TimeoutError:
            return self._create_timeout_result(step, start_time)
        except Exception as e:
            return self._create_error_result(step, e, start_time)
    
    async def _select_and_validate_agent(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> BaseAgent:
        """Select and validate agent for step execution.
        
        Raises:
            RuntimeError: If no suitable agent is found
        """
        agent = await self._select_agent(step, context)
        if not agent:
            raise RuntimeError(f"No suitable agent found for step: {step.name}")
        
        logger.info(f"Executing step '{step.name}' with agent: {agent.name}")
        return agent
    
    async def _execute_with_agent(
        self,
        agent: BaseAgent,
        step: WorkflowStep,
        context: WorkflowContext,
        start_time: datetime
    ) -> StepResult:
        """Execute step with selected agent.
        
        Handles prompt enrichment, timeout, and result creation.
        """
        # Prepare prompt with context
        enriched_prompt = self._enrich_prompt(step.prompt, context)
        
        # Execute with or without timeout
        if step.timeout:
            result = await self._execute_with_timeout(
                agent, enriched_prompt, context, step.timeout
            )
        else:
            result = await agent.execute(enriched_prompt, context.to_dict())
        
        # Create and return step result
        return self._create_success_result(
            step, agent, result, start_time
        )
    
    async def _execute_with_timeout(
        self,
        agent: BaseAgent,
        prompt: str,
        context: WorkflowContext,
        timeout: float
    ) -> ExecutionResult:
        """Execute agent task with timeout."""
        execution_task = agent.execute(prompt, context.to_dict())
        return await asyncio.wait_for(execution_task, timeout=timeout)
    
    def _create_success_result(
        self,
        step: WorkflowStep,
        agent: BaseAgent,
        result: ExecutionResult,
        start_time: datetime
    ) -> StepResult:
        """Create successful step result."""
        duration = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step_name=step.name,
            success=result.success,
            agent_used=agent.name,
            content=result.content,
            duration=duration,
            cost=result.cost,
            error=result.error,
            metadata={
                "agent_metadata": result.metadata,
                "step_metadata": step.metadata
            }
        )
    
    def _create_timeout_result(
        self,
        step: WorkflowStep,
        start_time: datetime
    ) -> StepResult:
        """Create timeout error result."""
        duration = (datetime.now() - start_time).total_seconds()
        
        return StepResult(
            step_name=step.name,
            success=False,
            agent_used="none",
            content=None,
            duration=duration,
            error=f"Step timed out after {step.timeout} seconds"
        )
    
    def _create_error_result(
        self,
        step: WorkflowStep,
        error: Exception,
        start_time: datetime
    ) -> StepResult:
        """Create general error result."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Step execution failed: {error}")
        
        return StepResult(
            step_name=step.name,
            success=False,
            agent_used="none",
            content=None,
            duration=duration,
            error=str(error)
        )
    
    async def _select_agent(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> Optional[BaseAgent]:
        """Select the best agent for a workflow step.
        
        AI_CONTEXT:
            Selection follows a priority order: required > explicit > 
            capability-based > default. Each selection type is delegated
            to a specialized method.
        """
        # Try each selection strategy in priority order
        agent = await self._select_required_agent(step)
        if agent:
            return agent
        
        agent = await self._select_explicit_agent(step)
        if agent:
            return agent
        
        agent = await self._select_by_capability(step, context)
        if agent:
            return agent
        
        return self._select_default_agent()
    
    async def _select_required_agent(
        self,
        step: WorkflowStep
    ) -> Optional[BaseAgent]:
        """Select required agent if specified.
        
        Raises:
            ValueError: If required agent is not found
        """
        if not step.require:
            return None
        
        agent = self.registry.get_agent(step.require)
        if not agent:
            raise ValueError(f"Required agent not found: {step.require}")
        return agent
    
    async def _select_explicit_agent(
        self,
        step: WorkflowStep
    ) -> Optional[BaseAgent]:
        """Select explicitly named agent if available."""
        if not step.agent:
            return None
        
        return self.registry.get_agent(step.agent)
    
    async def _select_by_capability(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> Optional[BaseAgent]:
        """Select agent based on required capability."""
        if not step.capability:
            return None
        
        capability = self._parse_capability(step.capability)
        if not capability:
            return None
        
        # Build selection context for router
        selection_context = self._build_selection_context(step, context)
        
        # Use router for intelligent selection
        return self.router.select_agent(
            capability=capability,
            context=selection_context
        )
    
    def _parse_capability(
        self,
        capability_str: str
    ) -> Optional[AgentCapability]:
        """Parse capability string to enum."""
        try:
            return AgentCapability(capability_str)
        except ValueError:
            logger.warning(f"Unknown capability: {capability_str}")
            return None
    
    def _build_selection_context(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """Build context for agent selection."""
        return {
            "prefer": step.prefer,
            "fallback": step.fallback,
            "workflow_context": context.to_dict()
        }
    
    def _select_default_agent(self) -> Optional[BaseAgent]:
        """Select first available agent as fallback."""
        available = self.registry.get_available_agents()
        return available[0] if available else None
    
    def _enrich_prompt(self, prompt: str, context: WorkflowContext) -> str:
        """Enrich prompt with context information and parameter substitution.
        
        Adds relevant context from previous steps to help agents
        understand the full workflow state and substitutes parameters.
        """
        # First, perform parameter substitution
        enriched = prompt
        
        # Substitute from context data (includes initial_context)
        for key, value in context._data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in enriched:
                enriched = enriched.replace(placeholder, str(value))
        
        # Substitute from workflow parameters
        for key, value in context._parameters.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in enriched:
                enriched = enriched.replace(placeholder, str(value))
        
        # Get recent results summary
        recent_results = context.get_recent_results(n=3)
        
        if recent_results:
            # Build context section
            context_parts = ["Previous steps:"]
            for result in recent_results:
                if result.success:
                    context_parts.append(
                        f"- {result.step_name} ({result.agent_used}): Completed successfully"
                    )
                else:
                    context_parts.append(
                        f"- {result.step_name} ({result.agent_used}): Failed - {result.error}"
                    )
            
            # Add context to prompt
            enriched = f"{enriched}\n\nContext:\n" + "\n".join(context_parts)
        
        return enriched
    
    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate a step condition.
        
        Simple condition evaluation - can be enhanced with more
        complex logic as needed.
        """
        # For now, support simple comparisons
        # Example: "last_step.success == true"
        try:
            # This is a simplified implementation
            # In production, use a proper expression evaluator
            if "last_step.success" in condition:
                last_result = context.get_last_result()
                if last_result:
                    return "true" in condition and last_result.success
            
            # Default to true if we can't evaluate
            return True
            
        except Exception as e:
            logger.warning(f"Failed to evaluate condition: {e}")
            return True
    
    async def execute_workflow_file(
        self,
        workflow_path: Union[str, Path],
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[StepResult]:
        """Execute a workflow from a YAML file.
        
        Args:
            workflow_path: Path to workflow YAML file
            parameters: Parameters to pass to workflow
            
        Returns:
            List of step results
        """
        from .parser import WorkflowParser
        
        parser = WorkflowParser()
        workflow = parser.parse_file(workflow_path)
        
        # Apply parameters
        if parameters:
            workflow.parameters = parameters
        
        return await self.execute_workflow(workflow)
    
    def get_active_workflows(self) -> Dict[str, WorkflowContext]:
        """Get currently active workflows."""
        return self.active_workflows.copy()
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow.
        
        Args:
            workflow_id: ID of workflow to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        if workflow_id in self.active_workflows:
            # In a full implementation, this would:
            # - Cancel running agent tasks
            # - Clean up resources
            # - Notify agents of cancellation
            del self.active_workflows[workflow_id]
            logger.info(f"Cancelled workflow: {workflow_id}")
            return True
        return False