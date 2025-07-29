#!/usr/bin/env python
"""
Command-line interface for Robutler.
"""
import sys
import argparse
from robutler.settings import settings

def main():
    """Main entry point for the robutler command."""
    parser = argparse.ArgumentParser(
        description="Robutler - API client and tools for the Robutler ecosystem"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)
    
    # Proxy command
    proxy_parser = subparsers.add_parser("proxy", help="Run the Robutler Proxy server")
    proxy_parser.add_argument(
        "--target",
        required=not bool(settings.target_mcp),
        default=settings.target_mcp,
        help=f"Target MCP server URL to connect to (default: {settings.target_mcp or 'required'})",
    )
    proxy_parser.add_argument(
        "--transport",
        choices=["sse"],
        default=settings.proxy_transport,
        help=f"Transport protocol to use (default: {settings.proxy_transport})",
    )
    proxy_parser.add_argument(
        "--host",
        default=settings.proxy_host,
        help=f"Host address to bind to (default: {settings.proxy_host})",
    )
    proxy_parser.add_argument(
        "--port",
        type=int,
        default=settings.proxy_port,
        help=f"Port to listen on (default: {settings.proxy_port})",
    )
    proxy_parser.add_argument(
        "--name",
        default=settings.proxy_name,
        help=f"Name for the proxy server (default: {settings.proxy_name})",
    )
    
    # MCP command
    mcp_parser = subparsers.add_parser("mcp", help="Run the Robutler MCP server")
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=settings.mcp_transport,
        help=f"Transport protocol to use (default: {settings.mcp_transport})",
    )
    mcp_parser.add_argument(
        "--host",
        default=settings.mcp_host,
        help=f"Host address for HTTP-based transports (default: {settings.mcp_host})",
    )
    mcp_parser.add_argument(
        "--port",
        type=int,
        default=settings.mcp_port,
        help=f"Port for HTTP-based transports (default: {settings.mcp_port})",
    )
    mcp_parser.add_argument(
        "--path",
        default=settings.mcp_path,
        help=f"URL path for HTTP-based transport endpoints (default: {settings.mcp_path})",
    )
    mcp_parser.add_argument(
        "--name",
        default=settings.mcp_name,
        help=f"Name for the MCP server (default: {settings.mcp_name})",
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Print version information")
    
    args = parser.parse_args()
    
    if args.command == "proxy":
        from robutler.proxy.proxy import run_proxy
        run_proxy([
            f"--target={args.target}", 
            f"--transport={args.transport}", 
            f"--host={args.host}", 
            f"--port={args.port}", 
            f"--name={args.name}"
        ])
    elif args.command == "mcp":
        from tests.server import run_mcp
        cmd_args = [
            f"--transport={args.transport}",
            f"--host={args.host}", 
            f"--port={args.port}",
            f"--name={args.name}"
        ]
        if args.path:
            cmd_args.append(f"--path={args.path}")
        run_mcp(cmd_args)
    elif args.command == "version":
        from robutler import __version__
        print(f"Robutler version: {__version__}")

if __name__ == "__main__":
    main() 