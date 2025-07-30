"""Cache manager for Meta-MCP Server.

AI_CONTEXT:
    This module implements the caching layer that stores results from
    downstream services to improve performance. It provides:
    - Multiple cache backends (memory, disk)
    - Configurable caching strategies per tool
    - Automatic cache invalidation
    - Cache statistics and monitoring
"""

import hashlib
import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

from ..types import CacheEntry, CacheError
from .strategies import CacheStrategy, DefaultStrategy

logger = logging.getLogger(__name__)


class CacheManager:
    """Main cache manager for Meta-MCP.
    
    AI_CONTEXT:
        The CacheManager coordinates different cache backends and strategies.
        It determines what to cache, where to cache it, and for how long.
        Key features:
        - Automatic key generation from tool name and arguments
        - Strategy-based caching decisions
        - Multiple storage backends
        - Cache statistics tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cache manager.
        
        Args:
            config: Cache configuration including:
                - memory_max_size: Maximum memory cache size
                - disk_path: Path for disk cache
                - default_ttl: Default TTL in seconds
                - enable_memory: Enable memory cache
                - enable_disk: Enable disk cache
        """
        self.config = config or {}
        
        # Cache backends
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_cache_path = self.config.get("disk_path", "~/.agtos/cache")
        
        # Strategies
        self.strategies: Dict[str, CacheStrategy] = {}
        self.default_strategy = DefaultStrategy()
        
        # Configuration
        self.memory_max_size = self.config.get("memory_max_size", 100 * 1024 * 1024)  # 100MB
        self.default_ttl = self.config.get("default_ttl", 300)  # 5 minutes
        self.enable_memory = self.config.get("enable_memory", True)
        self.enable_disk = self.config.get("enable_disk", False)
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_size": 0
        }
    
    def generate_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Generate cache key from tool name and arguments.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Cache key string
        """
        # Create stable string representation
        key_data = {
            "tool": tool_name,
            "args": self._normalize_args(args)
        }
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Generate hash for compact key
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Try memory cache first
        if self.enable_memory and key in self.memory_cache:
            entry = self.memory_cache[key]
            if not entry.is_expired():
                entry.hit_count += 1
                self.stats["hits"] += 1
                logger.debug(f"Memory cache hit for key: {key}")
                return entry.value
            else:
                # Remove expired entry
                del self.memory_cache[key]
                self.stats["evictions"] += 1
        
        # Try disk cache
        if self.enable_disk:
            value = await self._get_from_disk(key)
            if value is not None:
                self.stats["hits"] += 1
                
                # Promote to memory cache
                if self.enable_memory:
                    await self._add_to_memory(key, value)
                
                return value
        
        self.stats["misses"] += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        tool_name: Optional[str] = None,
        ttl: Optional[int] = None
    ):
        """Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            tool_name: Tool name for strategy lookup
            ttl: Time to live in seconds (overrides strategy)
        """
        # Get caching strategy
        strategy = self.strategies.get(tool_name, self.default_strategy)
        
        # Check if we should cache
        if not strategy.should_cache(value):
            logger.debug(f"Strategy rejected caching for {tool_name}")
            return
        
        # Determine TTL
        if ttl is None:
            ttl = strategy.get_ttl(value)
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=datetime.now().timestamp() + ttl if ttl > 0 else None
        )
        
        # Store in appropriate caches
        if self.enable_memory and strategy.use_memory_cache:
            await self._add_to_memory(key, value, ttl)
        
        if self.enable_disk and strategy.use_disk_cache:
            await self._add_to_disk(key, value, ttl)
        
        logger.debug(f"Cached value for key: {key} (ttl: {ttl}s)")
    
    def configure_tool_cache(
        self,
        tool_name: str,
        strategy: CacheStrategy
    ):
        """Configure caching strategy for a specific tool.
        
        Args:
            tool_name: Name of the tool
            strategy: Caching strategy to use
        """
        logger.info(f"Configuring cache strategy for {tool_name}")
        self.strategies[tool_name] = strategy
    
    async def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries.
        
        Args:
            pattern: Optional pattern to match keys (prefix match)
        """
        if pattern:
            # Invalidate matching keys
            keys_to_remove = [
                k for k in self.memory_cache.keys()
                if k.startswith(pattern)
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]
                self.stats["evictions"] += 1
            
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
        else:
            # Clear all
            count = len(self.memory_cache)
            self.memory_cache.clear()
            self.stats["evictions"] += count
            logger.info("Cleared entire cache")
    
    async def flush(self):
        """Flush all caches to disk if applicable."""
        if self.enable_disk:
            # TODO: Implement disk flush
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / max(total_requests, 1)
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"],
            "memory_entries": len(self.memory_cache),
            "memory_size_bytes": self.stats["memory_size"],
            "strategies_configured": len(self.strategies)
        }
    
    def _normalize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize arguments for consistent key generation.
        
        Handles special cases like:
        - Sorting dict keys
        - Converting sets to sorted lists
        - Handling None values
        """
        if not isinstance(args, dict):
            return args
        
        normalized = {}
        for key, value in sorted(args.items()):
            if isinstance(value, dict):
                normalized[key] = self._normalize_args(value)
            elif isinstance(value, (list, tuple)):
                normalized[key] = [self._normalize_args(v) for v in value]
            elif isinstance(value, set):
                normalized[key] = sorted(list(value))
            else:
                normalized[key] = value
        
        return normalized
    
    async def _add_to_memory(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Add entry to memory cache."""
        # Simple size estimation (not accurate but good enough)
        import sys
        size = sys.getsizeof(value)
        
        # Check if we need to evict entries
        while (self.stats["memory_size"] + size > self.memory_max_size
               and len(self.memory_cache) > 0):
            # Evict oldest entry (simple LRU)
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].created_at
            )
            evicted = self.memory_cache.pop(oldest_key)
            self.stats["memory_size"] -= sys.getsizeof(evicted.value)
            self.stats["evictions"] += 1
        
        # Add new entry
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=(
                datetime.now().timestamp() + (ttl or self.default_ttl)
                if ttl != 0 else None
            ),
            size_bytes=size
        )
        
        self.memory_cache[key] = entry
        self.stats["memory_size"] += size
    
    async def _get_from_disk(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        # TODO: Implement disk cache
        return None
    
    async def _add_to_disk(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Add entry to disk cache."""
        # TODO: Implement disk cache
        pass