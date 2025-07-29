"""
Test that pricing decorators work with @agent endpoints
"""

import pytest
from robutler.server import RobutlerServer, get_server_context, ReportUsage
from fastapi.testclient import TestClient


def test_pricing_with_agent_decorator():
    """Test that pricing works with @agent decorator"""
    app = RobutlerServer()
    
    @app.agent("/assistant")
    @app.pricing(credits_per_token=5)
    def assistant():
        """Test assistant"""
        return ReportUsage("Hello from assistant", 10)
    
    with TestClient(app) as client:
        # Make a request to the agent endpoint
        response = client.post(
            "/assistant",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "Hello from assistant"
        
        # Verify pricing info is available
        pricing_response = client.get("/assistant")
        assert pricing_response.status_code == 200
        pricing_data = pricing_response.json()
        assert pricing_data["pricing"]["credits_per_token"] == 5










if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 