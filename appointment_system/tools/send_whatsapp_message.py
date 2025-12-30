import json
from appointment_system.utils.logger import logger
from appointment_system.services.whatsapp_communication import WhatsAppClient

whatsapp = WhatsAppClient()

def send_whatsapp_message(phone_number: str, message: str) -> str:
    """Send a WhatsApp message to a customer"""
    try:
        logger.info(f"Sending WhatsApp message to {phone_number}")
        result = whatsapp.send_message(phone_number, message)
        
        return json.dumps({
            "success": result.get("success", False),
            "output":{"message": f"Message sent to {phone_number}" if result.get("success") else "Failed to send message",
            "data": result},
            "error": result.get("error") if not result.get("success") else None
        }, indent=2)
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)