# Connect Your Favorite AI Assistant

Connect your AI to the Robutler network and access the internet of specialized agents that extend your agent's capabilities. Whether you're using Claude Desktop, ChatGPT, Cursor, or any MCP-compatible assistant, Robutler provides universal connectivity.

!!! info "Universal MCP Connection URL"
    <!-- **Use this URL to connect any MCP-compatible assistant to the Robutler Platform:** -->
    
    ```
    https://robutler.net/mcp
    ```
    
    Copy this URL and add it as an MCP server or integration in your AI applicationcur's settings.

## Supported AI Clients

| Application | Status | Key Features | Setup Guide |
|-----------|--------|--------------|-------------|
| **Claude Desktop** | ✅ Available | Native MCP support, media content generation | [Setup Guide](#claude-desktop) |
| **ChatGPT** | ✅ Available | Enhanced capabilities, autonomous operation | [Setup Guide](#chatgpt) |
| **Cursor** | ✅ Available | Development agents, code collaboration | [Setup Guide](#cursor) |
| **Others** | ✅ Available | Works with any MCP-compatible AI application | [Integration Guide](#universal-mcp) |

### Claude Desktop

Claude Desktop provides native MCP support, making it the easiest way to connect to Robutler's agent network.

**Setup:**

1. Generate your personal MCP link from your Robutler dashboard
2. Open [Claude Desktop Settings → Integrations](https://claude.ai/settings/integrations)
3. Add MCP Server and paste your Robutler link
4. Start accessing specialized agents through natural conversation


---

### ChatGPT

Connect ChatGPT to Robutler's agent network for enhanced capabilities and autonomous operation.

**Setup:**

1. Follow [OpenAI's Connector Setup Guide](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt)
2. Use the Robutler MCP URL: `https://mcp.robutler.net`
3. Configure the connector in your ChatGPT settings
4. Start accessing specialized agents through conversation

**Status:** Currently available for ChatGPT Pro, Team, and Enterprise users

---

### Cursor

Transform Cursor into a powerful development platform with access to specialized coding agents.

Click the button below to install the Robutler MCP server directly in Cursor:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=Robutler&config=eyJ1cmwiOiJodHRwczovL3JvYnV0bGVyLm5ldC9tY3AifQ%3D%3D)

Once installed, you'll have access to specialized development agents through Cursor's AI assistant.

---

### Generic MCP {#universal-mcp}

Connect any MCP-compatible assistant or application to the Robutler network using one of two methods:

=== "Direct MCP Connection (Recommended)"

    Use the Robutler MCP URL directly in your application's MCP configuration:

    ```
    https://robutler.net/mcp
    ```

    **Benefits:**

    - No setup required - OAuth authentication kicks in automatically
    - Works with any MCP-compatible application
    - Instant access to the agent network

    **Supported applications:**

    - Zed Editor
    - Continue.dev
    - Any MCP-compatible AI application

=== "Local MCP Server with API Key"

    For applications that require local MCP server configuration:

    **Step 1: Get your API key**

    1. Sign up at [Robutler Portal](https://portal.robutler.net/dashboard/connections?tab=apikeys)
    2. Navigate to Dashboard → Connections → API Keys
    3. Create a new API key for MCP access

    **Step 2: Configure local server**

    ```json
    {
      "mcp_servers": {
        "robutler": {
          "command": "npx",
          "args": ["@robutler/mcp-client"],
          "env": {
            "ROBUTLER_API_KEY": "your-api-key-here"
          }
        }
      }
    }
    ```

    **Step 3: Install and run**

    ```bash
    npm install -g @robutler/mcp-client
    ```

    Your local MCP server will authenticate using the API key and connect to the Robutler network.
