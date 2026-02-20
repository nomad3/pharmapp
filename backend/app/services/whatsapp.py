"""
WhatsApp messaging service — PharmApp-specific message templates
dispatched through ServiceTsunami's OpenClaw WhatsApp skill.

All outbound WhatsApp messages go through this service so we have
a single place to manage message copy and formatting.
"""

import logging
from app.services.servicetsunami import tsunami_client

logger = logging.getLogger(__name__)


async def send_otp(phone_number: str, code: str) -> dict:
    """Send OTP verification code via WhatsApp."""
    message = (
        f"🔐 *PharmApp — Código de verificación*\n\n"
        f"Tu código es: *{code}*\n\n"
        f"Expira en 5 minutos. No compartas este código con nadie."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_order_confirmation(phone_number: str, order_id: str, total: float, payment_url: str) -> dict:
    """Send order creation + payment link via WhatsApp."""
    short_id = order_id[:8]
    message = (
        f"🛒 *PharmApp — Pedido #{short_id}*\n\n"
        f"Total: *${total:,.0f} CLP*\n\n"
        f"Completa tu pago aquí:\n{payment_url}\n\n"
        f"Una vez confirmado el pago, coordinaremos el delivery."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_payment_confirmed(phone_number: str, order_id: str) -> dict:
    """Notify user that payment was received."""
    short_id = order_id[:8]
    message = (
        f"✅ *PharmApp — Pago confirmado*\n\n"
        f"Pedido #{short_id}: tu pago fue recibido.\n"
        f"Estamos preparando tu pedido para delivery."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_delivery_update(phone_number: str, order_id: str, status: str, rider_name: str | None = None, eta_minutes: int | None = None) -> dict:
    """Send delivery status update via WhatsApp."""
    short_id = order_id[:8]

    if status == "dispatched":
        rider_info = f" con *{rider_name}*" if rider_name else ""
        eta_info = f"\nTiempo estimado: *{eta_minutes} minutos*" if eta_minutes else ""
        message = (
            f"🚴 *PharmApp — En camino*\n\n"
            f"Pedido #{short_id} salió{rider_info}.{eta_info}"
        )
    elif status == "delivered":
        message = (
            f"📦 *PharmApp — Entregado*\n\n"
            f"Pedido #{short_id} fue entregado.\n"
            f"¡Gracias por usar PharmApp!"
        )
    else:
        message = (
            f"📋 *PharmApp — Actualización*\n\n"
            f"Pedido #{short_id}: estado actualizado a *{status}*."
        )

    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_price_alert(phone_number: str, medication_name: str, pharmacy_name: str, price: float) -> dict:
    """Notify user about a price drop on a favorited medication."""
    message = (
        f"💊 *PharmApp — Alerta de precio*\n\n"
        f"*{medication_name}* bajó a *${price:,.0f} CLP*\n"
        f"en {pharmacy_name}.\n\n"
        f"Busca en PharmApp para comparar precios."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def handle_incoming_message(sender_phone: str, message_body: str, message_id: str) -> dict:
    """
    Process an incoming WhatsApp message from a user.

    Routes the message to ServiceTsunami's supervisor agent via
    chat session for conversational handling (medication search,
    order status, etc.).
    """
    logger.info("Incoming WhatsApp from %s: %s", sender_phone, message_body[:100])

    session = await tsunami_client.create_chat_session(
        title=f"PharmApp WhatsApp — {sender_phone}",
    )
    session_id = session["id"]

    context_message = (
        f"[PharmApp WhatsApp]\n"
        f"From: {sender_phone}\n"
        f"Message ID: {message_id}\n\n"
        f"{message_body}"
    )

    response = await tsunami_client.send_chat_message(session_id, context_message)
    assistant_reply = response.get("assistant_message", {}).get("content", "")

    if assistant_reply:
        await tsunami_client.send_whatsapp(sender_phone, assistant_reply)

    return {"session_id": session_id, "reply": assistant_reply}
