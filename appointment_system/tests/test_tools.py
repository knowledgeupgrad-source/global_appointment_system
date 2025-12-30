# appointment_system/mcp/tests/test_tools.py

import unittest
import json
import os
import subprocess
import time
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
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
            cls.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
            
            env = os.environ.copy()
            env["ENV"] = "production"
            
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root
            
            print(f"PYTHONPATH set to: {env['PYTHONPATH']}")
            
            cls.server_process = subprocess.Popen(
                ["python", "appointment_system/mcp/server.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=project_root,
                text=True,
                bufsize=1
            )
            
            time.sleep(3)
            
            if cls.server_process.poll() is not None:
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

    # ============================================
    # TESTS
    # ============================================

    async def test_get_all_tools(self):
        tools = await self.get_tools()
        self.assertTrue(len(tools) > 0)

        tool_names = [tool.name for tool in tools]
        print("Available tools:", tool_names)

        # WhatsApp
        self.assertIn("tool_send_whatsapp_message", tool_names)
        self.assertIn("tool_get_whatsapp_messages", tool_names)

        # Telegram
        self.assertIn("tool_send_telegram_message", tool_names)
        self.assertIn("tool_get_telegram_messages", tool_names)

    async def test_send_whatsapp_message(self):
        phone_number = "918826173493"
        message = "Hello, testing new output format!"

        result = await self._call_tool(
            "tool_send_whatsapp_message",
            {
                "phone_number": phone_number,
                "message": message
            }
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("\n=== WhatsApp Send Result ===")
        print(json.dumps(response, indent=2))
        
        # Check new format
        self.assertIn("success", response)
        self.assertIn("output", response)
        self.assertIn("message", response["output"])
        self.assertIn("data", response["output"])

    async def test_get_whatsapp_messages(self):
        phone_number = "918826173493"

        result = await self._call_tool(
            "tool_get_whatsapp_messages",
            {
                "phone_number": phone_number,
                "limit": 50
            }
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("\n=== WhatsApp Messages ===")
        print(json.dumps(response, indent=2))
        
        # Check new format
        self.assertIn("success", response)
        self.assertIn("output", response)
        if response["success"]:
            self.assertIn("data", response["output"])

    async def test_send_telegram_message(self):
        chat_id = "952901992"   
        message = "Hi, testing new output format!"

        result = await self._call_tool(
            "tool_send_telegram_message",
            {
                "chat_id": chat_id,
                "message": message
            }
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("\n=== Telegram Send Result ===")
        print(json.dumps(response, indent=2))
        
        # Check new format
        self.assertIn("success", response)
        self.assertIn("output", response)
        self.assertTrue(response["success"])

    async def test_get_telegram_messages(self):
        result = await self._call_tool(
            "tool_get_telegram_messages",
            {"limit": 20}
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("\n=== Telegram Messages ===")
        print(json.dumps(response, indent=2))
        
        # Check new format
        self.assertIn("success", response)
        self.assertIn("output", response)
        self.assertTrue(response["success"])

    async def test_get_restaurant_options(self):
        result = await self._call_tool(
            "tool_get_restaurant_menu_options",
            {}
        )

        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        print("\n=== Restaurant Menu Options ===")
        print(json.dumps(response, indent=2))
        
        # Check new format
        self.assertIn("success", response)
        self.assertTrue(response["success"])
        self.assertIn("output", response)
        self.assertIn("message", response["output"])
        self.assertIn("data", response["output"])

    async def test_get_menu_all(self):
        """Test getting all menu items"""
        result = await self._call_tool(
            "tool_get_menu",
            {"category": "all"}
        )
        
        self.assertTrue(result.content)
        response = json.loads(result.content[0].text)
        
        print("\n=== Full Menu ===")
        print(f"Message: {response['output']['message']}")
        print(f"Total items: {len(response['output']['data'])}")
        
        # Assertions
        self.assertTrue(response["success"])
        self.assertIn("output", response)
        self.assertIn("message", response["output"])
        self.assertIn("data", response["output"])
        self.assertIsInstance(response["output"]["data"], list)
        self.assertGreater(len(response["output"]["data"]), 0)

    async def test_get_menu_structure(self):
        """Test menu returns both message and data in new format"""
        result = await self._call_tool(
            "tool_get_menu",
            {"category": "Desserts"}
        )
        
        response = json.loads(result.content[0].text)
        
        print("\n=== MESSAGE (for display) ===")
        print(response["output"]["message"])
        
        print("\n=== DATA (structured) ===")
        print(json.dumps(response["output"]["data"], indent=2))
        
        # Assertions - new format
        self.assertTrue(response["success"])
        self.assertIn("output", response)
        self.assertIn("message", response["output"])
        self.assertIn("data", response["output"])
        self.assertIsInstance(response["output"]["data"], list)
        
        if len(response["output"]["data"]) > 0:
            first_item = response["output"]["data"][0]
            self.assertIn("name", first_item)
            self.assertIn("price", first_item)

    async def test_get_vegetarian_options(self):
        """Test vegetarian menu"""
        result = await self._call_tool(
            "tool_get_vegetarian_options",
            {}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Vegetarian Options ===")
        print(response["output"]["message"])
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)

    async def test_get_specials(self):
        """Test special dishes"""
        result = await self._call_tool(
            "tool_get_specials",
            {}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Today's Specials ===")
        print(response["output"]["message"])
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)

    async def test_get_gluten_free_items(self):
        """Test gluten-free items"""
        result = await self._call_tool(
            "tool_get_gluten_free_items",
            {}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Gluten-Free Options ===")
        print(response["output"]["message"])
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)

    async def test_get_desserts(self):
        """Test dessert menu"""
        result = await self._call_tool(
            "tool_get_desserts",
            {}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Desserts Menu ===")
        print(response["output"]["message"])
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)

    async def test_get_appetizers_under_price(self):
        """Test appetizers under specific price"""
        result = await self._call_tool(
            "tool_get_appetizers_under_price",
            {"max_price": 10.0}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Appetizers Under $10 ===")
        print(response["output"]["message"])
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)

    async def test_get_restaurant_location(self):
        """Test restaurant location"""
        result = await self._call_tool(
            "tool_get_restaurant_location",
            {}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Restaurant Location ===")
        print(response["output"]["message"])
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)
        self.assertIn("data", response["output"])

    async def test_is_restaurant_open(self):
        """Test restaurant open status"""
        result = await self._call_tool(
            "tool_is_restaurant_open",
            {}
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Restaurant Open Status ===")
        print(response["output"]["message"])
        print(f"Is Open: {response['output']['data']['is_open']}")
        
        self.assertTrue(response["success"])
        self.assertIn("output", response)
        self.assertIn("data", response["output"])
        self.assertIn("is_open", response["output"]["data"])

    async def test_send_menu_to_whatsapp(self):
        """Test sending menu via WhatsApp"""
        # Get menu first
        menu_result = await self._call_tool(
            "tool_get_menu",
            {"category": "Desserts"}
        )
        
        menu_response = json.loads(menu_result.content[0].text)
        
        # Send via WhatsApp
        send_result = await self._call_tool(
            "tool_send_whatsapp_message",
            {
                "phone_number": "918826173493",
                "message": menu_response["output"]["message"]
            }
        )
        
        send_response = json.loads(send_result.content[0].text)
        print("\n=== Menu Sent to WhatsApp ===")
        print(send_response["output"]["message"])
        
        self.assertTrue(send_response["success"])

    async def test_send_menu_to_telegram(self):
        """Test sending menu via Telegram"""
        # Get menu first
        menu_result = await self._call_tool(
            "tool_get_menu",
            {"category": "Appetizers"}
        )
        
        menu_response = json.loads(menu_result.content[0].text)
        
        # Send via Telegram
        send_result = await self._call_tool(
            "tool_send_telegram_message",
            {
                "chat_id": "952901992",
                "message": menu_response["output"]["message"]
            }
        )
        
        send_response = json.loads(send_result.content[0].text)
        print("\n=== Menu Sent to Telegram ===")
        print(send_response["output"]["message"])
        
        self.assertTrue(send_response["success"])

    async def test_place_order_simple(self):
        """Test placing order - simple return format"""
        
        result = await self._call_tool(
            "tool_restaurant_order_place_and_validate",
            {
                "phone_number": "918826173493",
                "table_number": "5",
                "item": "Pizza",
                "quantity": 2,
                "price": 12.99
            }
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Order Placed ===")
        print(json.dumps(response, indent=2))
        
        # Assertions
        self.assertTrue(response["success"])
        self.assertIn("output", response)
        self.assertIn("data", response["output"])
        
        # Check data structure
        data = response["output"]["data"]
        self.assertEqual(data["item"], "Pizza")
        self.assertEqual(data["quantity"], 2)
        self.assertEqual(data["price"], 12.99)
        
        # message should be None when no special instructions
        self.assertIsNone(response["output"]["message"])


    async def test_place_order_with_special_instructions(self):
        """Test placing order with special instructions"""
        
        result = await self._call_tool(
            "tool_restaurant_order_place_and_validate",
            {
                "phone_number": "918826173493",
                "table_number": "3",
                "item": "Spaghetti",
                "quantity": 1,
                "price": 15.99,
                "special_instructions": "Extra cheese, no onions"
            }
        )
        
        response = json.loads(result.content[0].text)
        print("\n=== Order with Special Instructions ===")
        print(json.dumps(response, indent=2))
        
        self.assertTrue(response["success"])
        
        # Check message contains special instructions
        self.assertEqual(response["output"]["message"], "Extra cheese, no onions")
        
        # Check data
        data = response["output"]["data"]
        self.assertEqual(data["item"], "Spaghetti")
        self.assertEqual(data["quantity"], 1)
        self.assertEqual(data["price"], 15.99)


if __name__ == "__main__":
    unittest.main()