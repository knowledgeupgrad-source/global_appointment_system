import json
from datetime import datetime, timedelta
from appointment_system.utils.postgres import AppointmentDB
from appointment_system.utils.logger import logger
from utils.db_queries import get_values, save_values


class AppointmentHandler:
    """
    Handles appointment booking conversation flow and business logic
    """
    
    def __init__(self):
        self.db = AppointmentDB()
    def _create_appointment(self, phone_number: str, customer_name: str, appointment_datetime: str) -> str:
        """Create appointment in database"""
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO appointments (phone_number, customer_name, appointment_date, appointment_type, status)
                    VALUES (%s, %s, %s, 'consultation', 'confirmed')
                    RETURNING id
                """, (phone_number, customer_name, appointment_datetime))
                
                result = cur.fetchone()
                conn.commit()
                
                if result:
                    return str(result[0])[:8]  # Return first 8 chars of UUID
        
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
        
        return None
    
    def get_appointments(self, phone_number: str) -> list:
        """Get appointments for a phone number"""
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, customer_name, appointment_date, appointment_type, status, notes
                    FROM appointments
                    WHERE phone_number = %s
                    ORDER BY appointment_date DESC
                """, (phone_number,))
                
                results = cur.fetchall()
                
                appointments = []
                for row in results:
                    apt_id, name, date, apt_type, status, notes = row
                    appointments.append({
                        "id": str(apt_id),
                        "customer_name": name,
                        "appointment_date": str(date),
                        "appointment_type": apt_type,
                        "status": status,
                        "notes": notes
                    })
                
                return appointments
        
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
    
    def get_available_slots(self, date: str = None) -> list:
        """Get available slots"""
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                if date:
                    cur.execute("""
                        SELECT slot_date, slot_time, max_capacity, current_bookings
                        FROM appointment_slots
                        WHERE slot_date = %s
                        AND is_available = TRUE
                        AND current_bookings < max_capacity
                        ORDER BY slot_time
                    """, (date,))
                else:
                    cur.execute("""
                        SELECT slot_date, slot_time, max_capacity, current_bookings
                        FROM appointment_slots
                        WHERE slot_date >= CURRENT_DATE
                        AND is_available = TRUE
                        AND current_bookings < max_capacity
                        ORDER BY slot_date, slot_time
                        LIMIT 20
                    """)
                
                results = cur.fetchall()
                
                slots = []
                for row in results:
                    slot_date, slot_time, max_capacity, current_bookings = row
                    slots.append({
                        "date": str(slot_date),
                        "time": str(slot_time)[:5],
                        "available_capacity": max_capacity - current_bookings
                    })
                
                return slots
        
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
        
    