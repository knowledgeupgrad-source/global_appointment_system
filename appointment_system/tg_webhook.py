from flask import Flask, request, jsonify
from appointment_system.utils.postgres import AppointmentDB
from appointment_system.utils.logger import logger

app = Flask(__name__)
db = AppointmentDB()

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.json
    logger.info(f"Incoming Telegram update: {data}")

    if "message" not in data:
        return jsonify({"ok": True})

    message = data["message"]

    chat_id = message["chat"]["id"]
    from_user = message["from"]

    end_user_id = from_user.get("id")
    username = from_user.get("username", "")
    text = message.get("text", "")

    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO appointment_management_system.conversation (
                    end_user_id,
                    end_user_mobile_number,
                    conversation_id,
                    input_message,
                    response_from,
                    create_at,
                    output_message,
                    handled_by_admin
                )
                VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
            """, (
                str(end_user_id),
                username,
                str(chat_id),
                text,
                "telegram",
                None,
                False
            ))
            conn.commit()

        logger.info("Telegram message saved successfully")

    except Exception as e:
        logger.error("DB insert failed", exc_info=True)

    # VERY IMPORTANT: Always return 200 OK
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
