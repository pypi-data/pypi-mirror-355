# Core Client

The core API client provides comprehensive access to all Robutler backend services including user management, credit tracking, payment tokens, integrations, and intent-based agent routing.

## Quick Start

```python
from robutler.api import RobutlerApi, RobutlerApiError

# Basic usage with context manager
async with RobutlerApi() as api:
    try:
        # Validate connection
        await api.validate_connection()
        
        # Get user information
        user = await api.get_user_info()
        print(f"Welcome {user['name']}!")
        
        # Check credit balance
        credits = await api.get_user_credits()
        print(f"Available credits: {credits['availableCredits']}")
        
    except RobutlerApiError as e:
        print(f"API Error: {e.message}")
```

## Environment Configuration

```bash
# Set environment variables
export ROBUTLER_API_KEY="your-api-key"
export ROBUTLER_BACKEND_URL="https://api.robutler.ai"
```

## Integration Examples

### Batch Operations

```python
import asyncio

async def get_account_summary():
    async with RobutlerApi() as api:
        # Run multiple operations concurrently
        user, credits, keys = await asyncio.gather(
            api.get_user_info(),
            api.get_user_credits(),
            api.list_api_keys()
        )
        
        return {
            "user": user,
            "credits": credits,
            "api_keys": len(keys)
        }
```

### Intent-Based Agent Discovery

```python
async def find_coding_agent():
    async with RobutlerApi() as api:
        # Search for agents that can help with programming
        results = await api.search_intents(
            intent="help with Python programming",
            top_k=3
        )
        
        if results['data']['results']:
            best_agent = results['data']['results'][0]
            print(f"Best match: {best_agent['agent_id']}")
            print(f"Similarity: {best_agent['similarity']:.2f}")
            return best_agent['url']
```

## API Reference

## RobutlerApi

::: robutler.api.client.RobutlerApi
    options:
        members:
            - __init__
            - validate_connection
            - health_check
            - get_user_info
            - get_user_credits
            - list_api_keys
            - create_api_key
            - get_api_key
            - delete_api_key
            - get_api_key_stats
            - validate_payment_token
            - redeem_payment_token
            - issue_payment_token
            - cancel_payment_token
            - list_integrations
            - create_integration
            - get_integration
            - delete_integration
            - intent_health_check
            - create_intent
            - search_intents
            - list_intents
            - delete_intent

## Initialization

::: robutler.api.client.initialize_api 