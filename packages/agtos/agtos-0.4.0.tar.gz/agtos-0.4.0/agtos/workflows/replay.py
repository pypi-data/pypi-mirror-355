"""Workflow replay system for agtos.

This module handles replaying recorded workflows with parameter substitution
and interactive credential prompts for security.

AI_CONTEXT: This is the workflow replay engine. It loads YAML workflows,
handles parameter substitution, prompts for missing credentials, and executes
the workflow steps in order. Security is maintained by never storing credentials
in workflows - they are always requested at runtime.
"""
import re
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set, Union
from dataclasses import dataclass
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import get_config_dir
from ..utils import get_logger
from ..providers import get_provider
from .integration import get_integration, track_workflow_execution, track_tool_execution

logger = get_logger(__name__)
console = Console()


@dataclass
class WorkflowStep:
    """A single step in a workflow execution.
    
    AI_CONTEXT: Represents one tool execution from a workflow file.
    Parameters may contain placeholders like {{variable}} that need
    substitution before execution.
    """
    tool_name: str
    tool_type: str
    parameters: Dict[str, Any]
    original_result: Optional[Any] = None
    original_error: Optional[str] = None
    original_duration: Optional[float] = None
    metadata: Dict[str, Any] = None


class ParameterSubstitutor:
    """Handles parameter substitution in workflows.
    
    AI_CONTEXT: This class manages variable substitution in workflow parameters.
    It supports {{variable}} syntax and can pull values from multiple sources:
    environment variables, command-line args, interactive prompts, and credentials.
    """
    
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')
    
    def __init__(self, provided_params: Dict[str, Any] = None):
        """Initialize with optionally provided parameters.
        
        Args:
            provided_params: Parameters provided via command line or API
        """
        self.provided_params = provided_params or {}
        self.resolved_params: Dict[str, Any] = {}
        self.credential_provider = get_provider()
    
    def substitute(self, data: Any, interactive: bool = True) -> Any:
        """Recursively substitute variables in data.
        
        Args:
            data: Data containing {{variable}} placeholders
            interactive: Whether to prompt for missing values
            
        Returns:
            Data with all placeholders substituted
            
        AI_CONTEXT: Walks through data structures looking for {{variable}}
        patterns. When found, resolves the variable value from available
        sources, prompting interactively if needed and allowed.
        """
        if isinstance(data, dict):
            return {
                key: self.substitute(value, interactive)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.substitute(item, interactive) for item in data]
        elif isinstance(data, str):
            return self._substitute_string(data, interactive)
        else:
            return data
    
    def _substitute_string(self, value: str, interactive: bool) -> str:
        """Substitute variables in a string value."""
        def replacer(match):
            var_name = match.group(1)
            return str(self._resolve_variable(var_name, interactive))
        
        return self.VARIABLE_PATTERN.sub(replacer, value)
    
    def _resolve_variable(self, var_name: str, interactive: bool) -> Any:
        """Resolve a variable value from available sources.
        
        Resolution order:
        1. Already resolved (cached)
        2. Provided parameters
        3. Environment variables
        4. Credential store (for _KEY, _TOKEN, etc. suffixes)
        5. Interactive prompt (if enabled)
        6. Raise error
        
        AI_CONTEXT: This method implements the variable resolution chain.
        Special handling for credential-like variables (ending in _KEY, _TOKEN, etc.)
        which are fetched from the secure credential store.
        """
        # Check cache
        if var_name in self.resolved_params:
            return self.resolved_params[var_name]
        
        # Check provided parameters
        if var_name in self.provided_params:
            value = self.provided_params[var_name]
            self.resolved_params[var_name] = value
            return value
        
        # Check environment
        import os
        env_value = os.getenv(var_name)
        if env_value:
            self.resolved_params[var_name] = env_value
            return env_value
        
        # Check if it's a credential
        if self._is_credential_var(var_name):
            value = self._get_credential(var_name)
            if value:
                self.resolved_params[var_name] = value
                return value
        
        # Interactive prompt
        if interactive:
            value = self._prompt_for_value(var_name)
            self.resolved_params[var_name] = value
            return value
        
        # Give up
        raise ValueError(f"Unresolved variable: {var_name}")
    
    def _is_credential_var(self, var_name: str) -> bool:
        """Check if variable name suggests it's a credential."""
        credential_suffixes = ['_KEY', '_TOKEN', '_SECRET', '_PASSWORD', '_PASS']
        return any(var_name.upper().endswith(suffix) for suffix in credential_suffixes)
    
    def _get_credential(self, var_name: str) -> Optional[str]:
        """Get credential from secure store."""
        # Try exact match first
        value = self.credential_provider.get_secret(var_name)
        if value:
            return value
        
        # Try common mappings (e.g., GITHUB_TOKEN -> github)
        service_mappings = {
            'GITHUB_TOKEN': 'github',
            'GITHUB_API_KEY': 'github',
            'OPENAI_API_KEY': 'openai',
            'ANTHROPIC_API_KEY': 'anthropic',
            'CLOUDFLARE_API_KEY': 'cloudflare',
        }
        
        if var_name.upper() in service_mappings:
            service = service_mappings[var_name.upper()]
            return self.credential_provider.get_secret(service)
        
        return None
    
    def _prompt_for_value(self, var_name: str) -> str:
        """Interactively prompt for a variable value."""
        if self._is_credential_var(var_name):
            # Use password prompt for credentials
            return typer.prompt(
                f"Enter value for {var_name}",
                hide_input=True
            )
        else:
            # Regular prompt for non-sensitive values
            return typer.prompt(f"Enter value for {var_name}")
    
    def get_required_variables(self, data: Any) -> Set[str]:
        """Extract all variable names from data.
        
        AI_CONTEXT: Scans data structure to find all {{variable}} references.
        Useful for pre-flight checks and showing users what will be needed.
        """
        variables = set()
        
        if isinstance(data, dict):
            for value in data.values():
                variables.update(self.get_required_variables(value))
        elif isinstance(data, list):
            for item in data:
                variables.update(self.get_required_variables(item))
        elif isinstance(data, str):
            variables.update(self.VARIABLE_PATTERN.findall(data))
        
        return variables


class WorkflowPlayer:
    """Replays recorded workflows with parameter substitution.
    
    AI_CONTEXT: Main interface for workflow replay. Loads workflows from YAML,
    handles parameter substitution, and executes steps through the Meta-MCP
    system. Provides progress feedback and error handling.
    """
    
    def __init__(self, workflow_dir: Optional[Path] = None):
        """Initialize workflow player.
        
        Args:
            workflow_dir: Directory containing workflows
        """
        self.workflow_dir = workflow_dir or (get_config_dir() / "workflows")
        self.tool_registry: Dict[str, Callable] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tool executors.
        
        AI_CONTEXT: Tools are registered by type (cli, rest, plugin, mcp).
        The actual execution is delegated to the appropriate subsystem.
        For now, this is a simplified implementation that can be enhanced
        when fully integrated with Meta-MCP.
        """
        self.tool_registry = {
            "cli": self._execute_cli_tool,
            "rest": self._execute_rest_tool,
            "plugin": self._execute_plugin_tool,
            "mcp": self._execute_mcp_tool
        }
    
    @track_tool_execution("cli")
    def _execute_cli_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Execute CLI tool through the bridge."""
        logger.info(f"Executing CLI tool: {name} with params: {params}")
        
        try:
            # Parse and validate tool name
            parts = self._parse_cli_tool_name(name)
            if "error" in parts:
                return parts
            
            # Build command from parts and parameters
            cmd = self._build_cli_command(parts, params)
            
            # Execute command and return result
            return self._run_cli_command(cmd)
            
        except Exception as e:
            logger.error(f"CLI tool execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _parse_cli_tool_name(self, name: str) -> Union[List[str], Dict[str, str]]:
        """Parse CLI tool name into command parts.
        
        Args:
            name: Tool name in format cli__command__subcommand
            
        Returns:
            List of command parts or error dict
        """
        parts = name.split("__")
        if len(parts) < 2:
            return {"status": "error", "error": f"Invalid CLI tool name: {name}"}
        
        # Remove 'cli' prefix if present
        if parts[0] == "cli":
            parts = parts[1:]
        
        return parts
    
    def _build_cli_command(self, parts: List[str], params: Dict[str, Any]) -> List[str]:
        """Build CLI command from parts and parameters.
        
        Args:
            parts: Command parts
            params: Command parameters
            
        Returns:
            Complete command list
        """
        cmd = parts.copy()
        
        # Add parameters as arguments
        for key, value in params.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])
        
        return cmd
    
    def _run_cli_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute CLI command and return result.
        
        Args:
            cmd: Command list to execute
            
        Returns:
            Execution result dictionary
        """
        import subprocess
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "status": "success", 
                "result": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            }
        else:
            return {
                "status": "error",
                "error": f"Command failed with code {result.returncode}",
                "result": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            }
    
    @track_tool_execution("rest")
    def _execute_rest_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Execute REST API tool."""
        logger.info(f"Executing REST tool: {name}")
        
        try:
            # In production, this would use the actual REST bridge
            # For now, return a placeholder
            return {
                "status": "success",
                "result": {
                    "message": f"REST API {name} called",
                    "params": params
                }
            }
        except Exception as e:
            logger.error(f"REST tool execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _execute_plugin_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Execute plugin tool."""
        logger.info(f"Executing plugin: {name}")
        
        try:
            # In production, this would use the actual plugin system
            # For now, return a placeholder
            return {
                "status": "success",
                "result": {
                    "message": f"Plugin {name} executed",
                    "params": params
                }
            }
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _execute_mcp_tool(self, name: str, params: Dict[str, Any]) -> Any:
        """Execute MCP server tool."""
        logger.info(f"Executing MCP tool: {name}")
        
        # For MCP tools, we need to connect through the proxy
        # This is a simplified version - in production it would use the connection pool
        return {"status": "success", "response": f"MCP tool {name} executed"}
    
    def load_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Load workflow from YAML file.
        
        Args:
            workflow_path: Path to workflow YAML file
            
        Returns:
            Workflow data dictionary
            
        Raises:
            FileNotFoundError: If workflow file doesn't exist
            yaml.YAMLError: If workflow file is invalid
        """
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")
        
        with open(workflow_path, 'r') as f:
            workflow_data = yaml.safe_load(f)
        
        # Validate workflow structure
        required_fields = ["name", "executions"]
        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Invalid workflow: missing '{field}' field")
        
        return workflow_data
    
    def replay(self, workflow_name: str, parameters: Dict[str, Any] = None,
              interactive: bool = True, dry_run: bool = False) -> bool:
        """Replay a workflow by name.
        
        Args:
            workflow_name: Name or path of workflow to replay
            parameters: Parameters to substitute in workflow
            interactive: Whether to prompt for missing parameters
            dry_run: Show what would be executed without running
            
        Returns:
            True if workflow completed successfully
            
        AI_CONTEXT: Main entry point for workflow replay. Handles the full
        lifecycle from loading to execution with proper error handling and
        user feedback.
        """
        # Find workflow file
        workflow_path = self._find_workflow(workflow_name)
        if not workflow_path:
            console.print(f"[red]Workflow not found: {workflow_name}[/red]")
            return False
        
        try:
            # Load workflow
            workflow_data = self.load_workflow(workflow_path)
            console.print(f"\n[bold]Replaying workflow: {workflow_data['name']}[/bold]")
            
            if workflow_data.get('description'):
                console.print(f"[dim]{workflow_data['description']}[/dim]")
            
            # Parse executions
            steps = [
                WorkflowStep(
                    tool_name=exec_data['tool_name'],
                    tool_type=exec_data['tool_type'],
                    parameters=exec_data.get('parameters', {}),
                    original_result=exec_data.get('result'),
                    original_error=exec_data.get('error'),
                    original_duration=exec_data.get('duration'),
                    metadata=exec_data.get('metadata', {})
                )
                for exec_data in workflow_data['executions']
            ]
            
            # Handle parameter substitution
            substitutor = ParameterSubstitutor(parameters)
            
            # Check required variables
            all_params = {}
            for step in steps:
                all_params.update(step.parameters)
            
            required_vars = substitutor.get_required_variables(all_params)
            if required_vars:
                console.print(f"\n[yellow]This workflow requires {len(required_vars)} variable(s)[/yellow]")
                
                if not interactive and not all(var in (parameters or {}) for var in required_vars):
                    missing = required_vars - set(parameters or {})
                    console.print(f"[red]Missing required variables: {', '.join(missing)}[/red]")
                    return False
            
            # Show execution plan in dry run
            if dry_run:
                return self._show_dry_run(steps, substitutor)
            
            # Execute workflow
            return self._execute_workflow(
                steps, substitutor, interactive,
                workflow_name=workflow_data.get('name', 'unknown'),
                workflow_version=workflow_data.get('version', '1.0.0')
            )
            
        except Exception as e:
            console.print(f"[red]Error replaying workflow: {e}[/red]")
            logger.exception("Workflow replay error")
            return False
    
    def _find_workflow(self, workflow_name: str) -> Optional[Path]:
        """Find workflow file by name or path."""
        # Check if it's a direct path
        direct_path = Path(workflow_name)
        if direct_path.exists() and direct_path.suffix in ['.yml', '.yaml']:
            return direct_path
        
        # Search in workflow directory
        for ext in ['.yml', '.yaml']:
            workflow_path = self.workflow_dir / f"{workflow_name}{ext}"
            if workflow_path.exists():
                return workflow_path
        
        # Search by partial name
        candidates = list(self.workflow_dir.glob(f"*{workflow_name}*.yml"))
        candidates.extend(self.workflow_dir.glob(f"*{workflow_name}*.yaml"))
        
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            console.print(f"[yellow]Multiple workflows match '{workflow_name}':[/yellow]")
            for i, candidate in enumerate(candidates, 1):
                console.print(f"  {i}. {candidate.stem}")
            return None
        
        return None
    
    def _show_dry_run(self, steps: List[WorkflowStep], 
                     substitutor: ParameterSubstitutor) -> bool:
        """Show what would be executed in a dry run."""
        console.print("\n[bold]Dry Run - Execution Plan:[/bold]")
        
        for i, step in enumerate(steps, 1):
            console.print(f"\n[cyan]Step {i}: {step.tool_name} ({step.tool_type})[/cyan]")
            
            # Substitute parameters for display
            try:
                params = substitutor.substitute(step.parameters, interactive=False)
                if params:
                    console.print("  Parameters:")
                    for key, value in params.items():
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        console.print(f"    {key}: {value}")
            except ValueError as e:
                console.print(f"  [red]Parameter error: {e}[/red]")
            
            if step.original_duration:
                console.print(f"  [dim]Original duration: {step.original_duration:.2f}s[/dim]")
        
        console.print("\n[green]Dry run complete - no actions taken[/green]")
        return True
    
    def check_workflow_updates(self, workflow_name: str) -> Dict[str, Any]:
        """Check if any tools in a workflow have updates available.
        
        Args:
            workflow_name: Name or path of workflow to check
            
        Returns:
            Update information for the workflow
        """
        # Find workflow file
        workflow_path = self._find_workflow(workflow_name)
        if not workflow_path:
            return {"error": f"Workflow not found: {workflow_name}"}
        
        # Use integration to check for updates
        integration = get_integration()
        return integration.check_workflow_updates(workflow_path)
    
    def _check_tool_versions(self, steps: List[WorkflowStep]) -> List[Dict[str, Any]]:
        """Check if all required tool versions are available.
        
        Args:
            steps: List of workflow steps
            
        Returns:
            List of version issues found
        """
        integration = get_integration()
        issues = []
        
        for step in steps:
            # Check if tool version is specified in metadata
            required_version = step.metadata.get("version")
            if required_version:
                # Check if this version is available
                version_manager = integration.version_manager
                available = version_manager.list_versions(step.tool_name)
                
                if required_version not in available:
                    issues.append({
                        "tool": step.tool_name,
                        "required_version": required_version,
                        "available_versions": available,
                        "issue": "Required version not available"
                    })
        
        return issues
    
    @track_workflow_execution
    def _execute_workflow(self, steps: List[WorkflowStep], 
                         substitutor: ParameterSubstitutor,
                         interactive: bool,
                         workflow_name: str = "unknown",
                         workflow_version: str = "1.0.0") -> bool:
        """Execute workflow steps in order."""
        total_steps = len(steps)
        succeeded = 0
        failed = 0
        
        # Check tool versions before execution
        version_issues = self._check_tool_versions(steps)
        if version_issues:
            console.print("\n[yellow]Warning: Tool version issues detected:[/yellow]")
            for issue in version_issues:
                console.print(f"  - {issue['tool']}: {issue['issue']}")
            
            if interactive:
                if not typer.confirm("Continue anyway?", default=False):
                    return False
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            workflow_task = progress.add_task(
                f"Executing workflow...", total=total_steps
            )
            
            for i, step in enumerate(steps, 1):
                progress.update(
                    workflow_task,
                    description=f"Step {i}/{total_steps}: {step.tool_name}"
                )
                
                try:
                    # Substitute parameters
                    params = substitutor.substitute(step.parameters, interactive)
                    
                    # Execute tool
                    if step.tool_type in self.tool_registry:
                        executor = self.tool_registry[step.tool_type]
                        result = executor(step.tool_name, params)
                        
                        # Check result
                        if isinstance(result, dict) and result.get('status') == 'success':
                            succeeded += 1
                            console.print(f"  [green]✓ {step.tool_name} completed[/green]")
                        else:
                            failed += 1
                            console.print(f"  [red]✗ {step.tool_name} failed[/red]")
                    else:
                        console.print(f"  [yellow]⚠ Unknown tool type: {step.tool_type}[/yellow]")
                        failed += 1
                    
                except Exception as e:
                    failed += 1
                    console.print(f"  [red]✗ {step.tool_name} error: {e}[/red]")
                    logger.exception(f"Error executing {step.tool_name}")
                
                progress.advance(workflow_task)
        
        # Summary
        console.print(f"\n[bold]Workflow Complete:[/bold]")
        console.print(f"  [green]Succeeded: {succeeded}[/green]")
        if failed > 0:
            console.print(f"  [red]Failed: {failed}[/red]")
        
        return failed == 0
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List available workflows.
        
        AI_CONTEXT: Returns summary information about all workflows in the
        workflow directory. Used by the CLI to show available workflows.
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
        
        return sorted(workflows, key=lambda w: w.get("created_at", ""), reverse=True)