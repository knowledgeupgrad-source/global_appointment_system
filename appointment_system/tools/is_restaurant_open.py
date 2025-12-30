import json
from datetime import datetime
from appointment_system.utils.logger import logger

def is_restaurant_open() -> str:
    """Check restaurant opening status"""
    try:
        logger.info("Checking restaurant status")
        
        now = datetime.now()
        current_day = now.strftime("%A")
        current_time = now.strftime("%H:%M")
        
        schedule = {
            "Monday": {"open": "11:00", "close": "22:00"},
            "Tuesday": {"open": "11:00", "close": "22:00"},
            "Wednesday": {"open": "11:00", "close": "22:00"},
            "Thursday": {"open": "11:00", "close": "22:00"},
            "Friday": {"open": "11:00", "close": "23:00"},
            "Saturday": {"open": "11:00", "close": "23:00"},
            "Sunday": {"open": "12:00", "close": "21:00"}
        }
        
        today_schedule = schedule.get(current_day, {})
        open_time = today_schedule.get("open", "11:00")
        close_time = today_schedule.get("close", "22:00")
        
        is_open = open_time <= current_time <= close_time
        
        if is_open:
            message = f"""✅ *YES, WE'RE OPEN!* ✅

🕐 Today's Hours: {open_time} - {close_time}
⏰ Current Time: {current_time}

We're happy to serve you! 🍽️

📞 Call: +1 (555) 123-4567"""
        else:
            message = f"""❌ *SORRY, WE'RE CLOSED* ❌

🕐 Today's Hours: {open_time} - {close_time}
⏰ Current Time: {current_time}

We'll be open again tomorrow!

📅 *Full Schedule:*
Mon-Thu: 11:00 AM - 10:00 PM
Fri-Sat: 11:00 AM - 11:00 PM
Sunday: 12:00 PM - 9:00 PM"""

        data = {
            "is_open": is_open,
            "current_day": current_day,
            "current_time": current_time,
            "opening_time": open_time,
            "closing_time": close_time,
            "schedule": schedule
        }
        
        return json.dumps({
            "success": True,
            "output":{"message": message,
            "data": data},
            "error": None
        }, indent=2)
    except Exception as e:
        logger.error(f"Error checking restaurant status: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)