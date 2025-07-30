"""Project registry management using YAML."""
import yaml
from pathlib import Path
from typing import Dict, Optional

class ProjectStore:
    """Manages project registry for agtos."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".agtos"
        self.config_file = self.config_dir / "projects.yml"
        self._ensure_config()
    
    def _ensure_config(self):
        """Ensure config directory and file exist with default general project."""
        self.config_dir.mkdir(exist_ok=True)
        
        if not self.config_file.exists():
            # Create default config with general project
            default_config = {
                "projects": {
                    "general": {
                        "path": str(Path.home() / "agtos-general"),
                        "agent": "claude"
                    }
                }
            }
            self.config_file.write_text(yaml.dump(default_config, default_flow_style=False))
            
            # Create default general directory
            general_dir = Path.home() / "agtos-general"
            general_dir.mkdir(exist_ok=True)
            
            # Create a helpful README in the general directory
            readme_content = """# agentctl General Workspace

This is your default workspace for quick AI agent sessions.

## Quick Start

1. Run `agentctl run` from anywhere to start here
2. Claude Code will open in this directory
3. Speak your commands naturally!

## Tips

- Store test files and experiments here
- Use `agentctl add myproject ~/path/to/project` to register specific projects
- Your API keys are securely managed by agentctl

Happy coding with AI! 🚀
"""
            (general_dir / "README.md").write_text(readme_content)
    
    def _load_config(self) -> dict:
        """Load projects from YAML."""
        with open(self.config_file) as f:
            return yaml.safe_load(f) or {"projects": {}}
    
    def _save_config(self, config: dict):
        """Save projects to YAML."""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def add_project(self, slug: str, path: Path, agent: str = "claude"):
        """Add or update a project."""
        # Validate slug
        if not slug or not slug.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Project slug must be alphanumeric (hyphens and underscores allowed)")
        
        # Validate path
        if not path.exists():
            raise ValueError(f"Path {path} does not exist")
        
        # Validate agent
        if agent not in ["claude", "codex"]:
            raise ValueError("Agent must be either 'claude' or 'codex'")
        
        config = self._load_config()
        config["projects"][slug] = {
            "path": str(path),
            "agent": agent
        }
        self._save_config(config)
    
    def remove_project(self, slug: str):
        """Remove a project."""
        if slug == "general":
            raise ValueError("Cannot remove the default 'general' project")
        
        config = self._load_config()
        config["projects"].pop(slug, None)
        self._save_config(config)
    
    def get_project(self, slug: str) -> Optional[Dict]:
        """Get project details."""
        config = self._load_config()
        return config["projects"].get(slug)
    
    def list_projects(self) -> Dict:
        """List all projects."""
        config = self._load_config()
        return config["projects"]
    
    def update_project_agent(self, slug: str, agent: str):
        """Update the default agent for a project."""
        if agent not in ["claude", "codex"]:
            raise ValueError("Agent must be either 'claude' or 'codex'")
        
        config = self._load_config()
        if slug in config["projects"]:
            config["projects"][slug]["agent"] = agent
            self._save_config(config)
        else:
            raise ValueError(f"Project '{slug}' not found")