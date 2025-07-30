"""Main MCP exporter class with core export logic.

AI_CONTEXT:
    This module contains the MCPExporter class which orchestrates the
    export process. It uses functions from other modules (metadata,
    templates, knowledge) to keep each component focused and maintainable.
"""
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from ..knowledge_store import get_knowledge_store

# Make plugins import conditional
try:
    from ..plugins import get_plugin
    PLUGINS_AVAILABLE = True
except ImportError:
    get_plugin = None
    PLUGINS_AVAILABLE = False

from .metadata import create_metadata, extract_requirements
from .templates import generate_mcp_server, generate_readme, generate_package_readme, generate_run_script
from .knowledge import export_plugin_knowledge
from .utils import ensure_directory, write_json, write_requirements, create_zip_package, make_executable


class MCPExporter:
    """Export agentctl plugins as standalone MCP tools.
    
    AI_CONTEXT:
        This is the main class for MCP export functionality. It coordinates
        the export process by delegating specific tasks to specialized
        modules. The class provides methods for exporting individual plugins
        and creating bundles of multiple tools.
    """
    
    def __init__(self):
        """Initialize the exporter with a knowledge store instance."""
        self.store = get_knowledge_store()
    
    def export_plugin_as_mcp(self, 
                            plugin_name: str,
                            output_dir: Path,
                            include_knowledge: bool = True,
                            include_examples: bool = True,
                            standalone: bool = True) -> Tuple[Path, Dict[str, Any]]:
        """Export a plugin as a standalone MCP tool.
        
        Args:
            plugin_name: Name of the plugin to export
            output_dir: Directory to export to
            include_knowledge: Include knowledge base
            include_examples: Include usage examples
            standalone: Make it fully standalone
            
        Returns:
            Tuple of (export_path, metadata)
            
        Raises:
            ValueError: If plugin is not found
            FileNotFoundError: If plugin source file is not found
        """
        # Check if plugins are available
        if not PLUGINS_AVAILABLE:
            raise ImportError("Plugins module not available - plugin export disabled")
            
        # Load plugin
        plugin = get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        # Create export directory
        export_name = f"mcp-tool-{plugin_name}"
        export_path = output_dir / export_name
        ensure_directory(export_path)
        
        # Get plugin source file
        plugin_file = self._get_plugin_source_file(plugin_name)
        
        # Create metadata
        metadata = create_metadata(plugin_name, plugin, self.store)
        
        # Export based on type
        if standalone:
            self._export_standalone(
                plugin_name, plugin, plugin_file, export_path, 
                metadata, include_knowledge, include_examples
            )
        else:
            self._export_simple(
                plugin_name, plugin, plugin_file, export_path, metadata
            )
        
        # Write metadata
        metadata_path = export_path / "mcp-tool.json"
        write_json(metadata_path, metadata)
        
        return export_path, metadata
    
    def create_mcp_package(self, 
                          plugin_names: List[str],
                          output_path: Path,
                          package_name: Optional[str] = None,
                          include_knowledge: bool = True) -> Path:
        """Create a package containing multiple MCP tools.
        
        Args:
            plugin_names: List of plugins to include
            output_path: Where to create the package
            package_name: Package name (default: mcp-tools-bundle)
            include_knowledge: Include knowledge bases
            
        Returns:
            Path to created package
        """
        if not package_name:
            package_name = "mcp-tools-bundle"
        
        # Create temporary directory for package contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / package_name
            package_dir.mkdir()
            
            # Export each plugin
            exported_tools = []
            for plugin_name in plugin_names:
                try:
                    tool_dir, metadata = self.export_plugin_as_mcp(
                        plugin_name,
                        package_dir,
                        include_knowledge=include_knowledge,
                        standalone=False
                    )
                    exported_tools.append({
                        "name": plugin_name,
                        "metadata": metadata
                    })
                except Exception as e:
                    print(f"Warning: Failed to export {plugin_name}: {e}")
            
            # Create package metadata
            package_metadata = self._create_package_metadata(
                package_name, exported_tools
            )
            
            metadata_path = package_dir / "package.json"
            write_json(metadata_path, package_metadata)
            
            # Create package README
            readme = generate_package_readme(package_name, exported_tools)
            readme_path = package_dir / "README.md"
            readme_path.write_text(readme)
            
            # Create zip file
            zip_path = output_path / f"{package_name}.zip"
            return create_zip_package(package_dir, zip_path)
    
    def publish_to_registry(self, 
                           export_path: Path,
                           registry_url: str,
                           auth_token: Optional[str] = None) -> bool:
        """Publish an exported MCP tool to a registry.
        
        Args:
            export_path: Path to exported tool
            registry_url: Registry URL
            auth_token: Authentication token
            
        Returns:
            Success status
            
        Raises:
            NotImplementedError: Registry publishing not yet available
        """
        # This is a placeholder for future registry integration
        # In practice, this would upload to npm, PyPI, or a custom MCP registry
        raise NotImplementedError(
            "Publishing to registries will be implemented when "
            "MCP tool registries become available"
        )
    
    # Private methods
    
    def _get_plugin_source_file(self, plugin_name: str) -> Path:
        """Get the source file path for a plugin."""
        # Check if plugin module is already loaded
        plugin_module = sys.modules.get(f"agtos.plugins.{plugin_name}")
        if plugin_module and hasattr(plugin_module, "__file__"):
            return Path(plugin_module.__file__)
        
        # Try to find in plugins directory
        plugin_file = Path(__file__).parent.parent / "plugins" / f"{plugin_name}.py"
        
        if not plugin_file.exists():
            raise FileNotFoundError(f"Plugin source file not found: {plugin_file}")
        
        return plugin_file
    
    def _export_standalone(self, 
                          plugin_name: str,
                          plugin: Dict[str, Any],
                          plugin_file: Path,
                          export_path: Path,
                          metadata: Dict[str, Any],
                          include_knowledge: bool,
                          include_examples: bool) -> None:
        """Export as a fully standalone MCP tool."""
        # Create main server file
        server_content = generate_mcp_server(plugin_name, plugin)
        server_path = export_path / "server.py"
        server_path.write_text(server_content)
        
        # Copy plugin file
        plugin_dest = export_path / f"{plugin_name}_plugin.py"
        shutil.copy2(plugin_file, plugin_dest)
        
        # Create requirements.txt
        requirements = extract_requirements(plugin_file)
        requirements_path = export_path / "requirements.txt"
        write_requirements(requirements_path, requirements)
        metadata["requirements"] = requirements
        
        # Export knowledge if requested
        if include_knowledge:
            knowledge_path = export_path / "knowledge.json"
            export_plugin_knowledge(self.store, plugin_name, knowledge_path)
            metadata["knowledge_included"] = True
        
        # Export examples if requested
        if include_examples:
            self._export_examples(plugin_name, export_path, metadata)
        
        # Create README
        readme_content = generate_readme(plugin_name, metadata)
        readme_path = export_path / "README.md"
        readme_path.write_text(readme_content)
        
        # Create run script
        run_script = generate_run_script()
        run_path = export_path / "run.py"
        run_path.write_text(run_script)
        make_executable(run_path)
    
    def _export_simple(self, 
                      plugin_name: str,
                      plugin: Dict[str, Any],
                      plugin_file: Path,
                      export_path: Path,
                      metadata: Dict[str, Any]) -> None:
        """Export as a simple MCP tool (just the plugin)."""
        # Copy plugin file
        shutil.copy2(plugin_file, export_path / f"{plugin_name}.py")
        
        # Create minimal requirements
        requirements = extract_requirements(plugin_file)
        if requirements:
            requirements_path = export_path / "requirements.txt"
            write_requirements(requirements_path, requirements)
            metadata["requirements"] = requirements
    
    def _export_examples(self, plugin_name: str, export_path: Path, 
                        metadata: Dict[str, Any]) -> None:
        """Export examples for a plugin."""
        examples = self.store.get_examples("plugin", plugin_name)
        if not examples:
            # Try to get examples from comprehensive knowledge
            knowledge = self.store.retrieve("comprehensive", plugin_name)
            if knowledge and "examples" in knowledge["data"]:
                examples = knowledge["data"]["examples"]
        
        if examples:
            examples_path = export_path / "examples.json"
            write_json(examples_path, examples)
            metadata["examples_included"] = True
    
    def _create_package_metadata(self, package_name: str, 
                                tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create metadata for a tool package."""
        from datetime import datetime
        
        return {
            "name": package_name,
            "version": "1.0.0",
            "description": f"Bundle of {len(tools)} MCP tools",
            "created_at": datetime.now().isoformat(),
            "tools": tools,
            "source": "agtos"
        }