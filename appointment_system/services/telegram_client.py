import os
import requests
from appointment_system.services.telegram_repo import save_telegram_message, save_sent_message


class TelegramClient:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_TOKEN").strip()

        if not self.bot_token:
            raise ValueError("TELEGRAM_TOKEN not set")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, chat_id: str, text: str, conversation_id: str = None) -> dict:
        """Send message and optionally update conversation"""
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        # Save sent message to database
        save_sent_message(chat_id, text, conversation_id)
        
        return response.json()

    def get_updates(self, limit: int = 20) -> list:
        """Fetch and save new messages from Telegram"""
        from appointment_system.services.telegram_offset import get_last_offset, save_last_offset

        last_offset = get_last_offset()
        url = f"{self.base_url}/getUpdates"
        params = {"limit": limit, "offset": last_offset + 1}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        updates = response.json().get("result", [])
        
        saved_messages = []
        for update in updates:
            chat_id, conv_id = save_telegram_message(update)
            if chat_id and conv_id:
                saved_messages.append({
                    "chat_id": chat_id,
                    "conversation_id": conv_id,
                    "update_id": update["update_id"]
                })
            save_last_offset(update["update_id"])
        
        return updates, saved_messages