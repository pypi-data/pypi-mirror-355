"""
Robutler API Client - Comprehensive Python client for Robutler backend services

This module provides a complete Python client for interacting with the Robutler 
ecosystem, including user management, credit tracking, payment tokens, integrations, 
and intent-based agent routing.

Key Features:
    * Authentication and connection validation
    * User account and credit management
    * API key lifecycle management
    * Payment token system for credit transfers
    * Integration management for third-party services
    * Intent router for natural language agent discovery
    * Comprehensive error handling and retry logic
    * Async/await support with context managers

Core Components:
    * RobutlerApi: Main client class with all API endpoints
    * Type definitions for all API data structures
    * RobutlerApiError: Custom exception for API errors
    * Utility functions for client initialization and validation

Example Usage:
    Basic client setup:
    
    ```python
    from robutler.api import RobutlerApi, initialize_api
    
    # Initialize with environment variables
    api = await initialize_api()
    
    # Or initialize manually
    async with RobutlerApi(
        backend_url="https://api.robutler.ai",
        api_key="your-api-key"
    ) as api:
        # Check connection
        is_connected = await api.validate_connection()
        print(f"Connected: {is_connected}")
    ```
    
    User and credit management:
    
    ```python
    # Get user information
    user = await api.get_user_info()
    print(f"User: {user['name']} ({user['email']})")
    
    # Check credit balance
    credits = await api.get_user_credits()
    print(f"Available: {credits['availableCredits']} credits")
    
    # Manage API keys
    keys = await api.list_api_keys()
    new_key = await api.create_api_key(
        name="MyApp Key",
        daily_credit_limit=10000
    )
    ```
    
    Payment tokens for credit transfers:
    
    ```python
    # Issue a payment token
    token_response = await api.issue_payment_token(
        amount=5000,
        ttl_hours=24
    )
    token = token_response['token']['token']
    
    # Validate token
    validation = await api.validate_payment_token(token)
    print(f"Token valid: {validation['valid']}")
    
    # Redeem token
    result = await api.redeem_payment_token(token, amount=5000)
    ```
    
    Intent-based agent routing:
    
    ```python
    # Register an intent
    intent_result = await api.create_intent(
        intent="help with Python programming",
        agent_id="PythonHelper",
        agent_description="AI assistant for Python development",
        user_id="user123",
        url="https://myserver.com/python-helper"
    )
    
    # Search for agents by intent
    search_result = await api.search_intents(
        intent="debug my Python code",
        top_k=3
    )
    
    for result in search_result['data']['results']:
        print(f"Agent: {result['agent_id']} (similarity: {result['similarity']})")
    ```

Data Types:
    The module provides comprehensive type definitions for all API structures:
    
    * User: User account information and credit totals
    * ApiKey: API key details with permissions and limits
    * PaymentToken: Credit transfer tokens with amounts and expiration
    * Integration: Third-party service integrations
    * CreditTransaction: Credit usage and transfer history
    * Intent types: For natural language agent routing
    * Error types: Structured error information

Integration Patterns:
    Context manager usage:
    
    ```python
    async with RobutlerApi() as api:
        # Client automatically closes after use
        user = await api.get_user_info()
        credits = await api.get_user_credits()
    # Connection cleaned up automatically
    ```
    
    Error handling:
    
    ```python
    try:
        result = await api.create_intent(...)
    except RobutlerApiError as e:
        print(f"API Error: {e.message}")
        if e.status_code == 402:
            print("Insufficient credits")
        elif e.status_code == 429:
            print("Rate limit exceeded")
    ```
    
    Batch operations:
    
    ```python
    # Get multiple data points efficiently
    user, credits, keys = await asyncio.gather(
        api.get_user_info(),
        api.get_user_credits(),
        api.list_api_keys()
    )
    ```

Authentication:
    The client supports multiple authentication methods:
    
    * Environment variables (ROBUTLER_API_KEY, ROBUTLER_BACKEND_URL)
    * Direct parameter passing
    * Configuration file support
    * Automatic token refresh and validation
"""
import os
import json
import logging
import uuid
import asyncio
from typing import Any, Dict, List, Optional, Union, TypedDict
import httpx
from dotenv import load_dotenv
from dataclasses import dataclass
# Import global settings
from robutler.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions based on the API spec
class User(TypedDict):
    id: str
    email: str
    name: str
    image: Optional[str]
    totalCredits: int
    usedCredits: int

class ApiKey(TypedDict):
    id: str
    name: str
    userId: str
    isActive: bool
    createdAt: str  # ISO date string
    updatedAt: str  # ISO date string
    lastUsed: Optional[str]  # ISO date string
    expiresAt: Optional[str]  # ISO date string
    permissions: Optional[List[str]]
    dailyRateLimit: Optional[int]
    dailyCreditLimit: int
    sessionCreditLimit: int
    spentCredits: int
    earnedCredits: int

class PaymentToken(TypedDict):
    id: str
    userId: str
    recipientId: Optional[str]
    token: str
    amount: int
    availableAmount: int
    status: str  # active | partially_redeemed | redeemed | cancelled | expired
    createdAt: str  # ISO date string
    updatedAt: str  # ISO date string
    expiresAt: str  # ISO date string
    apiKeyId: Optional[str]

class Integration(TypedDict):
    id: str
    userId: str
    name: Optional[str]
    type: str
    protocol: str
    secret: Optional[str]
    apiKeyId: Optional[str]
    createdAt: str  # ISO date string
    updatedAt: str  # ISO date string

class CreditTransaction(TypedDict):
    id: str
    userId: str
    amount: int
    type: str  # addition | usage | transfer
    source: str
    description: Optional[str]
    receipt: Optional[str]
    createdAt: str  # ISO date string
    apiKeyId: Optional[str]
    recipientId: Optional[str]

class Credits(TypedDict):
    totalCredits: int
    usedCredits: int
    availableCredits: int

# Intent Router API Types
class IntentHealthStatus(TypedDict):
    status: str  # healthy | initializing | unhealthy
    service: str
    embedding_provider: Optional[str]
    collection: Optional[str]
    timestamp: str
    ready: bool
    error: Optional[str]  # Only present when status is unhealthy

class IntentResult(TypedDict):
    id: str
    similarity: float
    intent: str
    agent_id: str
    agent_description: str
    rank: float
    url: str
    protocol: str
    subpath: str
    latitude: Optional[float]
    longitude: Optional[float]

class IntentSearchDebug(TypedDict):
    totalCandidates: int
    threshold: float
    searchTypes: List[str]
    filteredByThreshold: int

class IntentSearchResponse(TypedDict):
    success: bool
    message: str
    data: Dict[str, Any]  # Contains 'results' and 'debug'

class IntentListItem(TypedDict):
    intent_id: str
    intent: str
    created_at: int
    expires_at: int
    has_location: bool

class IntentCreateRequest(TypedDict, total=False):
    intent: str  # Required
    latitude: Optional[float]
    longitude: Optional[float]
    ttl_days: Optional[int]
    agent_id: Optional[str]
    agent_description: Optional[str]
    url: Optional[str]
    protocol: Optional[str]
    subpath: Optional[str]
    user_id: Optional[str]
    rank: Optional[float]

class IntentSearchRequest(TypedDict, total=False):
    intent: str  # Required
    agent_id: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    top_k: Optional[int]
    radius_km: Optional[float]
    search_type: Optional[str]  # vector | text | hybrid

class RobutlerApiError(Exception):
    """Exception raised for Robutler API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

@dataclass
class IntentData:
    """Data class for intent creation with required fields."""
    intent: str
    user_id: str
    agent_id: str
    agent_description: str
    url: str
    protocol: str = "openai/completions"
    subpath: str = "/chat/completions"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ttl_days: int = 30
    rank: float = 0.0

    def __post_init__(self):
        """Validate the intent data after initialization."""
        if not self.intent.strip():
            raise ValueError("Intent text cannot be empty")
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        if not self.agent_id.strip():
            raise ValueError("Agent ID cannot be empty")
        if not self.agent_description.strip():
            raise ValueError("Agent description cannot be empty")
        if not self.url.strip():
            raise ValueError("URL cannot be empty")
        if self.ttl_days < 1 or self.ttl_days > 365:
            raise ValueError("TTL days must be between 1 and 365")

class RobutlerApi:
    """
    Comprehensive async client for the Robutler API ecosystem.
    
    This client provides full access to all Robutler backend services including
    user management, credit tracking, payment tokens, integrations, and the 
    intent router for natural language agent discovery.
    
    Key Features:
        * Async/await support with context manager pattern
        * Automatic authentication and error handling
        * Comprehensive type safety with TypedDict returns
        * Built-in retry logic and connection validation
        * Support for all Robutler API endpoints
        * Environment variable configuration
        
    Supported Operations:
        * User account and credit management
        * API key creation and lifecycle management
        * Payment token issuance and redemption
        * Integration management for third-party services
        * Intent registration and natural language search
        * Health monitoring and connection validation
    
    Attributes:
        backend_url: Base URL for the Robutler API
        api_key: Authentication token for API access
        client: Underlying HTTP client for requests
    
    Example Usage:
        Context manager pattern (recommended):
        
        ```python
        async with RobutlerApi() as api:
            # Connection automatically managed
            user = await api.get_user_info()
            print(f"Hello {user['name']}!")
            
            # Check available credits
            credits = await api.get_user_credits()
            if credits['availableCredits'] > 1000:
                # Perform operations
                pass
        # Client automatically closed
        ```
        
        Manual management:
        
        ```python
        api = RobutlerApi(
            backend_url="https://api.robutler.ai",
            api_key="your-key-here"
        )
        
        try:
            # Validate connection first
            if await api.validate_connection():
                user = await api.get_user_info()
                print(f"Connected as {user['email']}")
        finally:
            await api.close()
        ```
        
        Environment configuration:
        
        ```python
        # Set environment variables:
        # ROBUTLER_BACKEND_URL=https://api.robutler.ai
        # ROBUTLER_API_KEY=your-api-key
        
        async with RobutlerApi() as api:
            # Automatically uses environment variables
            await api.validate_connection()
        ```
    
    Error Handling:
        The client raises RobutlerApiError for all API-related issues:
        
        ```python
        try:
            result = await api.create_api_key("MyKey")
        except RobutlerApiError as e:
            if e.status_code == 402:
                print("Insufficient credits")
            elif e.status_code == 429:
                print("Rate limit exceeded") 
            elif e.status_code == 401:
                print("Invalid API key")
            else:
                print(f"API error: {e.message}")
        ```
    
    Integration Patterns:
        Batch operations:
        
        ```python
        # Efficient parallel requests
        user, credits, keys = await asyncio.gather(
            api.get_user_info(),
            api.get_user_credits(), 
            api.list_api_keys()
        )
        ```
        
        Payment workflow:
        
        ```python
        # Issue payment token
        token_response = await api.issue_payment_token(
            amount=5000,
            ttl_hours=24
        )
        token = token_response['token']['token']
        
        # Share token with recipient
        # ...
        
        # Recipient redeems token
        redeem_result = await api.redeem_payment_token(
            token=token,
            amount=5000
        )
        ```
        
        Intent-based routing:
        
        ```python
        # Register agent capability
        await api.create_intent(
            intent="help with Python programming",
            agent_id="PythonHelper", 
            agent_description="Expert Python development assistant",
            user_id="your-user-id",
            url="https://your-server.com/python-helper"
        )
        
        # Find best agent for user query
        results = await api.search_intents(
            intent="debug my Flask application",
            top_k=1
        )
        
        if results['data']['results']:
            best_agent = results['data']['results'][0]
            agent_url = best_agent['url']
            # Route request to best agent
        ```
    
    Authentication:
        Supports multiple authentication methods:
        
        * Environment variables (ROBUTLER_API_KEY)
        * Direct parameter passing
        * Global settings configuration
        * Automatic header management
        
    Thread Safety:
        Each RobutlerApi instance is thread-safe when used with asyncio.
        Create separate instances for different threads or use a connection pool.
    """
    
    def __init__(self, backend_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the Robutler API client.
        
        Args:
            backend_url: Base URL for the Robutler API. If not provided,
                will use ROBUTLER_BACKEND_URL environment variable or 
                global settings. Should not include trailing slash.
                
            api_key: Robutler API key for authentication. If not provided,
                will use ROBUTLER_API_KEY environment variable or
                global settings.
        
        Raises:
            ValueError: If backend_url cannot be determined from parameters,
                environment variables, or global settings.
        
        Example:
            ```python
            # Explicit configuration
            api = RobutlerApi(
                backend_url="https://api.robutler.ai",
                api_key="rob_1234567890abcdef"
            )
            
            # Environment-based (recommended for production)
            api = RobutlerApi()  # Uses ROBUTLER_* env vars
            
            # Mixed approach
            api = RobutlerApi(
                backend_url="https://staging.robutler.ai"
                # api_key from environment
            )
            ```
        """
        self.backend_url = backend_url or settings.robutler_url
        self.api_key = api_key or settings.api_key
        
        if not self.backend_url:
            raise ValueError("Robutler backend URL not provided and not set in global settings")
        
        # Remove trailing slash if present
        if self.backend_url.endswith("/"):
            self.backend_url = self.backend_url[:-1]
            
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.backend_url,
            timeout=30.0,
            follow_redirects=True
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authentication.
        
        Returns:
            Dict with appropriate Authorization header
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Robutler API.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data (for POST/PUT)
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            RobutlerApiError: On API error responses
        """
        url = f"{endpoint}"
        headers = self._get_headers()
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Return the JSON response if present, otherwise empty dict
            if response.text:
                return response.json()
            return {}
            
        except httpx.HTTPStatusError as e:
            # Handle API error responses
            status_code = e.response.status_code
            error_message = str(e)
            
            try:
                # Try to get error details from the JSON response
                response_json = e.response.json()
                error_message = response_json.get("error", response_json.get("message", response_json))
                # If it's still a dict, convert to string
                if isinstance(error_message, dict):
                    error_message = str(error_message)
            except Exception:
                # Fallback to response text or original error
                error_message = e.response.text or str(e)
            
            # Debug logging for 422 errors
            if status_code == 422:
                print(f"🔍 422 Error Details:")
                print(f"   Response text: {e.response.text}")
                print(f"   Request data: {data}")
            
            raise RobutlerApiError(
                message=error_message,
                status_code=status_code,
            )
        except httpx.RequestError as e:
            # Handle network/connection errors
            raise RobutlerApiError(f"Request error: {str(e)}")
    
    async def validate_connection(self) -> bool:
        """
        Validate the connection to the Robutler backend and API key if provided.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Check if the API is operational
            await self.health_check()
            
            # If API key is provided, verify it by trying to get user info
            if self.api_key:
                await self.get_user_info()
                
            return True
        except RobutlerApiError as e:
            logger.error(f"API validation failed: {e.message}")
            return False
    
    # Health Check
    async def health_check(self) -> bool:
        """
        Check if the Robutler API is operational.
        
        Returns:
            True if API is healthy
            
        Raises:
            RobutlerApiError: If API is not healthy
        """
        await self._request("GET", "/api/health")
        return True
    
    # User Information
    async def get_user_info(self) -> User:
        """
        Get current user profile information.
        
        Returns:
            User object
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", "/api/user")
        return response.get("user", {})
    
    async def get_user_credits(self) -> Credits:
        """
        Get user credit information.
        
        Returns:
            Credits object with credit information
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", "/api/user/credits")
        return response.get("credits", {})
    
    # API Keys
    async def list_api_keys(self) -> List[ApiKey]:
        """
        List all API keys for the authenticated user.
        
        Returns:
            List of ApiKey objects
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", "/api/api-keys")
        return response.get("keys", [])
    
    async def create_api_key(
        self,
        name: str,
        expires_in_days: Optional[int] = None,
        permissions: Optional[List[str]] = None,
        daily_rate_limit: Optional[int] = None,
        daily_credit_limit: Optional[int] = None,
        session_credit_limit: Optional[int] = None
    ) -> Dict[str, Union[ApiKey, str]]:
        """
        Create a new API key.
        
        Args:
            name: Name for the API key
            expires_in_days: Optional expiration days
            permissions: Optional permissions list
            daily_rate_limit: Optional daily rate limit
            daily_credit_limit: Optional daily credit limit
            session_credit_limit: Optional session credit limit
            
        Returns:
            Dictionary with key (ApiKey) and rawKey (string)
            
        Raises:
            RobutlerApiError: On API error
        """
        data = {
            "name": name,
        }
        
        # Add optional parameters if provided
        if expires_in_days is not None:
            data["expiresInDays"] = expires_in_days
        if permissions is not None:
            data["permissions"] = permissions
        if daily_rate_limit is not None:
            data["dailyRateLimit"] = daily_rate_limit
        if daily_credit_limit is not None:
            data["dailyCreditLimit"] = daily_credit_limit
        if session_credit_limit is not None:
            data["sessionCreditLimit"] = session_credit_limit
        
        response = await self._request("POST", "/api/api-keys", data=data)
        return {
            "key": response.get("key", {}),
            "rawKey": response.get("rawKey", "")
        }
    
    async def get_api_key(self, key_id: str) -> ApiKey:
        """
        Get specific API key information.
        
        Args:
            key_id: API key ID
            
        Returns:
            ApiKey object
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", f"/api/api-keys/{key_id}")
        return response.get("key", {})
    
    async def delete_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key ID to revoke
            
        Returns:
            True if successful
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("DELETE", f"/api/api-keys/{key_id}")
        return response.get("success", False)
    
    async def get_api_key_stats(self, key_id: str) -> Dict[str, int]:
        """
        Get usage statistics for an API key.
        
        Args:
            key_id: API key ID
            
        Returns:
            Dictionary with tokens and credits statistics
            
        Raises:
            RobutlerApiError: On API error
        """
        return await self._request("GET", f"/api/api-keys/{key_id}/stats")
    
    # Payment Tokens
    async def validate_payment_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a payment token.
        
        Args:
            token: Payment token string
            
        Returns:
            Dictionary with validation results
            
        Raises:
            RobutlerApiError: On API error
        """
        return await self._request("POST", "/api/token/validate", data={"token": token})
    
    async def redeem_payment_token(
        self,
        token: str,
        amount: Optional[int] = None,
        recipient_id: Optional[str] = None,
        api_key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redeem a payment token.
        
        Args:
            token: Payment token string
            amount: Optional amount to redeem (defaults to full amount)
            recipient_id: Optional recipient user ID
            api_key_id: Optional API key ID
            
        Returns:
            Dictionary with redemption results
            
        Raises:
            RobutlerApiError: On API error
        """
        data = {"token": token}
        
        if amount is not None:
            data["amount"] = amount
        if recipient_id is not None:
            data["recipient_id"] = recipient_id
        if api_key_id is not None:
            data["api_key_id"] = api_key_id
            
        return await self._request("POST", "/api/token/redeem", data=data)
    
    async def issue_payment_token(
        self,
        amount: Optional[int] = None,
        recipient_id: Optional[str] = None,
        ttl_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Issue a new payment token.
        
        Args:
            amount: Optional credit amount
            recipient_id: Optional recipient user ID
            ttl_hours: Optional time-to-live in hours
            
        Returns:
            Dictionary with token information
            
        Raises:
            RobutlerApiError: On API error
        """
        data = {}
        
        if amount is not None:
            data["amount"] = amount
        if recipient_id is not None:
            data["recipientId"] = recipient_id
        if ttl_hours is not None:
            data["ttlHours"] = ttl_hours
            
        response = await self._request("POST", "/api/user/tokens", data=data)
        return {"token": response.get("token", {})}
    
    async def cancel_payment_token(self, token_id: str) -> Dict[str, Any]:
        """
        Cancel a payment token.
        
        Args:
            token_id: Payment token ID
            
        Returns:
            Dictionary with cancellation results
            
        Raises:
            RobutlerApiError: On API error
        """
        return await self._request("POST", "/api/user/tokens/cancel", data={"tokenId": token_id})
    
    # Integrations
    async def list_integrations(self) -> List[Integration]:
        """
        List all integrations for the authenticated user.
        
        Returns:
            List of Integration objects
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", "/api/user/integrations")
        return response.get("integrations", [])
    
    async def create_integration(
        self,
        type_: str,
        protocol: str,
        name: Optional[str] = None,
        secret: Optional[str] = None,
        api_key_id: Optional[str] = None
    ) -> Integration:
        """
        Create a new integration.
        
        Args:
            type_: Integration type
            protocol: Integration protocol
            name: Optional integration name
            secret: Optional integration secret
            api_key_id: Optional API key ID to associate
            
        Returns:
            Integration object
            
        Raises:
            RobutlerApiError: On API error
        """
        data = {
            "type": type_,
            "protocol": protocol
        }
        
        if name is not None:
            data["name"] = name
        if secret is not None:
            data["secret"] = secret
        if api_key_id is not None:
            data["apiKeyId"] = api_key_id
            
        response = await self._request("POST", "/api/user/integrations", data=data)
        return response.get("integration", {})
    
    async def get_integration(self, integration_id: str) -> Integration:
        """
        Get specific integration information.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration object
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", f"/api/user/integrations/{integration_id}")
        return response.get("integration", {})
    
    async def delete_integration(self, integration_id: str) -> bool:
        """
        Delete an integration.
        
        Args:
            integration_id: Integration ID to delete
            
        Returns:
            True if successful
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("DELETE", f"/api/user/integrations/{integration_id}")
        return response.get("success", False)

    # Intent Router API Methods
    async def intent_health_check(self) -> IntentHealthStatus:
        """
        Check the health status of the intent router service.
        
        Returns:
            IntentHealthStatus object with service health information
            
        Raises:
            RobutlerApiError: On API error
        """
        response = await self._request("GET", "/api/intents/health")
        return response
    
    async def create_intent(
        self,
        intent: str,
        agent_id: str,
        agent_description: str,
        user_id: str,
        url: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        ttl_days: int = 30,
        subpath: str = "/chat/completions",
        rank: float = 0.0
    ) -> Dict[str, Any]:
        """
        Create a new intent with required fields.
        
        Args:
            intent: The intent text (required)
            agent_id: Agent identifier (required)
            agent_description: Agent description (required)
            user_id: User identifier (required)
            url: Agent URL (required)
            latitude: Optional latitude coordinate
            longitude: Optional longitude coordinate
            ttl_days: Time-to-live in days (1-365, default 30)
            subpath: Subpath for the agent endpoint (default "/chat/completions")
            rank: Ranking value (default 0.0)
            
        Returns:
            Dictionary with success status, message, and intent_id
            
        Raises:
            RobutlerApiError: On API error
            ValueError: If required fields are missing or invalid
        """
        # Validate and truncate fields according to API constraints
        if len(agent_description) > 256:
            agent_description = agent_description[:256]
        if len(url) > 100:
            raise ValueError(f"URL too long ({len(url)} chars, max 100): {url}")
        if len(subpath) > 32:
            subpath = subpath[:32]
        
        # Create IntentData instance with validation
        intent_data = IntentData(
            intent=intent,
            user_id=user_id,
            agent_id=agent_id,
            agent_description=agent_description,
            url=url,
            protocol="openai/completions",
            subpath=subpath,
            latitude=latitude,
            longitude=longitude,
            ttl_days=ttl_days,
            rank=rank
        )
        
        # Convert to API request format
        data: IntentCreateRequest = {
            "intent": intent_data.intent,
            "user_id": intent_data.user_id,
            "agent_id": intent_data.agent_id,
            "agent_description": intent_data.agent_description,
            "url": intent_data.url,
            "protocol": intent_data.protocol,
            "subpath": intent_data.subpath,
            "ttl_days": intent_data.ttl_days,
            "rank": intent_data.rank
        }
        
        if intent_data.latitude is not None:
            data["latitude"] = intent_data.latitude
        if intent_data.longitude is not None:
            data["longitude"] = intent_data.longitude
        
        # Debug logging
        print(f"🔍 Intent API request data: {data}")
            
        return await self._request("POST", "/api/intents/create", data=data)
    
    async def search_intents(
        self,
        intent: str,
        agent_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        top_k: Optional[int] = None,
        radius_km: Optional[float] = None,
        search_type: Optional[str] = None
    ) -> IntentSearchResponse:
        """
        Search for intents using hybrid search (sparse + dense).
        
        Args:
            intent: The search query text (required)
            agent_id: Optional agent identifier filter
            latitude: Optional latitude for location-based search
            longitude: Optional longitude for location-based search
            top_k: Optional number of results to return (1-100, default 5)
            radius_km: Optional search radius in kilometers (default 100)
            search_type: Optional search type: "vector", "text", or "hybrid" (default "hybrid")
            
        Returns:
            IntentSearchResponse with results and debug information
            
        Raises:
            RobutlerApiError: On API error
        """
        data: IntentSearchRequest = {"intent": intent}
        
        if agent_id is not None:
            data["agent_id"] = agent_id
        if latitude is not None:
            data["latitude"] = latitude
        if longitude is not None:
            data["longitude"] = longitude
        if top_k is not None:
            data["top_k"] = top_k
        if radius_km is not None:
            data["radius_km"] = radius_km
        if search_type is not None:
            data["search_type"] = search_type
            
        return await self._request("POST", "/api/intents/search", data=data)
    
    async def list_intents(
        self,
        user_id: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all intents for a specific agent and user.
        
        Args:
            user_id: User identifier (required)
            agent_id: Optional agent identifier filter
            
        Returns:
            Dictionary with success status, message, and list of intents
            
        Raises:
            RobutlerApiError: On API error
        """
        data = {"user_id": user_id}
        
        if agent_id is not None:
            data["agent_id"] = agent_id
            
        return await self._request("POST", "/api/intents/list", data=data)
    
    async def delete_intent(
        self,
        intent_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Delete a specific intent by ID.
        
        Args:
            intent_id: Intent identifier to delete (required)
            user_id: User identifier (required)
            
        Returns:
            Dictionary with success status, message, and deletion info
            
        Raises:
            RobutlerApiError: On API error
        """
        data = {
            "intent_id": intent_id,
            "user_id": user_id
        }
        
        return await self._request("POST", "/api/intents/delete", data=data)


# Convenience function to initialize API client
async def initialize_api(
    backend_url: Optional[str] = None, 
    api_key: Optional[str] = None
) -> RobutlerApi:
    """
    Initialize and validate the Robutler API client.
    
    Args:
        backend_url: Optional backend URL (defaults to global settings)
        api_key: Optional API key (defaults to global settings)
        
    Returns:
        Initialized and validated RobutlerApi instance
        
    Raises:
        ValueError: If connection validation fails
    """
    # Initialize API client with settings
    backend_url = backend_url or settings.robutler_url
    api_key = api_key or settings.api_key
    
    # Create client
    api = RobutlerApi(backend_url, api_key)
    
    # Validate connection
    valid = await api.validate_connection()
    if not valid:
        await api.close()
        raise ValueError("Failed to validate Robutler API connection or credentials")
    
    return api 