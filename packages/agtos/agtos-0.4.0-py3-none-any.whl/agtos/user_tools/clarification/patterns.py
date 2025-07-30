"""
Pattern learning system for tool creation.

AI_CONTEXT: This module learns from successful tool creations to improve
future suggestions and reduce clarification needs. It tracks common patterns,
parameter mappings, and user preferences.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from pathlib import Path


@dataclass
class ToolPattern:
    """Represents a learned pattern from successful tool creation."""
    intent: str
    provider: str
    endpoint: str
    auth_type: str
    parameter_mappings: Dict[str, str]
    success_count: int = 1
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolPattern':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class IntentPattern:
    """Tracks how user intents map to providers and tools."""
    intent_keywords: List[str]
    common_providers: List[Tuple[str, int]]  # (provider, count)
    common_parameters: Dict[str, int]  # parameter -> usage count
    success_rate: float = 1.0
    
    def add_success(self, provider: str, parameters: List[str]):
        """Record a successful tool creation."""
        # Update provider counts
        provider_found = False
        for i, (prov, count) in enumerate(self.common_providers):
            if prov == provider:
                self.common_providers[i] = (prov, count + 1)
                provider_found = True
                break
        
        if not provider_found:
            self.common_providers.append((provider, 1))
        
        # Sort by count
        self.common_providers.sort(key=lambda x: x[1], reverse=True)
        
        # Update parameter counts
        for param in parameters:
            self.common_parameters[param] = self.common_parameters.get(param, 0) + 1


class PatternLearner:
    """
    Learns from successful tool creations to improve future interactions.
    
    AI_CONTEXT: This class maintains a database of successful patterns,
    tracking what worked well for different types of requests. It helps
    reduce the need for clarification in future similar requests.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.expanduser("~/.agtos/patterns.json")
        self.patterns: List[ToolPattern] = []
        self.intent_patterns: Dict[str, IntentPattern] = {}
        self.parameter_aliases: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                    # Load tool patterns
                    self.patterns = [
                        ToolPattern.from_dict(p) 
                        for p in data.get('patterns', [])
                    ]
                    
                    # Load intent patterns
                    for intent, pattern_data in data.get('intent_patterns', {}).items():
                        self.intent_patterns[intent] = IntentPattern(
                            intent_keywords=pattern_data['intent_keywords'],
                            common_providers=pattern_data['common_providers'],
                            common_parameters=pattern_data['common_parameters'],
                            success_rate=pattern_data.get('success_rate', 1.0)
                        )
                    
                    # Load parameter aliases
                    self.parameter_aliases = defaultdict(
                        dict, 
                        data.get('parameter_aliases', {})
                    )
            except Exception as e:
                print(f"Error loading patterns: {e}")
    
    def save_patterns(self):
        """Save patterns to storage."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'patterns': [p.to_dict() for p in self.patterns],
            'intent_patterns': {
                intent: {
                    'intent_keywords': pattern.intent_keywords,
                    'common_providers': pattern.common_providers,
                    'common_parameters': pattern.common_parameters,
                    'success_rate': pattern.success_rate
                }
                for intent, pattern in self.intent_patterns.items()
            },
            'parameter_aliases': dict(self.parameter_aliases)
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_success(self, 
                      intent: str,
                      provider: str,
                      endpoint: str,
                      auth_type: str,
                      parameters: Dict[str, str],
                      user_preferences: Optional[Dict[str, Any]] = None):
        """
        Record a successful tool creation.
        
        AI_CONTEXT: This method is called after a tool is successfully created
        and tested. It updates our pattern database to improve future suggestions.
        """
        # Check if we have a similar pattern
        for pattern in self.patterns:
            if (pattern.intent.lower() == intent.lower() and 
                pattern.provider == provider and
                pattern.endpoint == endpoint):
                # Update existing pattern
                pattern.success_count += 1
                pattern.last_used = datetime.now().isoformat()
                if user_preferences:
                    pattern.user_preferences.update(user_preferences)
                break
        else:
            # Create new pattern
            self.patterns.append(ToolPattern(
                intent=intent,
                provider=provider,
                endpoint=endpoint,
                auth_type=auth_type,
                parameter_mappings=parameters,
                user_preferences=user_preferences or {}
            ))
        
        # Update intent patterns
        intent_key = self._extract_intent_key(intent)
        if intent_key not in self.intent_patterns:
            self.intent_patterns[intent_key] = IntentPattern(
                intent_keywords=intent_key.split('_'),
                common_providers=[],
                common_parameters={}
            )
        
        self.intent_patterns[intent_key].add_success(
            provider, 
            list(parameters.keys())
        )
        
        # Save updates
        self.save_patterns()
    
    def suggest_provider(self, intent: str) -> Optional[Tuple[str, float]]:
        """
        Suggest a provider based on learned patterns.
        
        Returns tuple of (provider_name, confidence_score).
        """
        intent_key = self._extract_intent_key(intent)
        
        # Check direct intent patterns
        if intent_key in self.intent_patterns:
            pattern = self.intent_patterns[intent_key]
            if pattern.common_providers:
                provider, count = pattern.common_providers[0]
                total_count = sum(c for _, c in pattern.common_providers)
                confidence = count / total_count
                return provider, confidence
        
        # Check similar patterns
        similar_patterns = self._find_similar_patterns(intent)
        if similar_patterns:
            # Weight by success count and recency
            provider_scores = defaultdict(float)
            for pattern in similar_patterns:
                days_old = (datetime.now() - datetime.fromisoformat(pattern.last_used)).days
                recency_weight = 1.0 / (1 + days_old / 30)  # Decay over 30 days
                score = pattern.success_count * recency_weight
                provider_scores[pattern.provider] += score
            
            if provider_scores:
                best_provider = max(provider_scores.items(), key=lambda x: x[1])
                total_score = sum(provider_scores.values())
                return best_provider[0], best_provider[1] / total_score
        
        return None
    
    def suggest_parameters(self, intent: str, provider: str) -> Dict[str, str]:
        """
        Suggest parameter mappings based on learned patterns.
        
        AI_CONTEXT: This helps pre-fill common parameters based on what
        worked in similar past tool creations.
        """
        suggestions = {}
        
        # Find exact matches
        for pattern in self.patterns:
            if (pattern.intent.lower() == intent.lower() and 
                pattern.provider == provider):
                suggestions.update(pattern.parameter_mappings)
        
        # Find similar patterns for the same provider
        similar_patterns = [
            p for p in self.patterns 
            if p.provider == provider and self._similarity(p.intent, intent) > 0.5
        ]
        
        # Merge parameter mappings, weighted by similarity and success
        param_scores = defaultdict(lambda: defaultdict(float))
        for pattern in similar_patterns:
            similarity = self._similarity(pattern.intent, intent)
            weight = similarity * pattern.success_count
            
            for param, value in pattern.parameter_mappings.items():
                param_scores[param][value] += weight
        
        # Select best value for each parameter
        for param, values in param_scores.items():
            if param not in suggestions:
                best_value = max(values.items(), key=lambda x: x[1])
                suggestions[param] = best_value[0]
        
        return suggestions
    
    def learn_parameter_alias(self, provider: str, original: str, alias: str):
        """
        Learn that a user refers to a parameter by a different name.
        
        Example: User says "API token" but provider expects "apikey".
        """
        self.parameter_aliases[provider][alias.lower()] = original
        self.save_patterns()
    
    def resolve_parameter_alias(self, provider: str, user_term: str) -> str:
        """Resolve a user's term to the actual parameter name."""
        return self.parameter_aliases.get(provider, {}).get(
            user_term.lower(), 
            user_term
        )
    
    def get_common_parameters(self, intent: str) -> List[str]:
        """Get commonly used parameters for an intent type."""
        intent_key = self._extract_intent_key(intent)
        
        if intent_key in self.intent_patterns:
            pattern = self.intent_patterns[intent_key]
            # Sort by usage count
            sorted_params = sorted(
                pattern.common_parameters.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [param for param, _ in sorted_params]
        
        return []
    
    def _extract_intent_key(self, intent: str) -> str:
        """Extract a normalized intent key from user input."""
        # Simple keyword extraction
        keywords = []
        intent_lower = intent.lower()
        
        # Common intent keywords
        intent_words = [
            'weather', 'message', 'send', 'post', 'notify',
            'payment', 'charge', 'database', 'store', 'query',
            'email', 'sms', 'alert', 'webhook', 'api'
        ]
        
        for word in intent_words:
            if word in intent_lower:
                keywords.append(word)
        
        return '_'.join(keywords) if keywords else 'general'
    
    def _find_similar_patterns(self, intent: str) -> List[ToolPattern]:
        """Find patterns similar to the given intent."""
        similar = []
        
        for pattern in self.patterns:
            similarity = self._similarity(pattern.intent, intent)
            if similarity > 0.5:  # Threshold for similarity
                similar.append(pattern)
        
        # Sort by similarity and success count
        similar.sort(
            key=lambda p: (
                self._similarity(p.intent, intent) * p.success_count
            ),
            reverse=True
        )
        
        return similar[:5]  # Return top 5
    
    def _similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Simple implementation using word overlap.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        return {
            'total_patterns': len(self.patterns),
            'unique_providers': len(set(p.provider for p in self.patterns)),
            'unique_intents': len(self.intent_patterns),
            'total_successes': sum(p.success_count for p in self.patterns),
            'parameter_aliases': sum(
                len(aliases) for aliases in self.parameter_aliases.values()
            ),
            'most_used_providers': [
                (provider, sum(p.success_count for p in self.patterns if p.provider == provider))
                for provider in set(p.provider for p in self.patterns)
            ][:5]
        }