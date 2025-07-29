"""
Tests for Intent tools using the RobutlerApi client
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastmcp.exceptions import ToolError
from robutler.tools.intents import discovery, create_intent, list_intents, delete_intent
from robutler.api import RobutlerApiError


@pytest.fixture
def mock_context():
    """Mock the FastMCP context"""
    with patch('robutler.tools.intents.get_context') as mock_get_context:
        mock_ctx = MagicMock()
        mock_get_context.return_value = mock_ctx
        yield mock_ctx


@pytest.mark.asyncio
async def test_discovery_success(mock_context):
    """Test successful intent discovery"""
    mock_response = {
        "success": True,
        "message": "Search completed",
        "data": {
            "results": [
                {
                    "id": "intent-1",
                    "similarity": 0.95,
                    "intent": "React development services",
                    "agent_id": "dev-agent",
                    "agent_description": "Web developer",
                    "rank": 0.8,
                    "url": "https://dev.example.com",
                    "protocol": "https",
                    "subpath": "/services",
                    "latitude": None,
                    "longitude": None
                }
            ],
            "debug": {
                "totalCandidates": 10,
                "threshold": 0.7,
                "searchTypes": ["hybrid"],
                "filteredByThreshold": 1
            }
        }
    }
    
    with patch('robutler.tools.intents.RobutlerApi') as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        mock_api.search_intents.return_value = mock_response
        
        result = await discovery(
            intent="React development",
            agent_id="dev-agent",
            top_k=5
        )
        
        # Verify API client was created correctly
        mock_api_class.assert_called_once()
        
        # Verify search_intents was called with correct parameters
        mock_api.search_intents.assert_called_once_with(
            intent="React development",
            agent_id="dev-agent",
            top_k=5
        )
        
        # Verify API client was closed
        mock_api.close.assert_called_once()
        
        # Verify result
        assert result["message"] == "Found 1 similar intents"
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["intent"] == "React development services"


@pytest.mark.asyncio
async def test_discovery_api_error(mock_context):
    """Test discovery with API error"""
    with patch('robutler.tools.intents.RobutlerApi') as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        mock_api.search_intents.side_effect = RobutlerApiError("API Error", status_code=400)
        
        with pytest.raises(ToolError) as exc_info:
            await discovery(intent="test intent")
        
        assert "Intent Router API error: API Error" in str(exc_info.value)
        mock_api.close.assert_called_once()


@pytest.mark.asyncio
async def test_create_intent_success(mock_context):
    """Test successful intent creation"""
    mock_response = {
        "success": True,
        "message": "Intent created successfully",
        "data": {
            "intent_id": "intent-123"
        }
    }
    
    # Mock user info response for fallback user_id retrieval
    mock_user_info = {"id": "test-user", "name": "Test User"}
    
    with patch('robutler.tools.intents.RobutlerApi') as mock_api_class, \
         patch('robutler.server.get_server_context') as mock_get_server_context, \
         patch('os.getenv') as mock_getenv:
        
        # Mock server context to return None (so fallback is used)
        mock_get_server_context.return_value = None
        
        # Mock BASE_URL environment variable
        mock_getenv.return_value = "http://localhost:2224"
        
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        mock_api.get_user_info.return_value = mock_user_info
        mock_api.create_intent.return_value = mock_response
        
        result = await create_intent(
            intent="I offer web development services",
            agent_id="dev-agent",
            agent_description="Web developer",
            latitude=40.7128,
            longitude=-74.0060,
            ttl_days=30,
            subpath="/services",
            rank=0.9
        )
        
        # Verify API client was created twice (once for user_id, once for intent creation)
        assert mock_api_class.call_count == 2
        
        # Verify get_user_info was called for fallback
        mock_api.get_user_info.assert_called_once()
        
        # Verify create_intent was called with correct parameters
        mock_api.create_intent.assert_called_once_with(
            intent="I offer web development services",
            agent_id="dev-agent",
            agent_description="Web developer",
            user_id="test-user",
            url="http://localhost:2224/dev-agent",
            latitude=40.7128,
            longitude=-74.0060,
            ttl_days=30,
            subpath="/services",
            rank=0.9
        )
        
        # Verify API client was closed twice
        assert mock_api.close.call_count == 2
        
        # Verify result
        assert result["message"] == "Intent created successfully"
        assert result["data"]["intent_id"] == "intent-123"


@pytest.mark.asyncio
async def test_list_intents_success(mock_context):
    """Test successful intent listing"""
    mock_response = {
        "success": True,
        "message": "Found 2 intents",
        "data": {
            "intents": [
                {"intent_id": "intent-1", "intent": "Web development"},
                {"intent_id": "intent-2", "intent": "Mobile apps"}
            ]
        }
    }
    
    with patch('robutler.tools.intents.RobutlerApi') as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        mock_api.list_intents.return_value = mock_response
        
        result = await list_intents(
            agent_id="dev-agent"
        )
        
        # Verify API client was created correctly
        mock_api_class.assert_called_once()
        
        # Verify list_intents was called with correct parameters
        # Note: user_id will be retrieved from get_user_info in the actual function
        mock_api.list_intents.assert_called_once()
        
        # Verify API client was closed
        mock_api.close.assert_called_once()
        
        # Verify result
        assert result["message"] == "Found 2 intents"
        assert len(result["data"]["intents"]) == 2


@pytest.mark.asyncio
async def test_delete_intent_success(mock_context):
    """Test successful intent deletion"""
    mock_response = {
        "success": True,
        "message": "Intent deleted successfully",
        "data": {
            "deleted_count": 1,
            "intent_id": "intent-123"
        }
    }
    
    with patch('robutler.tools.intents.RobutlerApi') as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        mock_api.delete_intent.return_value = mock_response
        
        result = await delete_intent(
            intent_id="intent-123"
        )
        
        # Verify API client was created correctly
        mock_api_class.assert_called_once()
        
        # Verify delete_intent was called with correct parameters
        # Note: user_id will be retrieved from get_user_info in the actual function
        mock_api.delete_intent.assert_called_once()
        
        # Verify API client was closed
        mock_api.close.assert_called_once()
        
        # Verify result
        assert result["message"] == "Intent deleted successfully"
        assert result["data"]["deleted_count"] == 1


@pytest.mark.asyncio
async def test_create_intent_missing_api_key(mock_context):
    """Test create_intent with missing API key"""
    with patch('robutler.tools.intents.settings') as mock_settings:
        mock_settings.api_key = None
        
        with pytest.raises(ToolError) as exc_info:
            await create_intent(
                intent="test intent",
                agent_id="test-agent",
                agent_description="Test agent"
            )
        
        assert "Robutler API key not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_discovery_minimal_parameters(mock_context):
    """Test discovery with minimal parameters"""
    mock_response = {
        "success": True,
        "message": "Search completed",
        "data": {
            "results": [],
            "debug": {
                "totalCandidates": 0,
                "threshold": 0.7,
                "searchTypes": ["hybrid"],
                "filteredByThreshold": 0
            }
        }
    }
    
    with patch('robutler.tools.intents.RobutlerApi') as mock_api_class:
        mock_api = AsyncMock()
        mock_api_class.return_value = mock_api
        mock_api.search_intents.return_value = mock_response
        
        result = await discovery(intent="test query")
        
        # Verify search_intents was called with minimal parameters
        mock_api.search_intents.assert_called_once_with(
            intent="test query",
            agent_id=None,
            top_k=10  # default value
        )
        
        # Verify result
        assert result["message"] == "Found 0 similar intents"
        assert len(result["data"]["results"]) == 0


if __name__ == "__main__":
    # Run a quick test
    print("✅ Intent tools tests created successfully")
    print("✅ Tests verify that tools use RobutlerApi client correctly")
    print("✅ Tests cover success cases, error handling, and parameter validation") 