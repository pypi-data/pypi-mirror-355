# Server & Agent Setup

Robutler provides two main components: `RobutlerAgent` for creating AI agents and `RobutlerServer` for serving them as OpenAI-compatible APIs.

## RobutlerAgent

Creates AI agents with automatic usage tracking and payment integration.

### Basic Usage

```python
from robutler.agent import RobutlerAgent

agent = RobutlerAgent(
    name="assistant",
    instructions="You are a helpful AI assistant.",
    credits_per_token=10,
    model="gpt-4o-mini"
)

# Use the agent
messages = [{"role": "user", "content": "Hello!"}]
response = await agent.run(messages=messages, stream=False)
print(response)
```

### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | `str` | Agent identifier (URL-safe) | Required |
| `instructions` | `str` | System instructions | Required |
| `credits_per_token` | `int` | Cost per token | `10` |
| `tools` | `List[Callable]` | Functions the agent can call | `[]` |
| `model` | `str` | OpenAI model | `"gpt-4o-mini"` |
| `intents` | `List[str]` | Descriptions for routing | `[]` |

### Agent with Tools

```python
from agents import function_tool
from robutler.server import pricing

@function_tool
@pricing(credits_per_call=1000)
def get_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent = RobutlerAgent(
    name="assistant",
    instructions="You are a helpful assistant with access to tools.",
    tools=[get_time],
    credits_per_token=5,
    intents=["help with time"]
)
```

### Agent Methods

#### `async run(messages, stream=False)`

Execute the agent:

```python
# Non-streaming
response = await agent.run(messages=messages, stream=False)

# Streaming (returns FastAPI StreamingResponse)
streaming_response = await agent.run(messages=messages, stream=True)
```

## RobutlerServer

FastAPI server that automatically creates endpoints for agents.

### Automatic Endpoints

```python
from robutler.server import RobutlerServer
from robutler.agent import RobutlerAgent

# Create agents
assistant = RobutlerAgent(
    name="assistant",
    instructions="You are helpful",
    credits_per_token=5
)

# Create server - endpoints created automatically
app = RobutlerServer(agents=[assistant])

# Creates:
# POST /assistant/chat/completions - OpenAI chat completions
# GET  /assistant                  - Agent info
```

### Custom Agents

```python
app = RobutlerServer()

@app.agent("/weather/{location}")
@pricing(credits_per_token=12)
async def weather_agent(request, location: str):
    """Custom weather agent."""
    messages = request.messages
    # Add location context
    system_msg = {
        "role": "system", 
        "content": f"You are a weather assistant for {location}."
    }
    messages.insert(0, system_msg)
    
    # Process with OpenAI Agent SDK
    agent = Agent(
        name="weather",
        instructions=f"Provide weather for {location}",
        model="gpt-4o-mini"
    )
    result = await Runner.run(agent, messages)
    return result.final_output
```

### Usage Tracking

Every request gets automatic usage tracking:

```python
from robutler.server import get_server_context

@app.after_request
async def log_usage(request, response, context):
    """Log usage after request."""
    usage = context.get_usage()
    print(f"Total credits: {usage['total_credits']}")
    print(f"Total tokens: {usage['total_tokens']}")
```

### Payment Integration

The server handles payment tokens automatically:

```python
# Client request with payment token
headers = {"X-Payment-Token": "pt_abc123..."}

# Server automatically:
# 1. Validates token
# 2. Checks balance
# 3. Charges credits after request
# 4. Returns 402 if insufficient funds
```

### Running the Server

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

The server provides OpenAI-compatible endpoints with automatic payment handling and usage tracking. 