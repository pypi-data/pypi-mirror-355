"""
Global settings for the Robutler package.

This module provides a central place to manage all environment variables and configuration settings.
"""
import os
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Global settings for the Robutler package."""
    # API settings
    robutler_url: str = Field(
        default="https://robutler.net", 
        validation_alias="ROBUTLER_URL",
        description="Robutler backend URL"
    )
    api_key: Optional[str] = Field(
        default=None, 
        validation_alias="ROBUTLER_API_KEY",
        description="Robutler API key"
    )
    
    # Proxy server settings
    proxy_name: str = Field(
        default="Robutler Proxy", 
        validation_alias="ROBUTLER_PROXY_NAME",
        description="Name for the proxy server"
    )
    proxy_host: str = Field(
        default="127.0.0.1", 
        validation_alias="ROBUTLER_PROXY_HOST",
        description="Host address for proxy to bind to"
    )
    proxy_port: int = Field(
        default=4001, 
        validation_alias="ROBUTLER_PROXY_PORT",
        description="Port for proxy to listen on"
    )
    proxy_transport: str = Field(
        default="sse",
        validation_alias="ROBUTLER_PROXY_TRANSPORT",
        description="Transport protocol for proxy to use"
    )
    target_mcp: Optional[str] = Field(
        default=None,
        validation_alias="ROBUTLER_TARGET_MCP",
        description="Target MCP server URL"
    )
    
    # MCP server settings
    mcp_name: str = Field(
        default="Robutler MCP Server", 
        validation_alias="ROBUTLER_MCP_NAME",
        description="Name for the MCP server"
    )
    mcp_host: str = Field(
        default="127.0.0.1", 
        validation_alias="ROBUTLER_MCP_HOST",
        description="Host address for MCP to bind to"
    )
    mcp_port: int = Field(
        default=4000, 
        validation_alias="ROBUTLER_MCP_PORT",
        description="Port for MCP to listen on"
    )
    mcp_transport: str = Field(
        default="sse",
        validation_alias="ROBUTLER_MCP_TRANSPORT",
        description="Transport protocol for MCP to use"
    )
    mcp_path: str = Field(
        default="/sse",
        validation_alias="ROBUTLER_MCP_PATH",
        description="URL path for MCP HTTP-based transport endpoints"
    )
    
    
    # Logging settings
    log_level: str = Field(
        default="info",
        validation_alias="ROBUTLER_LOG_LEVEL",
        description="Logging level (debug, info, warning, error, critical)"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Create a global instance of settings
settings = Settings() 