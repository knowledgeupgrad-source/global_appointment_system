from __future__ import annotations
import os
import secrets
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Any, Dict, List


class MCPClient:
    """MCP Client for connecting to appointment system MCP server"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.value = secrets.randbelow(100)
        return cls._instance
    
    def __init__(self, serverFile: str = "server.py"):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            env = os.environ.copy()
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{os.getcwd()}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = os.getcwd()
            if os.path.isabs(serverFile):
                server_path = serverFile
            else:
                if os.path.exists(serverFile):
                    # If the file exists relative to current directory, use it
                    server_path = os.path.abspath(serverFile)
                else:
                    # Otherwise, try to find it relative to the module
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    potential_path = os.path.join(current_dir, '..', serverFile)
                    if os.path.exists(potential_path):
                        server_path = os.path.abspath(potential_path)
                    else:
                        # Last resort: use as-is
                        server_path = os.path.abspath(serverFile)
            
            self.server_params = StdioServerParameters(
                command="python",
                args=[server_path],
                env=env,
            )
            self.exit_stack = None
            self.session = None
            self.stdio = None
            self.write = None
            self._initialized = True

    async def start_session(self):
        """Start MCP session"""
        if self.session is not None:
            return
            
        # Create AsyncExitStack in this task so enter/exit happen in same task
        self.exit_stack = AsyncExitStack()
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            await self.session.initialize()
            print("MCP session started successfully")
        except Exception as e:
            # If initialization fails, clean up the exit stack
            if self.exit_stack is not None:
                await self.exit_stack.aclose()
                self.exit_stack = None
            self.session = None
            raise
       
    async def cleanup(self):
        """Cleanup MCP session"""
        if self.exit_stack is not None:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                print(f"Error closing exit stack: {e}")
            finally:
                self.exit_stack = None
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