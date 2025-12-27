import psycopg2
from datetime import datetime, UTC
from appointment_system.utils.postgres import get_connection

def save_telegram_message(update: dict):
    """Save telegram message - creates user first, then conversation"""
    message = update.get("message")
    if not message:
        return

    chat = message.get("chat", {})
    text = message.get("text")

    if not text:
        return

    # Extract user info
    chat_id = str(chat.get("id"))
    username = chat.get("username") or f"user_{chat_id}"
    first_name = chat.get("first_name", "")
    last_name = chat.get("last_name", "")

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # STEP 1: Insert user first (required for FK)
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
        cursor.execute("""
            INSERT INTO conversation 
            (conversation_id, end_user_id, input_message, response_from, create_at, handled_by_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (conversation_id) DO NOTHING
        """, (
            str(update["update_id"]),
            chat_id,
            text,
            "telegram",
            datetime.now(UTC),
            None  # No admin assigned initially
        ))
        
        conn.commit()
        print(f"✓ Saved: {username} said '{text[:50]}'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        
    finally:
        cursor.close()
        conn.close()

def save_sent_message(chat_id: str, message_text: str):
    """Save telegram message - creates user first, then conversation"""

    text = message_text

    if not text:
        return

    # Extract user info
    chat_id = chat_id

    conn = get_connection()
    cursor = conn.cursor()
    
    try:        
        cursor.execute("""
            UPDATE conversation
            SET
                output_message = %s,
                handled_by_admin = %s
            WHERE end_user_id = %s
            """, (
            text,          # output message
            None,
            chat_id
            ))

        
        conn.commit()
        print(f"✓ Saved: {chat_id} said '{text[:50]}'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        
    finally:
        cursor.close()
        conn.close()



# Query conversations
def get_all_conversations():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM conversation ORDER BY create_at DESC")
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rows


# ============ USER FUNCTIONS ============

def get_user_by_chat_id(chat_id: str):
    """Get user info"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE end_users_id = %s", (chat_id,))
    row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return row


def get_all_users():
    """Get all users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY create_at DESC")
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rows


# ============ ADMIN FUNCTIONS ============

def create_admin(user_id: str, password: str):
    """Create admin user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO admin (user_id, user_pass, created_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, password, datetime.now(UTC)))
        
        conn.commit()
        print(f"✓ Admin created: {user_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        
    finally:
        cursor.close()
        conn.close()


def assign_conversation_to_admin(conversation_id: str, admin_user_id: str):
    """Assign conversation to admin"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE conversation 
            SET handled_by_admin = %s 
            WHERE conversation_id = %s
        """, (admin_user_id, conversation_id))
        
        conn.commit()
        print(f"✓ Assigned conversation {conversation_id} to {admin_user_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        
    finally:
        cursor.close()
        conn.close()


def get_all_admins():
    """Get all admins"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, created_at, last_login FROM admin")
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rows


# ============ APPOINTMENT FUNCTIONS ============

def create_appointment_slot(slot_time: datetime, admin_user_id: str):
    """Create new appointment slot (admin only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO appointment_slot (slot_time, is_available, created_by_admin)
            VALUES (%s, %s, %s)
            RETURNING slot_id
        """, (slot_time, True, admin_user_id))
        
        slot_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✓ Created slot {slot_id} at {slot_time}")
        return slot_id
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        return None
        
    finally:
        cursor.close()
        conn.close()


def book_appointment(slot_id: int, chat_id: str):
    """Book appointment for user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if slot is available
        cursor.execute("""
            SELECT is_available, end_user_id 
            FROM appointment_slot 
            WHERE slot_id = %s
        """, (slot_id,))
        
        result = cursor.fetchone()
        
        if not result:
            print(f"✗ Slot {slot_id} not found")
            return False
        
        if not result[0] or result[1]:
            print(f"✗ Slot {slot_id} already booked")
            return False
        
        # Book the slot
        cursor.execute("""
            UPDATE appointment_slot 
            SET end_user_id = %s, is_available = FALSE, booked_at = %s
            WHERE slot_id = %s
        """, (chat_id, datetime.now(UTC), slot_id))
        
        conn.commit()
        print(f"✓ Booked slot {slot_id} for user {chat_id}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()


def get_available_slots():
    """Get all available appointment slots"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT slot_id, slot_time, created_by_admin
        FROM appointment_slot 
        WHERE is_available = TRUE 
        AND slot_time > NOW()
        ORDER BY slot_time ASC
    """)
    
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rows


def get_user_appointments(chat_id: str):
    """Get all appointments for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT slot_id, slot_time, booked_at
        FROM appointment_slot 
        WHERE end_user_id = %s
        ORDER BY slot_time DESC
    """, (chat_id,))
    
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rows


def cancel_appointment(slot_id: int):
    """Cancel appointment and make slot available again"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE appointment_slot 
            SET end_user_id = NULL, is_available = TRUE, booked_at = NULL
            WHERE slot_id = %s
        """, (slot_id,))
        
        conn.commit()
        print(f"✓ Cancelled appointment for slot {slot_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        
    finally:
        cursor.close()
        conn.close()