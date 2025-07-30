"""
Shell integration for agentctl auto-completion.

AI_CONTEXT:
    This module provides shell-specific completion scripts and integration
    for bash, zsh, and fish shells. It generates completion scripts that
    integrate with each shell's native completion system.
    
    The module also provides rich terminal formatting for interactive
    completion displays, making it easy to see suggestions with descriptions
    and type information.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from textwrap import dedent

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

from .engine import AutoCompleteEngine, CompletionContext, CompletionCandidate

logger = logging.getLogger(__name__)
console = Console()


class ShellIntegration:
    """Handles shell-specific completion integration.
    
    AI_CONTEXT:
        This class generates and installs completion scripts for different
        shells. Each shell has its own completion system:
        
        1. Bash: Uses complete/compgen commands
        2. Zsh: Uses compadd and completion functions
        3. Fish: Uses complete command with specific syntax
        
        The integration works by:
        - Generating a shell-specific completion script
        - Installing it in the appropriate location
        - Delegating to agtos's completion engine for suggestions
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize shell integration.
        
        Args:
            config_dir: Configuration directory for agentctl
        """
        self.config_dir = config_dir or Path.home() / ".agtos"
        self.completions_dir = self.config_dir / "completions"
        
    def generate_script(self, shell: str) -> str:
        """Generate completion script for the specified shell.
        
        Args:
            shell: Shell type ('bash', 'zsh', 'fish')
            
        Returns:
            Shell-specific completion script
            
        Raises:
            ValueError: If shell is not supported
        """
        if shell == "bash":
            return self._generate_bash_script()
        elif shell == "zsh":
            return self._generate_zsh_script()
        elif shell == "fish":
            return self._generate_fish_script()
        else:
            raise ValueError(f"Unsupported shell: {shell}")
    
    def _generate_bash_script(self) -> str:
        """Generate bash completion script."""
        return dedent('''
            # Bash completion for agentctl
            _agtos_complete() {
                local cur prev words cword
                _init_completion || return
                
                # Get completions from agtos
                local IFS=$'\\n'
                local completions=$(agentctl completion generate-candidates "$COMP_LINE" "$COMP_POINT" 2>/dev/null)
                
                if [[ -n "$completions" ]]; then
                    COMPREPLY=( $(compgen -W "$completions" -- "$cur") )
                fi
            }
            
            complete -F _agtos_complete agentctl
        ''').strip()
    
    def _generate_zsh_script(self) -> str:
        """Generate zsh completion script."""
        return dedent('''
            #compdef agentctl
            
            _agentctl() {
                local line state context
                local -a completions
                
                # Get current line and cursor position
                local cmd_line="${words[*]}"
                local cursor_pos=$CURSOR
                
                # Get completions from agtos
                completions=(${(f)"$(agentctl completion generate-candidates "$cmd_line" "$cursor_pos" 2>/dev/null)"})
                
                if [[ -n "$completions" ]]; then
                    _describe 'agtos' completions
                fi
            }
            
            _agentctl "$@"
        ''').strip()
    
    def _generate_fish_script(self) -> str:
        """Generate fish completion script."""
        return dedent('''
            # Fish completion for agentctl
            function __agtos_complete
                set -l cmd_line (commandline -c)
                set -l cursor_pos (commandline -C)
                
                # Get completions from agtos
                agentctl completion generate-candidates "$cmd_line" "$cursor_pos" 2>/dev/null
            end
            
            complete -c agentctl -f -a '(__agtos_complete)'
        ''').strip()
    
    def install(self, shell: str, force: bool = False) -> Tuple[bool, str]:
        """Install completion script for the specified shell.
        
        Args:
            shell: Shell type to install for
            force: Force overwrite existing scripts
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Determine installation path
            install_path = self._get_install_path(shell)
            
            if install_path.exists() and not force:
                return False, f"Completion script already exists at {install_path}. Use --force to overwrite."
            
            # Create directories
            install_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate and write script
            script = self.generate_script(shell)
            install_path.write_text(script)
            
            # Get sourcing instructions
            source_cmd = self._get_source_command(shell, install_path)
            
            message = f"Completion script installed at {install_path}\n"
            message += f"Add this to your shell config:\n  {source_cmd}"
            
            return True, message
            
        except Exception as e:
            logger.error(f"Failed to install completion script: {e}")
            return False, f"Installation failed: {str(e)}"
    
    def _get_install_path(self, shell: str) -> Path:
        """Get installation path for shell completion script."""
        if shell == "bash":
            # Try system locations first
            if Path("/usr/local/etc/bash_completion.d").exists():
                return Path("/usr/local/etc/bash_completion.d/agtos")
            elif Path("/etc/bash_completion.d").exists():
                return Path("/etc/bash_completion.d/agtos")
            else:
                # Fall back to user directory
                return self.completions_dir / "agtos.bash"
                
        elif shell == "zsh":
            # Check for oh-my-zsh
            if Path.home().joinpath(".oh-my-zsh").exists():
                return Path.home() / ".oh-my-zsh/completions/_agtos"
            else:
                return self.completions_dir / "_agtos"
                
        elif shell == "fish":
            # Fish has a standard user location
            return Path.home() / ".config/fish/completions/agtos.fish"
            
        else:
            return self.completions_dir / f"agtos.{shell}"
    
    def _get_source_command(self, shell: str, path: Path) -> str:
        """Get command to source the completion script."""
        if shell == "bash":
            if path.parent.name == "bash_completion.d":
                return "# Bash completion should load automatically"
            else:
                return f"source {path}"
                
        elif shell == "zsh":
            if path.parent.name == "completions":
                return "# Zsh completion should load automatically"
            else:
                return f"fpath+=({path.parent}) && autoload -Uz compinit && compinit"
                
        elif shell == "fish":
            return "# Fish completion loads automatically from ~/.config/fish/completions"
            
        else:
            return f"source {path}"


class CompletionFormatter:
    """Formats completion suggestions for terminal display.
    
    AI_CONTEXT:
        This class provides rich terminal formatting for completion
        suggestions. It creates visually appealing displays that show:
        
        1. The completion value
        2. Type information (tool, parameter, alias)
        3. Descriptions and help text
        4. Match quality indicators
        5. Usage statistics
        
        The formatter adapts to terminal width and can display
        completions in different formats (table, list, compact).
    """
    
    def __init__(self, width: Optional[int] = None):
        """Initialize formatter.
        
        Args:
            width: Terminal width (auto-detected if None)
        """
        self.console = Console(width=width)
        
    def format_candidates(self, candidates: List[CompletionCandidate], 
                         style: str = "table") -> None:
        """Format and display completion candidates.
        
        Args:
            candidates: List of completion candidates
            style: Display style ('table', 'list', 'compact')
        """
        if not candidates:
            self.console.print("[dim]No completions available[/dim]")
            return
            
        if style == "table":
            self._format_table(candidates)
        elif style == "list":
            self._format_list(candidates)
        elif style == "compact":
            self._format_compact(candidates)
        else:
            self._format_table(candidates)
    
    def _format_table(self, candidates: List[CompletionCandidate]) -> None:
        """Format candidates as a rich table."""
        table = Table(title="Completion Suggestions", show_lines=True)
        
        table.add_column("Completion", style="cyan", no_wrap=True)
        table.add_column("Type", style="yellow")
        table.add_column("Description", style="white")
        table.add_column("Score", style="green")
        
        for candidate in candidates[:10]:  # Limit to 10 for readability
            # Format type with icon
            type_icon = self._get_type_icon(candidate.type)
            type_text = f"{type_icon} {candidate.type}"
            
            # Format score as percentage
            score_text = f"{int(candidate.score * 100)}%"
            
            # Add row with conditional styling
            if candidate.score >= 0.9:
                completion_style = "bold cyan"
            elif candidate.score >= 0.7:
                completion_style = "cyan"
            else:
                completion_style = "dim cyan"
                
            table.add_row(
                Text(candidate.display, style=completion_style),
                type_text,
                Text(candidate.description, overflow="fold"),
                score_text
            )
        
        self.console.print(table)
        
        if len(candidates) > 10:
            self.console.print(f"\n[dim]... and {len(candidates) - 10} more[/dim]")
    
    def _format_list(self, candidates: List[CompletionCandidate]) -> None:
        """Format candidates as a detailed list."""
        for i, candidate in enumerate(candidates[:10]):
            # Create a panel for each candidate
            content = f"[bold]{candidate.display}[/bold]\n"
            content += f"Type: {candidate.type}\n"
            
            if candidate.description:
                content += f"Description: {candidate.description}\n"
                
            if candidate.metadata:
                if "aliases" in candidate.metadata:
                    content += f"Aliases: {', '.join(candidate.metadata['aliases'])}\n"
                if "match_type" in candidate.metadata:
                    content += f"Match: {candidate.metadata['match_type']}\n"
            
            content += f"Relevance: {int(candidate.score * 100)}%"
            
            # Color based on type
            border_color = {
                "tool": "cyan",
                "parameter": "yellow", 
                "alias": "green",
                "value": "magenta",
                "path": "blue"
            }.get(candidate.type, "white")
            
            panel = Panel(
                content,
                title=f"[{i+1}] {candidate.value}",
                border_style=border_color,
                expand=False
            )
            
            self.console.print(panel)
    
    def _format_compact(self, candidates: List[CompletionCandidate]) -> None:
        """Format candidates in a compact single-line format."""
        # Group by type
        by_type: Dict[str, List[CompletionCandidate]] = {}
        for candidate in candidates:
            if candidate.type not in by_type:
                by_type[candidate.type] = []
            by_type[candidate.type].append(candidate)
        
        # Display each type
        for comp_type, items in by_type.items():
            icon = self._get_type_icon(comp_type)
            self.console.print(f"\n{icon} [bold]{comp_type.title()}s:[/bold]")
            
            # Display items in columns
            values = [c.value for c in items[:20]]
            if len(values) > 4:
                # Multiple columns
                cols = 4
                for i in range(0, len(values), cols):
                    row = values[i:i+cols]
                    self.console.print("  " + "  ".join(f"[cyan]{v:20}[/cyan]" for v in row))
            else:
                # Single column with descriptions
                for item in items:
                    desc = f" - {item.description}" if item.description else ""
                    self.console.print(f"  [cyan]{item.value}[/cyan]{desc}")
    
    def _get_type_icon(self, comp_type: str) -> str:
        """Get icon for completion type."""
        icons = {
            "tool": "🔧",
            "parameter": "📝",
            "alias": "💬",
            "value": "📊",
            "path": "📁"
        }
        return icons.get(comp_type, "▪️")
    
    def format_inline(self, candidates: List[CompletionCandidate], 
                     current_input: str) -> str:
        """Format candidates for inline display (e.g., in REPL).
        
        Args:
            candidates: Completion candidates
            current_input: Current user input
            
        Returns:
            Formatted string for inline display
        """
        if not candidates:
            return ""
        
        # Take top 5 candidates
        top = candidates[:5]
        
        # Format as compact list
        items = []
        for c in top:
            if c.type == "alias":
                items.append(f"{c.value} ({c.metadata.get('aliases', [''])[0]})")
            else:
                items.append(c.value)
        
        return "  ".join(items)


def generate_candidates_for_shell(command_line: str, cursor_pos: int) -> List[str]:
    """Generate completion candidates for shell integration.
    
    This function is called by the shell completion scripts to get
    candidates for the current command line.
    
    Args:
        command_line: The full command line
        cursor_pos: Cursor position in the command line
        
    Returns:
        List of completion values (just the values, not full candidates)
    """
    try:
        # Create engine
        engine = AutoCompleteEngine()
        
        # Parse command line to create context
        parts = command_line.split()
        if not parts:
            partial = ""
        else:
            # Find which part we're completing
            current_pos = 0
            partial = ""
            
            for part in parts:
                part_end = current_pos + len(part)
                if current_pos <= cursor_pos <= part_end:
                    # We're in this part
                    offset = cursor_pos - current_pos
                    partial = part[:offset]
                    break
                current_pos = part_end + 1  # +1 for space
            else:
                # We're past all parts, probably typing a new one
                if command_line.endswith(' '):
                    partial = ""
                else:
                    partial = parts[-1]
        
        # Create context
        context = CompletionContext(
            partial_input=partial,
            cursor_position=cursor_pos,
            full_command=command_line
        )
        
        # Get candidates
        candidates = engine.complete(context)
        
        # Return just the values
        return [c.value for c in candidates]
        
    except Exception as e:
        logger.error(f"Error generating completions: {e}")
        return []


def detect_shell() -> Optional[str]:
    """Detect the current shell.
    
    Returns:
        Shell name ('bash', 'zsh', 'fish') or None if unknown
    """
    # Check SHELL environment variable
    shell_path = os.environ.get('SHELL', '')
    
    if 'bash' in shell_path:
        return 'bash'
    elif 'zsh' in shell_path:
        return 'zsh'
    elif 'fish' in shell_path:
        return 'fish'
    
    # Check parent process name as fallback
    try:
        import psutil
        parent = psutil.Process(os.getppid())
        parent_name = parent.name()
        
        if 'bash' in parent_name:
            return 'bash'
        elif 'zsh' in parent_name:
            return 'zsh'
        elif 'fish' in parent_name:
            return 'fish'
    except:
        pass
    
    return None