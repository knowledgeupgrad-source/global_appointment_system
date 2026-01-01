import json
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def get_whatsapp_message(phone_number: str, limit: int = 50) -> str:
    """Fetch unprocessed WhatsApp messages"""
    try:
        logger.info(f"Fetching WhatsApp messages for {phone_number}")
        phone_number = phone_number.lstrip('+')
        
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, end_user_mobile_number, conversation_id,
                       input_message, response_from, created_at
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
                "ouput":{"message": f"Found {len(messages)} unprocessed messages for {phone_number}",
                "data": {
                    "messages_count": len(messages),
                    "messages": messages
                }},
                "error": None
            }, indent=2)
    except Exception as e:
        logger.error("Error fetching WhatsApp messages", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)