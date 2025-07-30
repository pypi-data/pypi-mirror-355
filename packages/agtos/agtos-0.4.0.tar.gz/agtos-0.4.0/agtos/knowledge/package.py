"""Package knowledge acquisition from PyPI and npm registries.

This module handles discovery and knowledge extraction for packages from various
package registries like PyPI (Python) and npm (Node.js). It retrieves package
metadata, documentation, and identifies CLI tools and dependencies.

Key Features:
- PyPI package information retrieval
- npm package information retrieval  
- GitHub README fetching for documentation
- Automatic package type detection
- CLI tool discovery in packages
- Comprehensive package metadata extraction

The PackageKnowledge class provides methods to:
1. Get package info from PyPI including version, dependencies, and metadata
2. Get package info from npm including binaries and repository details
3. Fetch README files from GitHub repositories
4. Discover package knowledge comprehensively with caching

Example Usage:
    >>> from agtos.knowledge.package import PackageKnowledge
    >>> pkg = PackageKnowledge()
    >>> 
    >>> # Get Python package info
    >>> pypi_info = pkg.get_pypi_info("requests")
    >>> print(pypi_info["version"])
    >>> 
    >>> # Get npm package info
    >>> npm_info = pkg.get_npm_info("express")
    >>> print(npm_info["bin"])
    >>> 
    >>> # Comprehensive discovery with auto-detection
    >>> knowledge = pkg.discover_package_knowledge("fastapi")
    >>> print(knowledge["type"])  # "python"

The discovered knowledge is cached in the knowledge store for future use
with a 30-day TTL to avoid repeated API calls.
"""
import re
import requests
from typing import Dict, List, Any, Optional

from ..knowledge_store import get_knowledge_store


class PackageKnowledge:
    """Acquire knowledge about packages from various sources."""
    
    def __init__(self):
        self.store = get_knowledge_store()
    
    def get_pypi_info(self, package_name: str) -> Dict[str, Any]:
        """Get package information from PyPI."""
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{package_name}/json",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                info = data.get("info", {})
                
                return {
                    "name": package_name,
                    "version": info.get("version", ""),
                    "summary": info.get("summary", ""),
                    "description": info.get("description", ""),
                    "author": info.get("author", ""),
                    "license": info.get("license", ""),
                    "home_page": info.get("home_page", ""),
                    "docs_url": info.get("docs_url") or info.get("project_urls", {}).get("Documentation", ""),
                    "source_url": info.get("project_urls", {}).get("Source", ""),
                    "keywords": info.get("keywords", "").split(),
                    "classifiers": info.get("classifiers", []),
                    "requires_python": info.get("requires_python", ""),
                    "dependencies": list(data.get("requires_dist", []) or [])
                }
        except:
            pass
        return None
    
    def get_npm_info(self, package_name: str) -> Dict[str, Any]:
        """Get package information from npm."""
        try:
            response = requests.get(
                f"https://registry.npmjs.org/{package_name}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                latest = data.get("dist-tags", {}).get("latest", "")
                version_data = data.get("versions", {}).get(latest, {})
                
                return {
                    "name": package_name,
                    "version": latest,
                    "description": data.get("description", ""),
                    "author": data.get("author", ""),
                    "license": data.get("license", ""),
                    "homepage": data.get("homepage", ""),
                    "repository": data.get("repository", {}).get("url", ""),
                    "keywords": data.get("keywords", []),
                    "dependencies": list(version_data.get("dependencies", {}).keys()),
                    "main": version_data.get("main", ""),
                    "bin": version_data.get("bin", {})
                }
        except:
            pass
        return None
    
    def get_github_readme(self, repo_url: str) -> Optional[str]:
        """Fetch README from GitHub repository."""
        # Extract owner and repo from URL
        match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            return None
        
        owner, repo = match.groups()
        repo = repo.rstrip('.git')
        
        # Try different README formats
        readme_names = ["README.md", "README.rst", "README.txt", "README"]
        
        for readme in readme_names:
            try:
                response = requests.get(
                    f"https://raw.githubusercontent.com/{owner}/{repo}/main/{readme}",
                    timeout=10
                )
                if response.status_code == 200:
                    return response.text
                
                # Try master branch
                response = requests.get(
                    f"https://raw.githubusercontent.com/{owner}/{repo}/master/{readme}",
                    timeout=10
                )
                if response.status_code == 200:
                    return response.text
            except:
                continue
        
        return None
    
    def discover_package_knowledge(self, package_name: str, package_type: str = "auto") -> Dict[str, Any]:
        """Comprehensive package discovery across multiple sources."""
        knowledge = {
            "package": package_name,
            "type": package_type,
            "discovered": False,
            "info": None,
            "readme": None,
            "cli_tools": [],
            "api_endpoints": []
        }
        
        # Auto-detect package type if needed
        if package_type == "auto":
            # Try Python first
            pypi_info = self.get_pypi_info(package_name)
            if pypi_info:
                package_type = "python"
                knowledge["info"] = pypi_info
            else:
                # Try npm
                npm_info = self.get_npm_info(package_name)
                if npm_info:
                    package_type = "node"
                    knowledge["info"] = npm_info
        elif package_type == "python":
            knowledge["info"] = self.get_pypi_info(package_name)
        elif package_type == "node":
            knowledge["info"] = self.get_npm_info(package_name)
        
        if knowledge["info"]:
            knowledge["discovered"] = True
            knowledge["type"] = package_type
            
            # Get README if available
            repo_url = knowledge["info"].get("source_url") or knowledge["info"].get("repository") or knowledge["info"].get("home_page")
            if repo_url and "github.com" in repo_url:
                knowledge["readme"] = self.get_github_readme(repo_url)
            
            # Look for CLI tools in npm packages
            if package_type == "node" and knowledge["info"].get("bin"):
                for cmd_name in knowledge["info"]["bin"]:
                    knowledge["cli_tools"].append(cmd_name)
            
            # Store in cache
            self.store.store(
                type="package",
                name=package_name,
                data=knowledge,
                source=f"{package_type}_registry",
                ttl_hours=720  # 30 days
            )
        
        return knowledge