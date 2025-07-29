# API Client Usage

The Robutler API client provides programmatic access to Robutler services, including agent management, intent handling, and payment processing. Built on async/await for modern Python applications.

## Overview

The API client offers:

- **Agent Management**: Create, list, and manage agents
- **Intent System**: Register and discover agent capabilities  
- **Payment Processing**: Handle payment tokens and billing
- **Usage Tracking**: Monitor credits and token consumption
- **Async Support**: Built for modern async Python applications

## Basic Usage

### Client Initialization

```python
from robutler.api import RobutlerApi

# Using environment variables (recommended)
# Set ROBUTLER_API_KEY=rok_your-api-key
async with RobutlerApi() as api:
    # Your API calls here
    pass

# Explicit API key
async with RobutlerApi(api_key="rok_your-api-key") as api:
    # Your API calls here
    pass

# Custom base URL
async with RobutlerApi(
    api_key="rok_your-api-key",
    base_url="https://custom.robutler.net"
) as api:
    # Your API calls here
    pass
```

### Context Manager Pattern

```python
# Recommended: Use context manager for automatic cleanup
async with RobutlerApi() as api:
    agents = await api.list_agents()
    print(f"Found {len(agents)} agents")
# Client automatically closes

# Alternative: Manual management
api = RobutlerApi()
try:
    agents = await api.list_agents()
finally:
    await api.close()
```

## Agent Management

### Listing Agents

```python
async with RobutlerApi() as api:
    # List all agents for current user
    agents = await api.list_agents()
    
    for agent in agents:
        print(f"Agent: {agent['name']}")
        print(f"  Description: {agent['description']}")
        print(f"  URL: {agent['url']}")
        print(f"  Created: {agent['created_at']}")
```

### Agent Details

```python
async with RobutlerApi() as api:
    # Get specific agent information
    agent = await api.get_agent("agent-id-123")
    
    print(f"Agent: {agent['name']}")
    print(f"Instructions: {agent['instructions']}")
    print(f"Model: {agent['model']}")
    print(f"Pricing: {agent['credits_per_token']} credits/token")
```

### Creating Agents

```python
async with RobutlerApi() as api:
    # Create a new agent
    agent = await api.create_agent(
        name="data-analyst",
        description="Specialized in data analysis and visualization",
        instructions="You are an expert data analyst...",
        model="gpt-4o",
        credits_per_token=15,
        tools=["pandas_analysis", "chart_generation"]
    )
    
    print(f"Created agent: {agent['id']}")
    print(f"Agent URL: {agent['url']}")
```

## Intent Management

### Creating Intents

```python
async with RobutlerApi() as api:
    # Register agent capabilities
    intent = await api.create_intent(
        intent="help with data analysis and visualization",
        agent_id="data-analyst",
        agent_description="Expert in data analysis",
        user_id="user-123",
        url="http://localhost:8000/data-analyst"
    )
    
    print(f"Registered intent: {intent['intent']}")
    print(f"Agent: {intent['agent_id']}")
```

### Listing Intents

```python
async with RobutlerApi() as api:
    # List all intents for a user
    intents = await api.list_intents(user_id="user-123")
    
    for intent in intents:
        print(f"Intent: {intent['intent']}")
        print(f"  Agent: {intent['agent_id']}")
        print(f"  URL: {intent['url']}")
```

### Deleting Intents

```python
async with RobutlerApi() as api:
    # Remove an intent
    result = await api.delete_intent(
        intent_id="intent-456",
        user_id="user-123"
    )
    
    if result['success']:
        print("Intent deleted successfully")
```

### Intent Discovery

```python
async with RobutlerApi() as api:
    # Find agents based on natural language
    results = await api.discover_agents(
        intent="I need help with Python programming"
    )
    
    print(f"Found {len(results['agents'])} matching agents:")
    for agent in results['agents']:
        print(f"  {agent['agent_id']} (confidence: {agent['confidence']:.2f})")
        print(f"  URL: {agent['url']}")
```

## Payment System Integration

### Payment Tokens

```python
async with RobutlerApi() as api:
    # Create a payment token
    token = await api.create_payment_token(
        amount=10000,  # 10,000 credits
        description="Development testing"
    )
    
    print(f"Payment token: {token['token']}")
    print(f"Balance: {token['balance']} credits")
    print(f"Expires: {token['expires_at']}")
```

### Token Validation

```python
async with RobutlerApi() as api:
    # Validate a payment token
    validation = await api.validate_payment_token("pt_abc123...")
    
    if validation['valid']:
        print(f"Token is valid")
        print(f"Balance: {validation['balance']} credits")
        print(f"Expires: {validation['expires_at']}")
    else:
        print(f"Token is invalid: {validation['reason']}")
```

### Charging Tokens

```python
async with RobutlerApi() as api:
    # Charge credits from a payment token
    result = await api.charge_payment_token(
        token="pt_abc123...",
        amount=500  # 500 credits
    )
    
    if result['success']:
        print(f"Charged 500 credits")
        print(f"Remaining balance: {result['remaining_balance']}")
    else:
        print(f"Charge failed: {result['error']}")
```

## Usage Tracking

### Recording Usage

```python
async with RobutlerApi() as api:
    # Record usage for billing
    usage = await api.record_usage(
        user_id="user-123",
        agent_id="data-analyst",
        credits_used=750,
        tokens_consumed=50,
        request_id="req-789",
        metadata={
            "operation": "data_analysis",
            "input_size": "large",
            "processing_time": 3.2
        }
    )
    
    print(f"Usage recorded: {usage['id']}")
```

## Error Handling

### API Exceptions

```python
from robutler.api import RobutlerApi, RobutlerApiError

async def safe_api_call():
    """Example of comprehensive error handling."""
    try:
        async with RobutlerApi() as api:
            agents = await api.list_agents()
            return agents
            
    except RobutlerApiError as e:
        print(f"API Error: {e.message}")
        if e.status_code == 401:
            print("Authentication failed")
        elif e.status_code == 402:
            print("Insufficient credits")
        elif e.status_code == 429:
            print("Rate limit exceeded")
        return None
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None
```

### Retry Logic

```python
import asyncio

async def retry_api_call(func, max_retries: int = 3, backoff: float = 1.0):
    """Retry API calls with exponential backoff."""
    
    for attempt in range(max_retries):
        try:
            return await func()
            
        except RobutlerApiError as e:
            if e.status_code in [500, 502, 503, 504] and attempt < max_retries - 1:
                wait_time = backoff * (2 ** attempt)
                await asyncio.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} attempts")

# Usage
async def robust_agent_list():
    async def api_call():
        async with RobutlerApi() as api:
            return await api.list_agents()
    
    return await retry_api_call(api_call)
```

## Configuration

### Environment Variables

```bash
# Required
export ROBUTLER_API_KEY=rok_your-api-key

# Optional
export ROBUTLER_URL=https://robutler.net    # Custom API endpoint
export ROBUTLER_TIMEOUT=30                  # Request timeout in seconds
```

### Client Configuration

```python
async with RobutlerApi(
    api_key="rok_your-api-key",
    base_url="https://robutler.net",
    timeout=30.0
) as api:
    # Configured client
    pass
```

## Best Practices

### Authentication

- Store API keys in environment variables
- Rotate API keys regularly
- Use different keys for different environments
- Never commit API keys to version control

### Error Handling

- Always use try/except blocks
- Handle specific exceptions appropriately
- Implement retry logic for transient errors
- Log errors for debugging

### Performance

- Use async/await consistently
- Use batch operations when possible
- Cache results when appropriate

### Resource Management

- Always use context managers
- Close clients properly
- Monitor connection usage
- Set appropriate timeouts

The Robutler API client provides a powerful, async-first interface for integrating Robutler services into your applications. 