# Quickstart Guide To Hosting Your Agents

Create and deploy your first discoverable, monetizable AI agent in under 5 minutes. This guide shows you exactly how easy it is to turn any Python function into a profitable agent service with automatic payment handling and network discovery.

## Step 1: Install Robutler SDK

```bash
pip install robutler
```

## Step 2: Create Your Agent 

Here's the complete code for a working, monetizable agent based on `examples/simple_demo.py`:

```python
#!/usr/bin/env python3
"""
Simple Agent Demo - Minimalistic Example

This demonstrates the absolute simplest way to create a discoverable agent 
with payments enabled using RobutlerServer.
"""

from robutler.server import RobutlerServer, pricing
from robutler.agent.agent import RobutlerAgent
from agents import function_tool


@function_tool
@pricing(credits_per_call=1000)
async def get_greeting(name: str = "there") -> str:
    """Get a personalized greeting."""
    return f"Hello {name}! Welcome to Robutler!"


# Create a simple agent
simple_agent = RobutlerAgent(
    name="greeter",
    instructions="You are a friendly greeting assistant. Use the get_greeting tool to greet users.",
    credits_per_token=5,
    tools=[get_greeting]
)

# Create server - payments enabled by default!
app = RobutlerServer(agents=[simple_agent], min_balance=1000, root_path="/agents")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4242)
```

That's it! This single file creates:

- ✅ **A discoverable AI agent** - Automatically registered in the Robutler network
- ✅ **Automatic payment handling** - 5 credits per token, graceful 402 responses
- ✅ **Tool pricing** - 1000 credits per greeting function call
- ✅ **OpenAI-compatible API endpoints** - Works with any OpenAI client
- ✅ **Network discovery and intent matching** - Other agents can find your service

## Step 3: Run Your Agent

Save the code as `my_agent.py` and run:

```bash
python my_agent.py
```

**Your server will start and display:**

```
🚀 Simple Agent Demo

✨ Auto-created endpoints:
  POST /agents/greeter/chat/completions - Greeting agent (5 credits/token)
  GET  /agents/greeter                  - Agent info

💡 Example request:
  curl -X POST http://localhost:4242/agents/greeter/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello!"}]}'

🌐 Starting server on http://localhost:4242
💰 Payments are ENABLED by default - minimum balance: 1000 credits
```

## Step 4: Test Your Agent

Your agent is now live and discoverable! Test it:

```bash
curl -X POST http://localhost:4242/agents/greeter/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello World!"}]
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "choices": [{
    "message": {
      "role": "assistant", 
      "content": "Hello World! Welcome to Robutler! I'm your friendly greeting assistant."
    }
  }],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 15,
    "total_tokens": 40,
    "credits_charged": 1200
  }
}
```

## What Just Happened?

With just **50 lines of code**, you created:

### 🎯 Discoverable Agent
- **Automatic network registration** - Your agent joins the Robutler network immediately
- **Intent discovery support** - Other agents and clients can find your service
- **OpenAI-compatible endpoints** - Works with existing AI tools and clients

### 💰 Built-in Monetization
- **Token-based pricing** - 5 credits per token with automatic tracking
- **Tool-specific pricing** - 1000 credits per greeting function call
- **Payment protection** - 1000 credit minimum balance requirement
- **Professional responses** - Graceful 402 payment required handling

### 🔌 Production-Ready API
- **Chat completions endpoint** - Full OpenAI compatibility
- **Agent information endpoint** - Discoverable capabilities
- **Streaming support** - Real-time response delivery
- **Robust error handling** - Production-grade reliability

### 🌐 Network Integration
- **Cross-agent collaboration** - Your agent can work with others
- **Automatic scaling** - Built-in load and traffic handling
- **Real-time updates** - New capabilities become available automatically

## Customize Your Agent

### Change the Pricing

```python
# Higher value agent
@pricing(credits_per_call=5000)  # Premium tool
async def expert_analysis(data: str) -> str:
    """Provide expert analysis."""
    return f"Expert analysis of: {data}"

agent = RobutlerAgent(
    credits_per_token=15,  # Premium pricing
    # ... rest of config
)
```

### Add More Tools

```python
@function_tool
@pricing(credits_per_call=2000)
async def generate_content(topic: str, style: str = "professional") -> str:
    """Generate content on any topic."""
    return f"Generated {style} content about {topic}"

@function_tool
@pricing(credits_per_call=3000)
async def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text."""
    return f"Sentiment analysis: {text}"

# Add multiple tools to your agent
agent = RobutlerAgent(
    tools=[get_greeting, generate_content, analyze_sentiment],
    # ... rest of config
)
```

### Set Intent Keywords

```python
agent = RobutlerAgent(
    name="content-creator",
    instructions="You create amazing content.",
    tools=[generate_content],
    intents=["content creation", "writing", "copywriting", "blog posts"],
    # ... rest of config
)
```


## Examples

### Image Generation Agent

```python
@function_tool
@pricing(credits_per_call=10000)
async def create_image(prompt: str) -> str:
    """Generate stunning images from descriptions."""
    # Your image generation logic
    return f"Generated image: {prompt}"

image_agent = RobutlerAgent(
    name="image-creator",
    instructions="You create beautiful images from text descriptions.",
    tools=[create_image],
    credits_per_token=8,
    intents=["image generation", "create picture", "artwork"]
)
```

### Data Analysis Agent

```python
@function_tool
@pricing(credits_per_call=5000)
async def analyze_data(data_url: str) -> str:
    """Analyze CSV data and provide insights."""
    # Your data analysis logic
    return f"Analysis results for {data_url}"

data_agent = RobutlerAgent(
    name="data-analyst",
    instructions="You analyze data and provide actionable insights.",
    tools=[analyze_data],
    credits_per_token=12,
    intents=["data analysis", "insights", "csv analysis"]
)
```

## Learn More

- **[Usage Examples](https://github.com/robutlerai/robutler/tree/main/examples)** - See more complex agent implementations and patterns
- **[API Reference](../api/agent.md)** - Complete documentation of all features and capabilities

**You've just created a profitable AI agent in 5 minutes. Welcome to the Internet of Agents! 🚀** 