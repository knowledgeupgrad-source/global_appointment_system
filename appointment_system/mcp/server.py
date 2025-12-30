# appointment_system/mcp/server.py

from __future__ import annotations
import os
import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Import all tools
from appointment_system.tools import (
    # Messaging tools
    send_telegram_message,
    get_telegram_message,
    send_whatsapp_message,
    get_whatsapp_message,
    
    # Restaurant tools
    get_restaurant_menu_options,
    get_menu,
    get_vegetarian_options,
    get_specials,
    get_gluten_free_items,
    get_desserts,
    get_appetizers_under_price,
    get_restaurant_location,
    is_restaurant_open,
    restaurant_order_place_and_validate
)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

mcp = FastMCP("appointment_system")

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "ok"})

# Register Messaging Tools
@mcp.tool(description="Send a Telegram message to a user or group.")
def tool_send_telegram_message(chat_id: str, message: str) -> str:
    return send_telegram_message(chat_id, message)

@mcp.tool(description="Fetch new Telegram messages and save to database.")
def tool_get_telegram_messages(limit: int = 20) -> str:
    return get_telegram_message(limit)

@mcp.tool(description="Send WhatsApp message to a customer.")
def tool_send_whatsapp_message(phone_number: str, message: str) -> str:
    return send_whatsapp_message(phone_number, message)

@mcp.tool(description="Fetch unprocessed WhatsApp messages from conversation table by phone number.")
def tool_get_whatsapp_messages(phone_number: str, limit: int = 50) -> str:
    return get_whatsapp_message(phone_number, limit)

# Register Restaurant Tools
@mcp.tool(description="Get list of available restaurant queries/options")
def tool_get_restaurant_menu_options() -> str:
    return get_restaurant_menu_options()

@mcp.tool(description="Get restaurant menu with formatted message and structured data")
def tool_get_menu(category: str = "all") -> str:
    return get_menu(category)

@mcp.tool(description="Get vegetarian menu items")
def tool_get_vegetarian_options() -> str:
    return get_vegetarian_options()

@mcp.tool(description="Get today's special dishes")
def tool_get_specials() -> str:
    return get_specials()

@mcp.tool(description="Get gluten-free menu items")
def tool_get_gluten_free_items() -> str:
    return get_gluten_free_items()

@mcp.tool(description="Get dessert menu")
def tool_get_desserts() -> str:
    return get_desserts()

@mcp.tool(description="Get appetizers under a specific price")
def tool_get_appetizers_under_price(max_price: float = 10.0) -> str:
    return get_appetizers_under_price(max_price)

@mcp.tool(description="Get restaurant location and address")
def tool_get_restaurant_location() -> str:
    return get_restaurant_location()

@mcp.tool(description="Check if restaurant is open today")
def tool_is_restaurant_open() -> str:
    return is_restaurant_open()


@mcp.tool(description="Place a restaurant order for a single item")
def tool_restaurant_order_place_and_validate(
    phone_number: str,
    table_number: str,
    item: str,
    quantity: int,
    price: float,
    special_instructions: str = ""
) -> str:
    return restaurant_order_place_and_validate(
        phone_number=phone_number,
        table_number=table_number,
        item=item,
        quantity=quantity,
        price=price,
        special_instructions=special_instructions
    )

if __name__ == "__main__":
    env = os.environ.get("ENV", "local")
    if env == "local":
        mcp.run(transport="stdio")
    else:
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = 8000
        mcp.run(transport="streamable-http")