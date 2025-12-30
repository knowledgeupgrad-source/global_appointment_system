import json
from appointment_system.utils.logger import logger

def get_restaurant_menu_options() -> str:
    """Returns list of available restaurant information queries"""
    try:
        logger.info("Fetching restaurant menu options")
        
        message = """🍽️ *WHAT WOULD YOU LIKE TO KNOW?* 🍽️

Please choose from the following options:

1️⃣ What's on the menu today?
2️⃣ Do you have vegetarian options?
3️⃣ What are your specials?
4️⃣ Do you have gluten-free items?
5️⃣ What desserts do you have?
6️⃣ Show me appetizers under $10
7️⃣ Where is your restaurant located?
8️⃣ Is restaurant open today?

Just reply with the number or question! 😊"""

        data = {
            "options": [
                {"id": 1, "text": "What's on the menu today?"},
                {"id": 2, "text": "Do you have vegetarian options?"},
                {"id": 3, "text": "What are your specials?"},
                {"id": 4, "text": "Do you have gluten-free items?"},
                {"id": 5, "text": "What desserts do you have?"},
                {"id": 6, "text": "Show me appetizers under $10"},
                {"id": 7, "text": "Where is your restaurant located?"},
                {"id": 8, "text": "Is restaurant open today?"}
            ]
        }
        
        return json.dumps({
            "success": True,
            "output":{"message": message,
            "data": data},
            "error": None
        }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching options: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)