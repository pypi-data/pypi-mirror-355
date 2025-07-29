"""
Tests for RobutlerServer callback functionality
"""

import pytest
import json
from fastapi.testclient import TestClient
from fastapi import HTTPException
from robutler.server import RobutlerServer, ReportUsage, get_server_context


def test_before_request_callback():
    """Test that before_request callbacks are called and can modify context"""
    app = RobutlerServer()
    
    callback_called = False
    
    @app.before_request
    def auth_callback(request, context):
        nonlocal callback_called
        callback_called = True
        # Store user info in context
        auth_header = request.headers.get('authorization', 'Bearer user123')
        user_id = auth_header.replace('Bearer ', '')
        context.set_custom_data('user_id', user_id)
        context.set_custom_data('request_path', str(request.url.path))
    
    @app.agent("/test")
    @app.pricing(credits_per_token=5)
    def test_agent():
        context = get_server_context()
        user_id = context.get_custom_data('user_id')
        return f"Hello {user_id}"
    
    client = TestClient(app)
    
    response = client.post("/test", 
                          headers={"authorization": "Bearer alice"},
                          json={
                              "model": "test-model",
                              "messages": [{"role": "user", "content": "Hello"}],
                              "stream": False
                          })
    
    assert response.status_code == 200
    assert callback_called
    data = response.json()
    assert "Hello alice" in data['choices'][0]['message']['content']


def test_after_request_callback():
    """Test that after_request callbacks are called with usage data"""
    app = RobutlerServer()
    
    callback_called = False
    captured_usage = None
    captured_user_id = None
    
    @app.before_request
    def set_user(request, context):
        context.set_custom_data('user_id', 'test_user')
    
    @app.after_request
    def log_usage(request, response, context):
        nonlocal callback_called, captured_usage, captured_user_id
        callback_called = True
        captured_usage = context.get_usage()
        captured_user_id = context.get_custom_data('user_id')
    
    @app.pricing(credits_per_call=100)
    def expensive_tool():
        return "tool result"
    
    @app.agent("/test")
    @app.pricing(credits_per_token=3)
    def test_agent():
        result = expensive_tool()
        return f"Agent: {result}"
    
    client = TestClient(app)
    
    response = client.post("/test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    assert callback_called
    assert captured_user_id == 'test_user'
    assert captured_usage is not None
    assert captured_usage['total_credits'] > 0  # Should have credits from tool and agent
    assert 'custom_data' in captured_usage
    assert captured_usage['custom_data']['user_id'] == 'test_user'


def test_multiple_callbacks():
    """Test that multiple callbacks are called in order"""
    app = RobutlerServer()
    
    call_order = []
    
    @app.before_request
    def first_before(request, context):
        call_order.append('before_1')
        context.set_custom_data('step_1', True)
    
    @app.before_request
    def second_before(request, context):
        call_order.append('before_2')
        assert context.get_custom_data('step_1') is True
        context.set_custom_data('step_2', True)
    
    @app.after_request
    def first_after(request, response, context):
        call_order.append('after_1')
        assert context.get_custom_data('step_1') is True
        assert context.get_custom_data('step_2') is True
    
    @app.after_request
    def second_after(request, response, context):
        call_order.append('after_2')
    
    @app.agent("/test")
    @app.pricing(credits_per_token=2)
    def test_agent():
        return "test response"
    
    client = TestClient(app)
    
    response = client.post("/test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    assert call_order == ['before_1', 'before_2', 'after_1', 'after_2']


def test_callback_error_handling():
    """Test that callback errors don't break the request"""
    app = RobutlerServer()
    
    @app.before_request
    def failing_before(request, context):
        raise Exception("Before callback error")
    
    @app.before_request
    def working_before(request, context):
        context.set_custom_data('working', True)
    
    @app.after_request
    def failing_after(request, response, context):
        raise Exception("After callback error")
    
    @app.agent("/test")
    @app.pricing(credits_per_token=1)
    def test_agent():
        context = get_server_context()
        working = context.get_custom_data('working', False)
        return f"Working: {working}"
    
    client = TestClient(app)
    
    # Request should still succeed despite callback errors
    response = client.post("/test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "Working: True" in data['choices'][0]['message']['content']


def test_authorization_callback():
    """Test using callbacks for authorization"""
    app = RobutlerServer()
    
    @app.before_request
    def authorize(request, context):
        auth_header = request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.replace('Bearer ', '')
        if token not in ['valid_token_1', 'valid_token_2']:
            raise HTTPException(status_code=403, detail="Invalid token")
        
        # Store user info based on token
        user_map = {'valid_token_1': 'user1', 'valid_token_2': 'user2'}
        context.set_custom_data('user_id', user_map[token])
    
    @app.agent("/secure")
    @app.pricing(credits_per_token=5)
    def secure_agent():
        context = get_server_context()
        user_id = context.get_custom_data('user_id')
        return f"Secure data for {user_id}"
    
    client = TestClient(app)
    
    # Test without authorization
    try:
        response = client.post("/secure", json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        })
        # If we get here, the test should fail because we expected an exception
        assert False, f"Expected HTTPException but got response with status {response.status_code}"
    except HTTPException as e:
        assert e.status_code == 401
    
    # Test with invalid token
    try:
        response = client.post("/secure", 
                              headers={"authorization": "Bearer invalid_token"},
                              json={
                                  "model": "test-model",
                                  "messages": [{"role": "user", "content": "Hello"}],
                                  "stream": False
                              })
        assert False, f"Expected HTTPException but got response with status {response.status_code}"
    except HTTPException as e:
        assert e.status_code == 403
    
    # Test with valid token
    response = client.post("/secure", 
                          headers={"authorization": "Bearer valid_token_1"},
                          json={
                              "model": "test-model",
                              "messages": [{"role": "user", "content": "Hello"}],
                              "stream": False
                          })
    assert response.status_code == 200
    data = response.json()
    assert "Secure data for user1" in data['choices'][0]['message']['content']


def test_payment_processing_callback():
    """Test using callbacks for payment processing"""
    app = RobutlerServer()
    
    user_credits = {'user1': 1000, 'user2': 5}  # Mock user credit balances
    
    @app.before_request
    def check_credits(request, context):
        # Extract user from auth header
        auth_header = request.headers.get('authorization', 'Bearer user1')
        user_id = auth_header.replace('Bearer ', '')
        context.set_custom_data('user_id', user_id)
        
        # Check if user has enough credits (we'll estimate based on request)
        current_credits = user_credits.get(user_id, 0)
        if current_credits < 10:  # Minimum required credits
            raise HTTPException(status_code=402, detail="Insufficient credits")
    
    @app.after_request
    def deduct_credits(request, response, context):
        user_id = context.get_custom_data('user_id')
        usage = context.get_usage()
        credits_used = usage['total_credits']
        
        # Deduct credits from user balance
        if user_id in user_credits:
            user_credits[user_id] -= credits_used
            context.set_custom_data('remaining_credits', user_credits[user_id])
    
    @app.pricing(credits_per_call=200)
    def expensive_operation():
        return "expensive result"
    
    @app.agent("/paid-service")
    @app.pricing(credits_per_token=10)
    def paid_agent():
        result = expensive_operation()
        context = get_server_context()
        remaining = context.get_custom_data('remaining_credits', 'unknown')
        return f"Result: {result}, Remaining credits: {remaining}"
    
    client = TestClient(app)
    
    # Test with user who has enough credits
    response = client.post("/paid-service", 
                          headers={"authorization": "Bearer user1"},
                          json={
                              "model": "test-model",
                              "messages": [{"role": "user", "content": "Hello"}],
                              "stream": False
                          })
    assert response.status_code == 200
    data = response.json()
    assert "expensive result" in data['choices'][0]['message']['content']
    assert "Remaining credits:" in data['choices'][0]['message']['content']
    
    # Test with user who doesn't have enough credits
    try:
        response = client.post("/paid-service", 
                              headers={"authorization": "Bearer user2"},
                              json={
                                  "model": "test-model",
                                  "messages": [{"role": "user", "content": "Hello"}],
                                  "stream": False
                              })
        assert False, f"Expected HTTPException but got response with status {response.status_code}"
    except HTTPException as e:
        assert e.status_code == 402


def test_async_callbacks():
    """Test that async callbacks work correctly"""
    app = RobutlerServer()
    
    callback_called = False
    
    @app.before_request
    async def async_before(request, context):
        nonlocal callback_called
        callback_called = True
        # Simulate async operation
        import asyncio
        await asyncio.sleep(0.01)
        context.set_custom_data('async_data', 'processed')
    
    @app.after_request
    async def async_after(request, response, context):
        # Simulate async logging
        import asyncio
        await asyncio.sleep(0.01)
        context.set_custom_data('logged', True)
    
    @app.agent("/async-test")
    @app.pricing(credits_per_token=1)
    def test_agent():
        context = get_server_context()
        async_data = context.get_custom_data('async_data')
        return f"Data: {async_data}"
    
    client = TestClient(app)
    
    response = client.post("/async-test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    assert callback_called
    data = response.json()
    assert "Data: processed" in data['choices'][0]['message']['content']


def test_callbacks_with_streaming():
    """Test that callbacks work with streaming responses"""
    app = RobutlerServer()
    
    before_called = False
    after_called = False
    
    @app.before_request
    def before_stream(request, context):
        nonlocal before_called
        before_called = True
        context.set_custom_data('stream_user', 'streamer')
    
    @app.after_request
    def after_stream(request, response, context):
        nonlocal after_called
        after_called = True
        # Should have usage data even for streaming
        usage = context.get_usage()
        context.set_custom_data('final_credits', usage['total_credits'])
    
    @app.agent("/stream-test")
    @app.pricing(credits_per_token=2)
    def streaming_agent():
        context = get_server_context()
        user = context.get_custom_data('stream_user')
        return f"Streaming for {user}"
    
    client = TestClient(app)
    
    # Test streaming request
    with client.stream("POST", "/stream-test", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Stream test"}],
        "stream": True
    }) as response:
        assert response.status_code == 200
        
        # Consume the stream
        chunks = []
        for line in response.iter_lines():
            if line and line.startswith("data: "):
                chunks.append(line)
        
        assert len(chunks) > 2  # Should have multiple chunks
        assert chunks[-1] == "data: [DONE]"
    
    assert before_called
    assert after_called


def test_response_modification():
    """Test that after_request callbacks can modify the response"""
    app = RobutlerServer()
    
    @app.before_request
    def set_user_data(request, context):
        context.set_custom_data('user_id', 'test_user')
        context.set_custom_data('remaining_credits', 500)
    
    @app.after_request
    def add_custom_headers(request, response, context):
        # Add custom headers to the response
        response.headers["X-User-ID"] = context.get_custom_data('user_id')
        response.headers["X-Remaining-Credits"] = str(context.get_custom_data('remaining_credits'))
        return response  # Return the modified response
    
    @app.agent("/test-modify")
    @app.pricing(credits_per_token=1)
    def test_agent():
        return "Hello World"
    
    client = TestClient(app)
    
    response = client.post("/test-modify", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    
    assert response.status_code == 200
    assert response.headers["X-User-ID"] == "test_user"
    assert response.headers["X-Remaining-Credits"] == "500"
    
    data = response.json()
    assert "Hello World" in data['choices'][0]['message']['content']


def test_callbacks_only_for_agent_endpoints():
    """Test that callbacks only trigger for agent endpoints, not regular FastAPI routes"""
    app = RobutlerServer()
    
    callback_called = False
    
    @app.before_request
    def track_calls(request, context):
        nonlocal callback_called
        callback_called = True
        context.set_custom_data('called', True)
    
    # Regular FastAPI route (should NOT trigger callbacks)
    @app.get("/regular-route")
    def regular_endpoint():
        return {"message": "regular route"}
    
    # Agent route (SHOULD trigger callbacks)
    @app.agent("/agent-route")
    @app.pricing(credits_per_token=1)
    def agent_endpoint():
        context = get_server_context()
        called = context.get_custom_data('called', False)
        return f"Agent route, callback called: {called}"
    
    client = TestClient(app)
    
    # Test regular route - callbacks should NOT be called
    callback_called = False
    response = client.get("/regular-route")
    assert response.status_code == 200
    assert response.json() == {"message": "regular route"}
    assert not callback_called  # Callback should not have been called
    
    # Test agent route - callbacks SHOULD be called
    callback_called = False
    response = client.post("/agent-route", json={
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    })
    assert response.status_code == 200
    assert callback_called  # Callback should have been called
    data = response.json()
    assert "callback called: True" in data['choices'][0]['message']['content']


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 