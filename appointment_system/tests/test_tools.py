import unittest
import json
import os
import subprocess
import time
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client  # Changed from streamablehttp_client
from dotenv import load_dotenv

load_dotenv()


class TestMessagingTools(unittest.IsolatedAsyncioTestCase):
    server_process = None
    
    @classmethod
    def setUpClass(cls):
        """Start MCP server once for all tests (only for SSE mode)"""
        cls.transport_mode = os.getenv("MCP_TRANSPORT_MODE", "stdio")
        print(f"Transport mode: {cls.transport_mode}")
        
        if cls.transport_mode == "sse":
            cls.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")  # Add /sse endpoint
            
            # Setup environment with correct PYTHONPATH
            env = os.environ.copy()
            env["ENV"] = "production"
            
            # Add project root to PYTHONPATH
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root
            
            print(f"PYTHONPATH set to: {env['PYTHONPATH']}")
            
            # Start the server process with output capture
            cls.server_process = subprocess.Popen(
                ["python", "appointment_system/mcp/server.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                cwd=project_root,
                text=True,
                bufsize=1
            )
            
            # Wait and check if server started successfully
            time.sleep(3)
            
            # Check if process is still running
            if cls.server_process.poll() is not None:
                # Process has terminated, print output
                output, _ = cls.server_process.communicate()
                print("SERVER FAILED TO START!")
                print("Server output:")
                print(output)
                raise RuntimeError("MCP server failed to start")
            
            print("✓ MCP Server started for SSE mode")
        else:
            cls.server_script = "appointment_system/mcp/server.py"
            cls.server_url = None
            print("✓ Using stdio mode (server auto-managed)")
    
    @classmethod
    def tearDownClass(cls):
        """Stop MCP server after all tests (only for SSE mode)"""
        if cls.server_process:
            print("Stopping MCP server...")
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=5)
                # Print any remaining output
                if cls.server_process.stdout:
                    remaining = cls.server_process.stdout.read()
                    if remaining:
                        print("Final server output:", remaining)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()
            print("✓ MCP Server stopped")
    
    def setUp(self):
        self.transport_mode = self.__class__.transport_mode
        if self.transport_mode == "sse":
            self.server_url = self.__class__.server_url
        else:
            self.server_script = self.__class__.server_script
            
    def _get_client_params(self):
        if self.transport_mode == "sse":
            return {"sse_url": self.server_url}
        else:
            return {"serverFile": self.server_script}

    async def _call_tool(self, tool_name, tool_input):
        """Unified method to call tools in both stdio and SSE modes"""
        mcpClient = None
        try:
            if self.transport_mode == "stdio":
                from appointment_system.mcp.client import MCPClient
                mcpClient = MCPClient(**self._get_client_params())
                await mcpClient.start_session()
                result = await mcpClient.call_tool(tool_name, tool_input)
                return result
            else:
                # SSE mode - use streamable_http_client (not streamablehttp_client)
                async with streamable_http_client(self.server_url) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, tool_input)
                        return result
        finally:
            if self.transport_mode == "stdio" and mcpClient:
                await mcpClient.cleanup()

    async def get_tools(self):
        """Get list of available tools"""
        mcpClient = None
        try:
            if self.transport_mode == "stdio":
                from appointment_system.mcp.client import MCPClient
                mcpClient = MCPClient(**self._get_client_params())
                await mcpClient.start_session()
                result = await mcpClient.get_tools()
                return result
            else:
                async with streamable_http_client(self.server_url) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        response = await session.list_tools()
                        return response.tools
        finally:
            if self.transport_mode == "stdio" and mcpClient:
                await mcpClient.cleanup()

    # ... rest of your test methods remain the same
    async def test_get_all_tools(self):
        tools = await self.get_tools()
        self.assertTrue(len(tools) > 0)

        tool_names = [tool.name for tool in tools]
        print("Available tools:", tool_names)

        # WhatsApp
        self.assertIn("send_whatsapp_message", tool_names)
        self.assertIn("get_whatsapp_messages", tool_names)

        # Telegram
        self.assertIn("send_telegram_message", tool_names)
        self.assertIn("get_telegram_messages", tool_names)

    async def test_send_whatsapp_message(self):
        phone_number = "918826173493"
        message = "Hello, which time would you like to book an appointment?"

        result = await self._call_tool(
            "send_whatsapp_message",
            {
                "phone_number": phone_number,
                "message": message
            }
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("WhatsApp send result:", response)
        self.assertIn("success", response)

    async def test_get_whatsapp_messages(self):
        phone_number = "918826173493"

        result = await self._call_tool(
            "get_whatsapp_messages",
            {
                "phone_number": phone_number,
                "limit": 50
            }
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("WhatsApp messages:", json.dumps(response, indent=2))
        self.assertIn("success", response)

    async def test_send_telegram_message(self):
        chat_id = "5200468446"   
        message = "Hi, we have discussed today, we will start. don't worry."

        result = await self._call_tool(
            "send_telegram_message",
            {
                "chat_id": chat_id,
                "message": message
            }
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("Telegram send result:", response)
        self.assertIn("success", response)

    async def test_get_telegram_messages(self):
        result = await self._call_tool(
            "get_telegram_messages",
            {"limit": 20}
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("\n=== Telegram Messages ===")
        print(json.dumps(response, indent=2))
        self.assertIn("success", response)
        self.assertTrue(response["success"])


if __name__ == "__main__":
    unittest.main()