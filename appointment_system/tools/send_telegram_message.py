import json
from appointment_system.utils.logger import logger
from appointment_system.services.telegram_client import TelegramClient

telegram = TelegramClient()

def send_telegram_message(chat_id: str, message: str) -> str:
    """Send a Telegram message using bot API"""
    try:
        logger.info(f"Sending Telegram message to {chat_id}: {message}")
        result = telegram.send_message(chat_id=chat_id, text=message)
        
        return json.dumps({
            "success": True,
            "output":{"message": f"Message sent successfully to {chat_id}",
            "data": result},
            "error": None
        }, indent=2)
    except Exception as e:
        logger.error("Error sending Telegram message", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)