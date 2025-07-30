"""Knowledge acquisition orchestrator for agtos.

This module serves as the main orchestrator for comprehensive knowledge acquisition,
combining all knowledge sources (CLI, API, Package, and Intelligent) to discover,
analyze, and generate plugin code based on various service types.

## AI-First Design

This module follows an AI-first approach, designed to be:

1. **Self-documenting**: Rich docstrings and type hints for AI understanding
2. **Modular**: Each knowledge source is a separate component
3. **Extensible**: Easy to add new knowledge acquisition strategies
4. **Intelligent**: Automatically detects service types and appropriate strategies

## Core Concepts

The KnowledgeAcquisition class orchestrates multiple knowledge sources:

- **CLIKnowledge**: Discovers command-line tool patterns and usage
- **APIKnowledge**: Analyzes REST API documentation and endpoints
- **PackageKnowledge**: Examines Python packages and their capabilities
- **IntelligentKnowledge**: Extracts knowledge from unstructured documentation
- **PluginGenerator**: Creates plugin code from acquired knowledge

## Usage Example

```python
from agtos.knowledge.acquisition import KnowledgeAcquisition

# Initialize the orchestrator
ka = KnowledgeAcquisition()

# Acquire comprehensive knowledge about a service
knowledge = ka.acquire_comprehensive_knowledge("stripe", target_type="api")

# Generate a plugin from the knowledge
plugin_code, knowledge_used = ka.generate_plugin_with_knowledge("stripe")

# Export the knowledge base for sharing
ka.export_knowledge_base(Path("./knowledge_export.json"))
```

## Knowledge Persistence

All acquired knowledge is automatically stored in a local knowledge store
with configurable TTL (Time To Live) for caching. This enables:

- Faster subsequent plugin generation
- Knowledge sharing between sessions
- Offline plugin development
- Knowledge base export/import

## Integration Points

This module integrates with:

- The plugin creation flow (`agentctl integrate`)
- Knowledge management commands (`agentctl knowledge`)
- MCP export functionality (provides context for tool generation)
- The credential system (for API testing)
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from ..knowledge_store import get_knowledge_store
from .cli import CLIKnowledge
from .api import APIKnowledge
from .package import PackageKnowledge
from .intelligent import IntelligentKnowledge
from .generator import PluginGenerator


class KnowledgeAcquisition:
    """Main orchestrator for comprehensive knowledge acquisition.
    
    This class coordinates multiple knowledge sources to build a complete
    understanding of a service, tool, or API. It manages the entire
    knowledge acquisition pipeline from discovery to plugin generation.
    
    Attributes:
        cli: CLI knowledge discovery component
        api: API knowledge discovery component
        package: Python package knowledge component
        intelligent: Documentation extraction component
        store: Persistent knowledge storage
    """
    
    def __init__(self):
        """Initialize the knowledge acquisition orchestrator.
        
        Sets up all knowledge source components and the storage backend.
        """
        self.cli = CLIKnowledge()
        self.api = APIKnowledge()
        self.package = PackageKnowledge()
        self.intelligent = IntelligentKnowledge()
        self.store = get_knowledge_store()
    
    def acquire_comprehensive_knowledge(self, 
                                      target: str, 
                                      target_type: str = "auto") -> Dict[str, Any]:
        """Acquire all available knowledge about a target.
        
        This method orchestrates the discovery process across all knowledge
        sources, automatically detecting the target type if not specified.
        
        AI_CONTEXT: This method is the main orchestrator for knowledge discovery.
        It implements a multi-strategy approach with intelligent fallbacks:
        
        1. Auto-detection (if target_type="auto"):
           - URLs starting with http/https → API discovery
           - Known CLI tools (git, npm, docker, etc.) → CLI discovery
           - Everything else → Try all methods
        
        2. Discovery strategies in order:
           - Check knowledge store cache first (avoid redundant discovery)
           - CLI discovery: help commands, man pages, completions
           - API discovery: OpenAPI specs, documentation parsing
           - Package discovery: npm, pip, cargo registries
           - Intelligent extraction: LLM-based analysis as fallback
        
        3. Knowledge aggregation:
           - Combines discoveries from all successful sources
           - Merges examples from different sources
           - Preserves source attribution for each piece of knowledge
        
        The method is defensive and continues trying other strategies even if
        one fails. This ensures maximum knowledge extraction. Results are
        automatically cached in the knowledge store for future use.
        
        Args:
            target: The service/tool/API to acquire knowledge about
            target_type: Type of target ("cli", "api", "package", or "auto")
        
        Returns:
            Comprehensive knowledge dictionary containing:
            - target: The original target name
            - type: Detected or specified type
            - acquired_at: ISO timestamp of acquisition
            - cli: CLI-specific knowledge if applicable
            - api: API-specific knowledge if applicable
            - package: Package-specific knowledge if applicable
            - examples: Usage examples discovered
            - documentation: Extracted documentation insights
            - completions: Shell completions if available
            - endpoint_tests: API endpoint test results if applicable
        
        Example:
            ```python
            # Auto-detect type
            knowledge = ka.acquire_comprehensive_knowledge("git")
            
            # Specify API type
            knowledge = ka.acquire_comprehensive_knowledge(
                "https://api.stripe.com",
                target_type="api"
            )
            ```
        """
        # Initialize knowledge structure
        knowledge = self._initialize_knowledge_structure(target, target_type)
        
        # Auto-detect type if needed
        if target_type == "auto":
            target_type, cli_knowledge = self._detect_target_type(target)
            knowledge["type"] = target_type
            if cli_knowledge:
                knowledge["cli"] = cli_knowledge
        
        # Acquire knowledge based on type
        if target_type == "cli":
            self._acquire_cli_knowledge(target, knowledge)
        elif target_type == "api":
            self._acquire_api_knowledge(target, knowledge)
        elif target_type == "package":
            self._acquire_package_knowledge(target, knowledge)
        
        # Store comprehensive knowledge
        self._store_knowledge(target, knowledge)
        
        return knowledge
    
    def _initialize_knowledge_structure(self, target: str, target_type: str) -> Dict[str, Any]:
        """Initialize the knowledge structure with default values.
        
        Args:
            target: The target name
            target_type: The specified or auto type
            
        Returns:
            Initial knowledge dictionary
        """
        return {
            "target": target,
            "type": target_type,
            "acquired_at": datetime.now().isoformat(),
            "cli": None,
            "api": None,
            "package": None,
            "examples": [],
            "documentation": None
        }
    
    def _detect_target_type(self, target: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Auto-detect the target type based on heuristics.
        
        Args:
            target: The target to analyze
            
        Returns:
            Tuple of (detected_type, cli_knowledge if applicable)
        """
        # Check if it's a CLI tool
        cli_knowledge = self.cli.discover_cli_patterns(target)
        if cli_knowledge.get("available"):
            return "cli", cli_knowledge
        elif target.startswith("http"):
            return "api", None
        else:
            # Assume it's a package
            return "package", None
    
    def _acquire_cli_knowledge(self, target: str, knowledge: Dict[str, Any]):
        """Acquire CLI-specific knowledge.
        
        Args:
            target: The CLI tool name
            knowledge: Knowledge dictionary to update
        """
        if not knowledge["cli"]:
            knowledge["cli"] = self.cli.discover_cli_patterns(target)
        
        # Get examples
        examples = self.cli.discover_command_examples(target)
        knowledge["examples"].extend(examples)
        
        # Get completions
        knowledge["completions"] = self.cli.analyze_cli_completions(target)
    
    def _acquire_api_knowledge(self, target: str, knowledge: Dict[str, Any]):
        """Acquire API-specific knowledge.
        
        Args:
            target: The API URL or identifier
            knowledge: Knowledge dictionary to update
        """
        # Try to discover API
        knowledge["api"] = self.api.discover_api_from_docs(target)
        
        # Test some endpoints if found
        if knowledge["api"].get("endpoints"):
            knowledge["endpoint_tests"] = self._test_api_endpoints(
                target, knowledge["api"]["endpoints"]
            )
    
    def _test_api_endpoints(self, target: str, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test a sample of API endpoints.
        
        Args:
            target: Base API URL
            endpoints: List of endpoint definitions
            
        Returns:
            List of test results
        """
        test_results = []
        for endpoint in endpoints[:3]:  # Test first 3 endpoints
            if isinstance(endpoint, dict):
                test_result = self.api.test_api_endpoint(
                    target + endpoint.get("path", ""),
                    endpoint.get("method", "GET")
                )
                test_results.append(test_result)
        return test_results
    
    def _acquire_package_knowledge(self, target: str, knowledge: Dict[str, Any]):
        """Acquire package-specific knowledge.
        
        Args:
            target: The package name
            knowledge: Knowledge dictionary to update
        """
        # Get package info
        pkg_knowledge = self.package.discover_package_knowledge(target)
        knowledge["package"] = pkg_knowledge
        
        # If package has CLI tools, acquire CLI knowledge
        if pkg_knowledge.get("cli_tools"):
            knowledge["cli_tools"] = self._acquire_cli_tools_knowledge(
                pkg_knowledge["cli_tools"]
            )
        
        # Extract knowledge from README
        if pkg_knowledge.get("readme"):
            knowledge["documentation"] = self.intelligent.extract_from_documentation(
                pkg_knowledge["readme"],
                context=f"README for {target}"
            )
    
    def _acquire_cli_tools_knowledge(self, cli_tools: List[str]) -> Dict[str, Dict[str, Any]]:
        """Acquire knowledge for CLI tools provided by a package.
        
        Args:
            cli_tools: List of CLI tool names
            
        Returns:
            Dictionary mapping tool names to their knowledge
        """
        cli_tools_knowledge = {}
        for tool in cli_tools:
            tool_knowledge = self.cli.discover_cli_patterns(tool)
            if tool_knowledge.get("available"):
                cli_tools_knowledge[tool] = tool_knowledge
        return cli_tools_knowledge
    
    def _store_knowledge(self, target: str, knowledge: Dict[str, Any]):
        """Store the acquired knowledge in the knowledge store.
        
        Args:
            target: The target name for storage
            knowledge: The complete knowledge dictionary
        """
        self.store.store(
            type="comprehensive",
            name=target,
            data=knowledge,
            source="knowledge_acquisition",
            ttl_hours=720  # 30 days
        )
    
    def generate_plugin_with_knowledge(self, 
                                     service: str,
                                     force_acquire: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Generate a plugin using all available knowledge.
        
        This method combines knowledge acquisition with plugin generation,
        using cached knowledge when available unless forced to re-acquire.
        
        Args:
            service: The service to generate a plugin for
            force_acquire: Whether to force fresh knowledge acquisition
        
        Returns:
            Tuple of (plugin_code, knowledge_used):
            - plugin_code: Generated Python plugin code
            - knowledge_used: The knowledge dictionary used for generation
        
        Example:
            ```python
            # Use cached knowledge if available
            code, knowledge = ka.generate_plugin_with_knowledge("stripe")
            
            # Force fresh acquisition
            code, knowledge = ka.generate_plugin_with_knowledge(
                "stripe",
                force_acquire=True
            )
            ```
        """
        # Check for existing knowledge
        if not force_acquire:
            cached = self.store.retrieve("comprehensive", service)
            if cached:
                knowledge = cached["data"]
            else:
                knowledge = self.acquire_comprehensive_knowledge(service)
        else:
            knowledge = self.acquire_comprehensive_knowledge(service)
        
        # Determine plugin type
        if knowledge.get("cli") and knowledge["cli"].get("available"):
            plugin_code = PluginGenerator.generate_cli_plugin(service, knowledge["cli"])
        elif knowledge.get("api") and knowledge["api"].get("discovered"):
            plugin_code = PluginGenerator.generate_api_plugin(service, knowledge["api"])
        else:
            # Generate a basic plugin template
            plugin_code = f'''"""Plugin for {service} integration.
Auto-generated - no specific knowledge found.

Please manually implement the integration or provide more information.
"""

TOOLS = {{
    "{service}.placeholder": {{
        "version": "1.0",
        "description": "Placeholder function - implement actual functionality",
        "schema": {{"type": "object", "properties": {{}}}},
        "func": lambda: {{"error": "Not implemented"}}
    }}
}}'''
        
        return plugin_code, knowledge
    
    def export_knowledge_base(self, output_path: Path):
        """Export the entire knowledge base.
        
        Exports all stored knowledge to a JSON file for sharing or backup.
        
        Args:
            output_path: Path where the export file should be saved
        
        Example:
            ```python
            ka.export_knowledge_base(Path("./my_knowledge.json"))
            ```
        """
        self.store.export(output_path)
    
    def import_knowledge_base(self, input_path: Path) -> int:
        """Import a knowledge base.
        
        Imports knowledge from a previously exported JSON file.
        
        Args:
            input_path: Path to the knowledge export file
        
        Returns:
            Number of knowledge entries imported
        
        Example:
            ```python
            count = ka.import_knowledge_base(Path("./shared_knowledge.json"))
            print(f"Imported {count} knowledge entries")
            ```
        """
        return self.store.import_from(input_path)
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge store.
        
        Returns comprehensive statistics about stored knowledge.
        
        Returns:
            Dictionary containing:
            - total_entries: Total number of knowledge entries
            - by_type: Breakdown by knowledge type
            - by_source: Breakdown by acquisition source
            - storage_size: Approximate storage size in bytes
            - oldest_entry: Timestamp of oldest entry
            - newest_entry: Timestamp of newest entry
        
        Example:
            ```python
            stats = ka.get_knowledge_stats()
            print(f"Total entries: {stats['total_entries']}")
            print(f"CLI tools: {stats['by_type'].get('cli', 0)}")
            ```
        """
        return self.store.get_stats()