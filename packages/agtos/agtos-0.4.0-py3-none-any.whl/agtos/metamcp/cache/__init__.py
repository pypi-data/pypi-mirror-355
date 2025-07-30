"""Caching layer for Meta-MCP Server.

AI_CONTEXT:
    This package provides intelligent caching to improve performance
    by avoiding redundant calls to downstream services.
"""

from .manager import CacheManager
from .strategies import CacheStrategy, DefaultStrategy

__all__ = ["CacheManager", "CacheStrategy", "DefaultStrategy"]