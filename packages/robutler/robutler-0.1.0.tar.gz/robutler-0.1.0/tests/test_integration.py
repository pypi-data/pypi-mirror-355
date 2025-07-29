"""
Integration tests for RobutlerServer with real server
"""

import pytest
import asyncio
import threading
import time
import requests
import uvicorn
from contextlib import contextmanager
from robutler.server import RobutlerServer, ReportUsage


class IntegrationTestServer:
    """Test server manager for integration tests"""
    
    def __init__(self, app, host="127.0.0.1", port=8888):
        self.app = app
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self):
        """Start the server in a background thread"""
        config = uvicorn.Config(
            self.app, 
            host=self.host, 
            port=self.port, 
            log_level="error"  # Suppress logs during tests
        )
        self.server = uvicorn.Server(config)
        
        def run_server():
            asyncio.run(self.server.serve())
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        
        # Wait for server to start
        for _ in range(50):  # 5 second timeout
            try:
                response = requests.get(f"http://{self.host}:{self.port}/docs")
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Server failed to start")
    
    def stop(self):
        """Stop the server"""
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=5)
    
    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"


@contextmanager
def integration_test_server(app, **kwargs):
    """Context manager for test server"""
    server = IntegrationTestServer(app, **kwargs)
    try:
        server.start()
        yield server
    finally:
        server.stop()


def test_integration_basic_agent():
    """Test basic agent functionality with real server"""
    app = RobutlerServer()
    
    @app.pricing(credits_per_call=100)
    def database_lookup(query: str):
        return f"Database result for: {query}"
    
    @app.agent("/research/{topic}")
    @app.pricing(credits_per_token=5)
    def research_agent(topic: str):
        result = database_lookup(f"papers about {topic}")
        return f"Research on {topic}: {result}"
    
    with integration_test_server(app, port=8889) as server:
        # Test GET endpoint (pricing info)
        response = requests.get(f"{server.base_url}/research/AI")
        assert response.status_code == 200
        data = response.json()
        assert data['server'] == 'research_agent'
        assert data['pricing']['credits_per_token'] == 5
        assert 'database_lookup' in data['tools']
        assert data['tools']['database_lookup']['credits_per_call'] == 100
        
        # Test POST endpoint (chat completion)
        response = requests.post(f"{server.base_url}/research/AI", json={
            "model": "research-model",
            "messages": [{"role": "user", "content": "Research AI"}],
            "stream": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data['object'] == 'chat.completion'
        assert 'Research on AI:' in data['choices'][0]['message']['content']
        assert 'Database result for: papers about AI' in data['choices'][0]['message']['content']
        assert data['usage']['completion_tokens'] > 0


def test_integration_streaming():
    """Test streaming functionality with real server"""
    app = RobutlerServer()
    
    @app.pricing(credits_per_call=50)
    def analytics_tool():
        return "analytics data"
    
    @app.agent("/stream/{topic}")
    @app.pricing(credits_per_token=3)
    def streaming_agent(topic: str):
        data = analytics_tool()
        return f"Streaming analysis of {topic} using {data}"
    
    with integration_test_server(app, port=8890) as server:
        # Test streaming request
        response = requests.post(f"{server.base_url}/stream/blockchain", json={
            "model": "stream-model",
            "messages": [{"role": "user", "content": "Analyze blockchain"}],
            "stream": True
        }, stream=True)
        
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/event-stream; charset=utf-8'
        
        # Collect streaming chunks
        chunks = []
        content_parts = []
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                chunks.append(line)
                if line != "data: [DONE]":
                    try:
                        import json
                        chunk_data = json.loads(line[6:])  # Parse JSON data
                        if 'choices' in chunk_data and chunk_data['choices']:
                            delta = chunk_data['choices'][0]['delta']
                            if 'content' in delta:
                                content_parts.append(delta['content'])
                    except json.JSONDecodeError:
                        pass  # Skip malformed chunks
        
        # Verify streaming worked
        assert len(chunks) > 2
        assert chunks[-1] == "data: [DONE]"
        
        # Verify content
        full_content = ''.join(content_parts)
        assert "Streaming analysis of blockchain" in full_content
        assert "analytics data" in full_content


def test_integration_report_usage():
    """Test ReportUsage with real server"""
    app = RobutlerServer()
    
    @app.agent("/report/{category}")
    @app.pricing(credits_per_token=4)
    def report_agent(category: str):
        content = f"Detailed report on {category} with comprehensive analysis and recommendations"
        return ReportUsage(content, 20)  # Explicitly report 20 tokens
    
    with integration_test_server(app, port=8891) as server:
        response = requests.post(f"{server.base_url}/report/finance", json={
            "model": "report-model",
            "messages": [{"role": "user", "content": "Generate report"}],
            "stream": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['choices'][0]['message']['content'] == "Detailed report on finance with comprehensive analysis and recommendations"
        assert data['usage']['completion_tokens'] == 20  # Should use explicit token count


def test_integration_custom_streaming_response():
    """Test custom StreamingResponse with real server"""
    app = RobutlerServer()
    
    @app.pricing(credits_per_call=25)
    def data_fetcher():
        return "fetched data"
    
    @app.agent("/custom/{mode}")
    @app.pricing(credits_per_token=2)
    async def custom_agent(mode: str):
        from fastapi.responses import StreamingResponse
        
        data = data_fetcher()
        
        async def generate():
            yield f"Starting {mode} processing\n"
            yield f"Processing {data}\n"
            yield "Processing complete\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    with integration_test_server(app, port=8892) as server:
        response = requests.post(f"{server.base_url}/custom/advanced", json={
            "model": "custom-model",
            "messages": [{"role": "user", "content": "Process data"}],
            "stream": False
        })
        
        assert response.status_code == 200
        content = response.text
        assert "Starting advanced processing" in content
        assert "Processing fetched data" in content
        assert "Processing complete" in content


def test_integration_multiple_tools():
    """Test agent with multiple tools and complex usage tracking"""
    app = RobutlerServer()
    
    @app.pricing(credits_per_call=30)
    def tool_a():
        return "result A"
    
    @app.pricing(credits_per_call=40)
    def tool_b():
        return "result B"
    
    @app.pricing(credits_per_token=2)
    def tool_c(text: str):
        return f"processed: {text}"
    
    @app.agent("/complex/{task}")
    @app.pricing(credits_per_token=6)
    def complex_agent(task: str):
        # Use multiple tools
        a = tool_a()
        b = tool_b()
        c = tool_c(f"{a} and {b}")
        
        return f"Complex {task} analysis: {c}"
    
    with integration_test_server(app, port=8893) as server:
        # Test pricing info
        response = requests.get(f"{server.base_url}/complex/optimization")
        assert response.status_code == 200
        data = response.json()
        assert data['server'] == 'complex_agent'
        assert data['pricing']['credits_per_token'] == 6
        assert len(data['tools']) == 3
        assert data['tools']['tool_a']['credits_per_call'] == 30
        assert data['tools']['tool_b']['credits_per_call'] == 40
        assert data['tools']['tool_c']['credits_per_token'] == 2
        
        # Test execution
        response = requests.post(f"{server.base_url}/complex/optimization", json={
            "model": "complex-model",
            "messages": [{"role": "user", "content": "Optimize system"}],
            "stream": False
        })
        
        assert response.status_code == 200
        data = response.json()
        content = data['choices'][0]['message']['content']
        assert "Complex optimization analysis:" in content
        assert "processed: result A and result B" in content
        assert data['usage']['completion_tokens'] > 0


def test_integration_concurrent_requests():
    """Test concurrent requests to ensure proper context isolation"""
    app = RobutlerServer()
    
    @app.pricing(credits_per_call=10)
    def shared_tool(identifier: str):
        return f"shared result for {identifier}"
    
    @app.agent("/concurrent/{id}")
    @app.pricing(credits_per_token=1)
    def concurrent_agent(id: str):
        result = shared_tool(id)
        return f"Agent {id}: {result}"
    
    with integration_test_server(app, port=8894) as server:
        import concurrent.futures
        
        def make_request(agent_id):
            response = requests.post(f"{server.base_url}/concurrent/{agent_id}", json={
                "model": "concurrent-model",
                "messages": [{"role": "user", "content": f"Process {agent_id}"}],
                "stream": False
            })
            return response.json()
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, f"agent{i}") for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all requests succeeded and have correct content
        assert len(results) == 5
        for result in results:
            assert result['object'] == 'chat.completion'
            content = result['choices'][0]['message']['content']
            assert "Agent agent" in content
            assert "shared result for agent" in content
            assert result['usage']['completion_tokens'] > 0


def test_integration_error_handling():
    """Test error handling with real server"""
    app = RobutlerServer()
    
    @app.pricing(credits_per_call=50)
    def failing_tool():
        raise ValueError("Tool failed")
    
    @app.agent("/error-test")
    @app.pricing(credits_per_token=3)
    def error_agent():
        try:
            failing_tool()
        except ValueError:
            return "Handled error gracefully"
    
    with integration_test_server(app, port=8895) as server:
        response = requests.post(f"{server.base_url}/error-test", json={
            "model": "error-model",
            "messages": [{"role": "user", "content": "Test error handling"}],
            "stream": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['choices'][0]['message']['content'] == "Handled error gracefully"


if __name__ == "__main__":
    # Run a quick integration test
    print("Running quick integration test...")
    test_integration_basic_agent()
    print("✅ Integration test passed!") 