"""Tool categorization system for Meta-MCP Server.

AI_CONTEXT:
    This module implements a comprehensive categorization system for organizing
    and discovering tools across all services. It provides:
    - Default categories based on common tool patterns
    - Dynamic categorization based on tool names and descriptions
    - User-defined custom categories and tags
    - Category-based filtering and search
    - Statistical analysis of tool distribution
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from .types import ToolSpec

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Default tool categories based on common patterns.
    
    AI_CONTEXT:
        These categories represent common groupings of tools across different
        services. They're designed to be intuitive for users while being
        broad enough to accommodate various tool types.
    """
    
    # Version Control & Development
    GIT = "Git Operations"
    VERSION_CONTROL = "Version Control"
    CODE_MANAGEMENT = "Code Management"
    
    # File & Data Management
    FILE_MANAGEMENT = "File Management"
    DATABASE = "Database Operations"
    DATA_PROCESSING = "Data Processing"
    
    # API & Integration
    API_INTEGRATION = "API Integrations"
    CLOUD_SERVICES = "Cloud Services"
    COMMUNICATION = "Communication & Messaging"
    
    # System & Infrastructure
    SYSTEM_UTILITIES = "System Utilities"
    CONTAINER_MANAGEMENT = "Container Management"
    INFRASTRUCTURE = "Infrastructure Management"
    MONITORING = "Monitoring & Logging"
    
    # Security & Authentication
    SECURITY = "Security & Authentication"
    SECRETS_MANAGEMENT = "Secrets Management"
    
    # AI & Machine Learning
    AI_ML = "AI & Machine Learning"
    LLM_TOOLS = "LLM Tools"
    
    # Documentation & Knowledge
    DOCUMENTATION = "Documentation"
    KNOWLEDGE_MANAGEMENT = "Knowledge Management"
    
    # Workflow & Automation
    WORKFLOW = "Workflow & Automation"
    CI_CD = "CI/CD & Deployment"
    
    # Miscellaneous
    UTILITIES = "General Utilities"
    UNCATEGORIZED = "Uncategorized"
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ToolCategory']:
        """Convert string to ToolCategory enum."""
        for category in cls:
            if category.value.lower() == value.lower():
                return category
        return None


@dataclass
class CategoryPattern:
    """Pattern for automatic categorization based on tool characteristics."""
    category: ToolCategory
    name_patterns: List[str] = field(default_factory=list)
    description_patterns: List[str] = field(default_factory=list)
    priority: int = 0  # Higher priority patterns are checked first
    
    def matches_tool(self, tool_name: str, tool_description: str) -> bool:
        """Check if tool matches this category pattern."""
        # Check name patterns
        for pattern in self.name_patterns:
            if re.search(pattern, tool_name, re.IGNORECASE):
                return True
        
        # Check description patterns
        for pattern in self.description_patterns:
            if re.search(pattern, tool_description, re.IGNORECASE):
                return True
        
        return False


@dataclass
class CategoryInfo:
    """Information about a tool category."""
    category: ToolCategory
    description: str
    icon: str = "📦"  # Default icon
    tools: Set[str] = field(default_factory=set)
    subcategories: Set[str] = field(default_factory=set)
    
    def add_tool(self, tool_name: str):
        """Add a tool to this category."""
        self.tools.add(tool_name)
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from this category."""
        self.tools.discard(tool_name)
    
    def tool_count(self) -> int:
        """Get number of tools in this category."""
        return len(self.tools)


class CategoryManager:
    """Manages tool categorization and organization.
    
    AI_CONTEXT:
        The CategoryManager is the central component for organizing tools
        into logical groups. It:
        1. Maintains mappings between tools and categories
        2. Supports automatic categorization based on patterns
        3. Allows custom category definitions
        4. Provides filtering and search capabilities
        5. Tracks category statistics and usage
    """
    
    def __init__(self):
        """Initialize the category manager."""
        # Core data structures
        self.categories: Dict[ToolCategory, CategoryInfo] = {}
        self.custom_categories: Dict[str, CategoryInfo] = {}
        self.tool_categories: Dict[str, Set[ToolCategory]] = defaultdict(set)
        self.tool_tags: Dict[str, Set[str]] = defaultdict(set)
        
        # Categorization patterns
        self.patterns: List[CategoryPattern] = []
        
        # Initialize default categories and patterns
        self._init_default_categories()
        self._init_categorization_patterns()
    
    def _init_default_categories(self):
        """Initialize default category definitions.
        
        AI_CONTEXT:
            Sets up the default categories with descriptions and icons.
            These provide a starting point for tool organization.
        """
        category_definitions = [
            (ToolCategory.GIT, "Git version control operations", "🔀"),
            (ToolCategory.VERSION_CONTROL, "Version control systems", "📝"),
            (ToolCategory.CODE_MANAGEMENT, "Code organization and management", "💻"),
            (ToolCategory.FILE_MANAGEMENT, "File system operations", "📁"),
            (ToolCategory.DATABASE, "Database operations and queries", "🗄️"),
            (ToolCategory.DATA_PROCESSING, "Data transformation and processing", "📊"),
            (ToolCategory.API_INTEGRATION, "External API integrations", "🔌"),
            (ToolCategory.CLOUD_SERVICES, "Cloud platform services", "☁️"),
            (ToolCategory.COMMUNICATION, "Messaging and communication tools", "💬"),
            (ToolCategory.SYSTEM_UTILITIES, "System-level utilities", "⚙️"),
            (ToolCategory.CONTAINER_MANAGEMENT, "Container and orchestration tools", "🐳"),
            (ToolCategory.INFRASTRUCTURE, "Infrastructure management", "🏗️"),
            (ToolCategory.MONITORING, "Monitoring and logging tools", "📈"),
            (ToolCategory.SECURITY, "Security and authentication", "🔐"),
            (ToolCategory.SECRETS_MANAGEMENT, "Secrets and credential management", "🔑"),
            (ToolCategory.AI_ML, "AI and machine learning tools", "🤖"),
            (ToolCategory.LLM_TOOLS, "Large language model tools", "🧠"),
            (ToolCategory.DOCUMENTATION, "Documentation tools", "📚"),
            (ToolCategory.KNOWLEDGE_MANAGEMENT, "Knowledge base management", "🎓"),
            (ToolCategory.WORKFLOW, "Workflow automation", "🔄"),
            (ToolCategory.CI_CD, "Continuous integration and deployment", "🚀"),
            (ToolCategory.UTILITIES, "General utility tools", "🛠️"),
            (ToolCategory.UNCATEGORIZED, "Uncategorized tools", "❓"),
        ]
        
        for category, description, icon in category_definitions:
            self.categories[category] = CategoryInfo(
                category=category,
                description=description,
                icon=icon
            )
    
    def _init_categorization_patterns(self):
        """Initialize patterns for automatic categorization.
        
        AI_CONTEXT:
            These patterns are used to automatically categorize tools based on
            their names and descriptions. Patterns are checked in priority order,
            with more specific patterns having higher priority.
        """
        self.patterns = [
            self._create_git_pattern(),
            self._create_file_management_pattern(),
            self._create_database_pattern(),
            self._create_api_integration_pattern(),
            self._create_cloud_services_pattern(),
            self._create_communication_pattern(),
            self._create_container_management_pattern(),
            self._create_security_pattern(),
            self._create_ai_ml_pattern(),
            self._create_documentation_pattern(),
            self._create_workflow_pattern(),
            self._create_ci_cd_pattern(),
            self._create_system_utilities_pattern(),
        ]
        
        # Sort patterns by priority (descending)
        self.patterns.sort(key=lambda p: p.priority, reverse=True)
    
    def _create_git_pattern(self) -> CategoryPattern:
        """Create pattern for Git operations."""
        return CategoryPattern(
            category=ToolCategory.GIT,
            name_patterns=[r"git_", r"cli__git__"],
            description_patterns=[r"git\s+(commit|push|pull|branch|merge|rebase|clone|checkout)", r"version control"],
            priority=10
        )
    
    def _create_file_management_pattern(self) -> CategoryPattern:
        """Create pattern for file management operations."""
        return CategoryPattern(
            category=ToolCategory.FILE_MANAGEMENT,
            name_patterns=[r"file_", r"fs_", r"filesystem_", r"read_", r"write_", r"create_", r"delete_"],
            description_patterns=[r"file\s+(system|operations|management)", r"read\s+files?", r"write\s+files?"],
            priority=8
        )
    
    def _create_database_pattern(self) -> CategoryPattern:
        """Create pattern for database operations."""
        return CategoryPattern(
            category=ToolCategory.DATABASE,
            name_patterns=[r"db_", r"database_", r"sql_", r"query_", r"postgres_", r"mysql_", r"mongo_"],
            description_patterns=[r"database", r"SQL", r"query", r"table", r"collection"],
            priority=8
        )
    
    def _create_api_integration_pattern(self) -> CategoryPattern:
        """Create pattern for API integrations."""
        return CategoryPattern(
            category=ToolCategory.API_INTEGRATION,
            name_patterns=[r"api_", r"rest_", r"graphql_", r"webhook_"],
            description_patterns=[r"API", r"REST", r"GraphQL", r"webhook", r"endpoint"],
            priority=7
        )
    
    def _create_cloud_services_pattern(self) -> CategoryPattern:
        """Create pattern for cloud services."""
        return CategoryPattern(
            category=ToolCategory.CLOUD_SERVICES,
            name_patterns=[r"aws_", r"azure_", r"gcp_", r"cloud_", r"s3_", r"lambda_"],
            description_patterns=[r"AWS", r"Azure", r"Google Cloud", r"cloud", r"S3", r"Lambda"],
            priority=7
        )
    
    def _create_communication_pattern(self) -> CategoryPattern:
        """Create pattern for communication tools."""
        return CategoryPattern(
            category=ToolCategory.COMMUNICATION,
            name_patterns=[r"slack_", r"discord_", r"email_", r"sms_", r"telegram_"],
            description_patterns=[r"Slack", r"Discord", r"email", r"SMS", r"messaging", r"notification"],
            priority=7
        )
    
    def _create_container_management_pattern(self) -> CategoryPattern:
        """Create pattern for container management."""
        return CategoryPattern(
            category=ToolCategory.CONTAINER_MANAGEMENT,
            name_patterns=[r"docker_", r"k8s_", r"kubernetes_", r"container_", r"pod_"],
            description_patterns=[r"Docker", r"Kubernetes", r"container", r"orchestration"],
            priority=7
        )
    
    def _create_security_pattern(self) -> CategoryPattern:
        """Create pattern for security tools."""
        return CategoryPattern(
            category=ToolCategory.SECURITY,
            name_patterns=[r"auth_", r"security_", r"encrypt_", r"decrypt_", r"oauth_"],
            description_patterns=[r"authentication", r"security", r"encryption", r"OAuth", r"JWT"],
            priority=6
        )
    
    def _create_ai_ml_pattern(self) -> CategoryPattern:
        """Create pattern for AI/ML tools."""
        return CategoryPattern(
            category=ToolCategory.AI_ML,
            name_patterns=[r"ai_", r"ml_", r"llm_", r"gpt_", r"claude_", r"openai_"],
            description_patterns=[r"AI", r"machine learning", r"LLM", r"GPT", r"Claude", r"OpenAI"],
            priority=6
        )
    
    def _create_documentation_pattern(self) -> CategoryPattern:
        """Create pattern for documentation tools."""
        return CategoryPattern(
            category=ToolCategory.DOCUMENTATION,
            name_patterns=[r"doc_", r"docs_", r"readme_", r"markdown_"],
            description_patterns=[r"documentation", r"readme", r"markdown", r"wiki"],
            priority=5
        )
    
    def _create_workflow_pattern(self) -> CategoryPattern:
        """Create pattern for workflow automation."""
        return CategoryPattern(
            category=ToolCategory.WORKFLOW,
            name_patterns=[r"workflow_", r"automation_", r"pipeline_", r"task_"],
            description_patterns=[r"workflow", r"automation", r"pipeline", r"orchestration"],
            priority=5
        )
    
    def _create_ci_cd_pattern(self) -> CategoryPattern:
        """Create pattern for CI/CD tools."""
        return CategoryPattern(
            category=ToolCategory.CI_CD,
            name_patterns=[r"ci_", r"cd_", r"deploy_", r"build_", r"jenkins_", r"github_actions_"],
            description_patterns=[r"CI/CD", r"continuous integration", r"deployment", r"build", r"Jenkins"],
            priority=5
        )
    
    def _create_system_utilities_pattern(self) -> CategoryPattern:
        """Create pattern for system utilities."""
        return CategoryPattern(
            category=ToolCategory.SYSTEM_UTILITIES,
            name_patterns=[r"system_", r"os_", r"process_", r"shell_", r"cli__"],
            description_patterns=[r"system", r"operating system", r"process", r"shell"],
            priority=3
        )
    
    def categorize_tool(self, tool: ToolSpec) -> Set[ToolCategory]:
        """Automatically categorize a tool based on its characteristics.
        
        Args:
            tool: The tool specification to categorize
            
        Returns:
            Set of categories the tool belongs to
        """
        categories = set()
        
        # Get tool details
        tool_name = tool.name
        tool_description = tool.description
        
        # Check each pattern
        for pattern in self.patterns:
            if pattern.matches_tool(tool_name, tool_description):
                categories.add(pattern.category)
        
        # If no categories matched, add to uncategorized
        if not categories:
            categories.add(ToolCategory.UNCATEGORIZED)
        
        # Update internal mappings
        self.tool_categories[tool_name] = categories
        for category in categories:
            if category in self.categories:
                self.categories[category].add_tool(tool_name)
        
        return categories
    
    def add_custom_category(self, name: str, description: str, icon: str = "📦"):
        """Add a custom category.
        
        Args:
            name: Category name
            description: Category description
            icon: Optional emoji icon
        """
        # Create a synthetic ToolCategory for custom categories
        custom_key = f"custom_{name.lower().replace(' ', '_')}"
        self.custom_categories[custom_key] = CategoryInfo(
            category=None,  # Custom categories don't have enum values
            description=description,
            icon=icon
        )
        logger.info(f"Added custom category: {name}")
    
    def assign_tool_to_category(self, tool_name: str, category: Union[ToolCategory, str]):
        """Manually assign a tool to a category.
        
        Args:
            tool_name: Name of the tool
            category: Category (enum or custom category name)
        """
        if isinstance(category, ToolCategory):
            self.tool_categories[tool_name].add(category)
            self.categories[category].add_tool(tool_name)
        else:
            # Handle custom category
            custom_key = f"custom_{category.lower().replace(' ', '_')}"
            if custom_key in self.custom_categories:
                self.tool_categories[tool_name].add(custom_key)
                self.custom_categories[custom_key].add_tool(tool_name)
            else:
                logger.warning(f"Unknown category: {category}")
    
    def remove_tool_from_category(self, tool_name: str, category: Union[ToolCategory, str]):
        """Remove a tool from a category.
        
        Args:
            tool_name: Name of the tool
            category: Category (enum or custom category name)
        """
        if isinstance(category, ToolCategory):
            self.tool_categories[tool_name].discard(category)
            self.categories[category].remove_tool(tool_name)
        else:
            custom_key = f"custom_{category.lower().replace(' ', '_')}"
            if custom_key in self.custom_categories:
                self.tool_categories[tool_name].discard(custom_key)
                self.custom_categories[custom_key].remove_tool(tool_name)
    
    def add_tag(self, tool_name: str, tag: str):
        """Add a tag to a tool.
        
        Args:
            tool_name: Name of the tool
            tag: Tag to add
        """
        self.tool_tags[tool_name].add(tag.lower())
    
    def remove_tag(self, tool_name: str, tag: str):
        """Remove a tag from a tool.
        
        Args:
            tool_name: Name of the tool
            tag: Tag to remove
        """
        self.tool_tags[tool_name].discard(tag.lower())
    
    def get_tool_categories(self, tool_name: str) -> Set[Union[ToolCategory, str]]:
        """Get all categories a tool belongs to.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Set of categories (both enum and custom)
        """
        categories = set(self.tool_categories.get(tool_name, set()))
        
        # Add any custom categories
        for custom_key, info in self.custom_categories.items():
            if tool_name in info.tools:
                categories.add(custom_key)
        
        return categories
    
    def get_tools_by_category(self, category: Union[ToolCategory, str]) -> Set[str]:
        """Get all tools in a category.
        
        Args:
            category: Category (enum or custom category name)
            
        Returns:
            Set of tool names
        """
        if isinstance(category, ToolCategory):
            if category in self.categories:
                return self.categories[category].tools.copy()
        else:
            custom_key = f"custom_{category.lower().replace(' ', '_')}"
            if custom_key in self.custom_categories:
                return self.custom_categories[custom_key].tools.copy()
        
        return set()
    
    def get_tools_by_tag(self, tag: str) -> Set[str]:
        """Get all tools with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            Set of tool names
        """
        tag_lower = tag.lower()
        return {
            tool_name
            for tool_name, tags in self.tool_tags.items()
            if tag_lower in tags
        }
    
    def search_tools(
        self,
        query: str,
        categories: Optional[List[Union[ToolCategory, str]]] = None,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """Search for tools based on query and filters.
        
        Args:
            query: Search query (matches tool names and descriptions)
            categories: Optional list of categories to filter by
            tags: Optional list of tags to filter by
            
        Returns:
            List of matching tool names
        """
        # Start with all tools
        matching_tools = set(self.tool_categories.keys())
        
        # Filter by categories if specified
        if categories:
            category_tools = set()
            for category in categories:
                category_tools.update(self.get_tools_by_category(category))
            matching_tools &= category_tools
        
        # Filter by tags if specified
        if tags:
            tag_tools = set()
            for tag in tags:
                tag_tools.update(self.get_tools_by_tag(tag))
            matching_tools &= tag_tools
        
        # Filter by query if specified
        if query:
            query_lower = query.lower()
            matching_tools = {
                tool for tool in matching_tools
                if query_lower in tool.lower()
            }
        
        return sorted(list(matching_tools))
    
    def get_all_categories(self) -> Dict[str, CategoryInfo]:
        """Get all categories (default and custom).
        
        Returns:
            Dictionary of category key to CategoryInfo
        """
        all_categories = {}
        
        # Add default categories
        for cat, info in self.categories.items():
            all_categories[cat.name] = info
        
        # Add custom categories
        all_categories.update(self.custom_categories)
        
        return all_categories
    
    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about tool distribution across categories.
        
        Returns:
            Dictionary of category statistics
        """
        stats = {}
        
        # Stats for default categories
        for category, info in self.categories.items():
            stats[category.value] = {
                "tool_count": info.tool_count(),
                "icon": info.icon,
                "description": info.description,
                "type": "default"
            }
        
        # Stats for custom categories
        for custom_key, info in self.custom_categories.items():
            name = custom_key.replace("custom_", "").replace("_", " ").title()
            stats[name] = {
                "tool_count": info.tool_count(),
                "icon": info.icon,
                "description": info.description,
                "type": "custom"
            }
        
        # Overall stats
        total_tools = len(self.tool_categories)
        categorized_tools = sum(1 for cats in self.tool_categories.values() if cats)
        
        stats["_summary"] = {
            "total_tools": total_tools,
            "categorized_tools": categorized_tools,
            "uncategorized_tools": total_tools - categorized_tools,
            "total_categories": len(self.categories) + len(self.custom_categories),
            "default_categories": len(self.categories),
            "custom_categories": len(self.custom_categories),
            "total_tags": len(set().union(*self.tool_tags.values()))
        }
        
        return stats
    
    def export_categorization(self) -> Dict[str, Any]:
        """Export the current categorization state.
        
        Returns:
            Dictionary containing full categorization data
        """
        return {
            "version": "1.0",
            "tool_categories": {
                tool: [cat.name if isinstance(cat, ToolCategory) else cat for cat in cats]
                for tool, cats in self.tool_categories.items()
            },
            "tool_tags": dict(self.tool_tags),
            "custom_categories": {
                key: {
                    "description": info.description,
                    "icon": info.icon,
                    "tools": list(info.tools)
                }
                for key, info in self.custom_categories.items()
            }
        }
    
    def import_categorization(self, data: Dict[str, Any]):
        """Import categorization data.
        
        Args:
            data: Categorization data to import
        """
        # Import tool categories
        for tool, categories in data.get("tool_categories", {}).items():
            for cat_name in categories:
                # Try to convert to enum
                category = ToolCategory.from_string(cat_name)
                if category:
                    self.assign_tool_to_category(tool, category)
                else:
                    # Treat as custom category
                    self.assign_tool_to_category(tool, cat_name)
        
        # Import tags
        for tool, tags in data.get("tool_tags", {}).items():
            self.tool_tags[tool] = set(tags)
        
        # Import custom categories
        for key, info in data.get("custom_categories", {}).items():
            name = key.replace("custom_", "").replace("_", " ").title()
            self.add_custom_category(name, info["description"], info.get("icon", "📦"))
            
            # Add tools to custom category
            for tool in info.get("tools", []):
                self.assign_tool_to_category(tool, name)
        
        logger.info("Imported categorization data")