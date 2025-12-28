import psycopg2
from datetime import datetime, UTC
from appointment_system.utils.postgres import get_connection

def save_telegram_message(update: dict):
    """Save incoming telegram message - creates user first, then conversation"""
    message = update.get("message")
    if not message:
        return None, None

    chat = message.get("chat", {})
    text = message.get("text")

    if not text:
        return None, None

    # Extract user info
    chat_id = str(chat.get("id"))
    username = chat.get("username") or f"user_{chat_id}"
    first_name = chat.get("first_name", "")
    last_name = chat.get("last_name", "")

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # STEP 1: Insert user first
        cursor.execute("""
            INSERT INTO users (userid, end_users_id, business_details, business_type, create_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (userid) DO NOTHING
        """, (
            username,
            chat_id,
            f"{first_name} {last_name}".strip(),
            "telegram",
            datetime.now(UTC)
        ))
        
        # STEP 2: Insert conversation
        conversation_id = str(update["update_id"])
        cursor.execute("""
            INSERT INTO conversation 
            (conversation_id, end_user_id, input_message, response_from, create_at, handled_by_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (conversation_id) DO NOTHING
        """, (
            conversation_id,
            chat_id,
            text,
            "telegram",
            datetime.now(UTC),
            None
        ))
        
        conn.commit()
        print(f"✓ Saved: {username} said '{text[:50]}'")
        
        return chat_id, conversation_id
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        return None, None
        
    finally:
        cursor.close()
        conn.close()


def save_sent_message(chat_id: str, text: str, conversation_id: str = None):
    """Save sent message to output_message field"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if conversation_id:
            # Update existing conversation by ID
            cursor.execute("""
                UPDATE conversation 
                SET output_message = %s 
                WHERE conversation_id = %s
            """, (text, conversation_id))
        else:
            # Find and update most recent conversation for this user
            cursor.execute("""
                UPDATE conversation 
                SET output_message = %s 
                WHERE conversation_id = (
                    SELECT conversation_id 
                    FROM conversation 
                    WHERE end_user_id = %s 
                    AND output_message IS NULL
                    ORDER BY create_at DESC 
                    LIMIT 1
                )
            """, (text, chat_id))
        
        conn.commit()
        print(f"✓ Saved sent message to {chat_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error saving sent message: {e}")
        
    finally:
        cursor.close()
        conn.close()
