from __future__ import annotations
import os
import secrets
from pathlib import Path
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from typing import Any, Dict, List


class MCPClient:
    """MCP Client for connecting to appointment system MCP server"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.value = secrets.randbelow(100)
        return cls._instance
    
    def __init__(self, serverFile: str = "server.py", sse_url: str = None):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self.sse_url = sse_url
            self.session = None
            self.exit_stack = None
            
            if not sse_url:  # stdio mode (local)
                env = os.environ.copy()
                
                # Set PYTHONPATH to project root
                if 'PYTHONPATH' in env:
                    env['PYTHONPATH'] = f"{os.getcwd()}:{env['PYTHONPATH']}"
                else:
                    env['PYTHONPATH'] = os.getcwd()
                
                # Handle server path - support both absolute and relative paths
                if os.path.isabs(serverFile):
                    server_path = serverFile
                else:
                    # If serverFile is relative, resolve from current working directory
                    server_path = os.path.abspath(serverFile)
                
                self.server_params = StdioServerParameters(
                    command="python",
                    args=[server_path],
                    env=env,
                )
            else:
                self.server_params = None
            
            self._initialized = True

    async def start_session(self):
        """Start MCP session"""
        if self.session is not None:
            return
        
        self.exit_stack = AsyncExitStack()
        
        if self.sse_url:  # SSE mode (remote)
            sse_transport = await self.exit_stack.enter_async_context(
                sse_client(self.sse_url)
            )
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(*sse_transport)
            )
        else:  # stdio mode (local)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
        
        await self.session.initialize()
        print("MCP session started successfully")
       
    async def cleanup(self):
        """Cleanup MCP session"""
        if self.session:
            await self.exit_stack.aclose()
            self.session = None
            print("MCP session closed!")

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        if self.session is None:
            raise RuntimeError("MCP session not started. Call start_session() first.")
        
        result = await self.session.call_tool(tool_name, tool_args)
        print(f"Tool '{tool_name}' called successfully")
        return result
       
    async def get_tools(self):
        """Get list of available tools from MCP server"""
        if self.session is None:
            raise RuntimeError("MCP session not started. Call start_session() first.")
        
        response = await self.session.list_tools()
        return response.tools
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
        return False