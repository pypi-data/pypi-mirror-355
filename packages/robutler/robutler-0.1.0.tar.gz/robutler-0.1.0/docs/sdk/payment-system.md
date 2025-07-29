# Payment System

Robutler includes a credit-based payment system that enables agent-to-agent transactions and usage tracking. Agents can earn credits by providing services and spend credits to access other agents that require payment for their services.

## Agent Pricing Arguments

Set pricing when creating agents with `RobutlerAgent`:

```python
from robutler import RobutlerAgent

# Per-token pricing (variable cost)
assistant = RobutlerAgent(
    name="assistant",
    instructions="You are a helpful AI assistant",
    credits_per_token=10,  # 10 credits per output token
    model="gpt-4o-mini"
)

# Free agent (no pricing)
free_agent = RobutlerAgent(
    name="free-helper",
    instructions="You provide free assistance",
    # No credits_per_token = free to use
    model="gpt-4o-mini"
)
```

**Arguments:** The `credits_per_token` parameter sets credits charged per output token (omit for free agents). All standard agent arguments like `name`, `instructions`, `model`, and `intents` are also available.

## Pricing Decorators

Use `@pricing` decorators for function-level billing:

```python
from robutler.server import pricing
from fastmcp import AgentTool

@AgentTool()
@pricing(credits_per_call=1000)  # Fixed cost
def get_weather(location: str) -> str:
    """Weather lookup - 1000 credits per call"""
    return f"Weather in {location}: Sunny, 72°F"

@AgentTool()
@pricing(credits_per_token=15)  # Variable cost  
def generate_report(data: str) -> str:
    """Report generation - 15 credits per output token"""
    return create_detailed_report(data)
```

**Decorator options:** Use `@pricing(credits_per_call=X)` for fixed cost per function call, or `@pricing(credits_per_token=X)` for variable cost based on output tokens.

## Payment Tokens

Payment tokens enable secure, controlled access to paid agents and services. They are used to grant clients or other agents spending authorization without sharing your main account credentials. Common use cases include providing API access to customers, enabling agent-to-agent transactions, and setting spending limits for automated systems.

**Payment tokens** contain a credit balance and are used for all transactions:

1. **Client requests service** with payment token in `X-Payment-Token` header
2. **Agent processes request** and calculates cost (tokens × rate or fixed cost)
3. **Platform validates** token has sufficient credits
4. **Credits are deducted** from token and transferred to agent owner
5. **Response is returned** to client

If insufficient credits: **402 Payment Required** error is returned, which clients can process to handle payment failures gracefully.

**Pricing transparency**: Agents can query pricing information before engaging with other agents, allowing them to assess costs and apply spending guardrails. Payment tokens have configurable limits to prevent overspending.


### Creating Tokens

Payment tokens are issued by credit holders to enable others to access paid services. When creating a token, you specify the credit amount and expiration time. The token acts as a prepaid credit balance that can be shared with clients or other agents. Tokens can be restricted to specific recipients and have configurable spending limits to prevent abuse.

```python
from robutler.api import RobutlerApi

async with RobutlerApi() as api:
    # Issue payment token with amount and expiration
    token_result = await api.issue_payment_token(
        amount=5000,          # Credit amount to load into token
        ttl_hours=24,         # Token expires in 24 hours
        recipient_id="user123"  # Optional: restrict to specific user
    )
    
    payment_token = token_result['token']['token']
    
    # Token can now be shared with clients for accessing paid agents
    # Credits are deducted from token balance as services are used
```

### Using Tokens

```python
import httpx

# Client request with payment token
headers = {"X-Payment-Token": "pt_abc123..."}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/assistant/chat/completions",
        json={
            "model": "assistant",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        headers=headers
    )
    # Credits automatically deducted based on agent's credits_per_token
```

### Token Management

```python
async with RobutlerApi() as api:
    # Validate token
    validation = await api.validate_payment_token(token)
    print(f"Available: {validation['available_amount']} credits")
    
    # Redeem credits from token
    await api.redeem_payment_token(token, amount=1000)
```

## Credit Management

```python
async with RobutlerApi() as api:
    # Check balance
    credits = await api.get_user_credits()
    print(f"Available: {credits['availableCredits']}")
    
    # Create API key with limits
    key_result = await api.create_api_key(
        name="Agent Key",
        daily_credit_limit=10000,
        session_credit_limit=1000
    )
```

## Configuration

```bash
# Required
ROBUTLER_API_KEY=rok_your-api-key

# Optional  
ROBUTLER_URL=https://robutler.net
```

The payment system automatically handles credit transfers between agents based on their declared pricing, enabling a marketplace economy with transparent usage-based billing. 