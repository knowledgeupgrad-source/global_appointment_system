# appointment_system/mcp/tools/restaurant_order_place_and_validate.py

import json
import random
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import get_connection

def restaurant_order_place_and_validate(
    phone_number: str,
    table_number: str,
    item: str,
    quantity: int,
    price: float,
    special_instructions: str = ""
) -> str:
    """
    Place a restaurant order - just save to database
    
    Args:
        phone_number: Customer phone number
        table_number: Table number
        item: Item name
        quantity: Quantity
        price: Item price
        special_instructions: Special requests (optional)
    """
    try:
        logger.info(f"Placing order: {item} x{quantity} for table {table_number}")
        
        conn = get_connection()
        with conn.cursor() as cur:
            # Generate order number
            order_number = f"ORD{random.randint(1000, 9999)}"
            
            # Get or create customer
            cur.execute("""
                SELECT id FROM restaurant.customers WHERE phone_number = %s
            """, (phone_number,))
            
            customer = cur.fetchone()
            if customer:
                customer_id = customer[0]
            else:
                cur.execute("""
                    INSERT INTO restaurant.customers (phone_number, name)
                    VALUES (%s, %s) RETURNING id
                """, (phone_number, f"Customer-{phone_number[-4:]}"))
                customer_id = cur.fetchone()[0]
            
            # Calculate totals
            item_total = quantity * price
            subtotal = item_total
            tax = subtotal * 0.08
            total = subtotal + tax
            
            # Create order
            cur.execute("""
                INSERT INTO restaurant.orders 
                (order_number, customer_id, customer_phone, table_number, 
                 status, special_instructions, subtotal, tax, total, created_at)
                VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (order_number, customer_id, phone_number, table_number, 
                  special_instructions, subtotal, tax, total))
            
            order_id = cur.fetchone()[0]
            
            # Insert order item (use menu_item_id = 1 as placeholder)
            cur.execute("""
                INSERT INTO restaurant.order_items 
                (order_id, menu_item_id, item_name, quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, 1, item, quantity, price, item_total))
            
            # Update table status
            cur.execute("""
                UPDATE restaurant.restaurant_tables
                SET status = 'occupied'
                WHERE table_number = %s
            """, (table_number,))
            
            conn.commit()
            
            # Return simple format
            return json.dumps({
                "success": True,
                "output": {
                    "message": special_instructions if special_instructions else None,
                    "data": {
                        "item": item,
                        "quantity": quantity,
                        "price": float(price)
                    }
                },
                "error": None
            }, indent=2)
    
    except Exception as e:
        logger.error(f"Error placing order: {e}", exc_info=True)
        if conn:
            conn.rollback()
        return json.dumps({
            "success": False,
            "output": {
                "message": None,
                "data": None
            },
            "error": str(e)
        }, indent=2)