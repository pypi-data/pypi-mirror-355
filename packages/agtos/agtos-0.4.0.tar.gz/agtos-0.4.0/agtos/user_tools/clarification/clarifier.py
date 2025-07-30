"""
Core clarification flow engine for tool creation.

AI_CONTEXT: This module orchestrates the clarification process, using the
provider knowledge base, pattern learning, and dialogue management to guide
users through tool creation with minimal friction.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
import threading
from datetime import datetime, timedelta
import logging

from .providers import ProviderKnowledgeBase, Provider
from .patterns import PatternLearner
from .dialogue import DialogueManager, DialogueState, DialogueContext

logger = logging.getLogger(__name__)


@dataclass
class ClarificationSession:
    """Represents a single clarification session."""
    intent: str
    analysis: Dict[str, Any]
    suggested_providers: List['Provider'] = None
    selected_provider: Optional['Provider'] = None
    patterns_applied: List[str] = None
    
    def __post_init__(self):
        if self.suggested_providers is None:
            self.suggested_providers = []
        if self.patterns_applied is None:
            self.patterns_applied = []


@dataclass
class ClarificationResult:
    """Result of the clarification process."""
    success: bool
    tool_config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    dialogue_history: List[Tuple[str, str]] = None
    confidence: float = 0.0
    provider_used: Optional[str] = None
    patterns_applied: List[str] = None


@dataclass
class ClarificationSessionData:
    """Container for session data including dialogue manager."""
    session: ClarificationSession
    dialogue_manager: DialogueManager
    created_at: datetime


class Clarifier:
    """
    Main clarification engine for natural language tool creation.
    
    AI_CONTEXT: This class orchestrates the entire clarification process,
    from understanding user intent to gathering all necessary information
    for tool creation. It uses learned patterns to minimize questions.
    """
    
    def __init__(self, 
                 provider_kb: Optional[ProviderKnowledgeBase] = None,
                 pattern_learner: Optional[PatternLearner] = None,
                 dialogue_manager: Optional[DialogueManager] = None):
        """Initialize the clarifier with its components."""
        self.provider_kb = provider_kb or ProviderKnowledgeBase()
        self.pattern_learner = pattern_learner or PatternLearner()
        # Note: We'll create dialogue managers per session now
        
        # Store multiple sessions indexed by session_id
        self.sessions: Dict[str, ClarificationSessionData] = {}
        self.session_lock = threading.Lock()
        
        # Session expiry time (30 minutes)
        self.session_timeout = timedelta(minutes=30)
    
    def start_clarification(self, user_intent: str, session_id: str) -> Tuple[str, DialogueContext]:
        """
        Start the clarification process for a user intent.
        
        Returns initial message and dialogue context.
        """
        # Analyze intent
        analysis = self._analyze_intent(user_intent)
        
        # Create session with its own dialogue manager
        dialogue_manager = DialogueManager()
        session = ClarificationSession(
            intent=user_intent,
            analysis=analysis
        )
        
        # Store session data with thread safety
        with self.session_lock:
            self.sessions[session_id] = ClarificationSessionData(
                session=session,
                dialogue_manager=dialogue_manager,
                created_at=datetime.now()
            )
            
            # Clean up expired sessions
            self._cleanup_expired_sessions()
        
        # Check if we can skip clarification based on patterns
        if self._can_auto_complete(analysis):
            # We have enough information from patterns
            tool_config = self._build_from_patterns(analysis)
            return self._generate_confirmation_only(tool_config)
        
        # Get provider suggestions
        suggested_providers = self._get_provider_suggestions(analysis)
        
        if not suggested_providers:
            # Check if user provided API details
            if self._has_api_details(user_intent):
                # Handle custom API naturally
                message, context, custom_session = self._handle_custom_api(user_intent, analysis)
                # Store the custom session
                with self.session_lock:
                    if session_id in self.sessions:
                        self.sessions[session_id].session = custom_session
                return message, context
            else:
                # Ask for more details
                return (
                    "I'd be happy to help create that tool! Could you tell me more about what you want to do? "
                    "For example, are you looking to send messages, get data from an API, or something else?",
                    DialogueContext(state=DialogueState.INITIAL)
                )
        
        # Start dialogue
        state, message = dialogue_manager.start_dialogue(user_intent)
        
        # If we have provider suggestions, show them
        if suggested_providers:
            dialogue_manager.current_context.state = DialogueState.PROVIDER_SELECTION
            message = dialogue_manager.generate_provider_selection_message(suggested_providers)
            
            # Store providers in session
            session.suggested_providers = suggested_providers
        
        return message, dialogue_manager.current_context
    
    def process_user_response(self, user_input: str, session_id: str) -> Tuple[str, DialogueState, Optional[ClarificationResult]]:
        """
        Process user response and return next message, state, and result if complete.
        
        AI_CONTEXT: This method handles the user's response at each step of the
        clarification process, updating the session state and determining what
        information is still needed.
        """
        # Strip whitespace from session_id to handle extra spaces
        if session_id:
            session_id = session_id.strip()
        
        # Get session data with thread safety
        with self.session_lock:
            session_data = self.sessions.get(session_id)
            
        if not session_data:
            # Log active sessions for debugging
            active_sessions = list(self.sessions.keys())
            logger.warning(f"Session {session_id} not found. Active sessions: {active_sessions}")
            return "Let's start fresh. What kind of tool would you like to create?", DialogueState.INITIAL, None
            
        if not session_data.dialogue_manager.current_context:
            logger.warning(f"Session {session_id} has no dialogue context")
            return "Let's start fresh. What kind of tool would you like to create?", DialogueState.INITIAL, None
        
        # Get session and dialogue manager
        current_session = session_data.session
        dialogue_manager = session_data.dialogue_manager
        
        # Let dialogue manager process the response
        state, message, data = dialogue_manager.process_response(user_input)
        
        # Handle state-specific logic
        if state == DialogueState.PROVIDER_SELECTION:
            # User selected a provider
            provider = self._resolve_provider_selection(user_input, current_session)
            if provider:
                dialogue_manager.current_context.selected_provider = provider
                current_session.selected_provider = provider
                
                # Check if we can pre-fill from patterns
                param_suggestions = self.pattern_learner.suggest_parameters(
                    current_session.intent,
                    provider.name
                )
                if param_suggestions:
                    dialogue_manager.current_context.parameter_mappings.update(param_suggestions)
                
                # Move to next state
                state = DialogueState.AUTH_SETUP
                message = dialogue_manager.generate_auth_message(provider)
        
        elif state == DialogueState.COMPLETE and data:
            # Tool creation complete
            result = ClarificationResult(
                success=True,
                tool_config=data,
                dialogue_history=dialogue_manager.current_context.clarification_history,
                confidence=self._calculate_confidence(current_session, dialogue_manager),
                provider_used=data.get('provider'),
                patterns_applied=current_session.patterns_applied
            )
            
            # Record success for learning
            if result.success:
                self._record_success(data, current_session, dialogue_manager)
                
            # Clean up session after completion
            with self.session_lock:
                if session_id in self.sessions:
                    del self.sessions[session_id]
            
            return message, state, result
        
        return message, state, None
    
    def _analyze_intent(self, user_intent: str) -> Dict[str, Any]:
        """
        Analyze user intent to extract key information.
        
        AI_CONTEXT: This method performs NLP analysis on the user's intent
        to extract service type, action, parameters, and other relevant details.
        """
        analysis = {
            'raw_intent': user_intent,
            'service_type': None,
            'action': None,
            'extracted_params': {},
            'confidence_scores': {}
        }
        
        intent_lower = user_intent.lower()
        
        # Detect service type
        service_keywords = {
            'weather': ['weather', 'temperature', 'forecast', 'climate'],
            'messaging': ['message', 'send', 'post', 'notify', 'slack', 'discord', 'telegram'],
            'payments': ['payment', 'charge', 'pay', 'transaction', 'stripe', 'paypal'],
            'database': ['database', 'store', 'save', 'query', 'data']
        }
        
        for service, keywords in service_keywords.items():
            if any(keyword in intent_lower for keyword in keywords):
                analysis['service_type'] = service
                analysis['confidence_scores']['service_type'] = 0.8
                break
        
        # Detect action
        action_keywords = {
            'send': ['send', 'post', 'notify', 'message'],
            'get': ['get', 'fetch', 'retrieve', 'check', 'find'],
            'create': ['create', 'make', 'add', 'new'],
            'update': ['update', 'modify', 'change', 'edit'],
            'delete': ['delete', 'remove', 'cancel']
        }
        
        for action, keywords in action_keywords.items():
            if any(keyword in intent_lower for keyword in keywords):
                analysis['action'] = action
                break
        
        # Extract potential parameters
        # Look for patterns like "to #channel" or "in London"
        param_patterns = {
            'channel': r'(?:to|in)\s+([#@]\w+)',
            'location': r'(?:in|at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'amount': r'(?:\$|€|£)\s*(\d+(?:\.\d{2})?)',
            'email': r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        }
        
        for param, pattern in param_patterns.items():
            match = re.search(pattern, user_intent)
            if match:
                analysis['extracted_params'][param] = match.group(1)
        
        # Check for provider mentions
        for provider in self.provider_kb.providers:
            if provider.name.lower() in intent_lower:
                analysis['mentioned_provider'] = provider.name
                analysis['confidence_scores']['provider'] = 0.9
        
        return analysis
    
    def _get_provider_suggestions(self, analysis: Dict[str, Any]) -> List[Provider]:
        """Get provider suggestions based on intent analysis."""
        suggestions = []
        
        # First, check if user mentioned a specific provider
        if 'mentioned_provider' in analysis:
            provider = self.provider_kb.get_provider(analysis['mentioned_provider'])
            if provider:
                return [provider]
        
        # Check pattern learner for suggestions
        if self.pattern_learner:
            learned_suggestion = self.pattern_learner.suggest_provider(
                analysis['raw_intent']
            )
            if learned_suggestion:
                provider_name, confidence = learned_suggestion
                if confidence > 0.7:
                    provider = self.provider_kb.get_provider(provider_name)
                    if provider:
                        suggestions.append(provider)
        
        # Use knowledge base suggestions
        kb_suggestions = self.provider_kb.suggest_providers(analysis['raw_intent'])
        
        # Combine and deduplicate
        seen = set()
        final_suggestions = []
        
        for provider in suggestions + kb_suggestions:
            if provider.name not in seen:
                seen.add(provider.name)
                final_suggestions.append(provider)
        
        return final_suggestions[:3]  # Return top 3
    
    def _can_auto_complete(self, analysis: Dict[str, Any]) -> bool:
        """
        Check if we have enough information to auto-complete without dialogue.
        
        This happens when patterns provide all necessary information.
        """
        # Check if we have high confidence in provider selection
        if analysis.get('confidence_scores', {}).get('provider', 0) < 0.8:
            return False
        
        # Check if we have a strong pattern match
        provider_suggestion = self.pattern_learner.suggest_provider(
            analysis['raw_intent']
        )
        
        if not provider_suggestion or provider_suggestion[1] < 0.8:
            return False
        
        # Check if we have parameter suggestions
        provider_name = provider_suggestion[0]
        param_suggestions = self.pattern_learner.suggest_parameters(
            analysis['raw_intent'],
            provider_name
        )
        
        # For now, don't auto-complete (require confirmation)
        # In future, could auto-complete for very high confidence
        return False
    
    def _build_from_patterns(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build tool configuration from learned patterns."""
        # This would construct a full tool config from patterns
        # For now, return None
        return None
    
    def _resolve_provider_selection(self, user_input: str, session: ClarificationSession) -> Optional[Provider]:
        """Resolve provider from user selection."""
        user_input = user_input.strip().lower()
        
        # Check if it's a number
        if user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(session.suggested_providers):
                return session.suggested_providers[index]
        
        # Check if it's a provider name
        for provider in session.suggested_providers:
            if provider.name.lower() in user_input or user_input in provider.name.lower():
                return provider
        
        # Try fuzzy matching
        for provider in session.suggested_providers:
            if any(word in provider.name.lower() for word in user_input.split()):
                return provider
        
        return None
    
    def _calculate_confidence(self, session: ClarificationSession, dialogue_manager: DialogueManager) -> float:
        """Calculate overall confidence in the tool configuration."""
        if not session:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Add confidence based on pattern matches
        if session.patterns_applied:
            confidence += 0.2 * len(session.patterns_applied)
        
        # Add confidence based on explicit provider mention
        if 'mentioned_provider' in session.analysis:
            confidence += 0.2
        
        # Add confidence based on number of clarifications needed
        clarification_count = len(
            dialogue_manager.current_context.clarification_history
        )
        if clarification_count <= 3:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions to prevent memory leaks."""
        now = datetime.now()
        expired_ids = []
        
        for session_id, session_data in self.sessions.items():
            if now - session_data.created_at > self.session_timeout:
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            del self.sessions[session_id]
    
    def _record_success(self, tool_config: Dict[str, Any], session: ClarificationSession, dialogue_manager: DialogueManager):
        """Record successful tool creation for pattern learning."""
        if not session:
            return
        
        self.pattern_learner.record_success(
            intent=session.intent,
            provider=tool_config['provider'],
            endpoint=tool_config['endpoint'],
            auth_type=tool_config['auth']['type'],
            parameters=tool_config.get('parameters', {}),
            user_preferences={
                'dialogue_turns': len(
                    dialogue_manager.current_context.clarification_history
                ),
                'extracted_params': session.analysis.get(
                    'extracted_params', {}
                )
            }
        )
    
    def _generate_confirmation_only(self, tool_config: Dict[str, Any]) -> Tuple[str, DialogueContext]:
        """Generate confirmation message for auto-completed tool."""
        context = DialogueContext(state=DialogueState.CONFIRMATION)
        message = self.dialogue_manager.generate_confirmation_message(tool_config)
        return message, context
    
    def get_clarification_stats(self) -> Dict[str, Any]:
        """Get statistics about clarification sessions."""
        pattern_stats = self.pattern_learner.get_statistics()
        
        return {
            'total_clarifications': pattern_stats.get('total_patterns', 0),
            'unique_providers_used': pattern_stats.get('unique_providers', 0),
            'average_confidence': 0.75,  # Would calculate from history
            'most_common_intents': pattern_stats.get('unique_intents', 0),
            'pattern_learning_stats': pattern_stats
        }
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active sessions."""
        with self.session_lock:
            return {
                session_id: {
                    'intent': data.session.intent,
                    'state': data.dialogue_manager.current_context.state.value if data.dialogue_manager.current_context else 'unknown',
                    'created_at': data.created_at.isoformat(),
                    'age_seconds': (datetime.now() - data.created_at).total_seconds()
                }
                for session_id, data in self.sessions.items()
            }
    
    def _has_api_details(self, user_intent: str) -> bool:
        """Check if user provided API URL or endpoint details."""
        # Check for URL patterns
        url_pattern = r'https?://[^\s]+|api\.[^\s]+|[^\s]+\.com/[^\s]+'
        if re.search(url_pattern, user_intent):
            return True
        
        # Check for API-related keywords with specifics
        api_indicators = [
            r'endpoint.+(?:GET|POST|PUT|DELETE)',
            r'api.+(?:at|endpoint|url)',
            r'https?://',
            r'/api/',
            r'\.com/',
            r'\.org/',
            r'\.io/'
        ]
        
        return any(re.search(pattern, user_intent, re.IGNORECASE) for pattern in api_indicators)
    
    def _handle_custom_api(self, user_intent: str, analysis: Dict[str, Any]) -> Tuple[str, DialogueContext, ClarificationSession]:
        """Handle custom API naturally without mentioning knowledge base."""
        # Use original analyzer to extract API details
        from agtos.user_tools import APIAnalyzer
        analyzer = APIAnalyzer()
        
        try:
            spec = analyzer.analyze(user_intent)
            
            # Create a custom provider representation
            custom_provider = self._create_custom_provider(spec)
            
            # Start dialogue with custom API context
            context = DialogueContext(state=DialogueState.PROVIDER_SELECTION)
            context.selected_provider = custom_provider
            
            # Generate natural response
            if spec.endpoints:
                endpoint = spec.endpoints[0]
                message = (
                    f"I'll help you create a tool for {endpoint.url}. "
                    f"I can see this is a {endpoint.method.value} endpoint"
                )
                
                if endpoint.parameters:
                    message += f" that takes {len(endpoint.parameters)} parameters"
                
                message += ". "
                
                if endpoint.authentication:
                    message += f"It looks like it uses {endpoint.authentication.type.value} authentication. "
                
                message += (
                    "\n\nI haven't worked with this specific API before, but I'll figure out "
                    "the details as we go. Let me ask you a few questions to make sure I set it up correctly."
                )
            else:
                message = (
                    f"I'll help you create a tool for that API. I haven't used this particular one before, "
                    "but I'll work out the details with you. \n\n"
                    "Could you tell me what HTTP method this endpoint uses? (GET, POST, etc.)"
                )
            
            # Store in session (needs session_id passed in)
            # Note: This method is called from start_clarification which has session_id
            # We'll need to update the method signature
            session = ClarificationSession(
                intent=user_intent,
                analysis=analysis,
                selected_provider=custom_provider
            )
            
            return message, context, session
            
        except Exception:
            # If parsing fails, ask for more details naturally
            return (
                "I'd love to help you create a tool for that API! To get started, could you tell me:\n"
                "- The full API endpoint URL\n"
                "- What HTTP method it uses (GET, POST, etc.)\n"
                "- What kind of authentication it needs (if any)\n\n"
                "I'll figure out the rest as we go!",
                DialogueContext(state=DialogueState.INITIAL)
            )
    
    def _create_custom_provider(self, spec) -> Provider:
        """Create a Provider object from analyzed API spec."""
        from .providers import Provider, Endpoint, AuthType
        
        # Extract base URL
        if spec.endpoints:
            from urllib.parse import urlparse
            parsed = urlparse(spec.endpoints[0].url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            base_url = "https://api.custom.com"
        
        # Map auth type
        auth_type = AuthType.NONE
        if spec.endpoints and spec.endpoints[0].authentication:
            auth_str = spec.endpoints[0].authentication.type.value.lower()
            if auth_str == "bearer":
                auth_type = AuthType.BEARER_TOKEN
            elif auth_str == "api_key":
                auth_type = AuthType.API_KEY
            elif auth_str == "basic":
                auth_type = AuthType.BASIC_AUTH
        
        # Create endpoints
        endpoints = []
        for ep in spec.endpoints:
            endpoints.append(Endpoint(
                path=urlparse(ep.url).path,
                method=ep.method.value,
                description=f"Custom endpoint at {ep.url}",
                parameters={
                    p.name: f"{p.name} parameter" 
                    for p in ep.parameters
                } if hasattr(ep, 'parameters') else {},
                required_params=[
                    p.name for p in ep.parameters 
                    if hasattr(p, 'required') and p.required
                ] if hasattr(ep, 'parameters') else []
            ))
        
        return Provider(
            name=spec.name,
            category="custom",
            base_url=base_url,
            auth_type=auth_type,
            description=spec.description or "Custom API integration",
            pros=["Tailored to your specific needs"],
            cons=["May require custom configuration"],
            endpoints=endpoints,
            setup_instructions="Custom API - configuration will be determined during setup",
            pricing="Check with API provider"
        )