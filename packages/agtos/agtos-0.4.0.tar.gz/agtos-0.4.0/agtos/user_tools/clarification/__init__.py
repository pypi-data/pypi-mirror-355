"""
Clarification system for natural language tool creation.

This system helps users create tools by:
- Detecting common service patterns
- Offering provider recommendations
- Asking for missing information conversationally
- Learning from successful patterns
"""

from .clarifier import Clarifier
from .dialogue import DialogueManager, DialogueState
from .patterns import PatternLearner
from .providers import ProviderKnowledgeBase

__all__ = [
    'Clarifier',
    'DialogueManager',
    'DialogueState',
    'PatternLearner',
    'ProviderKnowledgeBase'
]