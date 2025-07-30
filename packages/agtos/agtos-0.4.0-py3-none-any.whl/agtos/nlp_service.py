"""Natural Language Processing service for agent use.

PURPOSE: Shared NLP capabilities for all agents
CONTEXT: Extracted from completion and alias systems for agent access

AI_CONTEXT:
    This service provides natural language understanding capabilities
    that agents can use to:
    
    1. Map natural language to tool names
    2. Fuzzy match user requests to available tools
    3. Extract parameters from natural language
    4. Learn from usage patterns
    
    This centralizes NLP logic that was previously embedded in
    user-facing completion and alias systems.
"""

from typing import List, Tuple, Optional, Dict, Any
import re
from pathlib import Path
import json

from .metamcp.fuzzy_match import FuzzyMatcher
from .utils import get_logger

logger = get_logger(__name__)


class NLPService:
    """Natural language processing service for agents.
    
    AI_CONTEXT:
        Provides NLP capabilities to agents for understanding user
        requests and mapping them to available tools. Uses fuzzy
        matching and learned patterns from usage history.
    """
    
    def __init__(self):
        """Initialize NLP service with fuzzy matcher."""
        self.fuzzy_matcher = FuzzyMatcher()
        self.usage_patterns = self._load_usage_patterns()
        
        # Common patterns for extracting intent
        self.intent_patterns = [
            (r'show (?:me )?(.*)', 'query'),
            (r'list (?:all )?(.*)', 'list'),
            (r'create (?:a |new )?(.*)', 'create'),
            (r'delete (?:the )?(.*)', 'delete'),
            (r'update (?:the )?(.*)', 'update'),
            (r'run (?:the )?(.*)', 'execute'),
            (r'deploy (?:to )?(.*)', 'deploy'),
            (r'test (.*)', 'test'),
            (r'check (.*)', 'check'),
            (r'get (.*)', 'query'),
            (r'set (.*)', 'update'),
        ]
        
        # Tool name mappings from natural language
        self.tool_mappings = {
            'git status': 'cli__git__status',
            'git commit': 'cli__git__commit',
            'git log': 'cli__git__log',
            'docker ps': 'cli__docker__ps',
            'npm test': 'cli__npm__test',
            'pytest': 'cli__pytest',
            'list files': 'filesystem__list_directory',
            'read file': 'filesystem__read_file',
            'write file': 'filesystem__write_file',
            'show logs': 'cli__tail',
            'search code': 'cli__grep',
        }
    
    def find_matching_tool(
        self,
        query: str,
        available_tools: List[str],
        confidence_threshold: float = 0.5
    ) -> Optional[Tuple[str, float]]:
        """Find the best matching tool for a natural language query.
        
        Args:
            query: Natural language query from user
            available_tools: List of available tool names
            confidence_threshold: Minimum confidence for match
            
        Returns:
            Tuple of (tool_name, confidence) or None if no match
        """
        query_lower = query.lower().strip()
        
        # Check direct mappings first
        if query_lower in self.tool_mappings:
            tool = self.tool_mappings[query_lower]
            if tool in available_tools:
                return (tool, 1.0)
        
        # Use fuzzy matching
        matches = self.fuzzy_matcher.find_best_matches(
            query_lower,
            available_tools,
            limit=1
        )
        
        if matches and matches[0][1] >= confidence_threshold:
            return matches[0]
        
        return None
    
    def extract_intent(self, query: str) -> Tuple[str, str]:
        """Extract intent and target from natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (intent, target)
        """
        query_lower = query.lower().strip()
        
        # Try intent patterns
        for pattern, intent in self.intent_patterns:
            match = re.match(pattern, query_lower)
            if match:
                target = match.group(1).strip()
                return (intent, target)
        
        # Default to query intent
        return ('query', query_lower)
    
    def suggest_tools_for_intent(
        self,
        intent: str,
        target: str,
        available_tools: List[str]
    ) -> List[Tuple[str, float]]:
        """Suggest tools based on intent and target.
        
        Args:
            intent: Extracted intent (e.g., 'create', 'list')
            target: Target of the intent (e.g., 'file', 'docker container')
            available_tools: List of available tool names
            
        Returns:
            List of (tool_name, relevance_score) tuples
        """
        suggestions = []
        
        # Build search query from intent and target
        search_terms = []
        
        # Map intents to tool keywords
        intent_keywords = {
            'query': ['get', 'show', 'list', 'status', 'info'],
            'list': ['list', 'ls', 'show'],
            'create': ['create', 'new', 'add', 'init'],
            'delete': ['delete', 'remove', 'rm'],
            'update': ['update', 'set', 'modify', 'edit'],
            'execute': ['run', 'exec', 'start'],
            'deploy': ['deploy', 'push', 'publish'],
            'test': ['test', 'check', 'verify'],
        }
        
        # Add intent keywords
        if intent in intent_keywords:
            search_terms.extend(intent_keywords[intent])
        
        # Add target terms
        search_terms.extend(target.split())
        
        # Score each tool
        for tool in available_tools:
            score = 0.0
            tool_lower = tool.lower()
            
            # Check each search term
            for term in search_terms:
                if term in tool_lower:
                    score += 0.3
                elif any(part.startswith(term) for part in tool_lower.split('_')):
                    score += 0.2
            
            # Boost score for exact intent match
            if intent in tool_lower:
                score += 0.5
            
            if score > 0:
                suggestions.append((tool, min(score, 1.0)))
        
        # Sort by score
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:5]  # Top 5 suggestions
    
    def extract_parameters(self, query: str) -> Dict[str, Any]:
        """Extract potential parameters from natural language.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of extracted parameters
        """
        params = {}
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        if quoted:
            params['quoted_values'] = quoted
        
        # Extract key=value pairs
        kv_pairs = re.findall(r'(\w+)=([^\s]+)', query)
        for key, value in kv_pairs:
            params[key] = value
        
        # Extract file paths
        words = query.split()
        for word in words:
            if '/' in word or word.endswith(('.py', '.js', '.txt', '.json', '.yaml')):
                params.setdefault('paths', []).append(word)
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\b', query)
        if numbers:
            params['numbers'] = [int(n) for n in numbers]
        
        return params
    
    def learn_from_usage(self, query: str, selected_tool: str) -> None:
        """Learn from user's tool selection.
        
        Args:
            query: Original natural language query
            selected_tool: Tool that was actually used
        """
        # Add to tool mappings if high confidence
        query_lower = query.lower().strip()
        if len(query_lower) < 50:  # Only learn short queries
            self.tool_mappings[query_lower] = selected_tool
            self._save_usage_patterns()
    
    def _load_usage_patterns(self) -> Dict[str, Any]:
        """Load learned usage patterns from disk."""
        patterns_file = Path.home() / ".agtos" / "nlp_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    data = json.load(f)
                    # Merge loaded mappings
                    if 'tool_mappings' in data:
                        self.tool_mappings.update(data['tool_mappings'])
                    return data
            except Exception as e:
                logger.warning(f"Failed to load NLP patterns: {e}")
        return {}
    
    def _save_usage_patterns(self) -> None:
        """Save learned patterns to disk."""
        patterns_file = Path.home() / ".agtos" / "nlp_patterns.json"
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'tool_mappings': self.tool_mappings,
            'usage_patterns': self.usage_patterns
        }
        
        try:
            with open(patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save NLP patterns: {e}")


# Singleton instance
_nlp_service = None


def get_nlp_service() -> NLPService:
    """Get the singleton NLP service instance.
    
    AI_CONTEXT:
        Returns a shared NLP service instance that all agents
        can use for natural language understanding.
    """
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NLPService()
    return _nlp_service