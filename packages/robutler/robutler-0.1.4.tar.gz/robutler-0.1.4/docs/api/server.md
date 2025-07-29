# RobutlerServer

Deploy agents as OpenAI-compatible API endpoints with built-in credit tracking, payment token validation, and usage monitoring.

## Quick Start

```python
from robutler.agent import RobutlerAgent
from robutler.server import RobutlerServer

# Create an agent
agent = RobutlerAgent(
    name="my-agent",
    instructions="You are a helpful assistant.",
    credits_per_token=5
)

# Create server and add agent
server = RobutlerServer(agents=[agent])

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(server, host="0.0.0.0", port=8000)
```

## Response Formats

### Chat Completion Response
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "agent-name",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

### Error Response
```json
{
  "error": {
    "message": "Insufficient credits",
    "type": "insufficient_credits",
    "code": 402
  }
}
```

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `400` | Bad Request | Invalid request format |
| `401` | Unauthorized | Invalid or missing API key |
| `402` | Payment Required | Insufficient credits |
| `404` | Not Found | Agent/endpoint not found |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |

## API Reference

The RobutlerServer module provides a FastAPI-based server framework with built-in credit tracking, payment token validation, and OpenAI-compatible endpoints.

## Core Classes

::: robutler.server.server.RobutlerServer
    options:
        members:
            - __init__
            - agent
            - before_request
            - after_request
            - finalize_request

## Context Management

::: robutler.server.server.ServerContext
    options:
        members:
            - __init__
            - track_usage
            - get_usage
            - set_custom_data
            - get_custom_data

::: robutler.server.server.get_server_context

## Usage Tracking

::: robutler.server.server.ReportUsage

::: robutler.server.server.pricing

## Utility Functions

::: robutler.server.server._estimate_tokens_standalone

## Built-in Callbacks

::: robutler.server.server.robutler_before

::: robutler.server.server.robutler_extract_context 