# services/user_repo.py
from datetime import datetime, UTC
from appointment_system.utils.postgres import get_connection

def create_user_if_not_exists(user_id: str, username: str = None, first_name: str = None):
    """Create user if they don't exist"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM users WHERE end_users_id = %s", (user_id,))
        
        if cursor.fetchone():
            cursor.close()
            return  # User already exists
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (end_users_id, username, first_name, created_at)
            VALUES (%s, %s, %s, %s)
        """, (user_id, username, first_name, datetime.now(UTC)))
        
        cursor.close()
        print(f"✓ Created new user: {user_id}")