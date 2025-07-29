"""
Tests for Intent Router API client functionality
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from unittest import mock
from robutler.api import (
    RobutlerApi,
    RobutlerApiError,
    IntentHealthStatus,
    IntentResult,
    IntentSearchResponse,
    IntentListItem,
    IntentCreateRequest,
    IntentSearchRequest
)


@pytest.fixture
def api_client():
    """Create a test API client"""
    return RobutlerApi(backend_url="http://test.example.com", api_key="test-key")


@pytest.mark.asyncio
async def test_intent_health_check(api_client):
    """Test intent health check endpoint"""
    mock_response = {
        "status": "healthy",
        "service": "intent-router",
        "embedding_provider": "openai",
        "collection": "intents",
        "timestamp": "2024-01-01T00:00:00Z",
        "ready": True
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.intent_health_check()
        
        mock_request.assert_called_once_with("GET", "/api/intents/health")
        assert result["status"] == "healthy"
        assert result["service"] == "intent-router"
        assert result["ready"] is True


@pytest.mark.asyncio
async def test_create_intent_minimal(api_client):
    """Test creating an intent with minimal parameters"""
    mock_response = {
        "success": True,
        "message": "Intent created successfully",
        "data": {
            "intent_id": "test-intent-123"
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.create_intent(
            intent="Find a good restaurant",
            agent_id="restaurant-agent",
            agent_description="Restaurant recommendation agent",
            user_id="test-user",
            url="http://localhost:8000/restaurant-agent"
        )
        
        expected_data = {
            "intent": "Find a good restaurant",
            "user_id": "test-user",
            "agent_id": "restaurant-agent",
            "agent_description": "Restaurant recommendation agent",
            "url": "http://localhost:8000/restaurant-agent",
            "protocol": "openai/completions",
            "subpath": "/chat/completions",
            "ttl_days": 30,
            "rank": 0.0
        }
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/create", 
            data=expected_data
        )
        assert result["success"] is True
        assert result["data"]["intent_id"] == "test-intent-123"


@pytest.mark.asyncio
async def test_create_intent_full_parameters(api_client):
    """Test creating an intent with all parameters"""
    mock_response = {
        "success": True,
        "message": "Intent created successfully",
        "data": {
            "intent_id": "test-intent-456"
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.create_intent(
            intent="Book a hotel room",
            agent_id="booking-agent",
            agent_description="Hotel booking specialist",
            user_id="user-123",
            url="http://localhost:8000/booking-agent",
            latitude=40.7128,
            longitude=-74.0060,
            ttl_days=7,
            subpath="/hotels",
            rank=0.9
        )
        
        expected_data = {
            "intent": "Book a hotel room",
            "user_id": "user-123",
            "agent_id": "booking-agent",
            "agent_description": "Hotel booking specialist",
            "url": "http://localhost:8000/booking-agent",
            "protocol": "openai/completions",
            "subpath": "/hotels",
            "ttl_days": 7,
            "rank": 0.9,
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/create", 
            data=expected_data
        )
        assert result["success"] is True
        assert result["data"]["intent_id"] == "test-intent-456"


@pytest.mark.asyncio
async def test_search_intents_minimal(api_client):
    """Test searching intents with minimal parameters"""
    mock_response = {
        "success": True,
        "message": "Search completed",
        "data": {
            "results": [
                {
                    "id": "intent-1",
                    "similarity": 0.95,
                    "intent": "Find a restaurant",
                    "agent_id": "restaurant-agent",
                    "agent_description": "Restaurant finder",
                    "rank": 0.8,
                    "url": "https://restaurants.example.com",
                    "protocol": "https",
                    "subpath": "/search",
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            ],
            "debug": {
                "totalCandidates": 100,
                "threshold": 0.7,
                "searchTypes": ["hybrid"],
                "filteredByThreshold": 5
            }
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.search_intents("restaurant near me")
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/search", 
            data={"intent": "restaurant near me"}
        )
        assert result["success"] is True
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["similarity"] == 0.95


@pytest.mark.asyncio
async def test_search_intents_full_parameters(api_client):
    """Test searching intents with all parameters"""
    mock_response = {
        "success": True,
        "message": "Search completed",
        "data": {
            "results": [],
            "debug": {
                "totalCandidates": 0,
                "threshold": 0.8,
                "searchTypes": ["vector"],
                "filteredByThreshold": 0
            }
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.search_intents(
            intent="coffee shop",
            agent_id="coffee-agent",
            latitude=40.7128,
            longitude=-74.0060,
            top_k=10,
            radius_km=5.0,
            search_type="vector"
        )
        
        expected_data = {
            "intent": "coffee shop",
            "agent_id": "coffee-agent",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "top_k": 10,
            "radius_km": 5.0,
            "search_type": "vector"
        }
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/search", 
            data=expected_data
        )
        assert result["success"] is True


@pytest.mark.asyncio
async def test_list_intents(api_client):
    """Test listing intents"""
    mock_response = {
        "success": True,
        "message": "Intents retrieved successfully",
        "data": {
            "intents": [
                {
                    "intent_id": "intent-1",
                    "intent": "Find a restaurant",
                    "created_at": 1640995200,
                    "expires_at": 1643587200,
                    "has_location": True
                },
                {
                    "intent_id": "intent-2",
                    "intent": "Book a hotel",
                    "created_at": 1640995300,
                    "expires_at": 1643587300,
                    "has_location": False
                }
            ]
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.list_intents("user-123", "restaurant-agent")
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/list", 
            data={"user_id": "user-123", "agent_id": "restaurant-agent"}
        )
        assert result["success"] is True
        assert len(result["data"]["intents"]) == 2


@pytest.mark.asyncio
async def test_list_intents_no_agent_filter(api_client):
    """Test listing intents without agent filter"""
    mock_response = {
        "success": True,
        "message": "Intents retrieved successfully",
        "data": {
            "intents": []
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.list_intents("user-123")
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/list", 
            data={"user_id": "user-123"}
        )
        assert result["success"] is True


@pytest.mark.asyncio
async def test_delete_intent(api_client):
    """Test deleting an intent"""
    mock_response = {
        "success": True,
        "message": "Intent deleted successfully",
        "data": {
            "deleted_count": 1,
            "intent_id": "intent-123"
        }
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.delete_intent("intent-123", "user-123")
        
        mock_request.assert_called_once_with(
            "POST", 
            "/api/intents/delete", 
            data={"intent_id": "intent-123", "user_id": "user-123"}
        )
        assert result["success"] is True
        assert result["data"]["deleted_count"] == 1


@pytest.mark.asyncio
async def test_intent_health_check_unhealthy(api_client):
    """Test intent health check when service is unhealthy"""
    mock_response = {
        "status": "unhealthy",
        "service": "intent-router",
        "error": "Database connection failed",
        "collection": "intents",
        "timestamp": "2024-01-01T00:00:00Z",
        "ready": False
    }
    
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await api_client.intent_health_check()
        
        assert result["status"] == "unhealthy"
        assert result["ready"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_api_error_handling(api_client):
    """Test API error handling"""
    with patch.object(api_client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = RobutlerApiError("API Error", status_code=400)
        
        with pytest.raises(RobutlerApiError):
            await api_client.create_intent(
                intent="test intent",
                agent_id="test-agent",
                agent_description="Test agent",
                user_id="test-user",
                url="http://localhost:8000/test-agent"
            )


@pytest.mark.asyncio
async def test_intent_data_validation():
    """Test IntentData dataclass validation"""
    from robutler.api.client import IntentData
    
    # Test valid data
    valid_data = IntentData(
        intent="test intent",
        user_id="test-user",
        agent_id="test-agent",
        agent_description="Test agent description",
        url="http://localhost:8000"
    )
    assert valid_data.protocol == "openai/completions"
    assert valid_data.subpath == "/chat/completions"
    assert valid_data.ttl_days == 30
    assert valid_data.rank == 0.0
    
    # Test empty intent
    with pytest.raises(ValueError) as exc_info:
        IntentData(
            intent="",
            user_id="test-user",
            agent_id="test-agent",
            agent_description="Test agent description",
            url="http://localhost:8000"
        )
    assert "Intent text cannot be empty" in str(exc_info.value)
    
    # Test empty user_id
    with pytest.raises(ValueError) as exc_info:
        IntentData(
            intent="test intent",
            user_id="",
            agent_id="test-agent",
            agent_description="Test agent description",
            url="http://localhost:8000"
        )
    assert "User ID cannot be empty" in str(exc_info.value)
    
    # Test invalid TTL
    with pytest.raises(ValueError) as exc_info:
        IntentData(
            intent="test intent",
            user_id="test-user",
            agent_id="test-agent",
            agent_description="Test agent description",
            url="http://localhost:8000",
            ttl_days=400  # Too high
        )
    assert "TTL days must be between 1 and 365" in str(exc_info.value)


if __name__ == "__main__":
    # Run a quick test
    import asyncio
    
    async def quick_test():
        api = RobutlerApi(backend_url="http://test.example.com", api_key="test-key")
        print("✅ Intent Router API client created successfully")
        print("✅ All intent methods are available:")
        print(f"  - intent_health_check: {hasattr(api, 'intent_health_check')}")
        print(f"  - create_intent: {hasattr(api, 'create_intent')}")
        print(f"  - search_intents: {hasattr(api, 'search_intents')}")
        print(f"  - list_intents: {hasattr(api, 'list_intents')}")
        print(f"  - delete_intent: {hasattr(api, 'delete_intent')}")
        await api.close()
    
    asyncio.run(quick_test()) 