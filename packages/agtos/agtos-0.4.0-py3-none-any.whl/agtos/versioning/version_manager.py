"""Version management for agtOS tools.

Handles semantic versioning, version comparisons, and version storage.

AI_CONTEXT:
    This is the core of the versioning system. It manages how tools are
    stored in versioned directories, handles version comparisons, and
    maintains the active version symlinks.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime


@dataclass
class Version:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int
    
    @classmethod
    def parse(cls, version_string: str) -> 'Version':
        """Parse a semantic version string."""
        # Handle version strings like "1.2.3" or "v1.2.3"
        version_string = version_string.lstrip('v')
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_string)
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3))
        )
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'Version') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __eq__(self, other: 'Version') -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __le__(self, other: 'Version') -> bool:
        return self < other or self == other
    
    def bump_major(self) -> 'Version':
        """Create new version with bumped major number."""
        return Version(self.major + 1, 0, 0)
    
    def bump_minor(self) -> 'Version':
        """Create new version with bumped minor number."""
        return Version(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> 'Version':
        """Create new version with bumped patch number."""
        return Version(self.major, self.minor, self.patch + 1)
    
    def is_compatible_with(self, other: 'Version') -> bool:
        """Check if this version is compatible with another (same major)."""
        return self.major == other.major


class VersionManager:
    """Manages tool versions and version resolution.
    
    AI_CONTEXT:
        This class handles all version-related operations including storing
        multiple versions, switching between them, and resolving version
        constraints. It maintains a file structure where each tool can have
        multiple versions stored separately.
    """
    
    def __init__(self, tools_dir: Path):
        """Initialize version manager.
        
        Args:
            tools_dir: Base directory for user tools
        """
        self.tools_dir = Path(tools_dir)
        self.versions_dir = self.tools_dir / "versions"
        self.active_dir = self.tools_dir / "active"
        
        # Create directories if they don't exist
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.active_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_version(self, version_string: str) -> Version:
        """Parse a semantic version string.
        
        Args:
            version_string: Version string like "1.2.3" or "v1.2.3"
            
        Returns:
            Version object
        """
        return Version.parse(version_string)
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings.
        
        Args:
            v1: First version string
            v2: Second version string
            
        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        version1 = Version.parse(v1)
        version2 = Version.parse(v2)
        
        if version1 < version2:
            return -1
        elif version1 > version2:
            return 1
        else:
            return 0
    
    def get_available_versions(self, tool_name: str) -> List[str]:
        """Get all available versions of a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of version strings, sorted newest first
        """
        tool_versions_dir = self.versions_dir / tool_name
        if not tool_versions_dir.exists():
            return []
        
        versions = []
        for version_dir in tool_versions_dir.iterdir():
            if version_dir.is_dir():
                try:
                    # Validate it's a proper version
                    Version.parse(version_dir.name)
                    versions.append(version_dir.name)
                except ValueError:
                    continue
        
        # Sort versions newest first
        versions.sort(key=lambda v: Version.parse(v), reverse=True)
        return versions
    
    def get_active_version(self, tool_name: str) -> Optional[str]:
        """Get the currently active version of a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Active version string or None if not found
        """
        active_link = self.active_dir / f"{tool_name}.json"
        if not active_link.exists():
            return None
        
        if active_link.is_symlink():
            # Resolve symlink and extract version from path
            target = active_link.resolve()
            # Path should be like .../versions/tool_name/1.2.3/metadata.json
            parts = target.parts
            if len(parts) >= 3 and parts[-3] == tool_name:
                return parts[-2]
        
        return None
    
    def activate_version(self, tool_name: str, version: str) -> bool:
        """Switch the active version of a tool.
        
        Args:
            tool_name: Name of the tool
            version: Version to activate
            
        Returns:
            True if successful
        """
        version_dir = self.versions_dir / tool_name / version
        if not version_dir.exists():
            raise ValueError(f"Version {version} of {tool_name} not found")
        
        # Remove existing symlinks
        for ext in ['.py', '.json']:
            link_path = self.active_dir / f"{tool_name}{ext}"
            if link_path.exists() or link_path.is_symlink():
                link_path.unlink()
        
        # Create new symlinks
        py_file = version_dir / f"{tool_name}.py"
        json_file = version_dir / "metadata.json"
        
        if py_file.exists():
            os.symlink(py_file, self.active_dir / f"{tool_name}.py")
        if json_file.exists():
            os.symlink(json_file, self.active_dir / f"{tool_name}.json")
        
        # Update version in metadata
        self._update_active_version_metadata(tool_name, version)
        
        return True
    
    def install_version(self, tool_name: str, version: str, 
                       tool_code: str, metadata: Dict[str, Any],
                       changelog: Optional[str] = None) -> Path:
        """Install a new version of a tool.
        
        Args:
            tool_name: Name of the tool
            version: Version string
            tool_code: Python code for the tool
            metadata: Tool metadata dictionary
            changelog: Optional changelog for this version
            
        Returns:
            Path to installed version directory
        """
        # Validate version
        Version.parse(version)
        
        # Create version directory
        version_dir = self.versions_dir / tool_name / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Save tool code
        py_file = version_dir / f"{tool_name}.py"
        py_file.write_text(tool_code)
        
        # Update metadata with version info
        metadata['version'] = version
        metadata['version_info'] = {
            'current': version,
            'installed_at': datetime.now().isoformat()
        }
        
        # Save metadata
        json_file = version_dir / "metadata.json"
        json_file.write_text(json.dumps(metadata, indent=2))
        
        # Save changelog if provided
        if changelog:
            changelog_file = version_dir / "changelog.md"
            changelog_file.write_text(changelog)
        
        # Activate if it's the first version or a patch update
        existing_versions = self.get_available_versions(tool_name)
        if len(existing_versions) == 1:  # First version
            self.activate_version(tool_name, version)
        else:
            # Check if this is a patch update to active version
            active = self.get_active_version(tool_name)
            if active:
                active_v = Version.parse(active)
                new_v = Version.parse(version)
                if (active_v.major == new_v.major and 
                    active_v.minor == new_v.minor and
                    new_v.patch > active_v.patch):
                    self.activate_version(tool_name, version)
        
        return version_dir
    
    def is_compatible(self, tool_name: str, version1: str, version2: str) -> bool:
        """Check if two versions are compatible (same major version).
        
        Args:
            tool_name: Name of the tool
            version1: First version
            version2: Second version
            
        Returns:
            True if versions are compatible
        """
        v1 = Version.parse(version1)
        v2 = Version.parse(version2)
        return v1.is_compatible_with(v2)
    
    def find_best_match(self, versions: List[str], constraint: str) -> Optional[str]:
        """Find the best matching version given a constraint.
        
        Args:
            versions: List of available versions
            constraint: Version constraint (e.g., "^2.1.0", "~1.2.3", ">=1.0.0")
            
        Returns:
            Best matching version or None
        """
        if not versions:
            return None
        
        # Handle different constraint formats
        if constraint == "*" or constraint == "latest":
            return versions[0]  # Assume sorted newest first
        
        if constraint.startswith("^"):
            # Compatible with version (same major)
            target = Version.parse(constraint[1:])
            compatible = [v for v in versions 
                         if Version.parse(v).is_compatible_with(target) and
                         Version.parse(v) >= target]
            return compatible[0] if compatible else None
        
        if constraint.startswith("~"):
            # Approximately equivalent (same major.minor)
            target = Version.parse(constraint[1:])
            compatible = [v for v in versions 
                         if Version.parse(v).major == target.major and
                         Version.parse(v).minor == target.minor and
                         Version.parse(v) >= target]
            return compatible[0] if compatible else None
        
        if constraint.startswith(">="):
            # Greater than or equal
            target = Version.parse(constraint[2:])
            compatible = [v for v in versions if Version.parse(v) >= target]
            return compatible[0] if compatible else None
        
        # Exact match
        return constraint if constraint in versions else None
    
    def get_version_metadata(self, tool_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific version.
        
        Args:
            tool_name: Name of the tool
            version: Version string
            
        Returns:
            Metadata dictionary or None
        """
        metadata_file = self.versions_dir / tool_name / version / "metadata.json"
        if not metadata_file.exists():
            return None
        
        return json.loads(metadata_file.read_text())
    
    def list_all_tools(self) -> List[Tuple[str, str, int]]:
        """List all tools with their active version and total versions.
        
        Returns:
            List of (tool_name, active_version, total_versions) tuples
        """
        tools = []
        
        if self.versions_dir.exists():
            for tool_dir in self.versions_dir.iterdir():
                if tool_dir.is_dir():
                    tool_name = tool_dir.name
                    versions = self.get_available_versions(tool_name)
                    active = self.get_active_version(tool_name)
                    tools.append((tool_name, active or "none", len(versions)))
        
        return sorted(tools)
    
    def _update_active_version_metadata(self, tool_name: str, version: str):
        """Update the active version tracking in dependency index."""
        index_file = self.tools_dir / "dependency_index.json"
        
        # Load or create index
        if index_file.exists():
            index = json.loads(index_file.read_text())
        else:
            index = {"active_versions": {}, "dependencies": {}}
        
        # Update active version
        index["active_versions"][tool_name] = {
            "version": version,
            "activated_at": datetime.now().isoformat()
        }
        
        # Save index
        index_file.write_text(json.dumps(index, indent=2))