"""Knowledge acquisition for plugin creation.

This module helps agentctl understand how to use CLIs and APIs
by fetching documentation, parsing help text, and discovering endpoints.

DEPRECATED: This module is kept for backward compatibility.
All functionality has been moved to the knowledge package.
New code should import from agtos.knowledge instead.
"""

# Re-export for backward compatibility
from .knowledge import (
    CLIKnowledge,
    APIKnowledge,
    PackageKnowledge,
    IntelligentKnowledge,
    PluginGenerator,
    KnowledgeAcquisition
)

__all__ = [
    'CLIKnowledge',
    'APIKnowledge',
    'PackageKnowledge',
    'IntelligentKnowledge',
    'PluginGenerator',
    'KnowledgeAcquisition'
]

# Deprecation warning
import warnings
warnings.warn(
    "The knowledge_acquisition module is deprecated. "
    "Please import from agtos.knowledge instead.",
    DeprecationWarning,
    stacklevel=2
)