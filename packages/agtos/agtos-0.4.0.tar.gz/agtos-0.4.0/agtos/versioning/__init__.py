"""Tool versioning and dependency management system for agtOS.

This package provides sophisticated version control for user-created tools,
enabling safe evolution, dependency tracking, and intelligent migration.

AI_CONTEXT:
    This system allows tools to evolve over time without breaking existing
    workflows. It tracks dependencies, manages multiple versions, and provides
    migration assistance - all through natural language commands.
"""

from .version_manager import VersionManager, Version
from .dependency_tracker import DependencyTracker, DependencyInfo
from .migration_assistant import MigrationAssistant, MigrationPlan
from .update_notifier import UpdateNotifier, UpdateRecommendation

__all__ = [
    'VersionManager',
    'Version',
    'DependencyTracker', 
    'DependencyInfo',
    'MigrationAssistant',
    'MigrationPlan',
    'UpdateNotifier',
    'UpdateRecommendation'
]