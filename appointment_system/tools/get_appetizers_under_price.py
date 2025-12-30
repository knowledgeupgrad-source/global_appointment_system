import json
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def get_appetizers_under_price(max_price: float = 10.0) -> str:
    """Fetch appetizers under specified price"""
    try:
        logger.info(f"Fetching appetizers under ${max_price}")
        
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, price, description
                FROM restaurant.menu_items
                WHERE category = 'Appetizers' AND is_available = TRUE AND price <= %s
                ORDER BY price, name
            """, (max_price,))
            
            rows = cur.fetchall()
            
            if not rows:
                return json.dumps({
                    "success": True,
                    "output":{"message": f"🥗 No appetizers found under ${max_price}",
                    "data": []},
                    "error": None
                }, indent=2)
            
            message = f"🥗 *APPETIZERS UNDER ${max_price}* 🥗\n\n"
            data = []
            
            for name, price, desc in rows:
                message += f"{name} — ${price:.2f}\n"
                if desc:
                    message += f"  _{desc}_\n"
                message += "\n"
                
                data.append({"name": name, "price": float(price), "description": desc})
            
            message += "Perfect starters for your meal! 😋"
            
            return json.dumps({
                "success": True,
                "output":{"message": message,
                "data": data},
                "error": None
            }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching appetizers: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)