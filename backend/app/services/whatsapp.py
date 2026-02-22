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


async def send_gpo_threshold_reached(phone_number: str, product_name: str, quantity: int, member_count: int) -> dict:
    message = (
        f"🤝 *PharmApp GPO — Umbral alcanzado*\n\n"
        f"*{product_name}*: se alcanzó el mínimo de compra.\n"
        f"Cantidad total: *{quantity:,} unidades*\n"
        f"Miembros participantes: *{member_count}*\n\n"
        f"Ya puedes crear la orden grupal."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_gpo_order_status_update(phone_number: str, order_ref: str, new_status: str) -> dict:
    message = (
        f"📦 *PharmApp GPO — Actualización de orden*\n\n"
        f"Orden *{order_ref[:8]}*: estado actualizado a *{new_status}*."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_gpo_allocation_ready(phone_number: str, product_name: str, quantity: int, price: float) -> dict:
    message = (
        f"✅ *PharmApp GPO — Asignación lista*\n\n"
        f"Tu asignación de *{product_name}* está lista:\n"
        f"Cantidad: *{quantity:,} unidades*\n"
        f"Precio unitario: *${price:,.0f} CLP*"
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_refill_reminder(phone_number: str, medication_name: str, days_until: int, current_discount: float) -> dict:
    discount_text = f" (descuento actual: {round(current_discount * 100)}%)" if current_discount > 0 else ""
    message = (
        f"💊 *PharmApp — Recordatorio de recarga*\n\n"
        f"Tu recarga de *{medication_name}* vence en *{days_until} días*{discount_text}.\n\n"
        f"Recarga a tiempo para mantener tu racha y descuento."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_refill_completed(phone_number: str, medication_name: str, discount_pct: float, savings: float, streak: int, next_due: str) -> dict:
    message = (
        f"✅ *PharmApp — Recarga completada*\n\n"
        f"*{medication_name}*\n"
        f"Descuento aplicado: *{round(discount_pct * 100)}%* (ahorraste *${savings:,.0f} CLP*)\n"
        f"Racha: *{streak} recargas consecutivas*\n"
        f"Próxima recarga: *{next_due}*"
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_streak_broken(phone_number: str, medication_name: str, lost_discount_pct: float) -> dict:
    message = (
        f"⚠️ *PharmApp — Racha interrumpida*\n\n"
        f"No recogiste tu recarga de *{medication_name}* a tiempo.\n"
        f"Tu racha se reinició y perdiste el descuento de *{round(lost_discount_pct * 100)}%*.\n\n"
        f"Vuelve a recargar para comenzar a acumular descuentos nuevamente."
    )
    return await tsunami_client.send_whatsapp(phone_number, message)


async def send_tier_upgrade(phone_number: str, medication_name: str, new_discount_pct: float, streak: int) -> dict:
    message = (
        f"🎉 *PharmApp — Nuevo nivel de descuento*\n\n"
        f"¡Felicidades! Alcanzaste *{streak} recargas consecutivas* de *{medication_name}*.\n"
        f"Tu nuevo descuento es *{round(new_discount_pct * 100)}%*."
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
