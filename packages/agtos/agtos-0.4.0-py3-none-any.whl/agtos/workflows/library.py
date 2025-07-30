"""Official workflow library management for agtos.

This module manages the official library of production-ready workflows,
providing discovery, validation, and documentation features.

AI_CONTEXT: The workflow library provides curated, production-tested workflows
that users can immediately use. Each workflow includes comprehensive error
handling, rollback procedures, and clear documentation.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowMetadata:
    """Metadata about an official workflow.
    
    AI_CONTEXT: Captures key information about each workflow to enable
    search, filtering, and documentation generation.
    """
    name: str
    description: str
    version: str
    category: str
    tags: List[str] = field(default_factory=list)
    author: str = "agtos team"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    min_agtos_version: str = "0.3.0"
    supported_platforms: List[str] = field(default_factory=lambda: ["linux", "macos"])
    required_tools: List[str] = field(default_factory=list)
    required_env: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    @classmethod
    def from_workflow(cls, workflow_data: Dict[str, Any]) -> "WorkflowMetadata":
        """Extract metadata from workflow YAML data."""
        config = workflow_data.get("config", {})
        
        # Determine category from workflow name or content
        name = workflow_data.get("name", "")
        category = "general"
        
        if "release" in name or "deploy" in name:
            category = "deployment"
        elif "database" in name or "migration" in name:
            category = "database"
        elif "security" in name or "audit" in name:
            category = "security"
        elif "backup" in name or "restore" in name:
            category = "operations"
        elif "dependency" in name or "update" in name:
            category = "maintenance"
        
        # Extract tags from description and parameters
        tags = []
        description = workflow_data.get("description", "").lower()
        for tag_word in ["automated", "testing", "rollback", "monitoring", "notification"]:
            if tag_word in description:
                tags.append(tag_word)
        
        return cls(
            name=workflow_data.get("name", ""),
            description=workflow_data.get("description", ""),
            version=workflow_data.get("version", "1.0.0"),
            category=category,
            tags=tags,
            required_tools=config.get("required_tools", []),
            required_env=config.get("required_env", [])
        )


class WorkflowLibrary:
    """Manages the official workflow library.
    
    AI_CONTEXT: Central manager for discovering, loading, and documenting
    official workflows. Provides search and filtering capabilities.
    """
    
    def __init__(self, library_path: Optional[Path] = None):
        """Initialize the workflow library.
        
        Args:
            library_path: Path to workflow library directory.
                         Defaults to examples/workflows in project root.
        """
        if library_path is None:
            # Find project root
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    library_path = current / "examples" / "workflows"
                    break
                current = current.parent
            else:
                library_path = Path.cwd() / "examples" / "workflows"
        
        self.library_path = Path(library_path)
        self._metadata_cache: Dict[str, WorkflowMetadata] = {}
        self._workflows_cache: Dict[str, Dict[str, Any]] = {}
        
    def discover_workflows(self) -> List[WorkflowMetadata]:
        """Discover all workflows in the library.
        
        Returns:
            List of workflow metadata objects.
        """
        workflows = []
        
        if not self.library_path.exists():
            logger.warning(f"Workflow library not found at {self.library_path}")
            return workflows
        
        for yaml_file in self.library_path.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    workflow_data = yaml.safe_load(f)
                
                metadata = WorkflowMetadata.from_workflow(workflow_data)
                metadata.created_at = datetime.fromtimestamp(
                    yaml_file.stat().st_ctime
                ).isoformat()
                metadata.updated_at = datetime.fromtimestamp(
                    yaml_file.stat().st_mtime
                ).isoformat()
                
                workflows.append(metadata)
                self._metadata_cache[metadata.name] = metadata
                self._workflows_cache[metadata.name] = workflow_data
                
            except Exception as e:
                logger.error(f"Error loading workflow {yaml_file}: {e}")
        
        return workflows
    
    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow by name.
        
        Args:
            name: Workflow name.
            
        Returns:
            Workflow data or None if not found.
        """
        # Check cache first
        if name in self._workflows_cache:
            return self._workflows_cache[name]
        
        # Try to load from file
        workflow_file = self.library_path / f"{name}.yaml"
        if workflow_file.exists():
            try:
                with open(workflow_file, 'r') as f:
                    workflow_data = yaml.safe_load(f)
                self._workflows_cache[name] = workflow_data
                return workflow_data
            except Exception as e:
                logger.error(f"Error loading workflow {name}: {e}")
        
        return None
    
    def get_metadata(self, name: str) -> Optional[WorkflowMetadata]:
        """Get metadata for a specific workflow.
        
        Args:
            name: Workflow name.
            
        Returns:
            Workflow metadata or None if not found.
        """
        if name not in self._metadata_cache:
            workflow = self.get_workflow(name)
            if workflow:
                self._metadata_cache[name] = WorkflowMetadata.from_workflow(workflow)
        
        return self._metadata_cache.get(name)
    
    def search_workflows(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[WorkflowMetadata]:
        """Search workflows by query, category, or tags.
        
        Args:
            query: Text to search in name and description.
            category: Filter by category.
            tags: Filter by tags (any match).
            
        Returns:
            List of matching workflow metadata.
        """
        # Ensure cache is populated
        if not self._metadata_cache:
            self.discover_workflows()
        
        results = list(self._metadata_cache.values())
        
        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                w for w in results
                if query_lower in w.name.lower() or 
                   query_lower in w.description.lower()
            ]
        
        # Filter by category
        if category:
            results = [w for w in results if w.category == category]
        
        # Filter by tags
        if tags:
            results = [
                w for w in results
                if any(tag in w.tags for tag in tags)
            ]
        
        return results
    
    def get_categories(self) -> List[str]:
        """Get all available workflow categories.
        
        Returns:
            List of category names.
        """
        if not self._metadata_cache:
            self.discover_workflows()
        
        categories = set()
        for metadata in self._metadata_cache.values():
            categories.add(metadata.category)
        
        return sorted(list(categories))
    
    def get_all_tags(self) -> List[str]:
        """Get all tags used across workflows.
        
        Returns:
            List of tag names.
        """
        if not self._metadata_cache:
            self.discover_workflows()
        
        tags = set()
        for metadata in self._metadata_cache.values():
            tags.update(metadata.tags)
        
        return sorted(list(tags))
    
    def validate_workflow(self, name: str) -> List[str]:
        """Validate a workflow for completeness and correctness.
        
        Args:
            name: Workflow name to validate.
            
        Returns:
            List of validation errors (empty if valid).
        """
        errors = []
        
        workflow = self.get_workflow(name)
        if not workflow:
            return [f"Workflow '{name}' not found"]
        
        # Required fields
        required_fields = ["name", "description", "version", "steps"]
        for field in required_fields:
            if field not in workflow:
                errors.append(f"Missing required field: {field}")
        
        # Validate steps
        steps = workflow.get("steps", [])
        if not steps:
            errors.append("Workflow must have at least one step")
        else:
            for i, step in enumerate(steps):
                if "name" not in step:
                    errors.append(f"Step {i} missing 'name' field")
                if "tool" not in step:
                    errors.append(f"Step {i} missing 'tool' field")
        
        # Validate parameters
        params = workflow.get("parameters", {})
        for param_name, param_def in params.items():
            if "type" not in param_def:
                errors.append(f"Parameter '{param_name}' missing type")
            
            # Check enum values
            if "enum" in param_def and "default" in param_def:
                if param_def["default"] not in param_def["enum"]:
                    errors.append(
                        f"Parameter '{param_name}' default value not in enum"
                    )
        
        return errors
    
    def generate_documentation(self, name: str) -> str:
        """Generate detailed documentation for a workflow.
        
        Args:
            name: Workflow name.
            
        Returns:
            Markdown documentation string.
        """
        workflow = self.get_workflow(name)
        metadata = self.get_metadata(name)
        
        if not workflow or not metadata:
            return f"# Workflow '{name}' not found"
        
        # Generate documentation sections
        sections = [
            self._generate_header_section(workflow, metadata),
            self._generate_prerequisites_section(metadata),
            self._generate_parameters_section(workflow),
            self._generate_steps_section(workflow),
            self._generate_rollback_section(workflow),
            self._generate_usage_examples_section(name, workflow)
        ]
        
        return "".join(sections)
    
    # ========================================================================
    # Helper Methods for generate_documentation
    # ========================================================================
    
    def _generate_header_section(self, workflow: Dict[str, Any], metadata: WorkflowMetadata) -> str:
        """Generate the header section of documentation.
        
        Args:
            workflow: Workflow definition
            metadata: Workflow metadata
            
        Returns:
            Header section markdown
        """
        return f"""# {workflow['name']}

{workflow['description']}

**Version:** {workflow['version']}  
**Category:** {metadata.category}  
**Tags:** {', '.join(metadata.tags) if metadata.tags else 'None'}  

"""
    
    def _generate_prerequisites_section(self, metadata: WorkflowMetadata) -> str:
        """Generate the prerequisites section.
        
        Args:
            metadata: Workflow metadata
            
        Returns:
            Prerequisites section markdown
        """
        tools_list = chr(10).join(f"- {tool}" for tool in metadata.required_tools) if metadata.required_tools else "None"
        env_list = chr(10).join(f"- `{env}`" for env in metadata.required_env) if metadata.required_env else "None"
        
        return f"""## Prerequisites

### Required Tools
{tools_list}

### Required Environment Variables
{env_list}

"""
    
    def _generate_parameters_section(self, workflow: Dict[str, Any]) -> str:
        """Generate the parameters section.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            Parameters section markdown
        """
        doc = "## Parameters\n\n"
        params = workflow.get("parameters", {})
        
        if not params:
            return doc + "This workflow has no configurable parameters.\n\n"
        
        for param_name, param_def in params.items():
            doc += self._format_parameter_doc(param_name, param_def)
        
        return doc
    
    def _format_parameter_doc(self, param_name: str, param_def: Dict[str, Any]) -> str:
        """Format documentation for a single parameter.
        
        Args:
            param_name: Parameter name
            param_def: Parameter definition
            
        Returns:
            Formatted parameter documentation
        """
        required = param_def.get("required", False)
        default = param_def.get("default", "N/A")
        param_type = param_def.get("type", "string")
        
        doc = f"""### {param_name}
- **Type:** {param_type}
- **Required:** {"Yes" if required else "No"}
- **Default:** `{default}`
- **Description:** {param_def.get("description", "No description")}
"""
        
        if "enum" in param_def:
            doc += f"- **Allowed values:** {', '.join(f'`{v}`' for v in param_def['enum'])}\n"
        
        doc += "\n"
        return doc
    
    def _generate_steps_section(self, workflow: Dict[str, Any]) -> str:
        """Generate the workflow steps section.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            Steps section markdown
        """
        doc = "## Workflow Steps\n\n"
        steps = workflow.get("steps", [])
        
        for i, step in enumerate(steps, 1):
            doc += self._format_step_doc(i, step)
        
        return doc
    
    def _format_step_doc(self, index: int, step: Dict[str, Any]) -> str:
        """Format documentation for a single step.
        
        Args:
            index: Step number
            step: Step definition
            
        Returns:
            Formatted step documentation
        """
        doc = f"""### {index}. {step['name']}
- **Tool:** `{step['tool']}`
- **Description:** {step.get('description', 'No description')}
"""
        if "when" in step:
            doc += f"- **Condition:** `{step['when']}`\n"
        if "timeout" in step:
            doc += f"- **Timeout:** {step['timeout']} seconds\n"
        doc += "\n"
        
        return doc
    
    def _generate_rollback_section(self, workflow: Dict[str, Any]) -> str:
        """Generate the rollback section if applicable.
        
        Args:
            workflow: Workflow definition
            
        Returns:
            Rollback section markdown or empty string
        """
        if "rollback" not in workflow:
            return ""
        
        doc = "## Rollback Procedures\n\n"
        doc += "If the workflow fails, the following rollback steps will be executed:\n\n"
        
        for i, step in enumerate(workflow["rollback"], 1):
            doc += f"{i}. **{step['name']}** - {step.get('description', 'No description')}\n"
        
        doc += "\n"
        return doc
    
    def _generate_usage_examples_section(self, name: str, workflow: Dict[str, Any]) -> str:
        """Generate the usage examples section.
        
        Args:
            name: Workflow name
            workflow: Workflow definition
            
        Returns:
            Usage examples section markdown
        """
        doc = f"""## Usage Examples

### Basic Usage
```bash
agtos workflow run {name}
```

"""
        
        # Add parameter examples if applicable
        params = workflow.get("parameters", {})
        if params:
            doc += self._generate_parameter_examples(name, params)
        
        return doc
    
    def _generate_parameter_examples(self, name: str, params: Dict[str, Any]) -> str:
        """Generate parameter usage examples.
        
        Args:
            name: Workflow name
            params: Parameters dictionary
            
        Returns:
            Parameter examples markdown
        """
        doc = "### With Parameters\n```bash\n"
        example_params = []
        
        for param_name, param_def in params.items():
            example_value = self._get_example_value(param_def)
            example_params.append(f"--param {param_name}={example_value}")
        
        doc += f"agtos workflow run {name} \\\n  "
        doc += " \\\n  ".join(example_params)
        doc += "\n```\n"
        
        return doc
    
    def _get_example_value(self, param_def: Dict[str, Any]) -> str:
        """Get an example value for a parameter.
        
        Args:
            param_def: Parameter definition
            
        Returns:
            Example value string
        """
        if "default" in param_def and param_def["default"]:
            return param_def["default"]
        elif "enum" in param_def:
            return param_def["enum"][0]
        else:
            return "value"
    
    def export_catalog(self, output_path: Path) -> None:
        """Export a catalog of all workflows.
        
        Args:
            output_path: Path to write catalog file.
        """
        workflows = self.discover_workflows()
        
        catalog = {
            "generated_at": datetime.now().isoformat(),
            "total_workflows": len(workflows),
            "categories": self.get_categories(),
            "workflows": []
        }
        
        for metadata in workflows:
            catalog["workflows"].append({
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "category": metadata.category,
                "tags": metadata.tags,
                "required_tools": metadata.required_tools,
                "required_env": metadata.required_env
            })
        
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Exported workflow catalog to {output_path}")


# Singleton instance
_library_instance: Optional[WorkflowLibrary] = None


def get_library() -> WorkflowLibrary:
    """Get the singleton workflow library instance.
    
    AI_CONTEXT: Provides a single point of access to the workflow library,
    ensuring consistent caching across the application.
    """
    global _library_instance
    if _library_instance is None:
        _library_instance = WorkflowLibrary()
    return _library_instance