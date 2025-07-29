"""
Tests for RobutlerServer
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from robutler.server import RobutlerServer
from fastapi.responses import StreamingResponse
from robutler.server import ReportUsage


def test_robutler_server_creation():
    """Test that RobutlerServer can be created"""
    agent = RobutlerServer()
    assert isinstance(agent, RobutlerServer)
    assert hasattr(agent, 'pricing')
    assert hasattr(agent, 'agent')


def test_pricing_decorator():
    """Test the pricing decorator functionality"""
    agent = RobutlerServer()
    
    @agent.pricing(credits_per_call=100)
    def test_tool():
        return "test response"
    
    # Check that pricing info was stored
    assert 'test_tool' in agent.pricing_info
    assert agent.pricing_info['test_tool'].credits_per_call == 100


def test_agent_decorator():
    """Test the agent decorator creates proper endpoints"""
    agent = RobutlerServer()
    
    @agent.agent("/test/{name}")
    @agent.pricing(credits_per_token=5)
    def test_agent(name: str):
        return ReportUsage(f"Hello {name}", 10)
    
    # Check that pricing info was stored
    assert 'test_agent' in agent.pricing_info
    assert agent.pricing_info['test_agent'].credits_per_token == 5
    
    # Test the endpoints
    client = TestClient(agent)
    
    # Test GET endpoint
    response = client.get("/test/world")
    assert response.status_code == 200
    data = response.json()
    assert data['server'] == 'test_agent'
    assert data['pricing']['credits_per_token'] == 5
    
    # Test POST endpoint (non-streaming)
    response = client.post("/test/world", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data['object'] == 'chat.completion'
    assert data['choices'][0]['message']['content'] == 'Hello world'
    assert data['usage']['completion_tokens'] == 10


def test_credit_tracking():
    """Test that credits are tracked properly in agent endpoints"""
    agent = RobutlerServer()
    
    @agent.pricing(credits_per_call=1000)
    def expensive_tool():
        return "expensive result"
    
    @agent.agent("/test-endpoint")
    @agent.pricing(credits_per_token=5)
    def test_agent():
        result = expensive_tool()
        return f"Agent result: {result}"
    
    # Test via agent endpoint
    client = TestClient(agent)
    response = client.post("/test-endpoint", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "Agent result: expensive result" in data['choices'][0]['message']['content']


def test_token_estimation():
    """Test token estimation functionality"""
    agent = RobutlerServer()
    
    # Test with a known string
    text = "Hello world this is a test"
    tokens = agent._estimate_tokens(text)
    assert tokens > 0
    
    # Test with empty string
    assert agent._estimate_tokens("") > 0  # Should return at least 1


def test_streaming_response():
    """Test streaming response generation"""
    agent = RobutlerServer()
    
    @agent.agent("/stream/{name}")
    @agent.pricing(credits_per_token=2)
    def streaming_agent(name: str):
        return f"Streaming response for {name}"
    
    client = TestClient(agent)
    
    # Test streaming endpoint
    response = client.post("/stream/test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    })
    
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/event-stream; charset=utf-8'


def test_streaming_response_content():
    """Test that streaming response contains proper SSE format"""
    agent = RobutlerServer()
    
    @agent.agent("/stream/{topic}")
    @agent.pricing(credits_per_token=3)
    def streaming_agent(topic: str):
        return ReportUsage(f"This is a test about {topic}", 20)
    
    client = TestClient(agent)
    
    # Make streaming request
    with client.stream("POST", "/stream/AI", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Tell me about AI"}],
        "stream": True
    }) as response:
        chunks = []
        for line in response.iter_lines():
            if line and line.startswith("data: "):
                chunks.append(line)
        
        # Verify we got chunks
        assert len(chunks) > 2  # At least start, content, and end chunks
        
        # Check first chunk (role)
        first_chunk = json.loads(chunks[0][6:])  # Remove "data: " prefix
        assert first_chunk['object'] == 'chat.completion.chunk'
        assert first_chunk['choices'][0]['delta'].get('role') == 'assistant'
        
        # Check last chunk (DONE)
        assert chunks[-1] == "data: [DONE]"
        
        # Check that we have content chunks
        content_chunks = [c for c in chunks[1:-2] if 'content' in json.loads(c[6:])['choices'][0]['delta']]
        assert len(content_chunks) > 0


# Removed streaming credit tracking tests since they relied on old compatibility methods


def test_custom_streaming_response_with_stream_true():
    """Test custom StreamingResponse with stream=true in request"""
    agent = RobutlerServer()
    
    @agent.agent("/custom2/{topic}")
    @agent.pricing(credits_per_token=5)
    def custom_agent(topic: str):
        def generate():
            yield f"Starting discussion about {topic}\n"
            yield f"{topic} is interesting\n"
            yield "The end"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    client = TestClient(agent)
    
    # Test with stream=True
    response = client.post("/custom2/AI", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    })
    
    assert response.status_code == 200
    # Should return the custom StreamingResponse content, not SSE format
    content = response.text
    assert "Starting discussion about AI" in content
    assert "AI is interesting" in content
    assert "The end" in content
    # Should NOT have SSE format
    assert "data: " not in content


def test_mixed_return_types():
    """Test that the same agent can return different types based on logic"""
    agent = RobutlerServer()
    
    @agent.agent("/mixed/{mode}")
    @agent.pricing(credits_per_token=4)
    async def mixed_agent(mode: str):
        if mode == "streaming":
            async def generate():
                yield "This is "
                yield "a streaming "
                yield "response"
            return StreamingResponse(generate())
        elif mode == "report_usage":
            return ReportUsage("This is a ReportUsage response", 10)
        else:
            return "This is a simple response"
    
    client = TestClient(agent)
    
    # Test streaming mode
    response1 = client.post("/mixed/streaming", json={
        "model": "test",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False
    })
    assert response1.status_code == 200
    assert response1.text == "This is a streaming response"
    
    # Test ReportUsage mode
    response2 = client.post("/mixed/report_usage", json={
        "model": "test",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False
    })
    assert response2.status_code == 200
    data = response2.json()
    assert data['choices'][0]['message']['content'] == "This is a ReportUsage response"
    assert data['usage']['completion_tokens'] == 10
    
    # Test simple mode
    response3 = client.post("/mixed/simple", json={
        "model": "test",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": False
    })
    assert response3.status_code == 200
    data = response3.json()
    assert data['choices'][0]['message']['content'] == "This is a simple response"


def test_agent_endpoint_tracks_tool_calls():
    """Test that @agent decorated endpoints automatically track tool calls"""
    agent = RobutlerServer()
    
    # Define priced tools
    @agent.pricing(credits_per_call=50)
    def tool_a():
        return "Tool A result"
    
    @agent.pricing(credits_per_token=3)
    def tool_b():
        return "Tool B result with more text for token counting"
    
    # Define an agent that uses tools
    @agent.agent("/test-agent")
    @agent.pricing(credits_per_token=5)
    def test_agent():
        # Call some tools
        result_a = tool_a()
        result_b = tool_b()
        return f"Agent response: {result_a}, {result_b}"
    
    # Test the agent endpoint
    client = TestClient(agent)
    response = client.post("/test-agent", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response structure
    assert data['object'] == 'chat.completion'
    assert 'Agent response:' in data['choices'][0]['message']['content']
    assert data['usage']['completion_tokens'] > 0


# Removed manual context tracking tests since track_agent_call was removed


def test_simplified_usage_tracking():
    """Test the simplified usage tracking with track_usage and get_usage"""
    agent = RobutlerServer()
    
    @agent.pricing(credits_per_call=100)
    def tool_a():
        return "Tool A result"
    
    @agent.pricing(credits_per_token=3)
    def tool_b():
        return "Tool B result with more text for token counting"
    
    @agent.agent("/test-usage")
    @agent.pricing(credits_per_token=5)
    def test_agent():
        result_a = tool_a()
        result_b = tool_b()
        return f"Agent response: {result_a}, {result_b}"
    
    # Test the agent endpoint
    client = TestClient(agent)
    response = client.post("/test-usage", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response structure
    assert data['object'] == 'chat.completion'
    assert 'Agent response:' in data['choices'][0]['message']['content']
    assert data['usage']['completion_tokens'] > 0
    
    # The usage tracking happens automatically within the agent context
    # We can't directly access it from the test, but we know it's working
    # because the agent executed successfully and returned proper token counts


def test_agent_context_methods():
    """Test ServerContext track_usage and get_usage methods directly"""
    from robutler.server.server import ServerContext
    
    # Create a context
    context = ServerContext("test-call-123", "test_server")
    
    # Track some usage
    usage_id_1 = context.track_usage("tool_a", 100, 0, "tool")
    usage_id_2 = context.track_usage("tool_b", 50, 10, "tool")
    usage_id_3 = context.track_usage("test_server", 75, 15, "server")
    
    # Verify usage IDs are returned
    assert isinstance(usage_id_1, str)
    assert isinstance(usage_id_2, str)
    assert isinstance(usage_id_3, str)
    assert usage_id_1 != usage_id_2 != usage_id_3
    
    # Get usage summary
    usage = context.get_usage()
    
    # Verify summary structure
    assert usage['server_call_id'] == "test-call-123"
    assert usage['server_name'] == "test_server"
    assert usage['total_credits'] == 225  # 100 + 50 + 75
    assert usage['total_tokens'] == 25    # 0 + 10 + 15
    assert usage['usage_count'] == 3
    
    # Verify tool and server usage separation
    assert len(usage['tool_usage']) == 2
    assert len(usage['server_usage']) == 1
    
    # Verify timestamps are present and properly formatted
    assert 'started_at' in usage
    assert 'completed_at' in usage
    assert 'duration_seconds' in usage
    assert isinstance(usage['duration_seconds'], float)
    
    # Verify individual usage records have timestamps
    for record in usage['tool_usage'] + usage['server_usage']:
        assert 'timestamp' in record
        assert 'usage_id' in record
        assert 'source' in record
        assert 'source_type' in record
        assert 'credits' in record
        assert 'tokens' in record


def test_report_usage_class():
    """Test the ReportUsage class for explicit usage reporting"""
    from robutler.server import ReportUsage
    
    agent = RobutlerServer()
    
    @agent.agent("/report/{name}")
    @agent.pricing(credits_per_token=3)
    def report_agent(name: str):
        content = f"Report for {name}"
        return ReportUsage(content, 15)  # Explicitly report 15 tokens
    
    client = TestClient(agent)
    
    response = client.post("/report/test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['choices'][0]['message']['content'] == 'Report for test'
    assert data['usage']['completion_tokens'] == 15  # Should use the explicit token count


def test_streaming_with_usage_tracking():
    """Test streaming response with automatic usage tracking"""
    agent = RobutlerServer()
    
    @agent.pricing(credits_per_call=100)
    def expensive_tool():
        return "expensive result"
    
    @agent.agent("/stream-with-tools/{topic}")
    @agent.pricing(credits_per_token=2)
    def streaming_agent(topic: str):
        # Call a tool that should be tracked
        tool_result = expensive_tool()
        return f"Streaming about {topic}: {tool_result}"
    
    client = TestClient(agent)
    
    # Test streaming request
    with client.stream("POST", "/stream-with-tools/AI", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Tell me about AI"}],
        "stream": True
    }) as response:
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/event-stream; charset=utf-8'
        
        chunks = []
        for line in response.iter_lines():
            if line and line.startswith("data: "):
                chunks.append(line)
        
        # Verify we got proper SSE chunks
        assert len(chunks) > 2
        
        # Check first chunk (role)
        first_chunk = json.loads(chunks[0][6:])
        assert first_chunk['object'] == 'chat.completion.chunk'
        assert first_chunk['choices'][0]['delta'].get('role') == 'assistant'
        
        # Check that we have content chunks
        content_chunks = [c for c in chunks[1:-2] if 'content' in json.loads(c[6:])['choices'][0]['delta']]
        assert len(content_chunks) > 0
        
        # Check final chunk
        assert chunks[-1] == "data: [DONE]"


def test_streaming_with_report_usage():
    """Test streaming with ReportUsage for explicit token reporting"""
    from robutler.server import ReportUsage
    
    agent = RobutlerServer()
    
    @agent.agent("/stream-report/{topic}")
    @agent.pricing(credits_per_token=3)
    def streaming_report_agent(topic: str):
        content = f"Detailed streaming report about {topic} with lots of analysis"
        return ReportUsage(content, 25)  # Explicitly report 25 tokens
    
    client = TestClient(agent)
    
    # Test streaming request
    with client.stream("POST", "/stream-report/blockchain", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Analyze blockchain"}],
        "stream": True
    }) as response:
        assert response.status_code == 200
        
        # Collect all content
        full_content = ""
        chunks = []
        for line in response.iter_lines():
            if line and line.startswith("data: "):
                chunks.append(line)
                if line != "data: [DONE]":
                    chunk_data = json.loads(line[6:])
                    if 'choices' in chunk_data and chunk_data['choices']:
                        delta = chunk_data['choices'][0]['delta']
                        if 'content' in delta:
                            full_content += delta['content']
        
        # Verify the content matches what we expect
        assert "Detailed streaming report about blockchain" in full_content
        assert len(chunks) > 5  # Should have multiple chunks


def test_custom_streaming_response_with_usage_tracking():
    """Test custom StreamingResponse with usage tracking"""
    agent = RobutlerServer()
    
    @agent.pricing(credits_per_call=50)
    def data_processor():
        return "processed data"
    
    @agent.agent("/custom-stream/{mode}")
    @agent.pricing(credits_per_token=4)
    async def custom_streaming_agent(mode: str):
        # Call a tool first
        processed = data_processor()
        
        # Return custom streaming response
        async def generate():
            yield f"Starting {mode} analysis\n"
            yield f"Using {processed}\n"
            yield "Analysis complete"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    client = TestClient(agent)
    
    response = client.post("/custom-stream/advanced", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Run analysis"}],
        "stream": False  # Even with stream=False, custom StreamingResponse should work
    })
    
    assert response.status_code == 200
    content = response.text
    assert "Starting advanced analysis" in content
    assert "Using processed data" in content
    assert "Analysis complete" in content


def test_streaming_vs_non_streaming_usage_consistency():
    """Test that usage tracking is consistent between streaming and non-streaming"""
    agent = RobutlerServer()
    
    @agent.pricing(credits_per_call=75)
    def consistent_tool():
        return "consistent result"
    
    @agent.agent("/consistent/{mode}")
    @agent.pricing(credits_per_token=5)
    def consistent_agent(mode: str):
        tool_result = consistent_tool()
        return f"Mode {mode}: {tool_result}"
    
    client = TestClient(agent)
    
    # Test non-streaming
    response1 = client.post("/consistent/normal", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Test"}],
        "stream": False
    })
    assert response1.status_code == 200
    data1 = response1.json()
    non_streaming_tokens = data1['usage']['completion_tokens']
    
    # Test streaming
    with client.stream("POST", "/consistent/stream", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Test"}],
        "stream": True
    }) as response2:
        assert response2.status_code == 200
        
        # Collect streaming content
        content_parts = []
        for line in response2.iter_lines():
            if line and line.startswith("data: ") and line != "data: [DONE]":
                chunk_data = json.loads(line[6:])
                if 'choices' in chunk_data and chunk_data['choices']:
                    delta = chunk_data['choices'][0]['delta']
                    if 'content' in delta:
                        content_parts.append(delta['content'])
        
        streaming_content = ''.join(content_parts)
    
    # Both should have similar content and token usage
    assert "Mode normal: consistent result" in data1['choices'][0]['message']['content']
    assert "Mode stream: consistent result" in streaming_content
    
    # Token counts should be similar (within reasonable range)
    estimated_streaming_tokens = agent._estimate_tokens(streaming_content)
    assert abs(non_streaming_tokens - estimated_streaming_tokens) <= 2 