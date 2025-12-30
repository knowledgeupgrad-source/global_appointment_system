import json
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def get_menu(category: str = "all") -> str:
    """
    Get restaurant menu items
    
    Args:
        category: Filter by category - options: all, Appetizers, Mains, Desserts, Drinks
    """
    try:
        logger.info(f"Fetching menu - category: {category}")
        
        conn = get_connection()
        with conn.cursor() as cur:
            if category.lower() == "all":
                cur.execute("""
                    SELECT name, category, price
                    FROM restaurant.menu_items
                    WHERE is_available = TRUE
                    ORDER BY category, name
                """)
            else:
                cur.execute("""
                    SELECT name, category, price
                    FROM restaurant.menu_items
                    WHERE is_available = TRUE AND category = %s
                    ORDER BY name
                """, (category,))
            
            rows = cur.fetchall()
            
            if not rows:
                return json.dumps({
                    "success": True,
                    "output":{"message": f"Sorry, no items available in {category} category right now. 😔",
                    "data": []},
                    "error": None
                }, indent=2)
            
            # Build MESSAGE
            if category.lower() == "all":
                message = "🍽️ *OUR MENU* 🍽️\n\n"
            else:
                message = f"🍽️ *{category.upper()}* 🍽️\n\n"
            
            current_category = None
            data = []
            
            for name, cat, price in rows:
                if category.lower() == "all" and current_category != cat:
                    current_category = cat
                    if current_category != rows[0][1]:
                        message += "\n"
                    message += f"━━━ *{cat}* ━━━\n"
                
                message += f"{name} — ${price:.2f}\n"
                data.append({"name": name, "category": cat, "price": float(price)})
            
            message += "\n💬 Reply with item name to order!"
            
            return json.dumps({
                "success": True,
                "output":{"message": message,
                "data": data},
                "error": None
            }, indent=2)
        
    except Exception as e:
        logger.error(f"Error fetching menu: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)