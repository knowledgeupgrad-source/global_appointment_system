import json
from appointment_system.utils.logger import logger
from appointment_system.services.telegram_client import TelegramClient

telegram = TelegramClient()

def get_telegram_messages(limit: int = 20) -> str:
    """Fetch updates/messages from Telegram bot and save to database"""
    try:
        logger.info(f"Fetching {limit} Telegram messages")
        updates, saved_messages = telegram.get_updates(limit=limit)
        
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
            "output":{"message": f"Fetched {len(updates)} messages, saved {len(saved_messages)} to database",
            "data": {
                "messages_fetched": len(updates),
                "messages_saved": len(saved_messages),
                "messages": messages
            }},
            "error": None
        }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching Telegram messages: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)