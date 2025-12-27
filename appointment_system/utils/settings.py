from __future__ import annotations
import os
import secrets
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file into os.environ
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

@dataclass
class Settings:
    _instance = None

    env = os.environ.get('ENV', 'local')
    
    # Database Configuration
    agent_db_host = os.environ.get('DB_HOST', 'localhost')
    agent_db_name = os.environ.get('DB_NAME', 'appointments_db')
    agent_db_user = os.environ.get('DB_USER', 'postgres')
    agent_db_password = os.environ.get('DB_PASSWORD', 'postgres')
    agent_db_port = int(os.environ.get('DB_PORT', '5432'))
    
    # WhatsApp Configuration
    whatsapp_phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    whatsapp_access_token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    whatsapp_verify_token = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'my_simple_verify_token_123')
    whatsapp_api_version = os.environ.get('WHATSAPP_API_VERSION', 'v22.0')
    
    telegram_bot_token = os.environ.get('TELEGRAM_TOKEN')
     # LLM Configuration (for future AI enhancements)
    llm_type = os.environ.get('LLM_TYPE', 'openai')
    llm_model = os.environ.get('LLM_MODEL', 'gpt-4')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    openai_endpoint = os.environ.get('OPENAI_ENDPOINT')
    openai_api_version = os.environ.get('OPENAI_API_VERSION')
    
    # Application Configuration
    logging_level = os.environ.get('LOGGING_LEVEL', 'DEBUG')
    app_name = os.environ.get('APP_NAME', 'WhatsApp Appointment System')
    flask_host = os.environ.get('FLASK_HOST', '0.0.0.0')
    flask_port = int(os.environ.get('FLASK_PORT', '5000'))
    flask_debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Appointment Configuration
    max_appointments_per_day = int(os.environ.get('MAX_APPOINTMENTS_PER_DAY', '50'))
    appointment_duration_minutes = int(os.environ.get('APPOINTMENT_DURATION_MINUTES', '30'))
    business_hours_start = os.environ.get('BUSINESS_HOURS_START', '09:00')
    business_hours_end = os.environ.get('BUSINESS_HOURS_END', '17:00')
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.value = secrets.randbelow(100)
        return cls._instance
SETTINGS = Settings()