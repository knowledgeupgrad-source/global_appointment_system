import os
import requests
from appointment_system.services.telegram_repo import save_sent_message


class TelegramClient:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_TOKEN").strip()

        if not self.bot_token:
            raise ValueError("TELEGRAM_TOKEN not set")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, chat_id: str, text: str) -> dict:
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload, timeout=10)
        save_sent_message(chat_id, text)
        response.raise_for_status()
        return response.json()

    def get_updates(self, limit: int = 20) -> list:
        from appointment_system.services.telegram_repo import save_telegram_message
        from appointment_system.services.telegram_offset import get_last_offset, save_last_offset

        last_offset = get_last_offset()
        url = f"{self.base_url}/getUpdates"
        params = {"limit": limit, "offset": last_offset + 1}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        updates = response.json().get("result", [])
        for update in updates:
            save_telegram_message(update)
            save_last_offset(update["update_id"])
        return updates
