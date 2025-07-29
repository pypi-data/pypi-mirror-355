# MCP Integration

Robutler provides Model Context Protocol (MCP) integration, enabling AI assistants like Claude Desktop and ChatGPT to access Robutler agents and tools directly.

## Available Tools

The MCP server automatically provides these tools to AI clients:

### Agent Discovery
```python
# Tool: robutler_discovery
# Find agents based on natural language descriptions

result = await session.call_tool(
    "robutler_discovery",
    {"intent": "help with Python programming", "top_k": 5}
)
```

### Natural Language Interface
```python
# Tool: robutler_nli
# Communicate with any RobutlerAgent server

result = await session.call_tool(
    "robutler_nli",
    {
        "agent_url": "http://localhost:8000/assistant", 
        "message": "What's the weather like today?"
    }
)
```

## Running the MCP Server

### Command Line
```bash
# Default stdio transport (for Claude Desktop)
python -m robutler.connect.MCP

# SSE transport for web integration
python -m robutler.connect.MCP --transport=sse --port=8000

# HTTP transport for API integration
python -m robutler.connect.MCP --transport=streamable-http --port=8000
```

### Programmatic Usage
```python
from robutler.connect.MCP import run_mcp

# Run with custom configuration
run_mcp([
    "--transport", "sse",
    "--port", "8000",
    "--name", "Robutler MCP Server"
])
```

## Claude Desktop Integration

Add to your Claude Desktop MCP configuration file:

```json
{
  "mcpServers": {
    "robutler": {
      "command": "python",
      "args": ["-m", "robutler.connect.MCP"],
      "env": {
        "ROBUTLER_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Usage Example
```
User: Find me an agent that can help with data analysis

Claude: [Uses robutler_discovery tool]
I found a data-analyst agent. Would you like me to connect to it?

User: Yes, ask it to analyze my sales data

Claude: [Uses robutler_nli tool] 
The data-analyst responded: "Please provide your data in CSV format..."
```

## Transport Protocols

**stdio**: Direct integration with desktop AI assistants (default)
```bash
python -m robutler.connect.MCP  # For Claude Desktop
```

**sse**: Server-Sent Events for web applications  
```bash
python -m robutler.connect.MCP --transport=sse --port=8000
```

**streamable-http**: HTTP with streaming for API integration
```bash
python -m robutler.connect.MCP --transport=streamable-http --port=8000
```

## Configuration

### Environment Variables
```bash
# Required for tools to function
ROBUTLER_API_KEY=rok_your-api-key

# Optional
ROBUTLER_URL=https://robutler.net
```

### Command Line Arguments
```bash
python -m robutler.connect.MCP \
  --transport sse \              # Transport protocol
  --host 0.0.0.0 \              # Host address
  --port 8000 \                 # Port number
  --name "My MCP Server"        # Server name
```

## Custom Tools

Add custom tools to the MCP server:

```python
from robutler.connect.MCP import mcp

@mcp.tool()
async def custom_search(query: str) -> str:
    """Custom search tool."""
    return f"Search results for: {query}"

@mcp.tool()
async def data_analysis(data: str) -> str:
    """Analyze data and return insights."""
    return analyze_data(data)
```

## Client Integration

### Web Application
```javascript
// Connect to SSE MCP server
const eventSource = new EventSource('http://localhost:8000/sse');

// Call MCP tool
async function callTool(toolName, args) {
    const response = await fetch('http://localhost:8000/call-tool', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: toolName, arguments: args})
    });
    return await response.json();
}
```

### Python Client
```python
import httpx

async def discover_agents(intent: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
            "http://localhost:8000/call-tool",
                json={
                "name": "robutler_discovery",
                "arguments": {"intent": intent}
                }
            )
            return response.json()

# Usage
agents = await discover_agents("help with Python programming")
```

## Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["python", "-m", "robutler.connect.MCP", "--transport=sse", "--host=0.0.0.0", "--port=8000"]
```

```bash
docker run -d -p 8000:8000 -e ROBUTLER_API_KEY=your-key robutler-mcp
```

## Troubleshooting

**Tool not found**: Ensure `ROBUTLER_API_KEY` is set
**Connection refused**: Check agent URLs and availability  
**Port conflicts**: Use different port with `--port` argument

```bash
# Health check for HTTP transports
curl http://localhost:8000/health

# Test tool availability  
curl -X POST http://localhost:8000/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "robutler_discovery", "arguments": {"intent": "test"}}'
```

The MCP integration makes Robutler tools accessible to any MCP-compatible AI assistant, enabling seamless integration into existing AI workflows. 