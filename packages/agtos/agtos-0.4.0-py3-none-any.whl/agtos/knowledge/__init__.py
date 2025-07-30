"""Knowledge acquisition package for agtos.

PURPOSE: Automatically discover and understand CLI tools, APIs, and packages
CONTEXT: Core functionality for creating plugins with minimal manual effort
AI_NOTE: This package is split into focused modules for better organization

MODULES:
  - cli.py: CLI tool discovery and analysis
  - api.py: REST API discovery and parsing  
  - package.py: Package registry information
  - intelligent.py: Pattern-based knowledge extraction
  - generator.py: Plugin code generation
  - acquisition.py: Main orchestrator

PUBLIC_API:
  - CLIKnowledge: Discover CLI tool capabilities
  - APIKnowledge: Discover API endpoints
  - PackageKnowledge: Get package information
  - IntelligentKnowledge: Extract patterns from docs
  - PluginGenerator: Generate plugin code
  - KnowledgeAcquisition: Main orchestrator
"""

# Import all classes for backward compatibility
from .cli import CLIKnowledge
from .api import APIKnowledge
from .package import PackageKnowledge
from .intelligent import IntelligentKnowledge
from .generator import PluginGenerator
from .acquisition import KnowledgeAcquisition

# Re-export for public API
__all__ = [
    'CLIKnowledge',
    'APIKnowledge', 
    'PackageKnowledge',
    'IntelligentKnowledge',
    'PluginGenerator',
    'KnowledgeAcquisition'
]

# Version info
__version__ = '0.3.0'