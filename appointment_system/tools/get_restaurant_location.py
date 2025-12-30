import json
from appointment_system.utils.logger import logger

def get_restaurant_location() -> str:
    """Get restaurant location details"""
    try:
        logger.info("Fetching restaurant location")
        
        message = """📍 *RESTAURANT LOCATION* 📍

*Bella Italia Restaurant*

📍 *Address:*
123 Main Street, Downtown District
New York, NY 10001

🚗 *How to reach:*
- Near Central Park
- 5 min walk from Metro Station
- Free parking available

📞 *Contact:*
Phone: +1 (555) 123-4567
Email: info@bellaitalia.com

🗺️ Google Maps: https://maps.google.com/bella-italia"""

        data = {
            "name": "Bella Italia Restaurant",
            "address": {
                "street": "123 Main Street",
                "area": "Downtown District",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            },
            "contact": {
                "phone": "+1 (555) 123-4567",
                "email": "info@bellaitalia.com"
            },
            "maps_url": "https://maps.google.com/bella-italia"
        }
        
        return json.dumps({
            "success": True,
            "output":{"message": message,
            "data": data},
            "error": None
        }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching location: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "output":{"message": None,
            "data": None},
            "error": str(e)
        }, indent=2)