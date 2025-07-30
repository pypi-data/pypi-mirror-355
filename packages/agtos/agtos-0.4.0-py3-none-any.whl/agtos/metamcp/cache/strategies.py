"""Caching strategies for Meta-MCP Server.

AI_CONTEXT:
    This module defines different caching strategies that determine:
    - Whether a result should be cached
    - How long it should be cached (TTL)
    - Which cache backend to use (memory/disk)
    
    Strategies can be customized per tool or tool type.
"""

import re
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class CacheStrategy(ABC):
    """Base class for caching strategies.
    
    AI_CONTEXT:
        Strategies implement the logic for making caching decisions.
        They can inspect the tool name, arguments, and results to
        determine optimal caching behavior.
    """
    
    @abstractmethod
    def should_cache(self, value: Any) -> bool:
        """Determine if a value should be cached.
        
        Args:
            value: The value to potentially cache
            
        Returns:
            True if the value should be cached
        """
        pass
    
    @abstractmethod
    def get_ttl(self, value: Any) -> int:
        """Get TTL (time to live) for a cached value.
        
        Args:
            value: The value being cached
            
        Returns:
            TTL in seconds (0 means no expiration)
        """
        pass
    
    @property
    def use_memory_cache(self) -> bool:
        """Whether to use memory cache."""
        return True
    
    @property
    def use_disk_cache(self) -> bool:
        """Whether to use disk cache."""
        return False


class DefaultStrategy(CacheStrategy):
    """Default caching strategy.
    
    Conservative strategy that caches most results for a short time.
    """
    
    def should_cache(self, value: Any) -> bool:
        """Cache non-error results."""
        # Don't cache errors or None
        if value is None:
            return False
        
        # Don't cache if result indicates an error
        if isinstance(value, dict):
            if "error" in value or "errors" in value:
                return False
        
        return True
    
    def get_ttl(self, value: Any) -> int:
        """Default TTL of 5 minutes."""
        return 300


class ReadOnlyStrategy(CacheStrategy):
    """Strategy for read-only operations.
    
    Caches results for longer periods since data is unlikely to change.
    """
    
    def should_cache(self, value: Any) -> bool:
        """Cache all non-error results."""
        return value is not None
    
    def get_ttl(self, value: Any) -> int:
        """Cache for 1 hour."""
        return 3600
    
    @property
    def use_disk_cache(self) -> bool:
        """Also use disk cache for persistence."""
        return True


class WriteOperationStrategy(CacheStrategy):
    """Strategy for write operations.
    
    Never caches results from operations that modify state.
    """
    
    def should_cache(self, value: Any) -> bool:
        """Never cache write operations."""
        return False
    
    def get_ttl(self, value: Any) -> int:
        """Not applicable."""
        return 0


class ExpensiveOperationStrategy(CacheStrategy):
    """Strategy for expensive operations.
    
    Caches results aggressively to avoid repeated expensive calls.
    """
    
    def __init__(self, ttl: int = 1800):
        """Initialize with custom TTL.
        
        Args:
            ttl: Time to live in seconds (default: 30 minutes)
        """
        self.ttl = ttl
    
    def should_cache(self, value: Any) -> bool:
        """Cache all successful results."""
        return value is not None
    
    def get_ttl(self, value: Any) -> int:
        """Use configured TTL."""
        return self.ttl
    
    @property
    def use_disk_cache(self) -> bool:
        """Use disk cache for expensive results."""
        return True


class PatternBasedStrategy(CacheStrategy):
    """Strategy based on tool name patterns.
    
    Applies different caching rules based on regex patterns.
    """
    
    def __init__(self):
        """Initialize with default patterns."""
        self.patterns = [
            # Read operations - cache for longer
            (re.compile(r".*_(get|list|read|fetch|query).*"), 600),
            # Write operations - don't cache
            (re.compile(r".*_(create|update|delete|write|post|put).*"), 0),
            # Search operations - cache briefly
            (re.compile(r".*_(search|find).*"), 60),
        ]
        self.default_ttl = 300
    
    def add_pattern(self, pattern: str, ttl: int):
        """Add a custom pattern.
        
        Args:
            pattern: Regex pattern to match tool names
            ttl: TTL for matching tools
        """
        self.patterns.append((re.compile(pattern), ttl))
    
    def should_cache(self, value: Any) -> bool:
        """Cache based on TTL > 0."""
        return self.get_ttl(value) > 0
    
    def get_ttl(self, value: Any) -> int:
        """Get TTL based on pattern matching.
        
        Note: In practice, this would need the tool name,
        but for simplicity we use the default here.
        """
        # TODO: Pass tool name to strategy methods
        return self.default_ttl


class SizeBasedStrategy(CacheStrategy):
    """Strategy based on result size.
    
    Only caches results below a certain size threshold.
    """
    
    def __init__(self, max_size: int = 1024 * 1024):  # 1MB default
        """Initialize with size limit.
        
        Args:
            max_size: Maximum size in bytes to cache
        """
        self.max_size = max_size
    
    def should_cache(self, value: Any) -> bool:
        """Only cache if size is reasonable."""
        import sys
        
        try:
            size = sys.getsizeof(value)
            return size <= self.max_size
        except:
            # If we can't determine size, don't cache
            return False
    
    def get_ttl(self, value: Any) -> int:
        """Standard TTL for size-appropriate values."""
        return 300


class AdaptiveStrategy(CacheStrategy):
    """Adaptive strategy that learns from usage patterns.
    
    AI_CONTEXT:
        This advanced strategy tracks cache hit rates and adjusts
        its behavior based on actual usage patterns. It can:
        - Increase TTL for frequently accessed items
        - Decrease TTL for rarely accessed items
        - Disable caching for items that change frequently
    """
    
    def __init__(self):
        """Initialize adaptive strategy."""
        self.access_counts: Dict[str, int] = {}
        self.change_counts: Dict[str, int] = {}
        self.base_ttl = 300
        self.min_ttl = 60
        self.max_ttl = 3600
    
    def record_access(self, key: str):
        """Record that a cache key was accessed."""
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
    
    def record_change(self, key: str):
        """Record that a cached value changed."""
        self.change_counts[key] = self.change_counts.get(key, 0) + 1
    
    def should_cache(self, value: Any) -> bool:
        """Always cache initially to gather statistics."""
        return value is not None
    
    def get_ttl(self, value: Any) -> int:
        """Adapt TTL based on access patterns.
        
        Note: In practice, this would need the cache key.
        """
        # TODO: Implement adaptive TTL based on statistics
        return self.base_ttl


class CompositStrategy(CacheStrategy):
    """Combines multiple strategies with priority.
    
    Useful for complex caching policies that depend on multiple factors.
    """
    
    def __init__(self, strategies: List[CacheStrategy]):
        """Initialize with list of strategies.
        
        Args:
            strategies: List of strategies in priority order
        """
        self.strategies = strategies
    
    def should_cache(self, value: Any) -> bool:
        """All strategies must agree to cache."""
        return all(s.should_cache(value) for s in self.strategies)
    
    def get_ttl(self, value: Any) -> int:
        """Use minimum TTL from all strategies."""
        ttls = [s.get_ttl(value) for s in self.strategies]
        return min(ttls) if ttls else 0
    
    @property
    def use_memory_cache(self) -> bool:
        """Use memory if any strategy wants it."""
        return any(s.use_memory_cache for s in self.strategies)
    
    @property
    def use_disk_cache(self) -> bool:
        """Use disk if any strategy wants it."""
        return any(s.use_disk_cache for s in self.strategies)