"""Main server module for Robutler MCP."""

import argparse
import io
import sys
from typing import Literal, Optional

from fastmcp import FastMCP, Image
from PIL import Image as PILImage

from robutler.tools import discovery, robutler_nli
# Configure logging
from fastmcp.utilities.logging import get_logger
logger = get_logger(__name__)

class TestMCP:
    """Robutler MCP server implementation."""
    
    def __init__(self, name="Robutler Test Server", **kwargs):
        """
        Initialize the MCP server.
        
        Args:
            name: Name for the server
            **kwargs: Additional configuration options
        """
        self.config = kwargs
        self.name = name
        
        # Create the MCP server instance
        self.mcp = FastMCP(name)
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all tools with the MCP server."""
        
        @self.mcp.tool()
        async def echo(text: str) -> str:
            """Echo the provided text back to the client."""
            return text

        @self.mcp.tool()
        def generate_image(width: int, height: int, color: str) -> Image:
            """Generates a solid color image."""
            # Create image using Pillow
            img = PILImage.new("RGB", (width, height), color=color)

            # Save to a bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()

            # Return using FastMCP's Image helper - use only the data parameter
            return Image(data=img_bytes)

        @self.mcp.tool()
        def do_nothing() -> None:
            """This tool performs an action but returns no data."""
            logger.info("Performing a side effect...")
            return None

        # Register resources
        @self.mcp.resource("resource://greeting")
        def get_greeting():
            """Provides a simple greeting resource."""
            return {
                "content": "Hello from the Robutler Test Server!",
                "description": "A simple greeting resource"
            }

        # Register prompts
        @self.mcp.prompt("prompt://basic_instruction")
        def get_basic_instruction():
            """Provides a basic instruction prompt for the assistant."""
            return "You are a helpful assistant that provides concise answers."
            
    def run(self, transport="stdio", host="127.0.0.1", port=4000, path="/mcp", **kwargs):
        """
        Run the MCP server.
        
        Args:
            transport: Transport protocol (stdio, sse, streamable-http)
            host: Host address to bind to for HTTP-based transports
            port: Port to listen on for HTTP-based transports
            path: URL path for HTTP-based transport endpoints
            **kwargs: Additional runtime options
        """
        logger.info(f"Starting Robutler Test Server on {host}:{port}")
        
        if transport == "stdio":
            self.mcp.run(transport="stdio")
        elif transport == "sse":
            # For SSE transport, explicitly use /sse path
            self.mcp.run(transport="sse", host=host, port=port, path="/sse")
        elif transport == "streamable-http":
            self.mcp.run(transport="streamable-http", host=host, port=port, path=path)
        else:
            logger.error(f"Unsupported transport: {transport}")
            raise ValueError(f"Unsupported transport: {transport}")

def run_mcp(args=None) -> None:
    """Entry point for the Robutler Test Server."""
    parser = argparse.ArgumentParser(description="Robutler Test Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for HTTP-based transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP-based transports (default: 8000)",
    )
    parser.add_argument(
        "--path",
        default="/sse",
        help="URL path for HTTP-based transport endpoints (default: /sse)",
    )
    parser.add_argument(
        "--name",
        default="Robutler Test Server",
        help="Name for the test server (default: Robutler Test Server)",
    )
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
    
    # Create the MCP server
    mcp_server = TestMCP(name=args.name)
    
    # Run the server
    mcp_server.run(
        transport=args.transport,
        host=args.host,
        port=args.port,
        path=args.path
    ) 

# Allow direct execution of this file
if __name__ == "__main__":
    run_mcp() 