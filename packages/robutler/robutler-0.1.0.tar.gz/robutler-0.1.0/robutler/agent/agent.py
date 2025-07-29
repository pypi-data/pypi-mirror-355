"""
RobutlerAgent - Main agent class for OpenAI Agents SDK integration

This module contains the core RobutlerAgent class that wraps the OpenAI Agent
with RobutlerServer integration, usage tracking, and streaming support.

Example Usage:
    ```python
    from robutler.agent import RobutlerAgent
    from robutler.server import RobutlerServer
    
    # Create an agent
    agent = RobutlerAgent(
        name="CodeHelper",
        instructions="You are a helpful coding assistant",
        credits_per_token=5,
        model="gpt-4o-mini",
        intents=["help with coding", "debug programming issues"]
    )
    
    # Use with server (auto-creates endpoints)
    app = RobutlerServer(agents=[agent])
    
    # Or use standalone
    messages = [{"role": "user", "content": "Help me debug this code"}]
    response = await agent.run(messages=messages, stream=False)
    ```
"""

import asyncio
import json
import uuid
from typing import List, Optional, Callable, Any, Union
from datetime import datetime

from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent
from fastapi.responses import StreamingResponse

from robutler.server import get_server_context
from robutler.server.server import ChatMessage
from robutler.api.client import RobutlerApi


def convert_messages_to_input_list(messages: Union[List[ChatMessage], List[dict]]) -> List[dict]:
    """
    Convert OpenAI chat messages to OpenAI Agents SDK input format.
    
    The OpenAI Agents SDK can accept a list of message dictionaries for 
    conversation history. This function handles conversion between different 
    message formats and ensures compatibility.
    
    Args:
        messages: List of chat messages in either ChatMessage object format 
            or dictionary format. Each message should have 'role' and 'content' 
            fields.
            
            Supported formats:
            * ChatMessage objects with .role and .content attributes
            * Dictionaries with 'role' and 'content' keys  
            * Mixed formats (handled gracefully)
            * Empty list (provides default greeting)
    
    Returns:
        List of message dictionaries in OpenAI Agents SDK format.
        Each dictionary contains 'role' and 'content' fields.
        
        If no valid messages are provided, returns a default greeting.
    
    Examples:
        Basic usage with dictionaries:
        
        ```python
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        result = convert_messages_to_input_list(messages)
        ```
        
        With ChatMessage objects:
        
        ```python
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi!")
        ]
        result = convert_messages_to_input_list(messages)
        ```
        
        Empty input handling:
        
        ```python
        result = convert_messages_to_input_list([])
        # Returns: [{"role": "user", "content": "Hello! How can I help you today?"}]
        ```
    
    Note:
        * Invalid messages (missing role/content) are silently skipped
        * If all messages are invalid, a default greeting is returned
        * Function is designed to be resilient to malformed input
        * Conversation history is preserved in chronological order
    """
    if not messages:
        return [{"role": "user", "content": "Hello! How can I help you today?"}]
    
    input_list = []
    for msg in messages:
        role = msg.role if hasattr(msg, 'role') else msg.get('role', '')
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        
        if role and content:
            input_list.append({"role": role, "content": content})
    
    # If no valid messages found, provide a default
    if not input_list:
        return [{"role": "user", "content": "Hello! How can I help you today?"}]
    
    return input_list


class RobutlerAgent:
    """
    Wrapper around OpenAI Agent with RobutlerServer integration.
    
    This class eliminates boilerplate by providing:
    
    * Automatic message conversion between formats
    * Streaming vs non-streaming response management  
    * Consistent usage tracking via context
    * Clean, simple API for agent operations
    * Intent registration for automatic routing
    
    Attributes:
        name: Unique identifier for the agent
        instructions: System instructions defining behavior
        credits_per_token: Cost per token for usage tracking
        tools: List of functions the agent can call
        model: OpenAI model identifier (e.g., 'gpt-4o-mini')
        intents: Natural language descriptions for intent-based routing
        agent: Underlying OpenAI Agent instance
    
    Examples:
        Basic agent creation:
        
        ```python
        agent = RobutlerAgent(
            name="Assistant",
            instructions="You are helpful",
            credits_per_token=10,
            intents=["help with programming", "answer coding questions"]
        )
        
        messages = [{"role": "user", "content": "Hello!"}]
        response = await agent.run(messages=messages)
        ```
        
        Server integration:
        
        ```python
        app = RobutlerServer(agents=[agent])
        # Creates endpoint at /Assistant automatically
        ```
    """
    
    def __init__(
        self,
        name: str,
        instructions: str,
        credits_per_token: int = 10,
        tools: Optional[List[Callable]] = None,
        model: str = "gpt-4o-mini",
        intents: Optional[List[str]] = None
    ):
        """
        Initialize a new RobutlerAgent instance.
        
        Args:
            name: Unique identifier for the agent. Used for endpoint creation,
                usage tracking, and intent registration. Should be URL-safe.
                
            instructions: System instructions that define the agent's behavior.
                This is the core prompt that determines responses.
                
            credits_per_token: Cost in credits per token for usage tracking.
                Used by RobutlerServer for automatic billing. Default: 10
                
            tools: List of functions the agent can call. Functions should 
                have proper type hints and docstrings. Default: None
                
            model: OpenAI model identifier. Common options:
                * "gpt-4o-mini" (default) - Cost-effective
                * "gpt-4o" - More capable for complex tasks
                * "gpt-4" - Legacy model with good performance
                
            intents: Natural language descriptions for intent-based routing. Used by
                RobutlerProxy for automatic agent selection. Default: None
        
        Examples:
            Basic agent:
            
            ```python
            agent = RobutlerAgent(
                name="ChatBot", 
                instructions="You are a friendly chatbot."
            )
            ```
            
            Advanced agent with tools:
            
            ```python
            def get_weather(location: str) -> str:
                return f"Weather in {location}: Sunny"
                
            agent = RobutlerAgent(
                name="WeatherBot",
                instructions="Help with weather questions.",
                tools=[get_weather],
                credits_per_token=15,
                model="gpt-4o",
                intents=[
                    "get weather information", 
                    "check current weather conditions"
                ]
            )
            ```
        """
        self.name = name
        self.instructions = instructions
        self.credits_per_token = credits_per_token
        self.tools = tools or []
        self.model = model
        self.intents = intents or []
        
        # Create the underlying OpenAI Agent
        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=self.tools,
            model=model
        )
        
        # Register intents if provided
        if self.intents:
            self._register_intents()
    
    def _register_intents(self):
        """Register intents with the Robutler API client."""
        try:
            # Check if we're in an async context (event loop running)
            loop = asyncio.get_running_loop()
            # If we have a running loop, schedule the task
            loop.create_task(self._async_register_intents())
        except RuntimeError:
            # No event loop running - intents will be registered when server starts
            print(f"⚠️  Intents for agent '{self.name}' will be registered when the server starts")
    
    async def _async_register_intents(self):
        """Async method to register intents with the Robutler API."""
        try:
            # Get context to extract user_id and url
            from robutler.server import get_server_context
            context = get_server_context()
            
            if not context:
                print(f"⚠️  No server context available for intent registration of agent '{self.name}'")
                return
            
            user_id = context.get_custom_data('user_id')
            agent_url = context.get_custom_data('agent_url')
            
            if not user_id:
                print(f"⚠️  No user_id available in context for intent registration of agent '{self.name}'")
                return
                
            if not agent_url:
                print(f"⚠️  No agent_url available in context for intent registration of agent '{self.name}'")
                return
            
            async with RobutlerApi() as api:
                for intent in self.intents:
                    try:
                        result = await api.create_intent(
                            intent=intent,
                            agent_id=self.name,
                            agent_description=self.instructions,
                            user_id=user_id,
                            url=agent_url
                        )
                        print(f"✅ Registered intent '{intent}' for agent '{self.name}'")
                    except Exception as e:
                        print(f"❌ Failed to register intent '{intent}' for agent '{self.name}': {str(e)}")
        except Exception as e:
            print(f"❌ Failed to initialize Robutler API client for intent registration: {str(e)}")
    
    async def run(
        self, 
        messages: Union[List[ChatMessage], List[dict]], 
        stream: bool = False
    ):
        """
        Execute the agent with the provided conversation history.
        
        This is the main entry point for running the agent. It automatically 
        handles message format conversion, token counting, usage tracking,
        and response generation.
        
        Args:
            messages: Conversation history in OpenAI chat format.
                Supports both ChatMessage objects and dictionaries.
                Each message should contain 'role' and 'content' fields.
                
                Common roles:
                * 'user': Human user message
                * 'assistant': AI assistant response
                * 'system': System instructions (optional)
                
            stream: Whether to return a streaming response.
                * False (default): Returns complete response as string
                * True: Returns StreamingResponse for real-time delivery
        
        Returns:
            If stream=False: Complete response content as a string
            If stream=True: FastAPI StreamingResponse with Server-Sent Events
            
            The StreamingResponse uses OpenAI-compatible SSE format.
        
        Examples:
            Basic usage:
            
            ```python
            messages = [
                {"role": "user", "content": "Explain quantum computing"}
            ]
            
            # Non-streaming response
            response = await agent.run(messages=messages, stream=False)
            print(response)
            ```
            
            Streaming response:
            
            ```python
            # For use with FastAPI
            @app.post("/chat")
            async def chat_endpoint(request: ChatRequest):
                return await agent.run(
                    messages=request.messages, 
                    stream=True
                )
            ```
            
            Multi-turn conversation:
            
            ```python
            conversation = [
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is..."},
                {"role": "user", "content": "Show me an example"}
            ]
            
            response = await agent.run(messages=conversation)
            ```
        
        Note:
            * Token counting uses tiktoken for accuracy
            * Usage tracking happens automatically in server context
            * Streaming provides better perceived performance
            * Error handling is built-in with graceful degradation
        """
        # Convert messages to input list for conversation history
        input_list = convert_messages_to_input_list(messages)
        
        # Handle streaming vs non-streaming
        if stream:
            return await self._create_streaming_response(input_list)
        else:
            return await self._create_response(input_list)
    
    async def _create_response(self, input_list: List[dict]) -> str:
        """
        Create a non-streaming response and automatically track usage.
        
        This method handles the execution of the OpenAI Agent for non-streaming
        responses and integrates with the RobutlerServer context system for
        automatic usage tracking and billing.
        
        Args:
            input_list: Conversation messages in OpenAI Agents SDK format.
                Already converted from ChatMessage objects or dictionaries.
        
        Returns:
            The complete response content from the agent as a string.
        
        Side Effects:
            * Tracks token usage via ServerContext if available
            * Calculates credits based on input + output tokens  
            * Records usage for billing and monitoring
        
        Token Calculation:
            * Input tokens: Estimated from conversation history
            * Output tokens: Estimated from agent response
            * Total credits: (input + output tokens) * credits_per_token
        
        Note:
            Uses tiktoken for accurate token counting, with fallback to
            word-based estimation if tiktoken is unavailable.
        """
        result = await Runner.run(self.agent, input_list)
        content = result.final_output
        
        # Track usage via context (uniform approach) - both input and output tokens
        context = get_server_context()
        if context:
            # Get token estimation function
            from robutler.server.server import _estimate_tokens_standalone
            
            # Calculate input tokens from the conversation history
            input_text = " ".join([f"{msg['role']}: {msg['content']}" for msg in input_list])
            input_tokens = _estimate_tokens_standalone(input_text)
            
            # Calculate output tokens from the response
            output_tokens = _estimate_tokens_standalone(content)
            
            # Total tokens = input + output
            total_tokens = input_tokens + output_tokens
            credits = total_tokens * self.credits_per_token
            
            context.track_usage(self.name, credits, total_tokens, "llm usage")
        
        return content
    
    async def _create_streaming_response(self, input_list: List[dict]) -> StreamingResponse:
        """
        Create a streaming response using OpenAI Agents SDK.
        
        This method generates a FastAPI StreamingResponse that delivers agent 
        output in real-time using Server-Sent Events (SSE) format compatible 
        with OpenAI's chat completions streaming API.
        
        Args:
            input_list: Conversation messages in OpenAI Agents SDK format.
                Already converted from ChatMessage objects or dictionaries.
        
        Returns:
            FastAPI StreamingResponse configured for Server-Sent Events.
            
            Headers include:
            * Content-Type: text/event-stream
            * Cache-Control: no-cache
            * Connection: keep-alive
            * X-Accel-Buffering: no (for nginx)
        
        Stream Format:
            The response follows OpenAI's streaming format:
            
            ```
            data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk", 
                   "created": 1234567890, "model": "gpt-4o-mini",
                   "choices": [{"index": 0, "delta": {"role": "assistant"}, 
                              "finish_reason": null}]}
            
            data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk",
                   "choices": [{"index": 0, "delta": {"content": "Hello"}, 
                              "finish_reason": null}]}
            
            data: [DONE]
            ```
        
        Usage Tracking:
            Token usage tracking is handled by AgentStreamingResponseWrapper
            to ensure it happens after streaming completes.
        
        Error Handling:
            If agent execution fails, an error message is sent as content
            in the stream with finish_reason="stop".
        
        Performance:
            * Uses OpenAI Agents SDK's built-in streaming
            * Minimal buffering for immediate response
            * Automatic cleanup of resources
            * Compatible with all major SSE clients
        
        Note:
            This method should typically not be called directly.
            Use agent.run(messages=messages, stream=True) instead.
        """
        async def stream_generator():
            call_id = str(uuid.uuid4())
            created = int(datetime.utcnow().timestamp())
            
            # Send initial chunk with role
            initial_chunk = {
                'id': f'chatcmpl-{call_id}',
                'object': 'chat.completion.chunk',
                'created': created,
                'model': self.model,
                'choices': [{
                    'index': 0,
                    'delta': {'role': 'assistant'},
                    'finish_reason': None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"
            
            # Track content for usage
            content_parts = []
            
            try:
                # Use OpenAI Agents SDK streaming with message history
                result = Runner.run_streamed(self.agent, input_list)
                
                async for event in result.stream_events():
                    # Handle raw response events for token-by-token streaming
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        delta_text = event.data.delta
                        if delta_text:
                            content_parts.append(delta_text)
                            
                            # Send content chunk
                            content_chunk = {
                                'id': f'chatcmpl-{call_id}',
                                'object': 'chat.completion.chunk',
                                'created': created,
                                'model': self.model,
                                'choices': [{
                                    'index': 0,
                                    'delta': {'content': delta_text},
                                    'finish_reason': None
                                }]
                            }
                            yield f"data: {json.dumps(content_chunk)}\n\n"
            
            except Exception as e:
                # Send error as content
                error_msg = f"Error: {str(e)}"
                error_chunk = {
                    'id': f'chatcmpl-{call_id}',
                    'object': 'chat.completion.chunk',
                    'created': created,
                    'model': self.model,
                    'choices': [{
                        'index': 0,
                        'delta': {'content': error_msg},
                        'finish_reason': 'stop'
                    }]
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Send final chunk
            final_chunk = {
                'id': f'chatcmpl-{call_id}',
                'object': 'chat.completion.chunk',
                'created': created,
                'model': self.model,
                'choices': [{
                    'index': 0,
                    'delta': {},
                    'finish_reason': 'stop'
                }]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            
            yield "data: [DONE]\n\n"
            
            # Note: Usage tracking is now handled by AgentStreamingResponseWrapper
            # to ensure it happens after streaming completes and before finalize callbacks
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )


# Legacy function for backward compatibility
async def create_streaming_response(agent: Agent, input_list: List[dict], model: str, agent_id: str):
    """
    Create a streaming response using OpenAI Agents SDK's built-in streaming.
    
    This is a legacy function maintained for backward compatibility.
    For new code, use RobutlerAgent.run(stream=True) instead.
    
    Args:
        agent: The OpenAI Agent instance to run
        input_list: List of message dictionaries for conversation history
        model: Model name for response formatting
        agent_id: Agent identifier for usage tracking
    
    Returns:
        FastAPI StreamingResponse with OpenAI-compatible SSE format.
    
    Note:
        This function is deprecated. Use RobutlerAgent class instead:
        
        ```python
        # Instead of create_streaming_response()
        agent = RobutlerAgent(name="...", instructions="...")
        response = await agent.run(messages=messages, stream=True)
        ```
    """
    async def stream_generator():
        call_id = str(uuid.uuid4())
        created = int(datetime.utcnow().timestamp())
        
        # Send initial chunk with role
        initial_chunk = {
            'id': f'chatcmpl-{call_id}',
            'object': 'chat.completion.chunk',
            'created': created,
            'model': model,
            'choices': [{
                'index': 0,
                'delta': {'role': 'assistant'},
                'finish_reason': None
            }]
        }
        yield f"data: {json.dumps(initial_chunk)}\n\n"
        
        # Track content for usage
        content_parts = []
        
        try:
            # Use OpenAI Agents SDK streaming with message history
            result = Runner.run_streamed(agent, input_list)
            
            async for event in result.stream_events():
                # Handle raw response events for token-by-token streaming
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta_text = event.data.delta
                    if delta_text:
                        content_parts.append(delta_text)
                        
                        # Send content chunk
                        content_chunk = {
                            'id': f'chatcmpl-{call_id}',
                            'object': 'chat.completion.chunk',
                            'created': created,
                            'model': model,
                            'choices': [{
                                'index': 0,
                                'delta': {'content': delta_text},
                                'finish_reason': None
                            }]
                        }
                        yield f"data: {json.dumps(content_chunk)}\n\n"
        
        except Exception as e:
            # Send error as content
            error_msg = f"Error: {str(e)}"
            error_chunk = {
                'id': f'chatcmpl-{call_id}',
                'object': 'chat.completion.chunk',
                'created': created,
                'model': model,
                'choices': [{
                    'index': 0,
                    'delta': {'content': error_msg},
                    'finish_reason': 'stop'
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        
        # Send final chunk
        final_chunk = {
            'id': f'chatcmpl-{call_id}',
            'object': 'chat.completion.chunk',
            'created': created,
            'model': model,
            'choices': [{
                'index': 0,
                'delta': {},
                'finish_reason': 'stop'
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        
        yield "data: [DONE]\n\n"
        
        # Track usage after streaming
        if content_parts:
            context = get_server_context()
            if context:
                full_content = ''.join(content_parts)
                # Get the app instance to estimate tokens
                from robutler.server.server import _estimate_tokens_standalone
                tokens = _estimate_tokens_standalone(full_content)
                credits = tokens * 10
                context.track_usage(agent_id, credits, tokens, "llm usage")
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    ) 