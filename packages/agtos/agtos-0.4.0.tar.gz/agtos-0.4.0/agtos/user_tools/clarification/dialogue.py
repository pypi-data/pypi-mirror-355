"""
Conversational dialogue system for tool creation.

AI_CONTEXT: This module manages the conversational flow when creating tools,
asking for missing information in a natural, user-friendly way and providing
helpful context and examples.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from .providers import Provider, Endpoint, AuthType


class DialogueState(Enum):
    """States in the dialogue flow."""
    INITIAL = "initial"
    PROVIDER_SELECTION = "provider_selection"
    ENDPOINT_SELECTION = "endpoint_selection"
    AUTH_SETUP = "auth_setup"
    PARAMETER_MAPPING = "parameter_mapping"
    CONFIRMATION = "confirmation"
    COMPLETE = "complete"


@dataclass
class DialogueContext:
    """Maintains context throughout the dialogue."""
    state: DialogueState = DialogueState.INITIAL
    intent: str = ""
    selected_provider: Optional[Provider] = None
    selected_endpoint: Optional[Endpoint] = None
    auth_details: Dict[str, str] = field(default_factory=dict)
    parameter_mappings: Dict[str, str] = field(default_factory=dict)
    user_examples: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    clarification_history: List[Tuple[str, str]] = field(default_factory=list)


class DialogueManager:
    """
    Manages conversational flow for tool creation.
    
    AI_CONTEXT: This class handles the back-and-forth conversation with users
    when creating tools. It asks clarifying questions in a natural way and
    provides helpful examples and context.
    """
    
    def __init__(self):
        self.templates = self._load_templates()
        self.current_context: Optional[DialogueContext] = None
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load conversational templates for different scenarios."""
        return {
            'provider_choice': [
                "I found {count} providers that could work for {intent}. Here are the top options:\n\n{options}\n\nWhich would you prefer? (You can say the number or name)",
                "For {intent}, I'd recommend these {count} options:\n\n{options}\n\nWhich one matches what you're looking for?",
                "Great! I can help with {intent}. Here are {count} services that could work:\n\n{options}\n\nWhich would work best for you?"
            ],
            'provider_pros_cons': [
                "{number}. **{name}** - {description}\n   ✅ Pros: {pros}\n   ⚠️  Cons: {cons}\n   💰 {pricing}"
            ],
            'single_provider': [
                "For {intent}, I'd recommend using **{provider}**. {description}\n\n✅ {pros}\n\nDoes this work for you?",
                "I think **{provider}** would be perfect for {intent}. {description}\n\nShould I set this up for you?"
            ],
            'auth_request': {
                AuthType.API_KEY: [
                    "To use {provider}, you'll need an API key. {instructions}\n\nOnce you have it, please share the API key.",
                    "{provider} requires an API key for authentication. {instructions}\n\nWhat's your API key?"
                ],
                AuthType.BEARER_TOKEN: [
                    "For {provider}, you'll need an access token. {instructions}\n\nPlease provide your access token.",
                    "I'll need your {provider} access token. {instructions}\n\nWhat's the token?"
                ],
                AuthType.OAUTH2: [
                    "{provider} uses OAuth2. You'll need:\n- Client ID\n- Client Secret\n\n{instructions}\n\nCould you provide both?",
                    "For OAuth2 with {provider}, I need your app credentials. {instructions}\n\nWhat are your client ID and secret?"
                ],
                AuthType.BASIC_AUTH: [
                    "{provider} uses basic authentication. I'll need:\n- Username\n- Password\n\nWhat are your credentials?",
                    "For {provider}, please provide your username and password."
                ]
            },
            'parameter_request': [
                "For the {endpoint} endpoint, I need to know:\n\n{params}\n\nHow would you like to provide these values?",
                "To complete the setup, I need some details:\n\n{params}\n\nCould you help me fill these in?",
                "Almost done! For {endpoint}, I just need:\n\n{params}\n\nWhat should I use for these?"
            ],
            'parameter_example': [
                "• **{param}**: {description}\n  Example: {example}",
                "• **{param}** - {description} (e.g., {example})"
            ],
            'confirmation': [
                "Perfect! Here's what I'll create:\n\n**Tool**: {tool_name}\n**Provider**: {provider}\n**Endpoint**: {endpoint}\n**Purpose**: {purpose}\n\n{details}\n\nShall I create this tool?",
                "Great! I'm ready to create:\n\n**{tool_name}**\n- Using {provider} ({endpoint})\n- {purpose}\n\n{details}\n\nLook good?"
            ],
            'success': [
                "✅ Excellent! I've created the '{tool_name}' tool. You can now use it by saying things like:\n\n{examples}\n\nWould you like to test it now?",
                "🎉 Your '{tool_name}' tool is ready! Try it out with:\n\n{examples}\n\nLet me know if you need any adjustments!"
            ],
            'clarification': [
                "I'm not sure I understood that. Could you rephrase or provide an example?",
                "Let me make sure I understand - could you explain what you mean by '{term}'?",
                "Could you clarify what you'd like to do? For example, 'send a message to Slack' or 'check the weather in London'."
            ],
            'example_request': [
                "Could you give me an example of how you'd use this? For instance, what kind of {type} would you typically {action}?",
                "To better understand, could you show me an example {type} you might {action}?"
            ]
        }
    
    def start_dialogue(self, intent: str) -> Tuple[DialogueState, str]:
        """
        Start a new dialogue for tool creation.
        
        Returns the initial state and message to show the user.
        """
        self.current_context = DialogueContext(
            state=DialogueState.PROVIDER_SELECTION,
            intent=intent
        )
        
        return self.current_context.state, self._generate_initial_message(intent)
    
    def process_response(self, user_input: str) -> Tuple[DialogueState, str, Optional[Dict[str, Any]]]:
        """
        Process user response and return next state, message, and any extracted data.
        
        AI_CONTEXT: This is the main dialogue engine that processes user input
        based on the current state and generates appropriate responses.
        """
        if not self.current_context:
            return DialogueState.INITIAL, "Let's start over. What kind of tool would you like to create?", None
        
        # Record the interaction
        self.current_context.clarification_history.append((
            self.current_context.state.value,
            user_input
        ))
        
        # Process based on current state
        if self.current_context.state == DialogueState.PROVIDER_SELECTION:
            return self._handle_provider_selection(user_input)
        
        elif self.current_context.state == DialogueState.ENDPOINT_SELECTION:
            return self._handle_endpoint_selection(user_input)
        
        elif self.current_context.state == DialogueState.AUTH_SETUP:
            return self._handle_auth_setup(user_input)
        
        elif self.current_context.state == DialogueState.PARAMETER_MAPPING:
            return self._handle_parameter_mapping(user_input)
        
        elif self.current_context.state == DialogueState.CONFIRMATION:
            return self._handle_confirmation(user_input)
        
        return DialogueState.COMPLETE, "Tool creation complete!", None
    
    def _generate_initial_message(self, intent: str) -> str:
        """Generate the initial message based on intent analysis."""
        # This would be called by the Clarifier with provider suggestions
        # For now, return a placeholder
        return f"I'll help you create a tool for: {intent}"
    
    def generate_provider_selection_message(self, providers: List[Provider]) -> str:
        """Generate message for provider selection."""
        if len(providers) == 1:
            provider = providers[0]
            template = self._get_template('single_provider')
            pros = ' '.join(provider.pros[:2])  # First 2 pros
            
            return template.format(
                intent=self.current_context.intent,
                provider=provider.name,
                description=provider.description,
                pros=pros
            )
        
        # Multiple providers
        template = self._get_template('provider_choice')
        options = []
        
        for i, provider in enumerate(providers[:3], 1):  # Show top 3
            pros = '; '.join(provider.pros[:2])
            cons = '; '.join(provider.cons[:1]) if provider.cons else "None"
            
            option = self.templates['provider_pros_cons'][0].format(
                number=i,
                name=provider.name,
                description=provider.description,
                pros=pros,
                cons=cons,
                pricing=provider.pricing
            )
            options.append(option)
        
        return template.format(
            count=len(providers[:3]),
            intent=self.current_context.intent,
            options='\n\n'.join(options)
        )
    
    def generate_auth_message(self, provider: Provider) -> str:
        """Generate message for authentication setup."""
        templates = self.templates['auth_request'].get(
            provider.auth_type,
            ["I need authentication details for {provider}."]
        )
        
        template = templates[0]
        return template.format(
            provider=provider.name,
            instructions=provider.setup_instructions
        )
    
    def generate_parameter_message(self, endpoint: Endpoint, missing_params: List[str]) -> str:
        """Generate message for parameter collection."""
        template = self._get_template('parameter_request')
        
        param_descriptions = []
        for param in missing_params:
            desc = endpoint.parameters.get(param, "Required parameter")
            example = self._get_parameter_example(param)
            
            param_desc = self.templates['parameter_example'][0].format(
                param=param,
                description=desc,
                example=example
            )
            param_descriptions.append(param_desc)
        
        return template.format(
            endpoint=endpoint.description,
            params='\n'.join(param_descriptions)
        )
    
    def generate_confirmation_message(self, tool_config: Dict[str, Any]) -> str:
        """Generate confirmation message before creating tool."""
        template = self._get_template('confirmation')
        
        details = []
        if 'auth' in tool_config:
            details.append(f"**Auth**: {tool_config['auth']['type']}")
        
        if 'parameters' in tool_config:
            params = ', '.join(tool_config['parameters'].keys())
            details.append(f"**Parameters**: {params}")
        
        return template.format(
            tool_name=tool_config['name'],
            provider=self.current_context.selected_provider.name,
            endpoint=self.current_context.selected_endpoint.path,
            purpose=self.current_context.intent,
            details='\n'.join(details)
        )
    
    def generate_success_message(self, tool_name: str, examples: List[str]) -> str:
        """Generate success message after tool creation."""
        template = self._get_template('success')
        
        example_list = '\n'.join([f"- \"{ex}\"" for ex in examples[:3]])
        
        return template.format(
            tool_name=tool_name,
            examples=example_list
        )
    
    def _handle_provider_selection(self, user_input: str) -> Tuple[DialogueState, str, Optional[Dict[str, Any]]]:
        """Handle provider selection from user input."""
        # Simple number or name matching
        # In real implementation, this would be more sophisticated
        
        # Check if user said a number
        if user_input.strip().isdigit():
            # User selected by number
            selection = int(user_input.strip())
            # This would select from the presented options
        
        # For now, assume provider is selected
        self.current_context.state = DialogueState.AUTH_SETUP
        
        if self.current_context.selected_provider:
            return (
                DialogueState.AUTH_SETUP,
                self.generate_auth_message(self.current_context.selected_provider),
                None
            )
        
        return (
            DialogueState.PROVIDER_SELECTION,
            "I didn't catch that. Which provider would you like to use?",
            None
        )
    
    def _handle_auth_setup(self, user_input: str) -> Tuple[DialogueState, str, Optional[Dict[str, Any]]]:
        """Handle authentication setup."""
        provider = self.current_context.selected_provider
        
        if provider.auth_type == AuthType.API_KEY:
            # Extract API key from input
            self.current_context.auth_details['api_key'] = user_input.strip()
        
        elif provider.auth_type == AuthType.BEARER_TOKEN:
            self.current_context.auth_details['token'] = user_input.strip()
        
        elif provider.auth_type == AuthType.OAUTH2:
            # Parse client ID and secret
            lines = user_input.strip().split('\n')
            if len(lines) >= 2:
                self.current_context.auth_details['client_id'] = lines[0].strip()
                self.current_context.auth_details['client_secret'] = lines[1].strip()
        
        # Move to endpoint selection or parameter mapping
        if provider.endpoints and len(provider.endpoints) > 1:
            self.current_context.state = DialogueState.ENDPOINT_SELECTION
            return (
                DialogueState.ENDPOINT_SELECTION,
                "Which endpoint would you like to use?",
                None
            )
        else:
            # Single endpoint, move to parameters
            self.current_context.selected_endpoint = provider.endpoints[0]
            self.current_context.state = DialogueState.PARAMETER_MAPPING
            
            missing_params = self._get_missing_parameters()
            if missing_params:
                return (
                    DialogueState.PARAMETER_MAPPING,
                    self.generate_parameter_message(
                        self.current_context.selected_endpoint,
                        missing_params
                    ),
                    None
                )
            else:
                # No parameters needed, move to confirmation
                self.current_context.state = DialogueState.CONFIRMATION
                return self._prepare_confirmation()
    
    def _handle_parameter_mapping(self, user_input: str) -> Tuple[DialogueState, str, Optional[Dict[str, Any]]]:
        """Handle parameter mapping from user input."""
        # Parse user input for parameter values
        # This is simplified - real implementation would be more sophisticated
        
        lines = user_input.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                self.current_context.parameter_mappings[key.strip()] = value.strip()
        
        # Check if we have all required parameters
        missing = self._get_missing_parameters()
        
        if missing:
            return (
                DialogueState.PARAMETER_MAPPING,
                f"I still need values for: {', '.join(missing)}",
                None
            )
        
        # Move to confirmation
        self.current_context.state = DialogueState.CONFIRMATION
        return self._prepare_confirmation()
    
    def _handle_confirmation(self, user_input: str) -> Tuple[DialogueState, str, Optional[Dict[str, Any]]]:
        """Handle confirmation response."""
        user_input_lower = user_input.lower().strip()
        
        if any(word in user_input_lower for word in ['yes', 'ok', 'sure', 'create', 'looks good']):
            # User confirmed
            self.current_context.state = DialogueState.COMPLETE
            
            # Prepare tool configuration
            tool_config = self._build_tool_config()
            
            return (
                DialogueState.COMPLETE,
                self.generate_success_message(
                    tool_config['name'],
                    self._generate_usage_examples()
                ),
                tool_config
            )
        
        elif any(word in user_input_lower for word in ['no', 'cancel', 'stop']):
            return (
                DialogueState.INITIAL,
                "No problem! Let me know if you'd like to create a different tool.",
                None
            )
        
        else:
            # User wants to modify something
            return (
                DialogueState.CONFIRMATION,
                "What would you like to change?",
                None
            )
    
    def _get_template(self, template_key: str) -> str:
        """Get a random template for variety."""
        templates = self.templates.get(template_key, [""])
        return templates[0] if templates else ""
    
    def _get_parameter_example(self, param: str) -> str:
        """Get example value for a parameter."""
        examples = {
            'api_key': 'sk_test_abc123...',
            'token': 'Bearer eyJhbGc...',
            'channel': '#general',
            'text': 'Hello, world!',
            'q': 'London,UK',
            'city': 'San Francisco',
            'amount': '2000',
            'currency': 'usd',
            'limit': '10',
            'offset': '0'
        }
        
        return examples.get(param.lower(), f'your_{param}')
    
    def _get_missing_parameters(self) -> List[str]:
        """Get list of missing required parameters."""
        if not self.current_context.selected_endpoint:
            return []
        
        required = self.current_context.selected_endpoint.required_params
        provided = set(self.current_context.parameter_mappings.keys())
        
        return [p for p in required if p not in provided]
    
    def _build_tool_config(self) -> Dict[str, Any]:
        """Build final tool configuration."""
        provider = self.current_context.selected_provider
        endpoint = self.current_context.selected_endpoint
        
        # Generate tool name from intent
        tool_name = self._generate_tool_name()
        
        config = {
            'name': tool_name,
            'provider': provider.name,
            'base_url': provider.base_url,
            'endpoint': endpoint.path,
            'method': endpoint.method,
            'auth': {
                'type': provider.auth_type.value,
                'details': self.current_context.auth_details
            },
            'parameters': self.current_context.parameter_mappings,
            'description': f"{self.current_context.intent} using {provider.name}",
            'metadata': {
                'intent': self.current_context.intent,
                'created_from_dialogue': True,
                'dialogue_history': self.current_context.clarification_history
            }
        }
        
        return config
    
    def _generate_tool_name(self) -> str:
        """Generate a tool name from intent and provider."""
        # Simple name generation
        intent_words = self.current_context.intent.lower().split()
        
        # Remove common words
        stop_words = {'i', 'want', 'to', 'need', 'like', 'would', 'can', 'please'}
        key_words = [w for w in intent_words if w not in stop_words]
        
        if self.current_context.selected_provider:
            provider_name = self.current_context.selected_provider.name.lower()
            return f"{provider_name}_{'_'.join(key_words[:2])}"
        
        return '_'.join(key_words[:3])
    
    def _generate_usage_examples(self) -> List[str]:
        """Generate usage examples for the created tool."""
        tool_name = self._generate_tool_name()
        
        examples = []
        
        if 'weather' in self.current_context.intent.lower():
            examples = [
                f"Use {tool_name} to check weather in Paris",
                f"What's the weather in Tokyo?",
                f"Get me the forecast for next week"
            ]
        elif 'message' in self.current_context.intent.lower():
            examples = [
                f"Send 'Meeting at 3pm' to #general",
                f"Post an update to the team channel",
                f"Notify the team about the deployment"
            ]
        else:
            examples = [
                f"Use {tool_name}",
                f"Run the {tool_name} tool",
                f"Execute {tool_name} with parameters"
            ]
        
        return examples
    
    def _prepare_confirmation(self) -> Tuple[DialogueState, str, Optional[Dict[str, Any]]]:
        """Prepare confirmation state and message."""
        tool_config = self._build_tool_config()
        
        return (
            DialogueState.CONFIRMATION,
            self.generate_confirmation_message(tool_config),
            None
        )