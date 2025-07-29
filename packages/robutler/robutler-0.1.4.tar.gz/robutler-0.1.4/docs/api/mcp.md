# MCP (Model Context Protocol)

The MCP module provides a FastMCP-based server that integrates with the Robutler ecosystem, offering tools for intent discovery, natural language interface (NLI), and agent routing capabilities.

## Server Instance

::: robutler.connect.MCP.mcp

## Entry Point

::: robutler.connect.MCP.run_mcp

## Available Tools

The MCP server provides several built-in tools for interacting with the Robutler ecosystem:

### Utility Tools

- **echo**: Simple text echo for testing connectivity
- **generate_image**: Create solid color images for demonstrations

### Robutler Integration Tools

- **robutler_discovery**: Search for agents using natural language intents
- **robutler_nli**: Natural Language Interface for conversational queries

## Transport Protocols

The server supports multiple transport protocols:

- **stdio**: Standard input/output for desktop applications (default)
- **sse**: Server-Sent Events for web applications  
- **streamable-http**: HTTP with streaming support for API integration

## Configuration

The server can be configured via command-line arguments:

- `--transport`: Choose transport protocol
- `--host`: Host address for HTTP-based transports
- `--port`: Port number for HTTP-based transports
- `--path`: URL path for HTTP endpoints
- `--name`: Custom server name

## Usage Examples

### Command Line

```bash
# Default stdio transport
python -m robutler.connect.MCP

# Web application with SSE
python -m robutler.connect.MCP --transport=sse --port=3000

# Production API server
python -m robutler.connect.MCP --transport=streamable-http --port=8080
```

### Programmatic

```python
from robutler.connect.MCP import run_mcp

# Run with custom configuration
run_mcp(['--transport=sse', '--port=8080'])
```

### Claude Desktop Integration

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

# MCP Integration

Connect to Model Context Protocol servers for external tools and agent communication.

## Quick Start

```python
from robutler.connect.MCP import mcp, run_mcp

# Run MCP server with Robutler tools
if __name__ == "__main__":
    run_mcp()
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ROBUTLER_API_KEY` | Robutler API key for tool functionality | Required |
| `ROBUTLER_URL` | Robutler backend URL | `https://robutler.net` |
| `ROBUTLER_MCP_NAME` | MCP server display name | `"Robutler MCP Server"` |

## API Reference

::: robutler.connect.MCP 