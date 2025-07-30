"""Usage learning and pattern recognition for aliases.

This module implements learning algorithms that track how aliases are used
and adjusts their weights based on success patterns.

AI_CONTEXT:
    The learning system tracks:
    1. Which aliases are used most frequently
    2. Success/failure rates for different aliases
    3. Parameter patterns that work well
    4. Context patterns that lead to successful matches
    
    It then uses this information to:
    - Adjust alias weights for better future matching
    - Suggest new aliases based on usage patterns
    - Identify aliases that should be deprecated
    
    The learning is conservative - it requires significant evidence
    before making weight adjustments to avoid oscillation.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from .core import AliasRegistry, UsageStats

logger = logging.getLogger(__name__)


class AliasLearner:
    """Manages learning from alias usage patterns.
    
    AI_CONTEXT:
        This class extends the basic usage tracking in AliasRegistry
        with sophisticated learning algorithms. It:
        
        1. Tracks detailed usage patterns including context
        2. Analyzes success/failure rates
        3. Adjusts weights based on evidence
        4. Persists learning data for long-term improvement
        
        The learner is designed to be cautious - it requires multiple
        data points before making adjustments to avoid noise.
    """
    
    def __init__(self, registry: AliasRegistry):
        """Initialize the learner with a registry.
        
        Args:
            registry: The alias registry to enhance with learning
        """
        self.registry = registry
        self.learning_file = registry.config_dir / "alias_learning.json"
        self.learning_data: Dict[str, Dict[str, Any]] = {}
        
        # Load existing learning data
        self._load_learning_data()
        
        # Monkey-patch the registry's _record_usage method
        self._original_record_usage = registry._record_usage
        registry._record_usage = self._enhanced_record_usage
    
    def _enhanced_record_usage(self, command: str, tool_name: str, context: Dict[str, Any]):
        """Enhanced usage recording with detailed tracking.
        
        AI_CONTEXT:
            This method captures much more detail than the basic version:
            - Full command text for pattern analysis
            - Context at time of use
            - Timestamp for recency weighting
            - Session tracking for user behavior analysis
        """
        # Call original method
        self._original_record_usage(command, tool_name, context)
        
        # Add enhanced tracking
        if tool_name not in self.learning_data:
            self.learning_data[tool_name] = {
                "commands": [],
                "contexts": [],
                "timestamps": [],
                "success_count": 0,
                "failure_count": 0,
                "last_adjusted": None
            }
        
        data = self.learning_data[tool_name]
        data["commands"].append(command)
        data["contexts"].append(context)
        data["timestamps"].append(datetime.now().isoformat())
        
        # Keep only recent data (last 100 uses)
        if len(data["commands"]) > 100:
            data["commands"] = data["commands"][-100:]
            data["contexts"] = data["contexts"][-100:]
            data["timestamps"] = data["timestamps"][-100:]
    
    def record_success(self, tool_name: str):
        """Record that a tool execution was successful.
        
        Args:
            tool_name: The tool that was successfully executed
        """
        # Update basic stats
        if tool_name in self.registry.usage_stats:
            self.registry.usage_stats[tool_name].successful_uses += 1
        
        # Update learning data
        if tool_name in self.learning_data:
            self.learning_data[tool_name]["success_count"] += 1
            
        # Save periodically
        self._save_learning_data()
    
    def record_failure(self, tool_name: str):
        """Record that a tool execution failed.
        
        Args:
            tool_name: The tool that failed
        """
        if tool_name in self.learning_data:
            self.learning_data[tool_name]["failure_count"] += 1
            
        # Save periodically
        self._save_learning_data()
    
    def adjust_weights_from_usage(self):
        """Adjust alias weights based on usage patterns.
        
        AI_CONTEXT:
            This method implements the core learning algorithm:
            
            1. For each tool with sufficient data (>10 uses):
               - Calculate success rate
               - Check recency of use
               - Analyze context patterns
               
            2. Adjust weights for aliases:
               - High success rate (>80%): increase weight by 10%
               - Low success rate (<30%): decrease weight by 10%
               - Recent frequent use: small weight boost
               - Stale aliases: small weight penalty
               
            3. Constraints:
               - Weights stay in [0.1, 1.0] range
               - Maximum adjustment per cycle: 20%
               - Requires 24h between adjustments
        """
        now = datetime.now()
        adjustments_made = 0
        
        for tool_name, data in self.learning_data.items():
            # Skip if not ready for adjustment
            if not self._should_adjust_tool(tool_name, data, now):
                continue
            
            # Calculate performance metrics
            metrics = self._calculate_tool_metrics(data, now)
            
            # Adjust weights for this tool's aliases
            for mapping in self.registry.mappings:
                if mapping.tool_name == tool_name:
                    old_weight = mapping.weight
                    new_weight = self._calculate_new_weight(old_weight, metrics)
                    new_weight = self._apply_weight_constraints(old_weight, new_weight)
                    
                    # Apply adjustment
                    if new_weight != old_weight:
                        mapping.weight = new_weight
                        adjustments_made += 1
                        self._log_weight_adjustment(mapping.alias, tool_name, old_weight, new_weight)
            
            # Mark as adjusted
            data["last_adjusted"] = now.isoformat()
        
        # Save if adjustments were made
        if adjustments_made > 0:
            self._save_learning_data()
            logger.info(f"Made {adjustments_made} weight adjustments based on usage")
    
    def _should_adjust_tool(self, tool_name: str, data: Dict[str, Any], now: datetime) -> bool:
        """Check if a tool is ready for weight adjustment.
        
        Args:
            tool_name: Name of the tool
            data: Learning data for the tool
            now: Current timestamp
            
        Returns:
            True if the tool should be adjusted
            
        AI_CONTEXT:
            Ensures we have sufficient data and haven't adjusted recently.
            This prevents oscillation and ensures stable learning.
        """
        # Check for sufficient data
        total_uses = data["success_count"] + data["failure_count"]
        if total_uses < 10:
            return False
        
        # Check if adjusted recently (within 24 hours)
        if data.get("last_adjusted"):
            last_adjusted = datetime.fromisoformat(data["last_adjusted"])
            if now - last_adjusted < timedelta(hours=24):
                return False
        
        return True
    
    def _calculate_tool_metrics(self, data: Dict[str, Any], now: datetime) -> Dict[str, float]:
        """Calculate performance metrics for a tool.
        
        Args:
            data: Learning data for the tool
            now: Current timestamp
            
        Returns:
            Dictionary with success_rate and recency_factor
            
        AI_CONTEXT:
            These metrics drive the weight adjustment algorithm:
            - success_rate: How often the tool executes successfully
            - recency_factor: How recently the tool has been used
        """
        # Calculate success rate
        total_uses = data["success_count"] + data["failure_count"]
        success_rate = data["success_count"] / total_uses
        
        # Calculate recency - how many uses in last 7 days
        recent_uses = 0
        week_ago = now - timedelta(days=7)
        for timestamp in data["timestamps"]:
            if datetime.fromisoformat(timestamp) > week_ago:
                recent_uses += 1
        
        recency_factor = recent_uses / len(data["timestamps"]) if data["timestamps"] else 0
        
        return {
            "success_rate": success_rate,
            "recency_factor": recency_factor
        }
    
    def _calculate_new_weight(self, old_weight: float, metrics: Dict[str, float]) -> float:
        """Calculate new weight based on metrics.
        
        Args:
            old_weight: Current weight
            metrics: Performance metrics
            
        Returns:
            New calculated weight
            
        AI_CONTEXT:
            Applies the learning algorithm:
            - High success (>80%): +10% weight
            - Low success (<30%): -10% weight
            - Recent use (>50%): +5% weight
            - Stale use (<10%): -5% weight
        """
        new_weight = old_weight
        
        # Success rate adjustment
        if metrics["success_rate"] > 0.8:
            new_weight *= 1.1
        elif metrics["success_rate"] < 0.3:
            new_weight *= 0.9
        
        # Recency adjustment
        if metrics["recency_factor"] > 0.5:
            new_weight *= 1.05  # Small boost for recent use
        elif metrics["recency_factor"] < 0.1:
            new_weight *= 0.95  # Small penalty for stale
        
        return new_weight
    
    def _apply_weight_constraints(self, old_weight: float, new_weight: float) -> float:
        """Apply constraints to weight adjustments.
        
        Args:
            old_weight: Current weight
            new_weight: Proposed new weight
            
        Returns:
            Constrained weight value
            
        AI_CONTEXT:
            Ensures weights stay within bounds and changes are gradual:
            - Range: [0.1, 1.0]
            - Max change per adjustment: 20%
        """
        # Apply range constraints
        new_weight = max(0.1, min(1.0, new_weight))
        
        # Limit maximum change
        max_change = old_weight * 0.2
        if abs(new_weight - old_weight) > max_change:
            if new_weight > old_weight:
                new_weight = old_weight + max_change
            else:
                new_weight = old_weight - max_change
        
        return new_weight
    
    def _log_weight_adjustment(self, alias: str, tool_name: str, old_weight: float, new_weight: float):
        """Log a weight adjustment.
        
        Args:
            alias: The alias being adjusted
            tool_name: The tool name
            old_weight: Previous weight
            new_weight: New weight
        """
        logger.info(f"Adjusted weight for '{alias}' -> {tool_name}: "
                    f"{old_weight:.2f} -> {new_weight:.2f}")
    
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns to identify trends.
        
        Returns:
            Dictionary with analysis results
            
        AI_CONTEXT:
            This method provides insights that can be used to:
            - Suggest new aliases based on common commands
            - Identify problematic aliases with low success
            - Find context patterns that predict success
            - Recommend alias deprecation
        """
        analysis = {
            "most_used_tools": [],
            "high_success_aliases": [],
            "low_success_aliases": [],
            "context_patterns": {},
            "common_command_patterns": []
        }
        
        # Analyze different aspects of usage
        analysis["most_used_tools"] = self._analyze_most_used_tools()
        
        # Get alias success statistics
        alias_stats = self._calculate_alias_success_rates()
        
        # Categorize aliases by success rate
        high_success, low_success = self._categorize_aliases_by_success(alias_stats)
        analysis["high_success_aliases"] = high_success
        analysis["low_success_aliases"] = low_success
        
        # Analyze context patterns
        analysis["context_patterns"] = self._analyze_context_patterns()
        
        return analysis
    
    def _analyze_most_used_tools(self) -> List[Tuple[str, int]]:
        """Analyze and return the most frequently used tools.
        
        Returns:
            List of (tool_name, usage_count) tuples, sorted by usage
        """
        tool_uses = {}
        for tool_name, stats in self.registry.usage_stats.items():
            tool_uses[tool_name] = stats.total_uses
        
        # Sort by usage and return top 10
        sorted_tools = sorted(tool_uses.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools[:10]
    
    def _calculate_alias_success_rates(self) -> Dict[str, Dict[str, Any]]:
        """Calculate success rates for each alias.
        
        Returns:
            Dictionary mapping alias to stats (tool, success_rate, total_uses)
        """
        alias_stats = {}
        
        for mapping in self.registry.mappings:
            tool_name = mapping.tool_name
            if tool_name in self.learning_data:
                data = self.learning_data[tool_name]
                total = data["success_count"] + data["failure_count"]
                
                if total > 5:  # Minimum data requirement
                    success_rate = data["success_count"] / total
                    alias_stats[mapping.alias] = {
                        "tool": tool_name,
                        "success_rate": success_rate,
                        "total_uses": total
                    }
        
        return alias_stats
    
    def _categorize_aliases_by_success(
        self, 
        alias_stats: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Categorize aliases into high and low success groups.
        
        Args:
            alias_stats: Dictionary of alias statistics
            
        Returns:
            Tuple of (high_success_aliases, low_success_aliases)
        """
        high_success = []
        low_success = []
        
        for alias, stats in alias_stats.items():
            alias_info = {
                "alias": alias,
                "tool": stats["tool"],
                "success_rate": stats["success_rate"]
            }
            
            if stats["success_rate"] > 0.8:
                high_success.append(alias_info)
            elif stats["success_rate"] < 0.3:
                low_success.append(alias_info)
        
        return high_success, low_success
    
    def _analyze_context_patterns(self) -> Dict[str, Dict[str, int]]:
        """Analyze usage patterns by context.
        
        Returns:
            Dictionary mapping context types to usage statistics
        """
        context_success = {}
        
        for tool_name, data in self.learning_data.items():
            for context in data["contexts"]:
                # Extract context features
                project_type = context.get("project_type", "unknown")
                
                if project_type not in context_success:
                    context_success[project_type] = {"success": 0, "total": 0}
                
                context_success[project_type]["total"] += 1
                # Note: This is simplified - real implementation would track
                # success per individual context use
        
        return context_success
    
    def suggest_new_aliases(self) -> List[Dict[str, Any]]:
        """Suggest new aliases based on usage patterns.
        
        Returns:
            List of suggested aliases with explanations
            
        AI_CONTEXT:
            This method looks for patterns in commands that don't
            match existing aliases well, suggesting new aliases
            that would improve the user experience.
        """
        suggestions = []
        
        # Analyze commands that didn't match well
        for tool_name, data in self.learning_data.items():
            command_freq = {}
            for command in data["commands"]:
                # Skip if this command already has a good alias
                if self.registry.find_tool(command)[1] > 0.8:
                    continue
                
                # Count frequency
                command_lower = command.lower()
                command_freq[command_lower] = command_freq.get(command_lower, 0) + 1
            
            # Suggest aliases for frequent unmatched commands
            for command, count in command_freq.items():
                if count >= 3:  # Used at least 3 times
                    suggestions.append({
                        "suggested_alias": command,
                        "tool_name": tool_name,
                        "reason": f"Frequently used command ({count} times) with no good alias",
                        "suggested_weight": 0.8
                    })
        
        return suggestions[:10]  # Limit suggestions
    
    def _load_learning_data(self):
        """Load learning data from disk."""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    self.learning_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load learning data: {e}")
    
    def _save_learning_data(self):
        """Save learning data to disk."""
        try:
            self.registry.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")


# Module-level convenience functions
def enhance_registry_with_learning(registry: AliasRegistry) -> AliasLearner:
    """Enhance a registry with learning capabilities.
    
    Args:
        registry: The registry to enhance
        
    Returns:
        The AliasLearner instance
    """
    return AliasLearner(registry)


def record_tool_success(tool_name: str):
    """Record successful tool execution for learning."""
    from .core import get_registry
    registry = get_registry()
    
    # Get or create learner
    if not hasattr(registry, '_learner'):
        registry._learner = AliasLearner(registry)
    
    registry._learner.record_success(tool_name)


def record_tool_failure(tool_name: str):
    """Record failed tool execution for learning."""
    from .core import get_registry
    registry = get_registry()
    
    # Get or create learner
    if not hasattr(registry, '_learner'):
        registry._learner = AliasLearner(registry)
    
    registry._learner.record_failure(tool_name)