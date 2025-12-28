import unittest
import json
import os


class TestMessagingTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.transport_mode = os.getenv("MCP_TRANSPORT_MODE", "stdio")

        if self.transport_mode == "sse":
            self.server_url = os.getenv(
                "MCP_SERVER_URL", "http://localhost:8000"
            )
        else:
            self.server_script = "appointment_system/mcp/server.py"
    def _get_client_params(self):
        from appointment_system.mcp.client import MCPClient

        if self.transport_mode == "sse":
            return {"sse_url": self.server_url}
        else:
            return {"serverFile": self.server_script}

    async def test_get_all_tools(self):
        from appointment_system.mcp.client import MCPClient

        async with MCPClient(**self._get_client_params()) as client:
            tools = await client.get_tools()
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
        from appointment_system.mcp.client import MCPClient

        phone_number = "918826173493"
        message = "Hello, which time would you like to book an appointment?"

        async with MCPClient(**self._get_client_params()) as client:
            result = await client.call_tool(
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
        from appointment_system.mcp.client import MCPClient

        phone_number = "918826173493"

        async with MCPClient(**self._get_client_params()) as client:
            result = await client.call_tool(
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

    # --------------------------------------------------
    # TELEGRAM TESTS
    # --------------------------------------------------
    async def test_send_telegram_message(self):
        from appointment_system.mcp.client import MCPClient

        chat_id = "952901992"   
        message = "Hi, we have discussed today, we will start. don't worry."

        async with MCPClient(**self._get_client_params()) as client:
            result = await client.call_tool(
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
        from appointment_system.mcp.client import MCPClient

        async with MCPClient(**self._get_client_params()) as client:
            # Fetch new messages
            result = await client.call_tool(
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
