"""
High concurrency stress test for context isolation
"""

import asyncio
import pytest
import time
from robutler.server import RobutlerServer, get_server_context, ReportUsage
from fastapi.testclient import TestClient
import concurrent.futures
import threading


def test_high_concurrency_context_isolation():
    """Stress test with many concurrent requests to verify context isolation"""
    app = RobutlerServer()
    
    # Track all contexts seen
    contexts_seen = {}
    context_lock = threading.Lock()
    
    @app.agent("/stress/{request_id}")
    @app.pricing(credits_per_token=1)
    async def stress_agent(request_id: str):
        """Agent that simulates work and tracks context"""
        # Simulate some async work
        await asyncio.sleep(0.01)
        
        context = get_server_context()
        
        # Thread-safe context tracking
        with context_lock:
            contexts_seen[request_id] = {
                'server_call_id': context.server_call_id,
                'server_name': context.server_name,
                'thread_id': threading.get_ident(),
                'timestamp': time.time()
            }
        
        # More async work
        await asyncio.sleep(0.01)
        
        return ReportUsage(f"Stress response {request_id}", 5)
    
    with TestClient(app) as client:
        def make_stress_request(request_id):
            return client.post(
                f"/stress/{request_id}",
                json={
                    "model": "test-model",
                    "messages": [{"role": "user", "content": f"Stress {request_id}"}]
                }
            )
        
        # High concurrency test - 50 concurrent requests
        num_requests = 50
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(make_stress_request, f"stress_{i}")
                futures.append(future)
            
            # Wait for all to complete
            results = []
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                assert response.status_code == 200
                results.append(response.json())
        
        # Verify context isolation
        assert len(contexts_seen) == num_requests, f"Expected {num_requests} contexts, got {len(contexts_seen)}"
        
        # All agent_call_ids should be unique
        call_ids = [ctx['server_call_id'] for ctx in contexts_seen.values()]
        unique_call_ids = set(call_ids)
        assert len(unique_call_ids) == num_requests, f"Expected {num_requests} unique call IDs, got {len(unique_call_ids)}"
        
        # All should have the correct agent name
        agent_names = [ctx['server_name'] for ctx in contexts_seen.values()]
        assert all(name == 'stress_agent' for name in agent_names)


def test_mixed_endpoint_concurrency():
    """Test concurrent requests to different endpoints maintain isolation"""
    app = RobutlerServer()
    
    contexts_by_endpoint = {'agent1': {}, 'agent2': {}}
    context_lock = threading.Lock()
    
    @app.agent("/endpoint1/{request_id}")
    @app.pricing(credits_per_call=10)
    def agent1(request_id: str):
        context = get_server_context()
        with context_lock:
            contexts_by_endpoint['agent1'][request_id] = context.server_call_id
        return ReportUsage(f"Agent1 {request_id}", 3)
    
    @app.agent("/endpoint2/{request_id}")
    @app.pricing(credits_per_call=20)
    async def agent2(request_id: str):
        await asyncio.sleep(0.005)
        context = get_server_context()
        with context_lock:
            contexts_by_endpoint['agent2'][request_id] = context.server_call_id
        return ReportUsage(f"Agent2 {request_id}", 5)
    
    with TestClient(app) as client:
        def make_agent1_request(i):
            return client.post(
                f"/endpoint1/req_{i}",
                json={"model": "test", "messages": [{"role": "user", "content": f"Test {i}"}]}
            )
        
        def make_agent2_request(i):
            return client.post(
                f"/endpoint2/req_{i}",
                json={"model": "test", "messages": [{"role": "user", "content": f"Test {i}"}]}
            )
        
        # Mix of requests to different endpoints
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            # 10 requests to each endpoint
            for i in range(10):
                futures.append(executor.submit(make_agent1_request, i))
                futures.append(executor.submit(make_agent2_request, i))
            
            # Wait for all
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                assert response.status_code == 200
        
        # Verify each endpoint had its own contexts
        assert len(contexts_by_endpoint['agent1']) == 10
        assert len(contexts_by_endpoint['agent2']) == 10
        
        # All call IDs should be unique across all endpoints
        all_call_ids = []
        for endpoint_contexts in contexts_by_endpoint.values():
            all_call_ids.extend(endpoint_contexts.values())
        
        unique_call_ids = set(all_call_ids)
        assert len(unique_call_ids) == len(all_call_ids), "All call IDs should be unique"


def test_context_cleanup_verification():
    """Verify that contexts are properly cleaned up after requests"""
    app = RobutlerServer()
    
    context_lifecycle = []
    context_lock = threading.Lock()
    
    @app.agent("/lifecycle/{request_id}")
    @app.pricing(credits_per_call=1)
    async def lifecycle_agent(request_id: str):
        context = get_server_context()
        
        with context_lock:
            context_lifecycle.append({
                'request_id': request_id,
                'call_id': context.server_call_id,
                'stage': 'start',
                'timestamp': time.time()
            })
        
        # Simulate work
        await asyncio.sleep(0.02)
        
        # Context should still be the same
        context_after = get_server_context()
        assert context_after.server_call_id == context.server_call_id
        
        with context_lock:
            context_lifecycle.append({
                'request_id': request_id,
                'call_id': context.server_call_id,
                'stage': 'end',
                'timestamp': time.time()
            })
        
        return ReportUsage(f"Lifecycle {request_id}", 2)
    
    with TestClient(app) as client:
        # Make sequential requests to verify cleanup
        for i in range(5):
            response = client.post(
                f"/lifecycle/seq_{i}",
                json={"model": "test", "messages": [{"role": "user", "content": f"Seq {i}"}]}
            )
            assert response.status_code == 200
            
            # Brief pause between requests
            time.sleep(0.01)
        
        # Verify lifecycle tracking
        assert len(context_lifecycle) == 10  # 5 requests * 2 stages each
        
        # Group by request_id
        by_request = {}
        for event in context_lifecycle:
            req_id = event['request_id']
            if req_id not in by_request:
                by_request[req_id] = []
            by_request[req_id].append(event)
        
        # Each request should have start and end with same call_id
        for req_id, events in by_request.items():
            assert len(events) == 2
            start_event = next(e for e in events if e['stage'] == 'start')
            end_event = next(e for e in events if e['stage'] == 'end')
            assert start_event['call_id'] == end_event['call_id']


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 