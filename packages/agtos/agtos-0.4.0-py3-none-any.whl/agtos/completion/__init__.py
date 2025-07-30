"""
Auto-completion system for agtos.

AI_CONTEXT:
    This package provides intelligent auto-completion for agentctl tools,
    integrating with various shells and providing context-aware suggestions.
    
    Key components:
    - engine.py: Core completion engine with fuzzy matching
    - shell.py: Shell-specific integration (bash, zsh, fish)
    - Interactive completion interfaces
    
    The system integrates with the existing alias and fuzzy matching
    systems to provide a seamless experience.
"""

from .engine import (
    AutoCompleteEngine,
    CompletionCandidate,
    CompletionContext
)

from .shell import (
    ShellIntegration,
    CompletionFormatter,
    detect_shell,
    generate_candidates_for_shell
)

__all__ = [
    "AutoCompleteEngine",
    "CompletionCandidate", 
    "CompletionContext",
    "ShellIntegration",
    "CompletionFormatter",
    "detect_shell",
    "generate_candidates_for_shell"
]