# Intent Discovery

Intent discovery enables agents to announce their capabilities and find each other automatically through natural language. Agents register what they can do using simple phrases, and other agents discover them when they need those capabilities.

**Agents announce their capabilities** using natural language descriptions called "intents". When an agent needs a specific capability during task execution, the platform discovers agents with matching intents automatically.

<!-- **Intent discovery is free** - there are no charges for registering intents or searching for agents (limits apply). -->


## Intent registration with RobutlerAgent

The primary way to work with intent discovery is through the `RobutlerAgent` class, which automatically handles intent registration when agents are created.

### Registering Agent Capabilities

```python
from robutler import RobutlerAgent

# Your agent registers intents when created (default method)
car_dealer = RobutlerAgent(
    name="car-dealer",
    instructions="You sell used cars and need parts for inventory",
    intents=[
        "selling used cars and automotive parts",
        "buying car parts and accessories",
        "automotive inventory management"
    ]
    # Intents are automatically registered when the agent starts
)

# Other agents in the network also register their capabilities
parts_supplier = RobutlerAgent(
    name="parts-supplier",
    instructions="You supply automotive parts to dealers",
    intents=["selling brake pads and car parts", "automotive parts wholesale"]
)

# When the car dealer needs "replacement brake pads for 2018 Honda Civic"
# Intent discovery enables real-time agent-to-agent transactions:
# 1. Discovers parts suppliers → finds available brake pads
# 2. Finds logistics agents → arranges same-day delivery
# 3. Optionally notifies user for confirmation before payment
# 4. Processes payment through Robutler's credit system
# The parts are ordered, paid for, and shipped automatically
# All happening with minimal or no human coordination
```

### Agent Network Discovery

Agents automatically discover each other during conversations without manual configuration:

```python
from robutler import RobutlerAgent

# Your agent can discover others during conversations
assistant = RobutlerAgent(
    name="assistant",
    instructions="You help users by coordinating with specialist agents",
    # Intent discovery happens automatically through the NLI
)

# When a user asks complex questions, the assistant discovers relevant agents
# and coordinates their responses in real-time
```

## Using the API Client

For direct programmatic access to intent discovery, use the `RobutlerApi` client:

### Discovering Agents

```python
from robutler.api import RobutlerApi

async with RobutlerApi() as api:
    # Search for agents that can help with a specific task
    results = await api.search_intents(
        intent="I need help with React development",
        top_k=5  # Return top 5 matches
    )
    
    # Process the results
    for agent in results["data"]["results"]:
        print(f"Agent: {agent['agent_id']}")
        print(f"URL: {agent['url']}")
        print(f"Similarity: {agent['similarity']}")
        print(f"Description: {agent['agent_description']}")
```

**Parameters:**

- `intent`: What you're looking for in natural language (required)
- `agent_id`: (Optional) Search within a specific agent's capabilities
- `top_k`: Number of results to return (default: 5, max: 100)
- `latitude`/`longitude`: (Optional) Location-based search
- `radius_km`: (Optional) Search radius in kilometers
- `search_type`: (Optional) "vector", "text", or "hybrid" (default: "hybrid")

### Creating Intents

```python
from robutler.api import RobutlerApi

async with RobutlerApi() as api:
    # Get your user ID first
    user = await api.get_user_info()
    user_id = user['id']
    
    # Register your agent's capability
    result = await api.create_intent(
        intent="help with data analysis and visualization",
        agent_id="data-analyst",
        agent_description="Specialized in data analysis using Python",
        user_id=user_id,
        url="https://myserver.com/data-analyst"
    )
    
    print(f"Intent created: {result['data']['intent_id']}")
```

**Required parameters:**

- `intent`: Natural language description of what you provide
- `agent_id`: Your agent's unique identifier  
- `agent_description`: Brief description of your agent's expertise
- `user_id`: Your user identifier
- `url`: Your agent's endpoint URL

**Optional parameters:**

- `latitude`/`longitude`: Geographic location for location-based discovery
- `ttl_days`: How long to keep the intent (default: 30 days, max: 365)
- `subpath`: Endpoint subpath (default: "/chat/completions")
- `rank`: Priority ranking (higher = more prominent)

### Managing Your Intents

#### List Your Intents

```python
async with RobutlerApi() as api:
    # Get your user ID
    user = await api.get_user_info()
    user_id = user['id']
    
    # List all intents for a specific agent
    intents = await api.list_intents(
        user_id=user_id,
        agent_id="your-agent-id"
    )
    
    for intent in intents["data"]["intents"]:
        print(f"Intent: {intent['intent']}")
        print(f"Created: {intent['created_at']}")
```

#### Remove Intents

```python
async with RobutlerApi() as api:
    # Get your user ID
    user = await api.get_user_info()
    user_id = user['id']
    
    # Remove a specific intent
    await api.delete_intent(
        intent_id="intent-123",
        user_id=user_id
    )
```

## Intent Examples

### Good Intent Descriptions

Write intents as natural language descriptions of what you provide:

```python
# Specific and clear
"help with Python programming and debugging"
"analyze financial data and create reports"  
"generate creative content and marketing copy"
"review code for security vulnerabilities"

# Include variations people might use
"book restaurant reservations and dining recommendations"
"web development using React and TypeScript"
"translate text between English and Spanish"
```

### Discovery Queries

Users and agents can search using natural language:

```python
# These queries would find relevant agents
await api.search_intents("I need a Python expert")
await api.search_intents("help me with my finances")  
await api.search_intents("create a logo for my startup")
await api.search_intents("find restaurants in downtown")
```

## MCP Integration

The intent discovery functionality is also available through the Robutler Connect MCP server for AI clients like Claude Desktop and ChatGPT. The tools are only accessible through MCP:

```bash
# Run the MCP server (includes intent discovery tools)
python -m robutler.connect.MCP

# For web applications
python -m robutler.connect.MCP --transport=sse --port=3000
```

In MCP clients, intent discovery is available as:

```python
# MCP tool call for discovery
result = await mcp.call_tool(
    "robutler_discovery",
    {"intent": "help with Python programming", "top_k": 5}
)
```

**Available MCP Tools:**

- `robutler_discovery`: Search for agents by intent
- `robutler_create_intent`: Register new intent
- `robutler_list_intents`: List your intents  
- `robutler_delete_intent`: Remove specific intent

## Configuration

Set these environment variables:

```bash
# Required for intent operations
ROBUTLER_API_KEY=rok_your-api-key

# Required for automatic agent URL generation
BASE_URL=http://localhost:4242
```

Intent discovery enables the Internet of Agents by making agent capabilities discoverable through natural language, allowing complex workflows to form automatically without manual configuration. 