# Clarification System for Natural Language Tool Creation

The clarification system helps users create tools through conversational interaction, automatically detecting their intent and guiding them through the process with minimal friction.

## Overview

When a user says something like "I need to send notifications to my team", the system:

1. **Detects Intent** - Understands they want messaging capabilities
2. **Suggests Providers** - Offers options like Slack, Discord, Telegram
3. **Gathers Information** - Asks for credentials and preferences conversationally
4. **Learns Patterns** - Remembers successful configurations for future use
5. **Creates Tools** - Generates working, validated tool code

## Components

### 1. Provider Knowledge Base (`providers.py`)

A curated database of popular API providers organized by category:

- **Weather**: OpenWeatherMap, WeatherAPI
- **Messaging**: Slack, Discord, Telegram  
- **Payments**: Stripe, PayPal
- **Database**: Supabase

Each provider includes:
- Endpoints with parameters
- Authentication methods
- Pros/cons for decision making
- Setup instructions
- Pricing information

### 2. Clarifier Engine (`clarifier.py`)

The main orchestrator that:
- Analyzes user intent using NLP
- Manages the clarification flow
- Integrates with pattern learning
- Builds tool configurations

### 3. Dialogue Manager (`dialogue.py`)

Handles conversational interactions:
- Natural language responses
- State management with proper session isolation
- Context preservation across multiple turns
- User-friendly prompts
- Thread-safe session handling for concurrent users
- Automatic session expiration (30 minutes)

### 4. Pattern Learner (`patterns.py`)

Learns from successful tool creations:
- Tracks common intent → provider mappings
- Remembers parameter preferences
- Improves suggestions over time
- Reduces future clarification needs

## Usage Examples

### Basic Flow

```python
User: "I need to send notifications to my team"

Bot: "I found 3 providers that could work for sending notifications to my team. 
     Here are the top options:

     1. **Slack** - Team collaboration and messaging platform
        ✅ Pros: Rich formatting with blocks and attachments; Interactive components
        ⚠️  Cons: Complex OAuth flow for full access
        💰 Free for basic API usage

     2. **Discord** - Gaming and community chat platform
        ✅ Pros: Webhooks for easy message posting; Rich embeds with images
        ⚠️  Cons: Bot requires server admin to add
        💰 Free

     Which would you prefer? (You can say the number or name)"

User: "1"

Bot: "For Slack, you'll need an access token. 
     1. Create Slack app at api.slack.com
     2. Add OAuth scopes (chat:write)
     3. Install to workspace
     4. Use Bot User OAuth Token
     
     Please provide your access token."

User: "xoxb-1234567890-..."

Bot: "Perfect! Here's what I'll create:

     **Tool**: slack_send_notifications
     **Provider**: Slack
     **Endpoint**: /chat.postMessage
     **Purpose**: send notifications to my team

     Shall I create this tool?"

User: "yes"

Bot: "✅ Excellent! I've created the 'slack_send_notifications' tool. 
     You can now use it by saying things like:
     
     - 'Send Meeting at 3pm to #general'
     - 'Post an update to the team channel'
     - 'Notify the team about the deployment'
     
     Would you like to test it now?"
```

### Pattern Learning

After successful creations, the system learns:

```python
# First time - full clarification needed
User: "post to slack"
Bot: [Full clarification flow]

# Next time - learned preferences applied
User: "send slack message" 
Bot: "I'll set up Slack messaging (like last time). 
     I just need your access token."
```

## Session Management

The clarification system supports multiple concurrent sessions:

### Features
- **Session Isolation**: Each user's clarification flow is completely independent
- **Thread Safety**: Multiple users can interact simultaneously without conflicts
- **Session Expiration**: Sessions automatically expire after 30 minutes of inactivity
- **Graceful Recovery**: Expired sessions are handled with helpful messages
- **Unique Session IDs**: Each clarification flow gets a unique identifier

### Example
```python
# User A starts clarification
session_a = tool_creator_clarify(intent="send emails", session_id="user_a_123")

# User B starts different clarification concurrently
session_b = tool_creator_clarify(intent="check weather", session_id="user_b_456")

# Both can continue independently
result_a = tool_creator_continue(session_id="user_a_123", response="gmail")
result_b = tool_creator_continue(session_id="user_b_456", response="weatherapi")
```

## Integration with Tool Creator

The clarification system integrates seamlessly with the tool creator plugin:

```python
# In Claude/orchestrator agent
if user_needs_tool_that_doesnt_exist:
    # Start clarification
    result = tool_creator_clarify(intent="send notifications")
    
    # Continue dialogue
    while result.requires_response:
        user_response = get_user_input(result.message)
        result = tool_creator_continue(
            session_id=result.session_id,
            user_response=user_response
        )
    
    # Tool is created and ready to use
    if result.tool_created:
        use_new_tool(result.tool_config.name)
```

## Customization

### Adding New Providers

Add providers to the knowledge base in `providers.py`:

```python
Provider(
    name="NewService",
    category="messaging",
    base_url="https://api.newservice.com",
    auth_type=AuthType.API_KEY,
    description="Description of the service",
    pros=["List of advantages"],
    cons=["List of limitations"],
    endpoints=[...],
    setup_instructions="How to get started"
)
```

### Extending Pattern Learning

The system automatically learns from usage, but you can also:

- Pre-seed common patterns
- Adjust confidence thresholds
- Customize similarity algorithms
- Add domain-specific intelligence

## Benefits

1. **User-Friendly**: No need to read API docs or understand authentication
2. **Intelligent**: Learns and improves from each interaction
3. **Comprehensive**: Covers the most common integration scenarios
4. **Extensible**: Easy to add new providers and patterns
5. **Secure**: Guides proper credential handling

## Future Enhancements

- [ ] Auto-discovery of API endpoints from documentation
- [ ] GraphQL support
- [ ] WebSocket/real-time API support
- [ ] Multi-step authentication flows (OAuth2)
- [ ] Batch tool creation from requirements
- [ ] Export/import pattern databases