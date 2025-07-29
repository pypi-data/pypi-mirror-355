"""Pytest configuration and fixtures."""

import asyncio
import os
import pytest
import signal
import socket
import subprocess
import sys
import time
from typing import AsyncGenerator, Generator

from fastmcp import Client

# Import the MCP server from tests.server instead of robutler.mcp
from tests.server import TestMCP


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use.
    
    Args:
        port: The port number to check
        
    Returns:
        True if the port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


@pytest.fixture
async def in_memory_client() -> Client:
    """
    Fixture that creates a client connected directly to the server in memory.
    
    This is the most efficient way to test the server as it doesn't
    require any subprocess or network communication.
    """
    # Create a server instance
    server = TestMCP()
    
    # Create the client without using context manager
    client = Client(server.mcp)
    
    # Manually connect and set up session
    try:
        await client.__aenter__()
        yield client
    finally:
        # Suppress exceptions during teardown
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            # Log the error but don't let it fail the test
            print(f"Suppressed teardown error: {e}")


@pytest.fixture
def stdio_server_process() -> Generator[subprocess.Popen, None, None]:
    """
    Fixture that starts the MCP server as a subprocess using stdio transport.
    
    This is useful for testing the server's CLI interface and stdio transport.
    """
    # Start server as a subprocess
    process = subprocess.Popen(
        [sys.executable, "-m", "robutler", "mcp", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,  # We need binary mode for MCP messages
    )
    
    # Give the server a moment to start up
    time.sleep(0.5)
    
    # Make sure the process is running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        raise RuntimeError(
            f"Server process exited unexpectedly with code {process.returncode}.\n"
            f"stdout: {stdout.decode('utf-8')}\n"
            f"stderr: {stderr.decode('utf-8')}"
        )
    
    yield process
    
    # Clean up after the test
    if process.poll() is None:  # Process is still running
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture
async def stdio_client(stdio_server_process: subprocess.Popen) -> Client:
    """
    Fixture that creates a client connected to the stdio server process.
    
    This tests the full client-server communication over stdio.
    """
    # Create the client without using context manager
    client = Client(stdio_server_process)
    
    # Manually connect and set up session
    try:
        await client.__aenter__()
        yield client
    finally:
        # Suppress exceptions during teardown
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            # Log the error but don't let it fail the test
            print(f"Suppressed teardown error: {e}")


@pytest.fixture
def http_server_process() -> Generator[subprocess.Popen, None, None]:
    """
    Fixture that starts the MCP server as a subprocess using HTTP transport.
    
    This is useful for testing the server's HTTP transport.
    """
    port = 4000  # Use a specific port for testing
    
    # Check if a server is already running on this port
    if is_port_in_use(port):
        print(f"Using existing server on port {port}")
        # Return a dummy object since we don't need to manage the process
        class DummyProcess:
            def poll(self):
                return None  # Pretend the process is running
            
            def terminate(self):
                pass  # Don't terminate the existing process
            
            def kill(self):
                pass  # Don't kill the existing process
            
            def wait(self, timeout=None):
                pass  # No need to wait
            
            def send_signal(self, signal):
                pass  # Don't send signals to the existing process
        
        yield DummyProcess()
        return
    
    # Start server as a subprocess
    process = subprocess.Popen(
        [
            sys.executable, 
            "-m", 
            "robutler",
            "mcp",
            "--transport", 
            "streamable-http",
            "--port", 
            str(port)
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Give the server a moment to start up
    time.sleep(1)
    
    # Make sure the process is running
    if process.poll() is not None:
        _, stderr = process.communicate()
        raise RuntimeError(
            f"HTTP server process exited unexpectedly with code {process.returncode}.\n"
            f"stderr: {stderr}"
        )
    
    yield process
    
    # Clean up after the test
    if process.poll() is None:  # Process is still running
        # On Unix-based systems, we can use SIGTERM
        if os.name != "nt":  # Not Windows
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        else:
            # On Windows
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture
async def http_client(http_server_process: subprocess.Popen) -> Client:
    """
    Fixture that creates a client connected to the HTTP server process.
    
    This tests the full client-server communication over HTTP.
    """
    port = 4000  # Same port as in http_server_process
    server_url = f"http://localhost:{port}/mcp"
    
    # Wait a bit to ensure the server is ready
    await asyncio.sleep(0.5)
    
    # Create the client without using context manager
    client = Client(server_url)
    
    # Manually connect and set up session
    try:
        await client.__aenter__()
        yield client
    finally:
        # Suppress exceptions during teardown
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            # Log the error but don't let it fail the test
            print(f"Suppressed teardown error: {e}")


@pytest.fixture
def sse_server_process() -> Generator[subprocess.Popen, None, None]:
    """
    Fixture that starts the MCP server as a subprocess using SSE transport.
    
    This is useful for testing the server's SSE transport.
    """
    port = 4000  # Use a specific port for testing
    
    # Check if a server is already running on this port
    if is_port_in_use(port):
        print(f"Using existing server on port {port}")
        # Return a dummy object since we don't need to manage the process
        class DummyProcess:
            def poll(self):
                return None  # Pretend the process is running
            
            def terminate(self):
                pass  # Don't terminate the existing process
            
            def kill(self):
                pass  # Don't kill the existing process
            
            def wait(self, timeout=None):
                pass  # No need to wait
            
            def send_signal(self, signal):
                pass  # Don't send signals to the existing process
        
        yield DummyProcess()
        return
    
    # Start server as a subprocess
    process = subprocess.Popen(
        [
            sys.executable, 
            "-m", 
            "robutler",
            "mcp",
            "--transport", 
            "sse",
            "--port", 
            str(port)
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Give the server a moment to start up
    time.sleep(1)
    
    # Make sure the process is running
    if process.poll() is not None:
        _, stderr = process.communicate()
        raise RuntimeError(
            f"SSE server process exited unexpectedly with code {process.returncode}.\n"
            f"stderr: {stderr}"
        )
    
    yield process
    
    # Clean up after the test
    if process.poll() is None:  # Process is still running
        # On Unix-based systems, we can use SIGTERM
        if os.name != "nt":  # Not Windows
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        else:
            # On Windows
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture
async def sse_client(sse_server_process: subprocess.Popen) -> Client:
    """
    Fixture that creates a client connected to the SSE server process.
    
    This tests the full client-server communication over SSE.
    """
    port = 4000  # Same port as in sse_server_process
    server_url = f"http://localhost:{port}/sse"
    
    # Wait a bit to ensure the server is ready
    await asyncio.sleep(0.5)
    
    # Create the client without using context manager
    client = Client(server_url)
    
    # Manually connect and set up session
    try:
        await client.__aenter__()
        yield client
    finally:
        # Suppress exceptions during teardown
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            # Log the error but don't let it fail the test
            print(f"Suppressed teardown error: {e}")


@pytest.fixture
def proxy_process(sse_server_process: subprocess.Popen) -> Generator[subprocess.Popen, None, None]:
    """
    Fixture that starts the proxy server as a subprocess.
    
    This is useful for testing the proxy server.
    """
    port = 4001  # Use a different port for the proxy
    
    # Check if a proxy is already running on this port
    if is_port_in_use(port):
        print(f"Using existing proxy on port {port}")
        # Return a dummy object since we don't need to manage the process
        class DummyProcess:
            def poll(self):
                return None  # Pretend the process is running
            
            def terminate(self):
                pass  # Don't terminate the existing process
            
            def kill(self):
                pass  # Don't kill the existing process
            
            def wait(self, timeout=None):
                pass  # No need to wait
            
            def send_signal(self, signal):
                pass  # Don't send signals to the existing process
        
        yield DummyProcess()
        return
    
    # Start proxy as a subprocess
    process = subprocess.Popen(
        [
            sys.executable, 
            "-m", 
            "robutler",
            "proxy", 
            "--target", 
            "http://localhost:4000/sse",
            "--port", 
            str(port)
        ],
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Give the proxy a moment to start up
    time.sleep(1)
    
    # Make sure the process is running
    if process.poll() is not None:
        _, stderr = process.communicate()
        raise RuntimeError(
            f"Proxy process exited unexpectedly with code {process.returncode}.\n"
            f"stderr: {stderr}"
        )
    
    yield process
    
    # Clean up after the test
    if process.poll() is None:  # Process is still running
        # On Unix-based systems, we can use SIGTERM
        if os.name != "nt":  # Not Windows
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        else:
            # On Windows
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture
async def proxy_client(proxy_process: subprocess.Popen) -> Client:
    """
    Fixture that creates a client connected to the proxy server.
    
    This tests the full client-server communication through the proxy.
    """
    port = 4001  # Same port as in proxy_process
    proxy_url = f"http://localhost:{port}/sse"
    
    # Wait a bit to ensure the proxy is ready
    await asyncio.sleep(0.5)
    
    # Create the client without using context manager
    client = Client(proxy_url)
    
    # Manually connect and set up session
    try:
        await client.__aenter__()
        yield client
    finally:
        # Suppress exceptions during teardown
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            # Log the error but don't let it fail the test
            print(f"Suppressed teardown error: {e}") 