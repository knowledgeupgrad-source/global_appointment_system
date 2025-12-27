import requests
import os
from ..utils.settings import SETTINGS
from ..utils.logger import logger
from ..utils.postgres import get_connection
from datetime import datetime
from ..utils.db_queries import get_values, save_values

class WhatsAppClient:
    def __init__(self):
        self.phone_number_id = SETTINGS.whatsapp_phone_number_id
        self.access_token = SETTINGS.whatsapp_access_token
        self.api_version = SETTINGS.whatsapp_api_version 
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.db = get_connection()
    
    def send_message_from_whatsapp(self, to: str, message: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        # Normalize phone number (remove + if present)
        to = to.lstrip('+')
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            message_id = result['messages'][0]['id']
            data = {
                "end_user_id": to,
                "end_user_mobile_number": to,
                "conversation_id": message_id,
                "input_message": message,
                "response_from": "sent",
                "created_at": datetime.utcnow(),
                "output_message": "",
                "handle_by_admin":True
            }
            save_values("conversaion", data, schema="appointment_management_system")
            # Log message to database
            self._log_message(to, message, message_id, 'outgoing', 'sent')
            
            logger.info(f"Message sent to {to}: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "to": to
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                except:
                    error_msg = e.response.text or str(e)
            
            logger.error(f"Failed to send message to {to}: {error_msg}")
            
            # Log failed message
            self._log_message(to, message, None, 'outgoing', 'failed')
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_messages_from_api_from_whatsapp(self, phone_number: str, limit: int = 50) -> dict:
        try:
            # Normalize phone number
            phone_number = phone_number.lstrip('+')
            # Get messages from database which logs all incoming messages from webhooks
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, phone_number, message_body, message_id, message_type, status, created_at
                    FROM whatsapp_messages
                    WHERE phone_number = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (phone_number, limit))
                
                results = cur.fetchall()
                
                messages = []
                for row in results:
                    msg_id, phone, body, whatsapp_id, msg_type, status, created_at = row
                    messages.append({
                        "id": str(msg_id),
                        "phone_number": phone,
                        "message_body": body,
                        "message_id": whatsapp_id,
                        "message_type": msg_type,
                        "status": status,
                        "received_at": str(created_at)
                    })
                
                logger.info(f"Retrieved {len(messages)} messages for {phone_number}")
                
                return {
                    "success": True,
                    "phone_number": phone_number,
                    "messages_count": len(messages),
                    "messages": messages
                }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to fetch messages: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }