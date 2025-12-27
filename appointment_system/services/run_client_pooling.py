import time
from appointment_system.services.telegram_client import TelegramClient

tg = TelegramClient()

while True:
    tg.get_updates()
    time.sleep(2)
