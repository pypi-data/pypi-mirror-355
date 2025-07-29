# RobutlerAgent

The main class for creating AI agents with tools, conversation memory, and payment integration.

## Quick Start

```python
from robutler.agent import RobutlerAgent

agent = RobutlerAgent(
    name="my-agent",
    instructions="You are a helpful assistant.",
    credits_per_token=10,
    model="gpt-4o-mini"
)

# Basic usage
messages = [{"role": "user", "content": "Hello!"}]
response = await agent.run(messages=messages)
```

## Common Patterns

### Basic Agent
```python
agent = RobutlerAgent(
    name="assistant",
    instructions="You are helpful.",
    credits_per_token=5,
    model="gpt-4o-mini"
)

response = await agent.run(messages=[
    {"role": "user", "content": "Hello!"}
])
```

### Agent with Tools
```python
from agents import function_tool
from robutler.server import pricing

@function_tool
@pricing(credits_per_call=1000)
def calculate(expression: str) -> str:
    """Calculate a mathematical expression."""
    return str(eval(expression))

agent = RobutlerAgent(
    name="calculator",
    instructions="You can calculate math expressions.",
    tools=[calculate],
    credits_per_token=8
)
```

## API Reference

::: robutler.agent.agent

    options:
        members:
            - RobutlerAgent 