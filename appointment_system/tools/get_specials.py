import json
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def get_specials() -> str:
    """Fetch today's special menu items"""
    try:
        logger.info("Fetching specials")
        
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, category, price, discount_percentage
                FROM restaurant.menu_items
                WHERE is_special = TRUE AND is_available = TRUE
                ORDER BY category, name
            """)
            
            rows = cur.fetchall()
            
            if not rows:
                return json.dumps({
                    "success": True,
                    "output":{"message": "⭐ No special dishes today. Check our regular menu!",
                    "data": []},
                    "error": None
                }, indent=2)
            
            message = "⭐ *TODAY'S SPECIALS* ⭐\n\n"
            data = []
            
            for name, cat, price, discount in rows:
                if discount and discount > 0:
                    original_price = price / (1 - discount/100)
                    message += f"🌟 {name} ({cat})\n"
                    message += f"   ~~${original_price:.2f}~~ → *${price:.2f}* ({discount}% OFF)\n\n"
                else:
                    message += f"🌟 {name} ({cat}) — *${price:.2f}*\n\n"
                
                data.append({
                    "name": name,
                    "category": cat,
                    "price": float(price),
                    "discount_percentage": discount if discount else 0
                })
            
            message += "Limited availability - Order now! 🔥"
            
            return json.dumps({
                "success": True,
                "output":{"message": message,
                "data": data},
                "error": None
            }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching specials: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)