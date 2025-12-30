import json
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def get_desserts() -> str:
    """Fetch all dessert items"""
    try:
        logger.info("Fetching desserts")
        
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, price, description
                FROM restaurant.menu_items
                WHERE category = 'Desserts' AND is_available = TRUE
                ORDER BY name
            """)
            
            rows = cur.fetchall()
            
            if not rows:
                return json.dumps({
                    "success": True,
                    "output":{"message": "🍰 No desserts available right now.",
                    "data": []},
                    "error": None
                }, indent=2)
            
            message = "🍰 *DESSERTS MENU* 🍰\n\n"
            data = []
            
            for name, price, desc in rows:
                message += f"{name} — ${price:.2f}\n"
                if desc:
                    message += f"  _{desc}_\n"
                message += "\n"
                
                data.append({"name": name, "price": float(price), "description": desc})
            
            return json.dumps({
                "success": True,
                "output":{"message": message,
                "data": data},
                "error": None
            }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching desserts: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)