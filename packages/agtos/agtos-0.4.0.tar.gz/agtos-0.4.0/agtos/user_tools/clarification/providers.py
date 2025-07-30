"""
Knowledge base of common API providers with their capabilities and requirements.

AI_CONTEXT: This module contains a curated database of popular API providers
organized by service category. Each provider includes endpoints, authentication
methods, pros/cons, and example usage patterns to help guide users.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class AuthType(Enum):
    """Common authentication types for APIs."""
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    NONE = "none"


@dataclass
class Endpoint:
    """Represents an API endpoint with its details."""
    path: str
    method: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    example_response: Optional[Dict[str, Any]] = None


@dataclass
class Provider:
    """Represents an API provider with all its details."""
    name: str
    category: str
    base_url: str
    auth_type: AuthType
    description: str
    pros: List[str]
    cons: List[str]
    endpoints: List[Endpoint]
    setup_instructions: str
    pricing: str = "Free tier available"
    rate_limits: Optional[str] = None
    example_credentials: Optional[Dict[str, str]] = None


class ProviderKnowledgeBase:
    """
    Knowledge base of common API providers.
    
    AI_CONTEXT: This class maintains a comprehensive database of API providers
    organized by category. It helps suggest appropriate providers based on
    user intent and provides all necessary details for tool creation.
    """
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.categories = self._organize_by_category()
    
    def _initialize_providers(self) -> List[Provider]:
        """Initialize the provider database with common services."""
        return [
            # Weather Providers
            Provider(
                name="OpenWeatherMap",
                category="weather",
                base_url="https://api.openweathermap.org/data/2.5",
                auth_type=AuthType.API_KEY,
                description="Comprehensive weather data API with global coverage",
                pros=[
                    "Free tier with 1000 calls/day",
                    "Current weather, forecasts, and historical data",
                    "Global coverage with 200,000+ cities",
                    "Multiple data formats (JSON, XML)"
                ],
                cons=[
                    "API key required even for free tier",
                    "Rate limited on free plan",
                    "Some advanced features require paid plan"
                ],
                endpoints=[
                    Endpoint(
                        path="/weather",
                        method="GET",
                        description="Get current weather for a location",
                        parameters={
                            "q": "City name (e.g., 'London' or 'London,UK')",
                            "lat": "Latitude (use with lon)",
                            "lon": "Longitude (use with lat)",
                            "appid": "Your API key",
                            "units": "Temperature units (metric/imperial)"
                        },
                        required_params=["appid"],
                        example_response={
                            "weather": [{"main": "Clear", "description": "clear sky"}],
                            "main": {"temp": 20.5, "humidity": 65},
                            "wind": {"speed": 3.5}
                        }
                    ),
                    Endpoint(
                        path="/forecast",
                        method="GET",
                        description="Get 5 day forecast with 3 hour steps",
                        parameters={
                            "q": "City name",
                            "appid": "Your API key",
                            "units": "Temperature units",
                            "cnt": "Number of timestamps to return"
                        },
                        required_params=["q", "appid"]
                    )
                ],
                setup_instructions="1. Sign up at openweathermap.org\n2. Get free API key from dashboard\n3. Use 'appid' parameter in all requests",
                pricing="Free: 1000 calls/day, Paid: Starting at $40/month",
                rate_limits="60 calls/minute on free tier"
            ),
            
            Provider(
                name="WeatherAPI",
                category="weather",
                base_url="https://api.weatherapi.com/v1",
                auth_type=AuthType.API_KEY,
                description="Modern weather API with AI-powered forecasts",
                pros=[
                    "Generous free tier (1M calls/month)",
                    "Real-time and forecast data",
                    "Astronomy and sports data included",
                    "No credit card for free tier"
                ],
                cons=[
                    "Newer service with less track record",
                    "Some locations have limited historical data"
                ],
                endpoints=[
                    Endpoint(
                        path="/current.json",
                        method="GET",
                        description="Current weather conditions",
                        parameters={
                            "key": "Your API key",
                            "q": "Location (city, zip, coords)",
                            "aqi": "Include air quality (yes/no)"
                        },
                        required_params=["key", "q"]
                    )
                ],
                setup_instructions="1. Register at weatherapi.com\n2. API key instantly available\n3. Use 'key' parameter",
                pricing="Free: 1M calls/month, Pro: $4/month"
            ),
            
            # Messaging Providers
            Provider(
                name="Slack",
                category="messaging",
                base_url="https://slack.com/api",
                auth_type=AuthType.BEARER_TOKEN,
                description="Team collaboration and messaging platform",
                pros=[
                    "Rich formatting with blocks and attachments",
                    "Interactive components (buttons, menus)",
                    "Webhooks for simple posting",
                    "Extensive API for workspace automation"
                ],
                cons=[
                    "Complex OAuth flow for full access",
                    "Rate limits vary by method",
                    "Workspace admin approval often required"
                ],
                endpoints=[
                    Endpoint(
                        path="/chat.postMessage",
                        method="POST",
                        description="Post a message to a channel",
                        parameters={
                            "channel": "Channel ID or name (#general)",
                            "text": "Message text",
                            "blocks": "Rich block-based layout",
                            "thread_ts": "Thread timestamp for replies"
                        },
                        required_params=["channel", "text"]
                    ),
                    Endpoint(
                        path="/conversations.list",
                        method="GET",
                        description="List channels in workspace",
                        parameters={
                            "types": "Channel types (public_channel,private_channel)",
                            "limit": "Number of results"
                        },
                        required_params=[]
                    )
                ],
                setup_instructions="1. Create Slack app at api.slack.com\n2. Add OAuth scopes (chat:write)\n3. Install to workspace\n4. Use Bot User OAuth Token",
                pricing="Free for basic API usage",
                rate_limits="1+ per second for most methods"
            ),
            
            Provider(
                name="Discord",
                category="messaging",
                base_url="https://discord.com/api/v10",
                auth_type=AuthType.BEARER_TOKEN,
                description="Gaming and community chat platform",
                pros=[
                    "Webhooks for easy message posting",
                    "Rich embeds with images and fields",
                    "No approval needed for webhooks",
                    "Bot framework for advanced features"
                ],
                cons=[
                    "Bot requires server admin to add",
                    "Complex permissions system",
                    "Rate limits on message sending"
                ],
                endpoints=[
                    Endpoint(
                        path="/webhooks/{webhook_id}/{webhook_token}",
                        method="POST",
                        description="Post via webhook (easiest method)",
                        parameters={
                            "content": "Message text",
                            "username": "Override webhook username",
                            "avatar_url": "Override webhook avatar",
                            "embeds": "Rich embed objects"
                        },
                        required_params=["content"]
                    ),
                    Endpoint(
                        path="/channels/{channel_id}/messages",
                        method="POST",
                        description="Post as bot (requires bot token)",
                        parameters={
                            "content": "Message text",
                            "embeds": "Rich embeds",
                            "components": "Interactive components"
                        },
                        required_params=["content"]
                    )
                ],
                setup_instructions="Webhook: Server Settings → Integrations → Create Webhook\nBot: discord.com/developers → Create App → Add Bot",
                pricing="Free",
                rate_limits="5 messages per 5 seconds per channel"
            ),
            
            Provider(
                name="Telegram",
                category="messaging",
                base_url="https://api.telegram.org/bot{token}",
                auth_type=AuthType.API_KEY,
                description="Secure messaging with powerful bot API",
                pros=[
                    "Simple bot creation via @BotFather",
                    "No approval process",
                    "Rich formatting (Markdown/HTML)",
                    "File uploads up to 50MB"
                ],
                cons=[
                    "Users must start conversation with bot first",
                    "Need chat_id to send messages",
                    "Limited to bot interactions"
                ],
                endpoints=[
                    Endpoint(
                        path="/sendMessage",
                        method="POST",
                        description="Send text message",
                        parameters={
                            "chat_id": "Target chat ID",
                            "text": "Message text",
                            "parse_mode": "Markdown or HTML",
                            "reply_markup": "Inline keyboard"
                        },
                        required_params=["chat_id", "text"]
                    ),
                    Endpoint(
                        path="/getUpdates",
                        method="GET",
                        description="Get bot updates (messages, etc)",
                        parameters={
                            "offset": "Update ID to start from",
                            "limit": "Max updates to return"
                        },
                        required_params=[]
                    )
                ],
                setup_instructions="1. Message @BotFather on Telegram\n2. Send /newbot and follow prompts\n3. Copy bot token\n4. Get chat_id from getUpdates",
                pricing="Free",
                rate_limits="30 messages/second"
            ),
            
            # Payment Providers
            Provider(
                name="Stripe",
                category="payments",
                base_url="https://api.stripe.com/v1",
                auth_type=AuthType.BEARER_TOKEN,
                description="Full-featured payment processing platform",
                pros=[
                    "Excellent documentation",
                    "Test mode with fake cards",
                    "Handles compliance (PCI, etc)",
                    "Subscriptions and one-time payments"
                ],
                cons=[
                    "2.9% + 30¢ per transaction",
                    "Complex for simple use cases",
                    "KYC requirements for live mode"
                ],
                endpoints=[
                    Endpoint(
                        path="/payment_intents",
                        method="POST",
                        description="Create a payment intent",
                        parameters={
                            "amount": "Amount in cents",
                            "currency": "Three-letter ISO code",
                            "payment_method_types[]": "Payment methods",
                            "description": "Payment description"
                        },
                        required_params=["amount", "currency"]
                    ),
                    Endpoint(
                        path="/charges",
                        method="GET",
                        description="List charges",
                        parameters={
                            "limit": "Number of charges",
                            "created": "Filter by creation date"
                        },
                        required_params=[]
                    )
                ],
                setup_instructions="1. Sign up at stripe.com\n2. Get API keys from dashboard\n3. Use 'Bearer sk_test_...' for auth\n4. Test with card 4242 4242 4242 4242",
                pricing="2.9% + 30¢ per successful charge",
                example_credentials={"test_key": "sk_test_..."}
            ),
            
            Provider(
                name="PayPal",
                category="payments",
                base_url="https://api-m.sandbox.paypal.com",
                auth_type=AuthType.OAUTH2,
                description="Widely accepted payment platform",
                pros=[
                    "Trusted by consumers",
                    "International support",
                    "Buyer/seller protection",
                    "Multiple integration options"
                ],
                cons=[
                    "Higher fees than Stripe",
                    "Complex API structure",
                    "OAuth2 token management"
                ],
                endpoints=[
                    Endpoint(
                        path="/v2/checkout/orders",
                        method="POST",
                        description="Create an order",
                        parameters={
                            "intent": "CAPTURE or AUTHORIZE",
                            "purchase_units": "Array of items",
                            "application_context": "Checkout experience"
                        },
                        required_params=["intent", "purchase_units"]
                    )
                ],
                setup_instructions="1. Create app at developer.paypal.com\n2. Get client ID and secret\n3. Exchange for access token\n4. Use sandbox for testing",
                pricing="2.99% + 49¢ per transaction"
            ),
            
            # Database Providers
            Provider(
                name="Supabase",
                category="database",
                base_url="https://{project_ref}.supabase.co/rest/v1",
                auth_type=AuthType.API_KEY,
                description="Open source Firebase alternative with Postgres",
                pros=[
                    "Generous free tier",
                    "Real-time subscriptions",
                    "Built-in auth",
                    "SQL database with REST API"
                ],
                cons=[
                    "Requires project setup",
                    "RLS (security) configuration needed",
                    "Limited compute on free tier"
                ],
                endpoints=[
                    Endpoint(
                        path="/{table_name}",
                        method="GET",
                        description="Query table data",
                        parameters={
                            "select": "Columns to return",
                            "order": "Sort order",
                            "limit": "Max rows",
                            "offset": "Skip rows"
                        },
                        required_params=[]
                    ),
                    Endpoint(
                        path="/{table_name}",
                        method="POST",
                        description="Insert new rows",
                        parameters={
                            "_body": "JSON object or array"
                        },
                        required_params=["_body"]
                    )
                ],
                setup_instructions="1. Create project at supabase.com\n2. Get URL and anon key\n3. Set up tables and RLS policies\n4. Use 'apikey' header",
                pricing="Free: 500MB database, 2GB bandwidth"
            )
        ]
    
    def _organize_by_category(self) -> Dict[str, List[Provider]]:
        """Organize providers by category for easy lookup."""
        categories = {}
        for provider in self.providers:
            if provider.category not in categories:
                categories[provider.category] = []
            categories[provider.category].append(provider)
        return categories
    
    def get_providers_by_category(self, category: str) -> List[Provider]:
        """Get all providers in a specific category."""
        return self.categories.get(category.lower(), [])
    
    def search_providers(self, query: str) -> List[Provider]:
        """
        Search providers by name, category, or description.
        
        AI_CONTEXT: This performs fuzzy matching on provider attributes
        to find relevant providers based on user input.
        """
        query_lower = query.lower()
        matches = []
        
        for provider in self.providers:
            score = 0
            
            # Check name match
            if query_lower in provider.name.lower():
                score += 10
            
            # Check category match
            if query_lower in provider.category:
                score += 5
            
            # Check description match
            if query_lower in provider.description.lower():
                score += 3
            
            # Check if query matches common terms
            if any(query_lower in pro.lower() for pro in provider.pros):
                score += 2
            
            if score > 0:
                matches.append((score, provider))
        
        # Sort by score and return providers
        matches.sort(key=lambda x: x[0], reverse=True)
        return [provider for _, provider in matches]
    
    def get_provider(self, name: str) -> Optional[Provider]:
        """Get a specific provider by name."""
        for provider in self.providers:
            if provider.name.lower() == name.lower():
                return provider
        return None
    
    def suggest_providers(self, intent: str) -> List[Provider]:
        """
        Suggest providers based on user intent.
        
        AI_CONTEXT: This method analyzes the user's intent and suggests
        the most appropriate providers, considering factors like ease of use,
        features, and common use cases.
        """
        intent_lower = intent.lower()
        suggestions = []
        
        # Weather intent patterns
        if any(word in intent_lower for word in ['weather', 'temperature', 'forecast', 'climate']):
            suggestions.extend(self.get_providers_by_category('weather'))
        
        # Messaging intent patterns
        if any(word in intent_lower for word in ['message', 'notify', 'alert', 'send', 'post', 'chat']):
            suggestions.extend(self.get_providers_by_category('messaging'))
        
        # Payment intent patterns
        if any(word in intent_lower for word in ['payment', 'charge', 'pay', 'transaction', 'money']):
            suggestions.extend(self.get_providers_by_category('payments'))
        
        # Database intent patterns
        if any(word in intent_lower for word in ['database', 'store', 'save', 'query', 'data']):
            suggestions.extend(self.get_providers_by_category('database'))
        
        # If no specific matches, try general search
        if not suggestions:
            suggestions = self.search_providers(intent)[:3]
        
        return suggestions
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available categories."""
        return list(self.categories.keys())