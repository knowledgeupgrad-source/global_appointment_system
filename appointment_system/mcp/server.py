from __future__ import annotations
import os
from appointment_system.utils.logger import logger
from mcp.server.fastmcp import FastMCP
from appointment_system.utils.postgres import get_connection
from appointment_system.services.whatsapp_communication import WhatsAppClient
import json
import traceback
import logging
from flask import Blueprint, request
from appointment_system.utils.logger import logger
from appointment_system.services.whatsapp_communication import WhatsAppClient
from appointment_system.services.telegram_client import TelegramClient
from starlette.requests import Request
from starlette.responses import JSONResponse



webhook_bp = Blueprint("whatsapp_webhook", __name__)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

mcp = FastMCP("appointment_system")
whatsapp = WhatsAppClient()
telegram = TelegramClient()

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "ok"})
@mcp.tool(description="Send a Telegram message to a user or group.")
def send_telegram_message(chat_id: str, message: str) -> str:
    """
    Send a Telegram message using bot API
    """
    try:
        logger.info(f"Sending Telegram message to {chat_id}: {message}")

        result = telegram.send_message(
            chat_id=chat_id,
            text=message
        )

        return json.dumps({
            "success": True,
            "result": result
        }, indent=2)

    except Exception as e:
        logger.error("Error sending Telegram message", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e)
        })
@mcp.tool(description="Fetch new Telegram messages and save to database.")
def get_telegram_messages(limit: int = 20) -> str:
    """
    Fetch updates/messages from Telegram bot and save to database
    
    Args:
        limit: Maximum number of messages to fetch
    """
    try:
        logger.info(f"Fetching {limit} Telegram messages")

        updates, saved_messages = telegram.get_updates(limit=limit)

        # Format message details
        messages = []
        for update in updates:
            if "message" in update:
                msg = update["message"]
                messages.append({
                    "update_id": update.get("update_id"),
                    "chat_id": msg["chat"]["id"],
                    "username": msg.get("from", {}).get("username"),
                    "first_name": msg.get("from", {}).get("first_name"),
                    "text": msg.get("text"),
                    "timestamp": msg.get("date")
                })

        return json.dumps({
            "success": True,
            "messages_fetched": len(updates),
            "messages_saved": len(saved_messages),
            "messages": messages
        }, indent=2)

    except Exception as e:
        logger.error(f"Error fetching Telegram messages: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "messages": []
        })





@mcp.tool(description="Fetch unprocessed WhatsApp messages from conversation table by phone number.")
def get_whatsapp_messages(phone_number: str, limit: int = 50) -> str:
    try:
        logger.info(f"Fetching WhatsApp messages for {phone_number}")

        phone_number = phone_number.lstrip('+')

        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id,
                       end_user_mobile_number,
                       conversation_id,
                       input_message,
                       response_from,
                       created_at
                FROM conversation
                WHERE end_user_mobile_number = %s
                  AND response_from = 'customer'
                  AND processed = FALSE
                ORDER BY created_at ASC
                LIMIT %s
            """, (phone_number, limit))

            rows = cur.fetchall()

            messages = []
            for row in rows:
                conv_id, phone, msg_id, text, sender, created_at = row
                messages.append({
                    "db_id": str(conv_id),
                    "message_id": msg_id,
                    "phone_number": phone,
                    "message": text,
                    "timestamp": str(created_at)
                })

            return json.dumps({
                "success": True,
                "messages_count": len(messages),
                "messages": messages
            }, indent=2)

    except Exception as e:
        logger.error("Error fetching WhatsApp messages", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "messages": []
        })


@mcp.tool(description="Send WhatsApp message to a customer. Use this to send appointment confirmations, reminders, or any other communication.")
def send_whatsapp_message(phone_number: str, message: str) -> str:
    """
    Send a WhatsApp message to a customer
    
    Args:
        phone_number: Customer phone number with country code (e.g., "918826173493")
        message: Message text to send to the customer
    
    Returns:
        JSON string with result containing success status and message_id or error
    """
    try:
        logger.info(f"Sending WhatsApp message to {phone_number}: {message}")
        
        result = whatsapp.send_message(phone_number, message)
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}", exc_info=True)
        logger.error(traceback.format_exc())
        return json.dumps({
            "success": False,
            "error": str(e)
        })
if __name__ == "__main__":
    env = os.environ.get("ENV", "local")
    #env = 'local1'
    if env == "local":
        mcp.run(transport="stdio")
    else:
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = 8000
        mcp.run(transport="streamable-http")
