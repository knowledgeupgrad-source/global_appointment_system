import requests
import os
from appointment_system.utils.logger import logger


class TelegramClient1:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_TOKEN not set")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, chat_id: str, text: str) -> dict:
        """
        Send message to Telegram chat/user
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        return response.json()

    def get_updates(self, limit: int = 20) -> list:
        """
        Fetch messages received by bot
        """
        url = f"{self.base_url}/getUpdates"
        params = {
            "limit": limit
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return data.get("result", [])
