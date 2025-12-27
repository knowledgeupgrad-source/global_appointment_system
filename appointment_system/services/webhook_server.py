from __future__ import annotations
import os
from appointment_system.utils.logger import logger
from mcp.server.fastmcp import FastMCP
from appointment_system.utils.postgres import AppointmentDB
from appointment_system.services.whatsapp_communication import WhatsAppClient
import json
import traceback
import logging
from flask import Blueprint, request
from appointment_system.utils.logger import logger
from appointment_system.utils.postgres import AppointmentDB
from appointment_system.services.whatsapp_communication import WhatsAppClient

webhook_bp = Blueprint("whatsapp_webhook", __name__)
db = AppointmentDB()
whatsapp = WhatsAppClient()
@webhook_bp.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    payload = request.get_json(force=True, silent=True)
    logger.info("📩 Incoming WhatsApp webhook")

    if not payload:
        logger.warning("Empty webhook payload")
        return "EVENT_RECEIVED", 200

    messages = whatsapp.receive_message(payload)
    conn = db.get_connection()
    with conn.cursor() as cur:
        for msg in messages:
            cur.execute("""
                INSERT INTO appointment_management_system.conversation (
                    end_user_mobile_number,
                    conversation_id,
                    input_message,
                    response_from,
                    processed
                )
                VALUES (%s, %s, %s, 'customer', FALSE)
                ON CONFLICT (conversation_id) DO NOTHING
            """, (
                msg["from"],
                msg["message_id"],
                msg["text"]
            ))
        conn.commit()

    logger.info(f"Stored {len(messages)} WhatsApp messages")
    return "EVENT_RECEIVED", 200
