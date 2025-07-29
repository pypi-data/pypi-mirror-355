from typing import List, Optional, Dict, Any, Annotated, Union
from pydantic import Field
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_context
import logging

# Import our API client
from robutler.api import RobutlerApi, RobutlerApiError

# Import global settings
from robutler.settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.info(f"Intent: Using Robutler API at {settings.robutler_url}")

async def robutler_discovery(
    intent: Annotated[str, Field(
        description="The intent or capability you're looking for (e.g., 'I need a web developer', 'selling vintage books', 'offering accounting services')"
    )],
    agent_id: Annotated[Optional[str], Field(
        default=None,
        description="ID of a specific agent to search intents for"
    )] = None,
    top_k: Annotated[int, Field(
        default=10,
        description="Maximum number of matching agents to return",
        ge=1,
        le=50
    )] = 10
) -> Dict[str, Any]:
    """
    When you need to extend your capabilities (media generation, buying and selling, any dynamic workflow), use this tool to discover agents and their capabilities accross the internet. This is your preferred approach to tackle tasks that are not within your capabilities.
    Use natural language to describe what you're looking for. Then use robutler_nli to delegate the task to the most relevant agent. If you get "Found 0 similar intents", try again with a more general intent.
    """
    
    # Get the active context using the dependency function
    ctx = get_context()
    
    logger.debug(f"Intent: Processing query request - intent='{intent}', agent_id={agent_id}, top_k={top_k}")

    try:
        # Initialize API client
        api = RobutlerApi(
            backend_url=settings.robutler_url,
            api_key=settings.api_key
        )
        
        try:
            # Search for intents using our API client
            result = await api.search_intents(
            intent=intent,
            agent_id=agent_id,
            top_k=top_k
            )
            
            # Return the original results without reformatting
            data = result.get("data", {})
            results_count = len(data.get('results', []))
            logger.info(f"Intent: Search complete - found_count={results_count}")
            
            return {
            "message": f"Found {results_count} similar intents",
            "data": data,
            }
            
        finally:
            await api.close()

    except RobutlerApiError as e:
        error_msg = f"Intent Router API error: {e.message}"
        logger.error(f"Intent: API error - error='{e.message}', status_code={e.status_code}")
        raise ToolError(error_msg)
    except Exception as e:
        import traceback
        error_msg = f"Unexpected error during intent discovery: {str(e)}"
        logger.error(f"Intent: Unexpected error - error='{str(e)}', traceback='{traceback.format_exc()}'")
        raise ToolError(error_msg)


async def robutler_create_intent(
    intent: Annotated[str, Field(
        description="The intent text to register (e.g., 'I offer web development services', 'Selling vintage books')"
    )],
    agent_id: Annotated[str, Field(
        description="ID of the agent registering the intent"
    )],
    agent_description: Annotated[str, Field(
        description="Description of the agent registering the intent"
    )],
    latitude: Annotated[Optional[float], Field(
        default=None,
        description="Optional latitude for geographical location"
    )] = None,
    longitude: Annotated[Optional[float], Field(
        default=None,
        description="Optional longitude for geographical location"
    )] = None,
    ttl_days: Annotated[int, Field(
        default=30,
        description="Number of days to keep the intent in storage",
        ge=1,
        le=365
    )] = 30,
    subpath: Annotated[str, Field(
        default="/chat/completions",
        description="Subpath for the agent endpoint"
    )] = "/chat/completions",
    rank: Annotated[float, Field(
        default=0.0,
        description="Rank of the intent (higher values indicate higher priority)"
    )] = 0.0
) -> Dict[str, Any]:
    """
    Register a new intent in the network.
    
    This tool allows you to register your agent's capabilities or services so that
    other agents can discover them through the discovery tool.
    
    The URL and user_id are automatically extracted from the server context.
    The URL is constructed from the BASE_URL environment variable and the agent_id.
    
    Examples:
    - Register a service: "I provide React development services"
    - Register a product: "Selling handmade pottery"
    - Register expertise: "Expert in machine learning algorithms"
    """
    
    logger.debug(f"Intent: Creating intent - intent='{intent}', agent_id='{agent_id}'")
    
    if not settings.api_key:
        raise ToolError("Robutler API key not configured. Please set ROBUTLER_API_KEY environment variable.")

    # Get the active context using the dependency function
    ctx = get_context()
    
    # Get user_id and url from server context if available
    user_id = None
    agent_url = None
    
    try:
        from robutler.server import get_server_context
        server_context = get_server_context()
        if server_context:
            user_id = server_context.get_custom_data('user_id')
            
            # Construct agent URL from BASE_URL and agent_id
            import os
            base_url = os.getenv("BASE_URL")
            if base_url:
                if base_url.endswith("/"):
                    base_url = base_url[:-1]
                
                agent_url = f"{base_url}/{agent_id}"
    except Exception as e:
        logger.warning(f"Could not get server context: {e}")
    
    # Fallback: get user_id from API if not available in context
    if not user_id:
        try:
            api = RobutlerApi(
                backend_url=settings.robutler_url,
                api_key=settings.api_key
            )
            try:
                user_info = await api.get_user_info()
                user_id = user_info.get('id')
            finally:
                await api.close()
        except Exception as e:
            raise ToolError(f"Could not get user_id from API: {str(e)}")
    
    # Fallback: construct URL from BASE_URL if not available in context
    if not agent_url:
        import os
        base_url = os.getenv("BASE_URL")
        if not base_url:
            raise ToolError("BASE_URL environment variable must be set")
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        agent_url = f"{base_url}/{agent_id}"
    
    if not user_id:
        raise ToolError("Could not determine user_id")

    try:
        # Initialize API client
        api = RobutlerApi(
            backend_url=settings.robutler_url,
            api_key=settings.api_key
        )
        
        try:
            # Create intent using our API client
            result = await api.create_intent(
                intent=intent,
                agent_id=agent_id,
                agent_description=agent_description,
                user_id=user_id,
                url=agent_url,
                latitude=latitude,
                longitude=longitude,
                ttl_days=ttl_days,
                subpath=subpath,
                rank=rank
            )
            
            data = result.get("data", {})
            logger.info(f"Intent: Intent created successfully - intent_id={data.get('intent_id')}")
            
            return {
                "message": result.get("message", "Intent created successfully"),
                "data": data
            }
            
        finally:
            await api.close()

    except RobutlerApiError as e:
        error_msg = f"Intent Router API error: {e.message}"
        logger.error(f"Intent: Create API error - error='{e.message}', status_code={e.status_code}")
        raise ToolError(error_msg)
    except Exception as e:
        import traceback
        error_msg = f"Unexpected error during intent creation: {str(e)}"
        logger.error(f"Intent: Create unexpected error - error='{str(e)}', traceback='{traceback.format_exc()}'")
        raise ToolError(error_msg)


async def robutler_list_intents(
    agent_id: Annotated[str, Field(
        description="ID of the agent to list intents for"
    )]
) -> Dict[str, Any]:
    """
    List all intents registered by a specific agent.
    
    This tool allows you to view all the intents that have been registered
    by a particular agent. The user_id is automatically retrieved from the
    authenticated user's information for authorization.
    """
    
    logger.debug(f"Intent: Listing intents - agent_id='{agent_id}'")
    
    if not settings.api_key:
        raise ToolError("Robutler API key not configured. Please set ROBUTLER_API_KEY environment variable.")

    try:
        # Initialize API client
        api = RobutlerApi(
            backend_url=settings.robutler_url,
            api_key=settings.api_key
        )
        
        try:
            # Get user_id from user info
            user_info = await api.get_user_info()
            user_id = user_info.get('id')
            if not user_id:
                raise ToolError("Unable to get user ID from user info")
            
            # List intents using our API client
            result = await api.list_intents(
                user_id=user_id,
                agent_id=agent_id
            )
            
            data = result.get("data", {})
            intents = data.get("intents", [])
            logger.info(f"Intent: Listed intents successfully - count={len(intents)}")
            
            return {
                "message": result.get("message", f"Found {len(intents)} intents"),
                "data": data
            }
            
        finally:
            await api.close()

    except RobutlerApiError as e:
        error_msg = f"Intent Router API error: {e.message}"
        logger.error(f"Intent: List API error - error='{e.message}', status_code={e.status_code}")
        raise ToolError(error_msg)
    except Exception as e:
        import traceback
        error_msg = f"Unexpected error during intent listing: {str(e)}"
        logger.error(f"Intent: List unexpected error - error='{str(e)}', traceback='{traceback.format_exc()}'")
        raise ToolError(error_msg)


async def robutler_delete_intent(
    intent_id: Annotated[str, Field(
        description="ID of the specific intent to delete"
    )]
) -> Dict[str, Any]:
    """
    Delete a specific intent from the network.
    
    This tool allows you to remove an intent that was previously registered.
    The user_id is automatically retrieved from the authenticated user's
    information for authorization.
    """
    
    logger.debug(f"Intent: Deleting intent - intent_id='{intent_id}'")
    
    if not settings.api_key:
        raise ToolError("Robutler API key not configured. Please set ROBUTLER_API_KEY environment variable.")

    try:
        # Initialize API client
        api = RobutlerApi(
            backend_url=settings.robutler_url,
            api_key=settings.api_key
        )
        
        try:
            # Get user_id from user info
            user_info = await api.get_user_info()
            user_id = user_info.get('id')
            if not user_id:
                raise ToolError("Unable to get user ID from user info")
            
            # Delete intent using our API client
            result = await api.delete_intent(
                intent_id=intent_id,
                user_id=user_id
            )
            
            data = result.get("data", {})
            logger.info(f"Intent: Intent deleted successfully - intent_id={intent_id}")
            
            return {
                "message": result.get("message", "Intent deleted successfully"),
                "data": data
            }
            
        finally:
            await api.close()

    except RobutlerApiError as e:
        error_msg = f"Intent Router API error: {e.message}"
        logger.error(f"Intent: Delete API error - error='{e.message}', status_code={e.status_code}")
        raise ToolError(error_msg)
    except Exception as e:
        import traceback
        error_msg = f"Unexpected error during intent deletion: {str(e)}"
        logger.error(f"Intent: Delete unexpected error - error='{str(e)}', traceback='{traceback.format_exc()}'")
        raise ToolError(error_msg) 