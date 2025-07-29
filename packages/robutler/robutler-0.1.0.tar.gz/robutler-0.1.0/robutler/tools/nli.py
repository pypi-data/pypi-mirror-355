#!/usr/bin/env python3
"""
Natural Language Interface (NLI) Tool

This tool communicates with RobutlerAgent servers, handles payment tokens automatically,
and provides seamless integration with MCP servers.
"""

import os
import json
import asyncio
import httpx
import logging
from typing import Optional, Dict, Any, List
from robutler.api import initialize_api, RobutlerApiError

# Configure logging
logger = logging.getLogger(__name__)


class NLIClient:
    """Client for communicating with agents discovered with robutler_discovery."""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the NLI client.
        
        Args:
            api_token: Robutler API token (defaults to ROBUTLER_API_KEY env var)
        """
        self.api_token = api_token or os.getenv('ROBUTLER_API_KEY')
        self.api_client = None
        self.payment_tokens: Dict[str, str] = {}  # Cache payment tokens per server
        
    async def _ensure_api_client(self):
        """Ensure the API client is initialized."""
        if self.api_client is None:
            if not self.api_token:
                raise ValueError("Robutler API token not provided. Set ROBUTLER_API_KEY environment variable.")
            
            # Set the API key in settings for initialize_api
            from robutler.settings import settings
            original_api_key = settings.api_key
            settings.api_key = self.api_token
            
            try:
                self.api_client = await initialize_api()
                logger.info("NLI API client initialized successfully")
            except Exception as e:
                settings.api_key = original_api_key  # Restore original
                raise ValueError(f"Failed to initialize Robutler API client: {e}")
    
    async def _get_payment_token(self, server_url: str, min_balance: int = 10000) -> str:
        """
        Get or create a payment token for the specified server.
        
        Args:
            server_url: The RobutlerAgent server URL
            min_balance: Minimum balance required for the token
            
        Returns:
            Payment token string
        """
        await self._ensure_api_client()
        
        # Check if we have a cached token for this server
        if server_url in self.payment_tokens:
            token = self.payment_tokens[server_url]
            try:
                # Validate the cached token
                validation = await self.api_client.validate_payment_token(token)
                if validation.get('valid', False):
                    token_info = validation.get('token', {})
                    available = token_info.get('availableAmount', 0)
                    if available >= min_balance:
                        return token
                    else:
                        logger.warning(f"Cached token has insufficient balance: {available} < {min_balance}")
                else:
                    logger.warning("Cached token is invalid")
            except Exception as e:
                logger.warning(f"Error validating cached token: {e}")
            
            # Remove invalid/insufficient token from cache
            del self.payment_tokens[server_url]
        
        # Create a new payment token
        logger.info(f"Creating new payment token for {server_url}")
        try:
            # Create token with 2x the minimum balance to avoid frequent renewals
            token_amount = max(min_balance * 2, 50000)
            result = await self.api_client.issue_payment_token(
                amount=token_amount,
                ttl_hours=24  # Valid for 24 hours
            )
            
            token_info = result.get('token', {})
            token_string = token_info.get('token', '')
            
            if not token_string:
                raise ValueError("Failed to create payment token")
            
            # Cache the token
            self.payment_tokens[server_url] = token_string
            
            logger.info(f"Created payment token with {token_info.get('amount', 0)} credits")
            return token_string
            
        except Exception as e:
            raise ValueError(f"Failed to create payment token: {e}")
    
    async def chat_completion(
        self, 
        agent_url: str, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to a RobutlerAgent server.
        
        Args:
            agent_url: URL of the RobutlerAgent server endpoint
            messages: List of chat messages
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Response from the agent server
        """
        # Ensure URL ends with /chat/completions
        if not agent_url.endswith('/chat/completions'):
            if agent_url.endswith('/'):
                agent_url = agent_url + 'chat/completions'
            else:
                agent_url = agent_url + '/chat/completions'
        
        # Extract agent name from URL for model parameter
        # URL format: http://host:port/path/agent_name/chat/completions
        url_parts = agent_url.rstrip('/').split('/')
        # Remove 'chat' and 'completions' from the end to get agent name
        if len(url_parts) >= 3 and url_parts[-1] == 'completions' and url_parts[-2] == 'chat':
            agent_name = url_parts[-3]
        elif len(url_parts) >= 2:
            agent_name = url_parts[-2]
        else:
            agent_name = "gpt-4o-mini"
        
        # Prepare request data
        request_data = {
            "model": agent_name,  # Use agent name as model
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First attempt without payment token
            try:
                response = await client.post(agent_url, json=request_data, headers=headers)
                
                if response.status_code == 200:
                    if stream:
                        return {"status": "success", "content": response.text}
                    else:
                        return response.json()
                
                elif response.status_code == 402:
                    # Payment required - extract minimum balance from error message
                    error_text = response.text
                    min_balance = 10000  # Default
                    
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', '')
                        
                        # Try to extract minimum balance from error message
                        if 'Required:' in error_detail:
                            # Format: "Insufficient token balance. Available: X, Required: Y"
                            parts = error_detail.split('Required:')
                            if len(parts) > 1:
                                min_balance = int(parts[1].strip().split()[0])
                        elif 'minimum balance' in error_detail.lower():
                            # Try to extract number from error message
                            import re
                            numbers = re.findall(r'\d+', error_detail)
                            if numbers:
                                min_balance = int(numbers[-1])  # Take the last number
                    except Exception as e:
                        logger.warning(f"Could not parse payment error details: {e}")
                        pass  # Use default min_balance
                    
                    logger.info(f"💳 Payment required for {agent_url} (min balance: {min_balance} credits), obtaining payment token")
                    
                    # Get payment token and retry
                    try:
                        payment_token = await self._get_payment_token(agent_url, min_balance)
                        headers["X-Payment-Token"] = payment_token
                        
                        logger.info(f"🔄 Retrying request with payment token")
                        
                        # Retry with payment token
                        response = await client.post(agent_url, json=request_data, headers=headers)
                        
                        if response.status_code == 200:
                            logger.info(f"✅ Request successful with payment token")
                            if stream:
                                return {"status": "success", "content": response.text}
                            else:
                                return response.json()
                        else:
                            logger.error(f"❌ Request failed even with payment token: {response.status_code}")
                            raise ValueError(f"Request failed even with payment token: {response.status_code} - {response.text}")
                    except Exception as e:
                        logger.error(f"❌ Payment token handling failed: {e}")
                        raise ValueError(f"Payment token handling failed: {e}")
                
                else:
                    raise ValueError(f"Request failed: {response.status_code} - {response.text}")
                    
            except httpx.RequestError as e:
                raise ValueError(f"Network error communicating with {agent_url}: {e}")
    
    async def get_agent_info(self, agent_url: str) -> Dict[str, Any]:
        """
        Get information about a RobutlerAgent.
        
        Args:
            agent_url: Base URL of the RobutlerAgent server
            
        Returns:
            Agent information
        """
        # Remove /chat/completions if present
        if agent_url.endswith('/chat/completions'):
            agent_url = agent_url[:-len('/chat/completions')]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(agent_url)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise ValueError(f"Failed to get agent info: {response.status_code} - {response.text}")
            except httpx.RequestError as e:
                raise ValueError(f"Network error getting agent info from {agent_url}: {e}")
    
    async def close(self):
        """Close the API client."""
        if self.api_client:
            await self.api_client.close()


# Main NLI function for MCP integration
async def robutler_nli(agent_url: str, message: str) -> str:
    """
    Natural Language Interface to communicate with RobutlerAgent servers.
    
    Args:
        agent_url: URL of the RobutlerAgent server (e.g., http://localhost:2226/api/assistant)
        message: Message to send to the agent
        
    Returns:
        Response from the agent
    """
    client = NLIClient()
    
    try:
        messages = [{"role": "user", "content": message}]
        
        result = await client.chat_completion(
            agent_url=agent_url,
            messages=messages,
            stream=False
        )
        
        choices = result.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "No response")
        else:
            return "No response from agent"
                
    except Exception as e:
        return f"Error communicating with agent: {e}"
    finally:
        await client.close()


# CLI Interface for testing
async def main():
    """CLI interface for testing the NLI tool."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python nli.py <agent_url> <message>")
        print("Example: python nli.py http://localhost:2226/api/assistant 'What time is it?'")
        return
    
    agent_url = sys.argv[1]
    message = sys.argv[2]
    
    print(f"🤖 Sending message to {agent_url}")
    print(f"💬 Message: {message}")
    print()
    
    # Send chat message
    print("💬 Sending chat message...")
    response = await robutler_nli(agent_url, message)
    print(f"🤖 Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
