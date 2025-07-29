"""
Test that concurrent requests maintain isolated contexts
"""

import asyncio
import pytest
from robutler.server import RobutlerServer, get_server_context, ReportUsage
from fastapi.testclient import TestClient
import httpx


def test_concurrent_agent_requests():
    """Test that concurrent agent requests maintain isolated contexts"""
    app = RobutlerServer()
    
    # Track which context each request sees
    request_contexts = {}
    
    @app.agent("/test/{request_id}")
    @app.pricing(credits_per_token=5)
    async def test_agent(request_id: str):
        """Test agent that tracks its context"""
        # Small delay to ensure requests overlap
        await asyncio.sleep(0.1)
        
        # Get the current context
        context = get_server_context()
        
        # Store the context info for this request
        request_contexts[request_id] = {
            'server_call_id': context.server_call_id,
            'server_name': context.server_name
        }
        
        return ReportUsage(f"Response for {request_id}", 10)
    
    with TestClient(app) as client:
        # Make multiple concurrent requests
        import concurrent.futures
        
        def make_request(request_id):
            response = client.post(
                f"/test/{request_id}",
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": f"Request {request_id}"}]
                }
            )
            return request_id, response
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(5):
                future = executor.submit(make_request, f"req_{i}")
                futures.append(future)
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                request_id, response = future.result()
                assert response.status_code == 200
                results.append((request_id, response.json()))
        
        # Verify each request had its own context
        assert len(request_contexts) == 5
        
        # Check that all agent_call_ids are unique
        call_ids = [ctx['server_call_id'] for ctx in request_contexts.values()]
        assert len(set(call_ids)) == 5, "Each request should have a unique agent_call_id"
        
        # Verify all contexts have the correct agent name
        for ctx in request_contexts.values():
            assert ctx['server_name'] == 'test_agent'



def test_nested_context_isolation():
    """Test that nested function calls maintain the same context"""
    app = RobutlerServer()
    
    context_chain = []
    
    @app.pricing(credits_per_call=50)
    def inner_tool():
        """Inner tool that checks context"""
        context = get_server_context()
        if context:
            context_chain.append({
                'function': 'inner_tool',
                'call_id': context.server_call_id,
                'usage_before': len(context.usage_records)
            })
        return "inner result"
    
    @app.agent("/nested")
    @app.pricing(credits_per_token=10)
    def nested_agent():
        """Agent that calls another tool"""
        context = get_server_context()
        if context:
            context_chain.append({
                'function': 'nested_agent',
                'call_id': context.server_call_id,
                'usage_before': len(context.usage_records)
            })
        
        # Call the inner tool
        result = inner_tool()
        
        # Check context again
        if context:
            context_chain.append({
                'function': 'nested_agent_after',
                'call_id': context.server_call_id,
                'usage_after': len(context.usage_records)
            })
        
        return ReportUsage(f"Nested result: {result}", 5)
    
    with TestClient(app) as client:
        response = client.post(
            "/nested",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Test nested"}]
            }
        )
        
        assert response.status_code == 200
        
        # Verify the context was the same throughout the call chain
        assert len(context_chain) >= 2
        call_ids = [ctx['call_id'] for ctx in context_chain]
        assert len(set(call_ids)) == 1, "All functions should see the same context"
        
        # Verify usage was tracked for both functions
        assert context_chain[-1]['usage_after'] > context_chain[0]['usage_before']


@pytest.mark.asyncio
async def test_async_context_propagation():
    """Test that async context propagates correctly through await calls"""
    app = RobutlerServer()
    
    context_checks = []
    
    @app.pricing(credits_per_call=25)
    async def async_inner():
        await asyncio.sleep(0.01)
        context = get_server_context()
        if context:
            context_checks.append(('async_inner', context.server_call_id))
        return "async inner"
    
    @app.pricing(credits_per_call=50)
    async def async_middle():
        context = get_server_context()
        if context:
            context_checks.append(('async_middle_before', context.server_call_id))
        
        result = await async_inner()
        
        context = get_server_context()
        if context:
            context_checks.append(('async_middle_after', context.server_call_id))
        
        return f"middle: {result}"
    
    @app.agent("/async_test")
    @app.pricing(credits_per_token=2)
    async def async_agent():
        context = get_server_context()
        if context:
            context_checks.append(('async_agent', context.server_call_id))
        
        result = await async_middle()
        return ReportUsage(result, 20)
    
    with TestClient(app) as client:
        response = client.post(
            "/async_test",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Test async"}]
            }
        )
        
        assert response.status_code == 200
        
        # Verify all async functions saw the same context
        assert len(context_checks) > 0
        call_ids = [check[1] for check in context_checks]
        assert len(set(call_ids)) == 1, "All async functions should see the same context"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 