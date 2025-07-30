"""Codex agent implementation for OpenAI Codex CLI integration.

AI_CONTEXT:
    This module implements the Codex agent that uses the official
    Codex CLI tool from OpenAI. Key features:
    - Integration with Codex CLI (npm install -g @openai/codex)
    - Support for both API key and OAuth authentication
    - Configurable approval modes (suggest, auto-edit, full-auto)
    - Multimodal support (can process screenshots)
    
    In the multi-agent architecture:
    - Codex excels at quick code generation and automation
    - Runs in network-disabled sandbox for security
    - Pairs well with Claude (design → implement)
"""

import os
import asyncio
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import shutil
from pathlib import Path

from .base import BaseAgent, AgentStatus, ExecutionResult

logger = logging.getLogger(__name__)


class CodexAgent(BaseAgent):
    """Codex CLI agent for code generation and automation.
    
    AI_CONTEXT:
        Codex is the implementation specialist in agtOS:
        - Uses the official Codex CLI from OpenAI
        - Supports both API key and OAuth authentication
        - Runs in a network-disabled sandbox for security
        - Configurable approval modes for different trust levels
        
        It executes through the Codex CLI and can leverage
        Meta-MCP tools through its file operations.
    """
    
    def __init__(self, config):
        """Initialize Codex agent."""
        super().__init__(config)
        self.codex_cmd = config.metadata.get("codex_command", "codex")
        self.model = config.metadata.get("model", "o4-mini")
        self.approval_mode = config.metadata.get("approval_mode", "suggest")
        self.api_key = None
        self.config_path = Path.home() / ".codex" / "config.json"
        
    async def initialize(self) -> None:
        """Initialize Codex CLI connection.
        
        AI_CONTEXT:
            Sets up the Codex CLI with proper authentication.
            Checks if CLI is installed and configured.
            Supports both API key and OAuth authentication.
        """
        try:
            self.status = AgentStatus.INITIALIZING
            logger.info(f"Initializing Codex agent: {self.name}")
            
            # Check if Codex CLI is installed
            if not await self._check_codex_installed():
                raise RuntimeError(
                    "Codex CLI not found. Install with: npm install -g @openai/codex"
                )
            
            # Set up authentication
            if not await self._setup_authentication():
                raise RuntimeError(
                    "Codex authentication not configured. "
                    "Run 'agtos codex-setup' or set OPENAI_API_KEY"
                )
            
            # Verify CLI is working
            if not await self._test_cli():
                raise RuntimeError("Failed to verify Codex CLI functionality")
            
            self.status = AgentStatus.READY
            logger.info(f"Codex agent initialized with model: {self.model}")
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Failed to initialize Codex agent: {e}")
            raise
    
    async def _check_codex_installed(self) -> bool:
        """Check if Codex CLI is installed."""
        try:
            result = await asyncio.create_subprocess_exec(
                self.codex_cmd, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"Found Codex CLI: {version}")
                return True
            else:
                logger.debug(f"Codex CLI not found: {stderr.decode()}")
                return False
                
        except FileNotFoundError:
            return False
    
    async def _setup_authentication(self) -> bool:
        """Set up Codex authentication.
        
        AI_CONTEXT:
            Checks authentication in this order:
            1. Environment variable (OPENAI_API_KEY)
            2. Codex config file (~/.codex/config.json)
            3. OAuth configuration (if present)
        """
        # Check environment variable
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            logger.info("Using API key from environment variable")
            return True
        
        # Check config metadata
        self.api_key = self.config.metadata.get("api_key")
        if self.api_key:
            # Set environment variable for CLI
            os.environ["OPENAI_API_KEY"] = self.api_key
            logger.info("Using API key from agent config")
            return True
        
        # Check Codex config file
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    codex_config = json.load(f)
                    
                # Check if OAuth is configured
                if codex_config.get("oauth_configured"):
                    logger.info("Using OAuth authentication from Codex config")
                    return True
                    
            except Exception as e:
                logger.debug(f"Could not read Codex config: {e}")
        
        # Check agtos credentials file
        try:
            creds_path = Path.home() / ".agtos" / "credentials.json"
            if creds_path.exists():
                with open(creds_path, 'r') as f:
                    creds = json.load(f)
                    api_key = creds.get("openai", {}).get("api_key")
                    if api_key:
                        self.api_key = api_key
                        os.environ["OPENAI_API_KEY"] = api_key
                        logger.info("Using API key from agtos credentials")
                        return True
        except Exception as e:
            logger.debug(f"Could not read credentials file: {e}")
        
        return False
    
    async def _test_cli(self) -> bool:
        """Test Codex CLI functionality."""
        try:
            # Simple test with minimal prompt
            result = await asyncio.create_subprocess_exec(
                self.codex_cmd,
                "--quiet",
                "--model", self.model,
                "--approval-mode", "suggest",
                "echo test",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Codex CLI test failed: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Codex CLI is healthy."""
        try:
            if self.status != AgentStatus.READY:
                return False
            
            # Quick CLI check
            return await self._test_cli()
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ExecutionResult:
        """Execute a task with Codex CLI.
        
        AI_CONTEXT:
            Codex execution flow:
            1. Build full prompt with context
            2. Set up CLI arguments based on config
            3. Execute via subprocess
            4. Parse output and track metrics
            
            The CLI runs in a network-disabled sandbox for security.
            File operations are allowed based on approval mode.
        
        Args:
            prompt: Task description for Codex
            context: Context from previous workflow steps
            **kwargs: Additional parameters (model, approval_mode, etc.)
            
        Returns:
            ExecutionResult with Codex's response
        """
        start_time = datetime.now()
        
        try:
            # Build full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Build command with parameters
            cmd = await self._build_command(full_prompt, **kwargs)
            
            # Execute Codex CLI
            result = await self._execute_cli(cmd, **kwargs)
            
            # Calculate metrics and build response
            return await self._build_execution_result(
                result,
                full_prompt,
                start_time,
                context,
                **kwargs
            )
            
        except Exception as e:
            return self._build_error_result(e, start_time)
    
    async def _build_command(
        self,
        full_prompt: str,
        **kwargs
    ) -> List[str]:
        """Build Codex CLI command with parameters.
        
        AI_CONTEXT:
            Constructs the command-line arguments for Codex CLI
            based on configuration and runtime parameters.
        """
        # Get execution parameters
        model = kwargs.get("model", self.model)
        approval_mode = kwargs.get("approval_mode", self.approval_mode)
        quiet = kwargs.get("quiet", True)
        
        # Build command
        cmd = [
            self.codex_cmd,
            "--model", model,
            "--approval-mode", approval_mode
        ]
        
        if quiet:
            cmd.append("--quiet")
        
        # Add the prompt
        cmd.append(full_prompt)
        
        logger.debug(f"Built Codex CLI command: {' '.join(cmd[:4])}...")
        return cmd
    
    async def _execute_cli(
        self,
        cmd: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute Codex CLI subprocess.
        
        AI_CONTEXT:
            Runs the Codex CLI command and captures output.
            Handles process execution with proper async handling.
        """
        logger.debug("Executing Codex CLI subprocess")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=kwargs.get("working_dir", os.getcwd())
        )
        
        stdout, stderr = await process.communicate()
        
        # Parse response
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Codex CLI failed: {error_msg}")
        
        return {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode
        }
    
    async def _build_execution_result(
        self,
        cli_result: Dict[str, Any],
        full_prompt: str,
        start_time: datetime,
        context: Optional[Dict[str, Any]],
        **kwargs
    ) -> ExecutionResult:
        """Build ExecutionResult from CLI output.
        
        AI_CONTEXT:
            Parses CLI output, calculates metrics, and constructs
            the final ExecutionResult with all metadata.
        """
        content = cli_result["stdout"].decode()
        
        # Calculate metrics
        duration = (datetime.now() - start_time).total_seconds()
        
        # Estimate tokens and cost
        model = kwargs.get("model", self.model)
        estimated_tokens = len(full_prompt.split()) + len(content.split())
        estimated_cost = self._estimate_cost(estimated_tokens, model)
        
        # Record metrics
        self.record_execution(duration, estimated_cost, estimated_tokens)
        
        return ExecutionResult(
            success=True,
            content=content,
            agent=self.name,
            duration=duration,
            cost=estimated_cost,
            tokens_used=estimated_tokens,
            metadata={
                "model": model,
                "approval_mode": kwargs.get("approval_mode", self.approval_mode),
                "context_used": bool(context),
                "cli_version": await self._get_cli_version()
            }
        )
    
    def _build_error_result(
        self,
        error: Exception,
        start_time: datetime
    ) -> ExecutionResult:
        """Build ExecutionResult for error cases.
        
        AI_CONTEXT:
            Constructs a consistent error response with
            proper duration tracking and error metadata.
        """
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Codex execution failed: {error}")
        
        return ExecutionResult(
            success=False,
            content=None,
            agent=self.name,
            duration=duration,
            error=str(error),
            metadata={"error_type": type(error).__name__}
        )
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build full prompt for Codex CLI.
        
        AI_CONTEXT:
            Prompt construction strategy:
            - Include relevant context from previous steps
            - Add clear instructions for code generation
            - Maintain conversational flow for better results
        """
        parts = []
        
        # Add context if available
        if context:
            # Include relevant context from previous steps
            context_parts = []
            
            for step_name, result in context.items():
                if isinstance(result, dict) and "content" in result:
                    context_parts.append(f"[Previous step - {step_name}]:\n{result['content']}")
            
            if context_parts:
                parts.append("Based on the following context:")
                parts.extend(context_parts)
                parts.append("")  # Empty line
        
        # Add main prompt
        parts.append(prompt)
        
        return "\n".join(parts)
    
    def _estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost based on token usage.
        
        Rough estimates for Codex models:
        - o4-mini: Most cost-effective
        - o4: Higher quality, higher cost
        """
        # These are rough estimates as Codex pricing varies
        cost_per_1k = {
            "o4-mini": 0.015,
            "o4": 0.030,
            "gpt-4": 0.045,  # Fallback
        }
        
        rate = cost_per_1k.get(model, 0.030)
        return (tokens / 1000) * rate
    
    async def _get_cli_version(self) -> Optional[str]:
        """Get Codex CLI version."""
        try:
            result = await asyncio.create_subprocess_exec(
                self.codex_cmd, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                return stdout.decode().strip()
                
        except Exception:
            pass
        
        return None
    
    async def shutdown(self) -> None:
        """Shutdown Codex agent."""
        try:
            logger.info(f"Shutting down Codex agent: {self.name}")
            
            # Clean up any temporary files
            # Codex CLI handles its own cleanup
            
            self.status = AgentStatus.SHUTDOWN
            logger.info(f"Codex agent shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise
    
    # ========================================================================
    # Codex-specific methods
    # ========================================================================
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Codex model being used."""
        return {
            "model": self.model,
            "cli_tool": "codex",
            "approval_mode": self.approval_mode,
            "supports_multimodal": True,
            "runs_sandboxed": True,
            "strengths": [
                "Fast code generation",
                "Script automation",
                "API integration",
                "Terminal operations",
                "Algorithm implementation",
                "Test generation",
                "Diagram/screenshot understanding"
            ],
            "weaknesses": [
                "Complex architectural decisions",
                "Long-form documentation",
                "Real-time interaction (in quiet mode)"
            ]
        }
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        approval_mode: str = "suggest"
    ) -> ExecutionResult:
        """Specialized method for code generation.
        
        Args:
            description: What code to generate
            language: Target programming language
            approval_mode: How much autonomy to give Codex
            
        Returns:
            ExecutionResult with generated code
        """
        prompt = f"""Write {language} code for: {description}

Requirements:
- Complete, working implementation
- Proper error handling
- Follow best practices
- Include usage example"""
        
        return await self.execute(prompt, approval_mode=approval_mode)
    
    async def refactor_code(
        self,
        file_path: str,
        instructions: str,
        approval_mode: str = "auto-edit"
    ) -> ExecutionResult:
        """Refactor existing code.
        
        Args:
            file_path: Path to file to refactor
            instructions: Refactoring instructions
            approval_mode: Level of autonomy
            
        Returns:
            ExecutionResult with refactoring results
        """
        prompt = f"""Refactor the code in {file_path}:

{instructions}

Ensure:
- Maintain functionality
- Improve readability
- Follow project conventions
- Update tests if needed"""
        
        return await self.execute(
            prompt,
            approval_mode=approval_mode,
            working_dir=os.path.dirname(file_path)
        )
    
    async def execute_with_screenshot(
        self,
        prompt: str,
        screenshot_path: str,
        **kwargs
    ) -> ExecutionResult:
        """Execute task with screenshot context.
        
        AI_CONTEXT:
            Codex CLI supports multimodal inputs including
            screenshots and diagrams. This method allows
            passing visual context for UI-related tasks.
        
        Args:
            prompt: Task description
            screenshot_path: Path to screenshot/image
            **kwargs: Additional parameters
            
        Returns:
            ExecutionResult with Codex's response
        """
        # Codex CLI can process images directly in the prompt
        full_prompt = f"""[Image: {screenshot_path}]

{prompt}"""
        
        return await self.execute(full_prompt, **kwargs)