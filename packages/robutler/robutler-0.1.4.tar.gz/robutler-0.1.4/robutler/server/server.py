"""
RobutlerServer - FastAPI-based server framework with credit tracking

This module provides the core RobutlerServer class that extends FastAPI with 
built-in credit tracking, payment token validation, automatic agent 
registration, and OpenAI-compatible endpoints.

Key Features:
    * Automatic agent endpoint creation with /chat/completions
    * Built-in credit tracking and usage monitoring
    * Payment token validation and charging
    * OpenAI-compatible streaming responses
    * Intent-based agent routing
    * Middleware for request/response lifecycle management
    * Tool pricing decorators with automatic billing

Core Components:
    * RobutlerServer: Main FastAPI server class with agent integration
    * ServerContext: Request-scoped context for tracking usage and metadata
    * @pricing: Decorator for automatic tool cost tracking
    * Payment token system for credit management
    * Streaming response wrappers for real-time usage tracking

Example Usage:
    Basic server with agents:
    
    ```python
    from robutler.server import RobutlerServer
    from robutler.agent import RobutlerAgent
    
    # Create agents
    agent = RobutlerAgent(
        name="Assistant",
        instructions="You are helpful",
        credits_per_token=10
    )
    
    # Create server with automatic endpoints
    app = RobutlerServer(
        agents=[agent],
        min_balance=1000  # Minimum credits required
    )
    
    # Server automatically creates:
    # POST /Assistant/chat/completions
    # GET /Assistant/info
    # GET /Assistant/pricing
    ```
    
    Custom endpoints with pricing:
    
    ```python
    from robutler.server import RobutlerServer, pricing
    
    app = RobutlerServer()
    
    @app.agent("/weather", intents=["get weather information"])
    @pricing(credits_per_call=5000)
    async def weather_agent(request):
        # Custom agent logic
        return {"response": "Weather data..."}
    
    @pricing(credits_per_token=2)
    def expensive_tool(query: str) -> str:
        # Tool with per-token pricing
        return process_query(query)
    ```
    
    Context and usage tracking:
    
    ```python
    from robutler.server import get_server_context
    
    @app.before_request
    async def setup_context(request, context):
        # Add custom data to context
        context.set_custom_data('user_id', request.headers.get('X-User-ID'))
    
    @app.after_request  
    async def log_usage(request, response, context):
        # Access usage data
        usage = context.get_usage()
        print(f"Total credits used: {usage['total_credits']}")
    ```

Integration Points:
    * Automatic agent registration with intent routing
    * Payment token validation via Robutler API
    * OpenAI SDK compatibility for chat completions
    * FastAPI middleware for request lifecycle
    * tiktoken integration for accurate token counting
    * Server-Sent Events for streaming responses
"""

import uuid
import asyncio
import json
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from functools import wraps
from datetime import datetime
from contextvars import ContextVar
import os

from fastapi import FastAPI, Request, Response, HTTPException, Path
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import tiktoken
from contextlib import asynccontextmanager

# Import settings for API key validation
from robutler.settings import settings

# Import API client for payment token functionality
from robutler.api import RobutlerApi, initialize_api, RobutlerApiError, User

# Context variable to track the current server call ID
_current_server_call_id: ContextVar[Optional[str]] = ContextVar('current_server_call_id', default=None)

# Context variable to track the current server context
_current_server_context: ContextVar[Optional['ServerContext']] = ContextVar('current_server_context', default=None)

class ReportUsage:
    """
    Wrapper class for explicit usage reporting from functions.
    
    This class provides a clean alternative to returning tuples when functions 
    need to report both content and token usage. It helps distinguish between 
    regular return values and usage reporting data.
    
    Attributes:
        content: The actual content/result from the function
        tokens: Number of tokens consumed (for billing calculation)
    
    Example Usage:
        Without ReportUsage (tuple approach):
        
        ```python
        @pricing(credits_per_token=10)
        def process_text(text: str) -> Tuple[str, int]:
            result = expensive_processing(text)
            tokens = estimate_tokens(result)
            return result, tokens  # Tuple format
        ```
        
        With ReportUsage (cleaner approach):
        
        ```python
        @pricing(credits_per_token=10) 
        def process_text(text: str) -> ReportUsage:
            result = expensive_processing(text)
            tokens = estimate_tokens(result)
            return ReportUsage(content=result, tokens=tokens)
        ```
        
        For tools that auto-calculate tokens:
        
        ```python
        @pricing(credits_per_token=5)
        def ai_summary(text: str) -> ReportUsage:
            summary = generate_summary(text)
            # Automatic token calculation for billing
            return ReportUsage(content=summary, tokens=len(summary.split()))
        ```
    
    Note:
        * Provides better type safety than tuples
        * Makes usage reporting intent explicit
        * Integrates seamlessly with @pricing decorator
        * Supports both fixed and token-based pricing models
    """
    def __init__(self, content: Any, tokens: int):
        self.content = content
        self.tokens = tokens

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = None
    n: Optional[int] = 1


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


class PricingInfo(BaseModel):
    credits_per_call: Optional[int] = None
    credits_per_token: Optional[int] = None


# Global registry for standalone pricing decorators
_standalone_pricing_registry: Dict[str, PricingInfo] = {}


class EndpointInfo(BaseModel):
    path: str
    method: str
    pricing: PricingInfo
    description: Optional[str] = None


class ServerContext:
    """
    Request-scoped context for tracking usage, metadata, and lifecycle data.
    
    ServerContext provides a centralized way to track credits, tokens, and custom 
    data throughout the lifetime of a single request. It's automatically created 
    by RobutlerServer middleware and accessible via get_server_context().
    
    Key Features:
        * Automatic usage tracking for tools and agents
        * Custom data storage for request metadata
        * Comprehensive usage summaries and reporting
        * Integration with payment token billing
        * Support for multiple usage sources per request
    
    Attributes:
        server_call_id: Unique identifier for this request
        server_name: Name of the server handling the request
        start_time: Timestamp when the request started
        usage_records: List of all usage tracking records
        custom_data: Dictionary for storing custom request data
    
    Example Usage:
        Basic usage tracking:
        
        ```python
        context = get_server_context()
        
        # Track tool usage
        usage_id = context.track_usage(
            source="weather_api",
            credits=1000,
            tokens=50,
            source_type="tool"
        )
        
        # Track agent usage  
        context.track_usage(
            source="ChatBot",
            credits=500,
            tokens=25,
            source_type="agent"
        )
        ```
        
        Custom data management:
        
        ```python
        # Store request metadata
        context.set_custom_data('user_id', request.headers.get('X-User-ID'))
        context.set_custom_data('session_id', generate_session_id())
        
        # Retrieve data later
        user_id = context.get_custom_data('user_id')
        session_id = context.get_custom_data('session_id', 'default-session')
        ```
        
        Usage summary and reporting:
        
        ```python
        # Get comprehensive usage summary
        usage_summary = context.get_usage()
        print(f"Total credits: {usage_summary['total_credits']}")
        print(f"Total tokens: {usage_summary['total_tokens']}")
        print(f"Request duration: {usage_summary['duration_seconds']}s")
        
        # Access individual usage records
        for record in usage_summary['tool_usage']:
            print(f"Tool {record['source']}: {record['credits']} credits")
        ```
    
    Integration:
        * Automatically created by RobutlerServer middleware
        * Used by @pricing decorator for automatic billing
        * Integrated with payment token validation and charging
        * Available in before_request, after_request, and finalize_request callbacks
        * Supports both synchronous and asynchronous request handling
    """
    
    def __init__(self, server_call_id: str, server_name: str):
        self.server_call_id = server_call_id
        self.server_name = server_name
        self.start_time = datetime.utcnow()
        self.usage_records: List[Dict[str, Any]] = []
        self.custom_data: Dict[str, Any] = {}  # For storing custom data from callbacks
        
    def track_usage(self, source: str, credits: int, tokens: int = 0, source_type: str = "tool") -> str:
        """
        Track usage from any source (tool, agent, or custom).
        
        Records credit and token consumption for billing and monitoring purposes.
        Each usage record is timestamped and assigned a unique ID for tracking.
        
        Args:
            source: Identifier for the source consuming credits (e.g., tool name, agent name)
            credits: Number of credits consumed by this operation
            tokens: Number of tokens processed (optional, for token-based billing)
            source_type: Type of source consuming credits. Options:
                * "tool" - Function call or tool usage
                * "agent" - AI agent processing
                * "llm" - Direct LLM API usage
                * "custom" - Custom usage tracking
        
        Returns:
            Unique usage ID for this tracking record
        
        Example:
            ```python
            # Track expensive API call
            usage_id = context.track_usage(
                source="google_search_api",
                credits=2000,
                tokens=0,
                source_type="tool"
            )
            
            # Track LLM processing
            context.track_usage(
                source="gpt-4o-mini", 
                credits=150,
                tokens=75,
                source_type="llm"
            )
            ```
        """
        usage_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        usage_record = {
            'usage_id': usage_id,
            'source': source,
            'source_type': source_type,  # "tool" or "agent"
            'credits': credits,
            'tokens': tokens,
            'timestamp': timestamp.isoformat()
        }
        
        self.usage_records.append(usage_record)
        return usage_id
    
    def get_usage(self) -> Dict[str, Any]:
        """
        Get comprehensive usage summary for the current request.
        
        Returns a complete summary of all credits, tokens, and metadata 
        tracked during this request's lifetime.
        
        Returns:
            Dictionary containing:
            * server_call_id: Unique request identifier
            * server_name: Name of the handling server
            * total_credits: Sum of all credits consumed
            * total_tokens: Sum of all tokens processed
            * tool_usage: List of tool-specific usage records
            * server_usage: List of server-level usage records
            * started_at: ISO timestamp when request started
            * completed_at: ISO timestamp when summary was generated
            * duration_seconds: Total request processing time
            * usage_count: Number of individual usage records
            * custom_data: Any custom data stored in context
        
        Example:
            ```python
            usage = context.get_usage()
            
            # Access summary data
            print(f"Request {usage['server_call_id']} consumed:")
            print(f"  Credits: {usage['total_credits']}")
            print(f"  Tokens: {usage['total_tokens']}")
            print(f"  Duration: {usage['duration_seconds']:.2f}s")
            
            # Analyze tool usage
            for tool_record in usage['tool_usage']:
                print(f"  {tool_record['source']}: {tool_record['credits']} credits")
            ```
        """
        total_credits = sum(record['credits'] for record in self.usage_records)
        total_tokens = sum(record['tokens'] for record in self.usage_records)
        
        tool_records = [r for r in self.usage_records if r['source_type'] == 'tool']
        server_records = [r for r in self.usage_records if r['source_type'] == 'server']
        
        return {
            'server_call_id': self.server_call_id,
            'server_name': self.server_name,
            'total_credits': total_credits,
            'total_tokens': total_tokens,
            'tool_usage': tool_records,
            'server_usage': server_records,
            'started_at': self.start_time.isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'usage_count': len(self.usage_records),
            'custom_data': self.custom_data
        }
    
    def set_custom_data(self, key: str, value: Any) -> None:
        """
        Store custom data in the request context.
        
        Allows storing arbitrary data that persists throughout the request 
        lifetime. Useful for tracking user IDs, session data, or request metadata.
        
        Args:
            key: Unique identifier for the data
            value: Any JSON-serializable value to store
        
        Example:
            ```python
            # Store user information
            context.set_custom_data('user_id', '12345')
            context.set_custom_data('user_tier', 'premium')
            context.set_custom_data('request_source', 'mobile_app')
            
            # Store complex data
            context.set_custom_data('request_metadata', {
                'ip_address': '192.168.1.1',
                'user_agent': 'MyApp/1.0',
                'referrer': 'https://example.com'
            })
            ```
        """
        self.custom_data[key] = value
    
    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve custom data from the request context.
        
        Args:
            key: Identifier for the data to retrieve
            default: Value to return if key is not found
        
        Returns:
            The stored value, or default if not found
        
        Example:
            ```python
            # Get required data
            user_id = context.get_custom_data('user_id')
            
            # Get with fallback
            tier = context.get_custom_data('user_tier', 'basic')
            
            # Check if data exists
            if context.get_custom_data('premium_features'):
                enable_advanced_mode()
            ```
        """
        return self.custom_data.get(key, default)


def get_server_context() -> Optional[ServerContext]:
    """
    Get the current server context for the active request.
    
    Returns the ServerContext instance associated with the current request,
    providing access to usage tracking, custom data storage, and request 
    metadata. This function works similar to FastMCP's get_context().
    
    Returns:
        ServerContext instance if called within a request lifecycle, 
        None if called outside of a request context.
    
    Example Usage:
        Basic context access:
        
        ```python
        def my_tool(query: str) -> str:
            context = get_server_context()
            if context:
                # Track custom usage
                context.track_usage("my_tool", credits=100)
                
                # Access request data
                user_id = context.get_custom_data('user_id')
            
            return process_query(query)
        ```
        
        In request callbacks:
        
        ```python
        @app.before_request
        async def setup_request(request, context):
            # Context is automatically available
            context.set_custom_data('start_time', time.time())
        
        @app.after_request
        async def log_request(request, response, context):
            # Same context instance throughout request
            start_time = context.get_custom_data('start_time')
            duration = time.time() - start_time
            logger.info(f"Request took {duration:.2f}s")
        ```
        
        Error handling:
        
        ```python
        def protected_tool(data: str) -> str:
            context = get_server_context()
            if not context:
                # Handle case where function is called outside request
                logger.warning("No server context available")
                return "Error: No context"
            
            # Safe to use context
            context.track_usage("protected_tool", credits=50)
            return process_data(data)
        ```
    
    Note:
        * Returns None when called outside of a request context
        * Context instance persists throughout the entire request lifecycle
        * Same context is accessible in middleware, route handlers, and callbacks
        * Thread-safe and async-safe using contextvars
        * Automatically cleaned up after request completion
    """
    return _current_server_context.get()


def pricing(credits_per_call: Optional[int] = None, credits_per_token: Optional[int] = None):
    """
    Decorator for automatic credit tracking and billing on functions and tools.
    
    This decorator enables automatic usage tracking for any function, making it 
    suitable for tools, API calls, or custom processing that should be billed.
    It integrates seamlessly with RobutlerServer's context system.
    
    Args:
        credits_per_call: Fixed credits charged per function invocation.
            Use for tools with predictable costs (API calls, database queries).
            
        credits_per_token: Credits charged per token of output.
            Use for functions that generate variable amounts of content.
            Token counting is automatic using tiktoken or word-based estimation.
    
    Pricing Models:
        Fixed pricing (per-call):
        
        ```python
        @pricing(credits_per_call=5000)
        def weather_api(location: str) -> str:
            # Fixed cost regardless of output size
            return get_weather_data(location)
        
        @pricing(credits_per_call=10000)
        def database_query(sql: str) -> List[dict]:
            # Database queries have predictable cost
            return execute_query(sql)
        ```
        
        Variable pricing (per-token):
        
        ```python
        @pricing(credits_per_token=10)
        def text_summary(content: str) -> str:
            # Cost scales with output length
            summary = generate_summary(content)
            return summary  # Tokens calculated automatically
        
        @pricing(credits_per_token=5)
        def ai_translation(text: str, target_lang: str) -> str:
            # Translation cost depends on output length
            return translate_text(text, target_lang)
        ```
        
        Explicit token reporting:
        
        ```python
        @pricing(credits_per_token=15)
        def custom_processing(data: str) -> ReportUsage:
            result = expensive_ai_processing(data)
            # Manual token calculation for precise billing
            tokens = calculate_exact_tokens(result)
            return ReportUsage(content=result, tokens=tokens)
        ```
    
    Integration Features:
        * Automatic integration with ServerContext
        * Support for both sync and async functions
        * Works with streaming responses (delayed billing)
        * Compatible with FastAPI route handlers
        * Graceful handling when no context is available
        
    Advanced Usage:
        Tool registration with server:
        
        ```python
        app = RobutlerServer()
        
        @pricing(credits_per_call=2000)
        def search_tool(query: str) -> str:
            return perform_search(query)
        
        # Tool is automatically tracked when called
        ```
        
        Conditional pricing:
        
        ```python
        @pricing(credits_per_token=10)
        def adaptive_tool(input_data: str) -> Union[str, ReportUsage]:
            result = process_data(input_data)
            
            if is_premium_processing(input_data):
                # Custom pricing for premium features
                return ReportUsage(content=result, tokens=len(result) * 2)
            
            # Standard pricing applies automatically
            return result
        ```
    
    Error Handling:
        * Functions work normally even without server context
        * Pricing tracking is optional and non-blocking
        * Errors in token calculation don't affect function execution
        * Graceful degradation for unsupported return types
    
    Note:
        * Cannot use both credits_per_call and credits_per_token simultaneously
        * Token-based pricing requires string output or ReportUsage wrapper
        * Streaming responses are billed after completion
        * Pricing info is stored globally for introspection
    """
    def decorator(func: Callable) -> Callable:
        # Store pricing info in global registry with unique key
        # Use module + qualname to avoid collisions
        module_name = getattr(func, '__module__', 'unknown')
        func_qualname = getattr(func, '__qualname__', func.__name__)
        unique_key = f"{module_name}.{func_qualname}"
        
        _standalone_pricing_registry[unique_key] = PricingInfo(
            credits_per_call=credits_per_call,
            credits_per_token=credits_per_token
        )
        
        def _track_usage(result):
            """Helper function to track usage - works for both sync and async"""
            context = get_server_context()
            if not context:
                return
                
            pricing_info = _standalone_pricing_registry[unique_key]
            
            # Skip tracking for StreamingResponse - it will be handled by the wrapper
            if isinstance(result, StreamingResponse):
                return
                
            credits_consumed = 0
            tokens = 0
            
            if isinstance(result, ReportUsage):
                tokens = result.tokens
                if pricing_info.credits_per_call:
                    credits_consumed = pricing_info.credits_per_call
                elif pricing_info.credits_per_token:
                    credits_consumed = tokens * pricing_info.credits_per_token
            else:
                # Handle other response types
                tokens = _estimate_tokens_standalone(str(result))
                if pricing_info.credits_per_call:
                    credits_consumed = pricing_info.credits_per_call
                elif pricing_info.credits_per_token:
                    credits_consumed = tokens * pricing_info.credits_per_token
            
            if credits_consumed > 0:
                context.track_usage(func.__name__, credits_consumed, tokens, "tool")
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                _track_usage(result)
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                _track_usage(result)
                return result
            return sync_wrapper
    
    return decorator


def _estimate_tokens_standalone(text: str) -> int:
    """Standalone token estimation function"""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = len(encoding.encode(text))
        return max(1, tokens)  # Always return at least 1
    except:
        # Fallback: 1 token ~= 3/4 words
        words = text.split()
        return max(1, int(len(words) * 4 / 3))


def robutler_before(request: Request, context: ServerContext) -> None:
    """
    Built-in before request hook for Robutler authentication
    
    Checks for API Bearer token in Authorization header and sets is_owner flag
    if the token matches the configured API key in settings.
    
    Args:
        request: FastAPI Request object
        context: ServerContext object for storing custom data
    """
    # Check for Authorization header
    auth_header = request.headers.get('authorization', '')
    
    # Extract Bearer token
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check if token matches configured API key
        if settings.api_key and token == settings.api_key:
            context.set_custom_data('is_owner', True)
            context.set_custom_data('auth_method', 'bearer_token')
        else:
            context.set_custom_data('is_owner', False)
            context.set_custom_data('auth_method', 'invalid_bearer_token')
    else:
        # No Bearer token provided
        context.set_custom_data('is_owner', False)
        context.set_custom_data('auth_method', 'none')


# Global flag to track server readiness
_server_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for RobutlerServer startup and shutdown."""
    global _server_ready
    
    # Startup phase
    async def register_intents_when_ready():
        """Register intents after ensuring server is fully ready."""
        # Wait for server to be fully initialized (configurable via environment)
        startup_delay = int(os.getenv("ROBUTLER_STARTUP_DELAY", "10"))
        print(f"⏳ Waiting {startup_delay}s for server initialization...")
        await asyncio.sleep(startup_delay)
        
        # Verify server is responding to health checks
        base_url = os.getenv("BASE_URL")
        if base_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Test health endpoint multiple times with backoff
                    for attempt in range(5):
                        try:
                            response = await client.get(f"{base_url}/health")
                            if response.status_code == 200:
                                print(f"✅ Server health check passed on attempt {attempt + 1}")
                                break
                        except Exception as e:
                            print(f"⚠️ Health check attempt {attempt + 1} failed: {e}")
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        print("⚠️ Server health checks failed, but continuing with intent registration")
            except ImportError:
                print("⚠️ httpx not available, skipping health check")
            except Exception as e:
                print(f"⚠️ Health check failed: {e}, continuing with intent registration")
        
        _server_ready = True
        
        # Register agent intents
        if hasattr(app, '_robutler_agents_with_intents') and app._robutler_agents_with_intents:
            call_id = str(uuid.uuid4())
            context = ServerContext(call_id, "startup")
            token = _current_server_context.set(context)
            
            try:
                if settings.api_key:
                    try:
                        from robutler.api.client import RobutlerApi
                        async with RobutlerApi() as api:
                            user_info = await api.get_user_info()
                            user_id = user_info.get('id')
                            if user_id:
                                context.set_custom_data('user_id', user_id)
                                print("🔍 Registering agent intents...")
                                await app._register_agent_intents(app._robutler_agents_with_intents)
                    except Exception as e:
                        print(f"⚠️  Could not register agent intents: {e}")
            finally:
                _current_server_context.reset(token)
        
        # Register decorator intents
        if hasattr(app, 'agent_intents') and app.agent_intents:
            call_id = str(uuid.uuid4())
            context = ServerContext(call_id, "startup")
            token = _current_server_context.set(context)
            
            try:
                if settings.api_key:
                    try:
                        from robutler.api.client import RobutlerApi
                        async with RobutlerApi() as api:
                            user_info = await api.get_user_info()
                            user_id = user_info.get('id')
                            if user_id:
                                context.set_custom_data('user_id', user_id)
                                print("🔍 Registering decorator intents...")
                                await app.register_decorator_intents()
                    except Exception as e:
                        print(f"⚠️  Could not register decorator intents: {e}")
            finally:
                _current_server_context.reset(token)
    
    # Schedule intent registration as background task during startup
    if (hasattr(app, '_robutler_agents_with_intents') and app._robutler_agents_with_intents) or \
       (hasattr(app, 'agent_intents') and app.agent_intents):
        asyncio.create_task(register_intents_when_ready())
    
    # Server is now running
    yield
    
    # Shutdown phase
    _server_ready = False


async def robutler_extract_context(request: Request, context: ServerContext) -> None:
    """
    Built-in callback to extract user_id and url from request context.
    
    This callback extracts:
    - user_id: From the authenticated user's information via API
    - url: Constructed from BASE_URL environment variable and request path
    
    Args:
        request: FastAPI Request object
        context: ServerContext object for storing custom data
    """
    # Extract user_id if we have API access
    try:
        if settings.api_key:
            from robutler.api.client import RobutlerApi
            async with RobutlerApi() as api:
                user_info = await api.get_user_info()
                user_id = user_info.get('id')
                if user_id:
                    context.set_custom_data('user_id', user_id)
    except Exception as e:
        # Log but don't fail the request
        print(f"Warning: Could not extract user_id: {e}")
    
    # Extract and construct URL from BASE_URL and request path
    try:
        base_url = os.getenv("BASE_URL")
        if base_url:
            # Remove trailing slash from base_url if present
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            
            # Extract agent name from path (e.g., "/agents/assistant/chat/completions" -> "assistant")
            path_parts = request.url.path.strip('/').split('/')
            if len(path_parts) >= 2:
                # For paths like "/agents/assistant/chat/completions" or "/assistant/chat/completions"
                agent_name = path_parts[-2] if path_parts[-1] in ['chat', 'completions'] else path_parts[-1]
                if path_parts[-1] == 'completions' and len(path_parts) >= 3:
                    agent_name = path_parts[-3]
                
                # Construct the agent URL
                agent_url = f"{base_url}/{agent_name}"
                context.set_custom_data('agent_url', agent_url)
    except Exception as e:
        # Log but don't fail the request
        print(f"Warning: Could not extract agent URL: {e}")


class RobutlerServer(FastAPI):
    """
    FastAPI-based server framework with credit tracking and OpenAI-compatible endpoints
    """
    
    def __init__(self, agents: Optional[List] = None, min_balance: int = 0, *args, **kwargs):
        # Set lifespan if not already provided
        if 'lifespan' not in kwargs:
            kwargs['lifespan'] = lifespan
        super().__init__(*args, **kwargs)
        self.agent_handlers: Dict[str, Callable] = {}
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.min_balance = min_balance
        
        # API client and user info for payment token functionality
        self.api_client: Optional[RobutlerApi] = None
        self.user_info: Optional[User] = None
        
        # Callback storage - robutler_before is automatically registered first
        self.before_request_callbacks: List[Callable] = [robutler_before, robutler_extract_context]
        self.after_request_callbacks: List[Callable] = []
        self.finalize_request_callbacks: List[Callable] = []
        
        # Add payment token callbacks
        self.before_request_callbacks.append(self._check_payment_token)
        self.finalize_request_callbacks.append(self._charge_payment_token)
        
        # Store reference to self for middleware
        server_self = self
        
        def _is_callback_endpoint(path: str) -> bool:
            """Check if the path is an agent endpoint that should trigger callbacks"""
            # Check for auto-created agent endpoints (from agents parameter)
            if agents:
                for agent in agents:
                    agent_name = agent.name
                    # Check both with and without root_path prefix
                    if (path == f"/{agent_name}/chat/completions" or 
                        path == f"/{agent_name}" or
                        path.endswith(f"/{agent_name}/chat/completions") or
                        path.endswith(f"/{agent_name}")):
                        return True
            
            # Check if it's an agent endpoint by looking at registered routes
            for route in server_self.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    # Check if this is a POST route (agent endpoints)
                    if 'POST' in route.methods:
                        # Extract the route pattern and check if it matches
                        route_pattern = route.path
                        # Simple pattern matching - convert FastAPI path params to match
                        if '{' in route_pattern and '}' in route_pattern:
                            # Convert {param} to a regex-like pattern for basic matching
                            import re
                            pattern = re.sub(r'\{[^}]+\}', r'[^/]+', route_pattern)
                            if re.match(f"^{pattern}$", path):
                                return True
                        elif route_pattern == path:
                            return True
            
            return False
        
        # Auto-create endpoints for passed agents
        if agents:
            self._create_agent_endpoints(agents)
            # Store agents with intents for startup registration
            self._robutler_agents_with_intents = [agent for agent in agents if hasattr(agent, 'intents') and agent.intents]
        
        # Add standard health check endpoint
        @self.get("/health")
        async def health_check():
            """Standard health check endpoint."""
            return {"status": "healthy", "ready": _server_ready}
        
        @self.get("/ready")
        async def readiness_check():
            """Standard readiness check endpoint."""
            if _server_ready:
                return {"status": "ready"}
            else:
                raise HTTPException(status_code=503, detail="Server not ready")
        
        # Add agent health endpoints for Intent Router validation
        if agents:
            for agent in agents:
                def create_agent_health_endpoint(agent_name: str):
                    @self.get(f"/{agent_name}/health")
                    async def agent_health_check():
                        """Agent health check endpoint that doesn't require payment."""
                        return {"status": "healthy", "agent": agent_name, "ready": True}
                
                create_agent_health_endpoint(agent.name)
        
        # Add middleware to ensure context for agent requests and handle callbacks
        @self.middleware("http")
        async def ensure_context_middleware(request: Request, call_next):
            """Ensure server context exists for agent requests and handle callbacks"""
            # Check if this is an agent endpoint that should trigger callbacks
            if _is_callback_endpoint(request.url.path):
                context = get_server_context()
                context_created = False
                token = None
                
                if not context:
                    # Create a temporary context for this request
                    call_id = str(uuid.uuid4())
                    context = ServerContext(call_id, "middleware")
                    token = _current_server_context.set(context)
                    context_created = True
                
                try:
                    # Store request in context for finalize callbacks
                    context.set_custom_data('_current_request', request)
                    
                    # Call before_request callbacks
                    for callback in server_self.before_request_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(request, context)
                            else:
                                callback(request, context)
                        except HTTPException as http_exc:
                            # For payment-related errors, log and return proper HTTP response
                            if http_exc.status_code == 402:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.info(f"💳 Payment required for {request.url.path}: {http_exc.detail}")
                                # Return proper 402 response instead of re-raising
                                from fastapi.responses import JSONResponse
                                return JSONResponse(
                                    status_code=402,
                                    content={"detail": http_exc.detail}
                                )
                            # For other HTTP exceptions, re-raise
                            raise
                        except Exception as e:
                            # Log other callback errors but don't fail the request
                            print(f"Before request callback error: {e}")
                    
                    # Process the request
                    response = await call_next(request)
                    
                    # Call after_request callbacks - they can modify the response
                    for callback in server_self.after_request_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                result = await callback(request, response, context)
                            else:
                                result = callback(request, response, context)
                            
                            # If callback returns a response, use it instead
                            if result is not None:
                                response = result
                        except HTTPException:
                            # Re-raise HTTPExceptions (though less common in after_request)
                            raise
                        except Exception as e:
                            # Log other callback errors but don't fail the request
                            print(f"After request callback error: {e}")
                    
                    # Skip AgentStreamingResponseWrapper as it handles finalize callbacks itself
                    is_agent_streaming = context.get_custom_data('_is_agent_streaming_response', False)
                    
                    if isinstance(response, AgentStreamingResponseWrapper) or is_agent_streaming:
                        # AgentStreamingResponseWrapper will call finalize callbacks after streaming
                        pass
                    elif not isinstance(response, StreamingResponse):
                    # For non-streaming responses, call finalize callbacks immediately
                        await server_self._call_finalize_callbacks(request, response, context)
                    
                    return response
                finally:
                    if context_created and token:
                        _current_server_context.reset(token)
            
            # For other requests, proceed normally without callbacks
            return await call_next(request)
        
    async def _register_agent_intents(self, agents: List) -> None:
        """Register intents for RobutlerAgent instances."""
        try:
            # Get context to extract user_id and url
            context = get_server_context()
            
            if not context:
                print("⚠️  No server context available for agent intent registration")
                return
            
            user_id = context.get_custom_data('user_id')
            
            if not user_id:
                print("⚠️  No user_id available in context for agent intent registration")
                return
            
            # Debug output
            print(f"🔍 Debug: Starting intent registration with user_id: {user_id}")
            base_url = os.getenv("BASE_URL")
            api_key = os.getenv("ROBUTLER_API_KEY") or settings.api_key
            print(f"🔍 Debug: BASE_URL: {base_url}, API_KEY present: {bool(api_key)}")
            
            from robutler.api.client import RobutlerApi
            async with RobutlerApi() as api:
                for agent in agents:
                    if hasattr(agent, 'intents') and agent.intents:
                        # Construct agent URL from BASE_URL and agent name
                        base_url = os.getenv("BASE_URL")
                        if not base_url:
                            print(f"⚠️  BASE_URL not set, skipping intent registration for agent '{agent.name}'")
                            continue
                        
                        if base_url.endswith("/"):
                            base_url = base_url[:-1]
                        
                        # Include root_path if set
                        root_path = getattr(self, 'root_path', '') or ''
                        if root_path and not root_path.startswith('/'):
                            root_path = f'/{root_path}'
                        
                        # Use health endpoint for Intent Router validation, but main endpoint for registration
                        agent_url = f"{base_url}{root_path}/{agent.name}"
                        
                        # Check URL length constraint (maxLength: 100)
                        if len(agent_url) > 100:
                            print(f"⚠️  Agent URL too long ({len(agent_url)} chars): {agent_url}")
                            continue
                        
                        for intent in agent.intents:
                            try:
                                print(f"🔍 Attempting to register intent: '{intent}' for agent: '{agent.name}'")
                                print(f"🔍 API call parameters:")
                                print(f"   - intent: '{intent}' (len: {len(intent)})")
                                print(f"   - agent_id: '{agent.name}' (len: {len(agent.name)})")
                                print(f"   - agent_description: '{agent.instructions[:50]}...' (len: {len(agent.instructions)})")
                                print(f"   - user_id: '{user_id}' (len: {len(user_id)})")
                                print(f"   - url: '{agent_url}' (len: {len(agent_url)})")
                                
                                # Add retry logic for intent registration
                                max_retries = 3
                                for retry_attempt in range(max_retries):
                                    try:
                                        result = await api.create_intent(
                                            intent=intent,
                                            agent_id=agent.name,
                                            agent_description=agent.instructions,
                                            user_id=user_id,
                                            url=agent_url
                                        )
                                        print(f"✅ Registered intent '{intent}' for agent '{agent.name}'")
                                        break  # Success, exit retry loop
                                    except Exception as retry_error:
                                        if retry_attempt < max_retries - 1:
                                            wait_time = 2 ** retry_attempt
                                            print(f"⚠️ Intent registration attempt {retry_attempt + 1} failed, retrying in {wait_time}s...")
                                            await asyncio.sleep(wait_time)
                                        else:
                                            raise retry_error  # Re-raise on final attempt
                            except Exception as e:
                                import traceback
                                error_details = f"Error: {str(e)}, Type: {type(e).__name__}"
                                if hasattr(e, 'status_code'):
                                    error_details += f", Status: {e.status_code}"
                                if hasattr(e, 'message'):
                                    error_details += f", Message: {e.message}"
                                print(f"❌ Failed to register intent '{intent}' for agent '{agent.name}': {error_details}")
                                print(f"   Traceback: {traceback.format_exc()}")
                                print(f"   Debug - user_id: {user_id}, agent_url: {agent_url}")
        except Exception as e:
            print(f"❌ Failed to initialize Robutler API client for intent registration: {str(e)}")
    
    async def register_decorator_intents(self) -> None:
        """Register intents for agents created via the @agent decorator."""
        if not hasattr(self, 'agent_intents') or not self.agent_intents:
            return
        
        try:
            # Get context to extract user_id and url
            context = get_server_context()
            
            if not context:
                print("⚠️  No server context available for decorator intent registration")
                return
            
            user_id = context.get_custom_data('user_id')
            
            if not user_id:
                print("⚠️  No user_id available in context for decorator intent registration")
                return
            
            from robutler.api.client import RobutlerApi
            async with RobutlerApi() as api:
                for agent_name, intents in self.agent_intents.items():
                    # Construct agent URL from BASE_URL and agent name
                    base_url = os.getenv("BASE_URL")
                    if not base_url:
                        print(f"⚠️  BASE_URL not set, skipping intent registration for agent '{agent_name}'")
                        continue
                    
                    if base_url.endswith("/"):
                        base_url = base_url[:-1]
                    
                    # Include root_path if set
                    root_path = getattr(self, 'root_path', '') or ''
                    if root_path and not root_path.startswith('/'):
                        root_path = f'/{root_path}'
                    
                    agent_url = f"{base_url}{root_path}/{agent_name}"
                    
                    for intent in intents:
                        try:
                            result = await api.create_intent(
                                intent=intent,
                                agent_id=agent_name,
                                agent_description=f"Agent {agent_name}",
                                user_id=user_id,
                                url=agent_url
                            )
                            print(f"✅ Registered intent '{intent}' for agent '{agent_name}'")
                        except Exception as e:
                            print(f"❌ Failed to register intent '{intent}' for agent '{agent_name}': {str(e)}")
        except Exception as e:
            print(f"❌ Failed to initialize Robutler API client for decorator intent registration: {str(e)}")
    
    def _create_agent_endpoints(self, agents: List) -> None:
        """
        Automatically create endpoints for RobutlerAgent instances.
        
        For each agent, creates endpoints at:
        - /{agent.name}/chat/completions (POST) - OpenAI-compatible chat completions
        - /{agent.name} (GET) - Agent info
        """
        for agent in agents:
            agent_name = agent.name
            base_path = f"/{agent_name}"
            
            # Create chat completions endpoint
            def create_chat_completions_handler(robutler_agent):
                async def chat_completions_handler(request: ChatCompletionRequest):
                    result = await robutler_agent.run(
                        messages=request.messages,
                        stream=getattr(request, 'stream', False)
                    )
                    
                    # If it's a streaming response, wrap it to call finalize callbacks
                    if isinstance(result, StreamingResponse):
                        wrapper = AgentStreamingResponseWrapper(
                            result, 
                                server=self,
                            request=request,
                            agent=robutler_agent
                        )
                        
                        # Store in context that this is an AgentStreamingResponseWrapper
                        # so middleware can detect it even if Starlette wraps it
                        context = get_server_context()
                        if context:
                            context.set_custom_data('_is_agent_streaming_response', True)
                        
                        return wrapper
                    
                    # For non-streaming responses, convert string to OpenAI format
                    if isinstance(result, str):
                        call_id = str(uuid.uuid4())
                        
                        # Calculate tokens for usage info
                        input_tokens = self._estimate_tokens(self._messages_to_text(request.messages))
                        output_tokens = self._estimate_tokens(result)
                        total_tokens = input_tokens + output_tokens
                        
                        # Create OpenAI-compatible response
                        return ChatCompletionResponse(
                            id=f"chatcmpl-{call_id}",
                            created=int(datetime.utcnow().timestamp()),
                            model=request.model,
                            choices=[
                                ChatCompletionChoice(
                                    index=0,
                                    message=ChatMessage(role="assistant", content=result),
                                    finish_reason="stop"
                                )
                            ],
                            usage=Usage(
                                prompt_tokens=input_tokens,
                                completion_tokens=output_tokens,
                                total_tokens=total_tokens
                            )
                        )
                    
                    return result
                return chat_completions_handler
            
            # Create agent info endpoint
            def create_info_handler(robutler_agent):
                async def info_handler():
                    return {
                        "name": robutler_agent.name,
                        "instructions": robutler_agent.instructions,
                        "model": robutler_agent.model,
                        "credits_per_token": robutler_agent.credits_per_token,
                        "tools": len(robutler_agent.tools),
                        "endpoints": {
                            "chat_completions": f"{base_path}/chat/completions",
                            "info": base_path
                        }
                    }
                return info_handler
            
            # Register the endpoints
            chat_handler = create_chat_completions_handler(agent)
            info_handler = create_info_handler(agent)
            
            self.post(f"{base_path}/chat/completions")(chat_handler)
            self.get(base_path)(info_handler)
        

    
    def agent(self, path: str, intents: Optional[List[str]] = None):
        """
        Decorator to create multiple agent endpoints
        
        Creates 4 endpoints for each agent:
        - {path} POST: Agent control endpoint (for future use)
        - {path} GET: Agent info endpoint (returns pricing and metadata)
        - {path}/chat/completions POST: OpenAI-compatible chat completions
        - {path}/chat/completions GET: Chat completions pricing info
        
        Args:
            path: The base endpoint path (e.g., "/agents/{agent_name}")
            intents: Optional list of intents to register for this agent
        
        Note: Use @pricing decorator to define agent pricing
        """
        def decorator(func: Callable) -> Callable:
            # Store as agent handler (pricing should be defined via @pricing decorator)
            self.agent_handlers[func.__name__] = func
            
            # Store intents for this agent if provided
            if intents:
                if not hasattr(self, 'agent_intents'):
                    self.agent_intents = {}
                self.agent_intents[func.__name__] = intents
            
            # Create a wrapper to handle the OpenAI chat completions logic
            async def chat_completions_handler(request: ChatCompletionRequest, *args, **kwargs):
                # Check if context already exists from middleware
                context = get_server_context()
                call_id = str(uuid.uuid4())  # Always generate a call_id for this request
                if not context:
                    # Create server context only if middleware didn't create one
                    context = ServerContext(call_id, func.__name__)
                    token = _current_server_context.set(context)
                else:
                    # Update the server name to the actual agent function name
                    context.server_name = func.__name__
                    token = None
                
                try:
                    # Call the decorated function with all parameters
                    # Check if function expects request parameter
                    sig = inspect.signature(func)
                    has_request_param = any(param.name == 'request' for param in sig.parameters.values())
                    
                    if has_request_param:
                        # Function expects request parameter, pass it as first argument
                        if asyncio.iscoroutinefunction(func):
                            result = await func(request, *args, **kwargs)
                        else:
                            result = func(request, *args, **kwargs)
                    else:
                        # Function doesn't expect request parameter, call normally
                        if asyncio.iscoroutinefunction(func):
                            result = await func(*args, **kwargs)
                        else:
                            result = func(*args, **kwargs)
                    
                    # Check if the function returned a StreamingResponse directly
                    if isinstance(result, StreamingResponse):
                        # For custom StreamingResponse, we need to wrap it to track credits
                        original_body_iterator = result.body_iterator
                        
                        async def wrapped_iterator():
                            content_parts = []
                            async for chunk in original_body_iterator:
                                content_parts.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
                                yield chunk
                            
                            # After streaming completes, calculate tokens and credits
                            full_content = ''.join(content_parts)
                            num_tokens = self._estimate_tokens(full_content)
                            
                            # Note: Usage tracking is now handled by the standalone @pricing decorator
                        
                        result.body_iterator = wrapped_iterator()
                        return result
                    
                    # Handle different return types
                    # Note: OpenAI Agents SDK returns StreamingResponse directly from agent functions
                    elif hasattr(result, 'stream_generator'):
                        # Handle StreamingAgentResponse - real-time streaming from agent
                        if request.stream:
                            async def streaming_wrapper():
                                async for chunk in self._stream_agent_response(result.stream_generator, request.model, call_id):
                                    yield chunk
                                # Usage is now tracked through context in the agent, no need to track here
                            
                            return StreamingResponse(
                                streaming_wrapper(),
                                media_type="text/event-stream",
                                headers={
                                    "Cache-Control": "no-cache",
                                    "Connection": "keep-alive",
                                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                                }
                            )
                        else:
                            # Collect streaming content for non-streaming response
                            content = await result.collect_content()
                            
                            # Estimate tokens for the response (usage already tracked through context)
                            num_tokens = self._estimate_tokens(content)
                            
                            # Create OpenAI-compatible response
                            response = ChatCompletionResponse(
                                id=f"chatcmpl-{call_id}",
                                created=int(datetime.utcnow().timestamp()),
                                model=request.model,
                                choices=[
                                    ChatCompletionChoice(
                                        index=0,
                                        message=ChatMessage(role="assistant", content=content),
                                        finish_reason="stop"
                                    )
                                ],
                                usage=Usage(
                                    prompt_tokens=self._estimate_tokens(self._messages_to_text(request.messages)),
                                    completion_tokens=num_tokens,
                                    total_tokens=self._estimate_tokens(self._messages_to_text(request.messages)) + num_tokens
                                )
                            )
                            return response
                    elif isinstance(result, ReportUsage):
                        response_content = result.content
                        num_tokens = result.tokens
                    else:
                        response_content = result
                        num_tokens = self._estimate_tokens(str(response_content))
                    
                    # Note: Usage tracking is now handled by the standalone @pricing decorator
                    
                    # Handle streaming vs non-streaming for non-StreamingAgentResponse
                    if request.stream and not hasattr(result, 'stream_generator'):
                        # For streaming, we'll calculate credits after streaming completes
                        async def streaming_wrapper():
                            async for chunk in self._stream_response(response_content, request.model, call_id):
                                yield chunk
                        
                        return StreamingResponse(
                            streaming_wrapper(),
                            media_type="text/event-stream"
                        )
                    elif not hasattr(result, 'stream_generator'):
                        # Create OpenAI-compatible response
                        response = ChatCompletionResponse(
                            id=f"chatcmpl-{call_id}",
                            created=int(datetime.utcnow().timestamp()),
                            model=request.model,
                            choices=[
                                ChatCompletionChoice(
                                    index=0,
                                    message=ChatMessage(role="assistant", content=response_content),
                                    finish_reason="stop"
                                )
                            ],
                            usage=Usage(
                                prompt_tokens=self._estimate_tokens(self._messages_to_text(request.messages)),
                                completion_tokens=num_tokens,
                                total_tokens=self._estimate_tokens(self._messages_to_text(request.messages)) + num_tokens
                            )
                        )
                        return response
                        
                finally:
                    # Clear the context only if we created one
                    if token:
                        _current_server_context.reset(token)
            
            # Create agent control handler (for future use)
            async def agent_control_handler(*args, **kwargs):
                return {
                    "message": "Agent control endpoint - not yet implemented",
                    "agent": func.__name__,
                    "available_endpoints": [
                        f"{path} GET - Agent info",
                        f"{path} POST - Agent control (not implemented)",
                        f"{path}/chat/completions POST - OpenAI chat completions",
                        f"{path}/chat/completions GET - Chat completions pricing"
                    ]
                }
            
            # Create agent info handler
            async def agent_info_handler(*args, **kwargs):
                agent_info = {
                    "agent": func.__name__,
                    "description": func.__doc__ or "AI Agent",
                    "endpoints": {
                        "control": f"{path}",
                        "info": f"{path}",
                        "chat_completions": f"{path}/chat/completions"
                    },
                    "note": "Pricing information is handled by the standalone @pricing decorator"
                        }
                
                return agent_info
            
            # Create chat completions pricing handler
            async def chat_completions_pricing_handler(*args, **kwargs):
                return {
                    "endpoint": f"{path}/chat/completions",
                    "agent": func.__name__,
                    "openai_compatible": True,
                    "supports_streaming": True,
                    "note": "Pricing information is handled by the standalone @pricing decorator"
                }
            
            # Copy the original function's signature to the handlers
            sig = inspect.signature(func)
            
            # For chat completions POST handler, check if request parameter already exists
            existing_params = list(sig.parameters.values())
            has_request_param = any(param.name == 'request' for param in existing_params)
            
            if has_request_param:
                # Function already has request parameter, but we need to ensure it's properly annotated
                # Replace the request parameter with the correct annotation for FastAPI
                new_params = []
                for param in existing_params:
                    if param.name == 'request':
                        # Replace with properly annotated request parameter
                        new_param = inspect.Parameter(
                            "request", 
                            inspect.Parameter.POSITIONAL_OR_KEYWORD, 
                            annotation=ChatCompletionRequest
                        )
                        new_params.append(new_param)
                    else:
                        new_params.append(param)
                chat_completions_handler.__signature__ = inspect.Signature(new_params)
            else:
                # Prepend the request parameter
                post_params = [inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=ChatCompletionRequest)]
                post_params.extend(existing_params)
                chat_completions_handler.__signature__ = inspect.Signature(post_params)
            
            # For other handlers, use the original signature (without request)
            if has_request_param:
                # Remove request parameter for other handlers
                get_params = [param for param in existing_params if param.name != 'request']
                signature_without_request = inspect.Signature(get_params)
                agent_control_handler.__signature__ = signature_without_request
                agent_info_handler.__signature__ = signature_without_request
                chat_completions_pricing_handler.__signature__ = signature_without_request
            else:
                agent_control_handler.__signature__ = sig
                agent_info_handler.__signature__ = sig
                chat_completions_pricing_handler.__signature__ = sig
            
            # Register the 4 endpoints
            # 1. Base path POST - Agent control (for future use)
            self.post(path)(agent_control_handler)
            
            # 2. Base path GET - Agent info
            self.get(path)(agent_info_handler)
            
            # 3. Chat completions POST - OpenAI-compatible endpoint
            self.post(f"{path}/chat/completions")(chat_completions_handler)
            
            # 4. Chat completions GET - Pricing info
            self.get(f"{path}/chat/completions")(chat_completions_pricing_handler)
            
            return func
        return decorator
    
    def before_request(self, func: Callable) -> Callable:
        """
        Decorator to register a callback that runs before agent endpoint requests
        
        Note: Callbacks only trigger for agent endpoints (decorated with @app.agent), 
        not for regular FastAPI routes.
        
        The callback function should accept (request, context) parameters:
        - request: FastAPI Request object
        - context: ServerContext object for storing custom data
        
        Example:
            @app.before_request
            def authorize_request(request, context):
                # Check authorization
                auth_header = request.headers.get('authorization')
                if not auth_header:
                    raise HTTPException(401, "Unauthorized")
                context.set_custom_data('user_id', extract_user_id(auth_header))
        """
        self.before_request_callbacks.append(func)
        return func
    
    def after_request(self, func: Callable) -> Callable:
        """
        Decorator to register a callback that runs after each request
        
        The callback function should accept (request, response, context) parameters:
        - request: FastAPI Request object
        - response: FastAPI Response object
        - context: ServerContext object with custom data and usage info
        
        The callback can optionally return a modified response to replace the original.
        
        Examples:
            @app.after_request
            def log_usage(request, response, context):
                user_id = context.get_custom_data('user_id')
                usage = context.get_usage()
                log_to_database(user_id, usage['total_credits'], usage['total_tokens'])
            
            @app.after_request
            def add_custom_header(request, response, context):
                response.headers["X-User-Credits"] = str(context.get_custom_data('remaining_credits', 0))
                return response  # Return modified response
        """
        self.after_request_callbacks.append(func)
        return func
    
    def finalize_request(self, func: Callable) -> Callable:
        """
        Decorator to register a callback that runs after the request is completely finished
        
        This callback runs after streaming is complete (for streaming responses) or after
        the response has been sent (for non-streaming responses). It's ideal for cleanup,
        final logging, analytics, or business logic that needs to run after everything is done.
        
        The callback function should accept (request, response, context) parameters:
        - request: FastAPI Request object
        - response: FastAPI Response object (may be None for streaming responses)
        - context: ServerContext object with complete usage info and custom data
        
        Note: Unlike after_request, finalize_request callbacks cannot modify the response
        since it has already been sent to the client.
        
        Examples:
            @app.finalize_request
            def log_final_usage(request, response, context):
                user_id = context.get_custom_data('user_id')
                usage = context.get_usage()
                # Log to analytics system after everything is complete
                analytics.log_request_complete(user_id, usage['total_credits'], usage['total_tokens'])
            
            @app.finalize_request
            async def cleanup_resources(request, response, context):
                # Clean up any resources or connections
                await cleanup_user_session(context.get_custom_data('session_id'))
        """
        self.finalize_request_callbacks.append(func)
        return func
    
    async def _call_finalize_callbacks(self, request: Request, response: Optional[Response], context: ServerContext):
        """Call all finalize_request callbacks"""
        for callback in self.finalize_request_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(request, response, context)
                else:
                    callback(request, response, context)
            except Exception as e:
                # Log callback errors but don't fail the request (it's already complete)
                print(f"Finalize request callback error: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using tiktoken or fallback to word-based estimation"""
        try:
            tokens = len(self.encoding.encode(text))
            return max(1, tokens)  # Always return at least 1
        except:
            # Fallback: 1 token ~= 3/4 words
            words = text.split()
            return max(1, int(len(words) * 4 / 3))
    
    def _messages_to_text(self, messages: List[ChatMessage]) -> str:
        """Convert messages to text for token counting"""
        return " ".join([f"{msg.role}: {msg.content}" for msg in messages])
    
    async def _stream_response(self, content: str, model: str, call_id: str):
        """Generate streaming response in OpenAI format"""
        # Initial response
        yield f"data: {json.dumps({'id': f'chatcmpl-{call_id}', 'object': 'chat.completion.chunk', 'created': int(datetime.utcnow().timestamp()), 'model': model, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
        
        # Stream content in chunks
        chunk_size = 20  # characters per chunk
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield f"data: {json.dumps({'id': f'chatcmpl-{call_id}', 'object': 'chat.completion.chunk', 'created': int(datetime.utcnow().timestamp()), 'model': model, 'choices': [{'index': 0, 'delta': {'content': chunk}, 'finish_reason': None}]})}\n\n"
            await asyncio.sleep(0.01)  # Small delay for streaming effect
        
        # Final response
        yield f"data: {json.dumps({'id': f'chatcmpl-{call_id}', 'object': 'chat.completion.chunk', 'created': int(datetime.utcnow().timestamp()), 'model': model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        yield "data: [DONE]\n\n"
    
    async def _stream_agent_response(self, stream_generator, model: str, call_id: str):
        """Generate real-time streaming response from agent in OpenAI format"""
        import json
        from datetime import datetime
        
        created = int(datetime.utcnow().timestamp())
        
        # Initial chunk with role
        initial_chunk = {
            "id": f"chatcmpl-{call_id}",
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant"},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        # Stream content chunks from agent in real-time
        try:
            async for text_chunk in stream_generator:
                if text_chunk:  # Only send non-empty chunks
                    content_chunk = {
                        "id": f"chatcmpl-{call_id}",
                        "object": "chat.completion.chunk", 
                        "created": created,
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": text_chunk},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(content_chunk)}\n\n"
        except Exception as e:
            # Send error as content
            error_chunk = {
                "id": f"chatcmpl-{call_id}",
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"Error: {str(e)}"},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # Final chunk with finish_reason
        final_chunk = {
            "id": f"chatcmpl-{call_id}",
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        
        # End of stream marker
        yield "data: [DONE]\n\n"

    async def _ensure_api_client(self):
        """
        Ensure the API client is initialized (lazy initialization).
        """
        if self.api_client is None:
            try:
                from robutler.api import initialize_api
                self.api_client = await initialize_api()
                self.user_info = await self.api_client.get_user_info()
                print(f"✅ API client initialized for user: {self.user_info.get('name', 'Unknown')}")
            except Exception as e:
                print(f"⚠️ Failed to initialize API client: {e}")
                self.api_client = False  # Mark as failed to avoid retrying
                self.user_info = None
    
    async def _check_payment_token(self, request: Request, context: ServerContext):
        """
        Before request callback to check payment token balance.
        
        Checks for 'X-Payment-Token' header and validates the token has sufficient balance.
        Only applies to non-GET requests since GET requests are informational.
        """
        # Skip payment validation for GET requests (info endpoints, health checks, etc.)
        if request.method == "GET":
            return
        
        # Ensure API client is initialized
        await self._ensure_api_client()
        
        if not self.api_client or self.api_client is False:
            # If no API client or failed to initialize, skip payment token checking
            return
        
        # Check for payment token in headers
        payment_token = request.headers.get('x-payment-token') or request.headers.get('X-Payment-Token')
        
        if not payment_token:
            # No payment token provided - inform about minimum balance requirement
            raise HTTPException(
                status_code=402,
                detail=f"Payment token required. Minimum balance: {self.min_balance} credits. Include X-Payment-Token header."
            )
        
        try:
            # Validate the payment token
            token_info = await self.api_client.validate_payment_token(payment_token)
            
            if not token_info.get('valid', False):
                raise HTTPException(
                    status_code=402, 
                    detail="Invalid payment token"
                )
            
            # Check available balance
            token_data = token_info.get('token', {})
            available_amount = token_data.get('availableAmount', 0)
            
            if available_amount < self.min_balance:
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient token balance. Available: {available_amount}, Required: {self.min_balance}"
                )
            
            # Store token info in context for charging later
            context.set_custom_data('payment_token', payment_token)
            context.set_custom_data('token_info', token_data)
            context.set_custom_data('available_balance', available_amount)
            
        except RobutlerApiError as e:
            raise HTTPException(
                status_code=402,
                detail=f"Payment token validation failed: {e.message}"
            )
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Payment token check failed: {str(e)}"
            )
    
    async def _charge_payment_token(self, request: Request, response: Optional[Response], context: ServerContext):
        """
        Finalize request callback to charge the payment token for credits used.
        """
        if not self.api_client or self.api_client is False:
            return
        
        payment_token = context.get_custom_data('payment_token')
        if not payment_token:
            # No payment token to charge
            return
        
        # Get total credits used
        usage = context.get_usage()
        total_credits = usage['total_credits']
        
        if total_credits <= 0:
            # No credits to charge
            return
        
        try:
            # Redeem credits from the payment token
            result = await self.api_client.redeem_payment_token(
                token=payment_token,
                amount=total_credits
            )
            
            if result.get('success', False):
                print(f"💳 Charged {total_credits} credits from payment token")
                context.set_custom_data('payment_charged', total_credits)
            else:
                print(f"⚠️ Failed to charge payment token: {result.get('message', 'Unknown error')}")
                
        except RobutlerApiError as e:
            print(f"⚠️ Payment token charge failed: {e.message}")
        except Exception as e:
            print(f"⚠️ Payment token charge error: {str(e)}")



# Custom streaming response that tracks usage after completion
class UsageTrackingStreamingResponse(StreamingResponse):
    def __init__(self, content, server, func_name, pricing, context, request=None, **kwargs):
        self.server = server
        self.func_name = func_name
        self.pricing = pricing
        self.context = context
        self.request = request
        self.original_content = content
        super().__init__(self._wrap_content(), **kwargs)
    
    async def _wrap_content(self):
        content_parts = []
        
        # Stream content and collect for usage tracking
        async for chunk in self.original_content:
            # Extract content from SSE chunks for token counting
            if isinstance(chunk, (str, bytes)):
                chunk_str = chunk.decode() if isinstance(chunk, bytes) else chunk
                if chunk_str.startswith('data: ') and not chunk_str.startswith('data: [DONE]'):
                    try:
                        # Parse JSON and extract delta content
                        import json
                        json_str = chunk_str[6:].strip()  # Remove 'data: ' prefix
                        if json_str:
                            data = json.loads(json_str)
                            choices = data.get('choices', [])
                            if choices and 'delta' in choices[0]:
                                delta_content = choices[0]['delta'].get('content', '')
                                if delta_content:
                                    content_parts.append(delta_content)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass  # Skip malformed chunks
            
            yield chunk
        
        # Track usage AFTER streaming completes
        if self.pricing and self.pricing.credits_per_token and content_parts:
            full_content = ''.join(content_parts)
            tokens = self.server._estimate_tokens(full_content)
            credits = tokens * self.pricing.credits_per_token
            
            if self.context:
                source_type = "server" if self.func_name in self.server.agent_handlers else "tool"
                self.context.track_usage(self.func_name, credits, tokens, source_type)
                print(f"🔄 Streaming completed: {tokens} tokens, {credits} credits")
        
        # Call finalize callbacks after streaming is complete
        if self.context:
            # Try to get request from context if not provided directly
            request = self.request or self.context.get_custom_data('_current_request')
            if request:
                await self.server._call_finalize_callbacks(request, None, self.context) 


class AgentStreamingResponseWrapper(StreamingResponse):
    """Wrapper for agent streaming responses to call finalize callbacks after completion"""
    
    def __init__(self, original_response: StreamingResponse, server, request, agent=None, **kwargs):
        self.original_response = original_response
        self.server = server
        self.request = request
        self.agent = agent
        
        # Copy properties from original response and wrap the content
        super().__init__(
            self._wrap_content(),
            status_code=original_response.status_code,
            headers=original_response.headers,
            media_type=original_response.media_type,
            background=original_response.background
        )
    
    async def _wrap_content(self):
        """Wrap the original content and call finalize callbacks after completion"""
        # Get the original content generator
        original_content = self.original_response.body_iterator
        
        # Collect content for usage tracking
        content_parts = []
        
        # Stream all content from the original response
        async for chunk in original_content:
            # Extract content from SSE chunks for token counting
            if isinstance(chunk, (str, bytes)):
                chunk_str = chunk.decode() if isinstance(chunk, bytes) else chunk
                if chunk_str.startswith('data: ') and not chunk_str.startswith('data: [DONE]'):
                    try:
                        # Parse JSON and extract delta content
                        import json
                        json_str = chunk_str[6:].strip()  # Remove 'data: ' prefix
                        if json_str:
                            data = json.loads(json_str)
                            choices = data.get('choices', [])
                            if choices and 'delta' in choices[0]:
                                delta_content = choices[0]['delta'].get('content', '')
                                if delta_content:
                                    content_parts.append(delta_content)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass  # Skip malformed chunks
            
            yield chunk
        
        # Track usage after streaming completes
        context = get_server_context()
        if context and content_parts:
            # Extract agent name from request path
            actual_request = context.get_custom_data('_current_request')
            if actual_request:
                path = actual_request.url.path
                # Extract agent name from path like "/agents/writer/chat/completions"
                path_parts = path.strip('/').split('/')
                if len(path_parts) >= 2:
                    agent_name = path_parts[-2] if path_parts[-1] == 'chat' else path_parts[-1]
                    
                    # Find the agent to get credits_per_token
                    # We need to get this from the request somehow
                    # For now, let's extract it from the original request data
                    request_data = getattr(self.request, '__dict__', {})
                    messages = getattr(self.request, 'messages', [])
                    
                    if messages:
                        # Calculate tokens
                        full_content = ''.join(content_parts)
                        input_text = " ".join([f"{msg.role}: {msg.content}" for msg in messages])
                        input_tokens = self.server._estimate_tokens(input_text)
                        output_tokens = self.server._estimate_tokens(full_content)
                        total_tokens = input_tokens + output_tokens
                        
                        # Get credits per token from agent
                        credits_per_token = self.agent.credits_per_token if self.agent else 6
                        credits = total_tokens * credits_per_token
                        
                        context.track_usage(agent_name, credits, total_tokens, "llm usage")
        
        # After streaming completes, call finalize callbacks
        if context and self.server:
            # Get the actual FastAPI request from context
            actual_request = context.get_custom_data('_current_request')
            if actual_request:
                await self.server._call_finalize_callbacks(actual_request, None, context) 