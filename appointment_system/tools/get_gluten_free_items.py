import json
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def get_gluten_free_items() -> str:
    """Fetch all gluten-free items"""
    try:
        logger.info("Fetching gluten-free items")
        
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, category, price
                FROM restaurant.menu_items
                WHERE is_gluten_free = TRUE AND is_available = TRUE
                ORDER BY category, name
            """)
            
            rows = cur.fetchall()
            
            if not rows:
                return json.dumps({
                    "success": True,
                    "output":{"message": "🌾 Sorry, no gluten-free options available right now.",
                    "data": []},
                    "error": None
                }, indent=2)
            
            message = "🌾 *GLUTEN-FREE OPTIONS* 🌾\n\n"
            current_category = None
            data = []
            
            for name, cat, price in rows:
                if current_category != cat:
                    current_category = cat
                    message += f"\n━━━ *{cat}* ━━━\n"
                
                message += f"{name} — ${price:.2f}\n"
                data.append({"name": name, "category": cat, "price": float(price)})
            
            message += "\n⚠️ Please inform staff about allergies"
            
            return json.dumps({
                "success": True,
                "output":{"message": message,
                "data": data},
                "error": None
            }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching gluten-free items: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)