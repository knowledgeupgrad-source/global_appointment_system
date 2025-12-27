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


webhook_bp = Blueprint("whatsapp_webhook", __name__)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

mcp = FastMCP("appointment_system")
db = get_connection()
whatsapp = WhatsAppClient()
telegram = TelegramClient()

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
@mcp.tool(description="Fetch latest Telegram messages received by the bot.")
def get_telegram_messages(limit: int = 20) -> str:
    """
    Fetch updates/messages from Telegram bot
    """
    try:
        logger.info("Fetching Telegram messages")

        updates = telegram.get_updates(limit=limit)

        messages = []
        for update in updates:
            if "message" in update:
                msg = update["message"]
                messages.append({
                    "update_id": update.get("update_id"),
                    "chat_id": msg["chat"]["id"],
                    "from": msg.get("from", {}).get("username"),
                    "text": msg.get("text"),
                    "timestamp": msg.get("date")
                })

        return json.dumps({
            "success": True,
            "messages_count": len(messages),
            "messages": messages
        }, indent=2)

    except Exception as e:
        logger.error("Error fetching Telegram messages", exc_info=True)
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

        conn = db.get_connection()
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




@mcp.tool(description="Create a new appointment for a customer.")
def create_appointment(phone_number: str, customer_name: str, appointment_date: str, appointment_type: str = "consultation", notes: str = None) -> str:
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO appointments (phone_number, customer_name, appointment_date, appointment_type, notes, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
                RETURNING id, phone_number, customer_name, appointment_date, appointment_type, status
            """, (phone_number, customer_name, appointment_date, appointment_type, notes))
            
            result = cur.fetchone()
            conn.commit()
            
            if result:
                appointment_id, phone, name, date, apt_type, status = result
                
                return json.dumps({
                    "success": True,
                    "appointment": {
                        "id": str(appointment_id),
                        "phone_number": phone,
                        "customer_name": name,
                        "appointment_date": str(date),
                        "appointment_type": apt_type,
                        "status": status
                    }
                }, indent=2)
    
    except Exception as e:
        logger.error(f"Error creating appointment: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool(description="Get available appointment slots for booking.")
def get_available_slots(date: str = None) -> str:
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            if date:
                cur.execute("""
                    SELECT id, slot_date, slot_time, max_capacity, current_bookings
                    FROM appointment_slots
                    WHERE slot_date = %s AND is_available = TRUE
                    AND current_bookings < max_capacity
                    ORDER BY slot_time
                """, (date,))
            else:
                cur.execute("""
                    SELECT id, slot_date, slot_time, max_capacity, current_bookings
                    FROM appointment_slots
                    WHERE slot_date >= CURRENT_DATE AND is_available = TRUE
                    AND current_bookings < max_capacity
                    ORDER BY slot_date, slot_time
                    LIMIT 20
                """)
            
            results = cur.fetchall()
            
            slots = []
            for row in results:
                slot_id, slot_date, slot_time, max_capacity, current_bookings = row
                slots.append({
                    "id": str(slot_id),
                    "date": str(slot_date),
                    "time": str(slot_time),
                    "available_capacity": max_capacity - current_bookings
                })
            
            return json.dumps({
                "success": True,
                "slots_count": len(slots),
                "slots": slots
            }, indent=2)
    
    except Exception as e:
        logger.error(f"Error getting available slots: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "slots": []
        })


@mcp.tool(description="Update appointment status (pending, confirmed, cancelled, completed).")
def update_appointment_status(appointment_id: str, status: str) -> str:
    try:
        valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed']
        if status not in valid_statuses:
            return json.dumps({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })
        
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE appointments
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, status
            """, (status, appointment_id))
            
            result = cur.fetchone()
            conn.commit()
            
            if result:
                apt_id, new_status = result
                return json.dumps({
                    "success": True,
                    "appointment_id": str(apt_id),
                    "new_status": new_status
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": "Appointment not found"
                })
    
    except Exception as e:
        logger.error(f"Error updating appointment status: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool(description="Save or update conversation state for a customer to track booking flow.")
def save_conversation_state(phone_number: str, current_step: str, context: str) -> str:
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO appointment_management_system.conversation(phone_number, current_step, context, last_interaction)
                VALUES (%s, %s, %s::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (phone_number)
                DO UPDATE SET
                    current_step = EXCLUDED.current_step,
                    context = EXCLUDED.context,
                    last_interaction = CURRENT_TIMESTAMP
                RETURNING id
            """, (phone_number, current_step, context))
            
            result = cur.fetchone()
            conn.commit()
            
            return json.dumps({
                "success": True,
                "conversation_id": str(result[0])
            }, indent=2)
    
    except Exception as e:
        logger.error(f"Error saving conversation state: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool(description="Get current conversation state for a customer.")
def get_conversation_state(phone_number: str) -> str:
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT current_step, context, last_interaction
                FROM conversation_state
                WHERE phone_number = %s
            """, (phone_number,))
            
            result = cur.fetchone()
            
            if result:
                step, context, last_interaction = result
                return json.dumps({
                    "success": True,
                    "conversation_state": {
                        "current_step": step,
                        "context": context,
                        "last_interaction": str(last_interaction)
                    }
                }, indent=2)
            else:
                return json.dumps({
                    "success": True,
                    "conversation_state": None
                }, indent=2)
    
    except Exception as e:
        logger.error(f"Error getting conversation state: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    env = os.environ.get("ENV", "local")
    if env == "local":
        mcp.run(transport="stdio")
    else:
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = 8000
        mcp.run(transport="stramable-http")
