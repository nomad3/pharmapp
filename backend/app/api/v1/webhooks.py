import hashlib
import hmac
import logging

import mercadopago
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services import whatsapp
from app.services.commission_service import record_commission
from app.services.adherence_service import record_refill_from_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ── WhatsApp incoming (from ServiceTsunami / OpenClaw) ───────────────

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive incoming WhatsApp messages forwarded by ServiceTsunami.

    OpenClaw receives the WhatsApp Cloud API webhook, parses the message,
    and forwards it here so PharmApp can handle domain-specific logic
    (medication search, order status, etc.).
    """
    body = await request.json()

    # Verify webhook signature if configured
    if settings.PHARMAPP_WEBHOOK_SECRET:
        signature = request.headers.get("X-Webhook-Signature", "")
        raw = await request.body()
        expected = hmac.new(
            settings.PHARMAPP_WEBHOOK_SECRET.encode(), raw, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # WhatsApp Cloud API format (forwarded by OpenClaw)
    entries = body.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                sender_phone = msg.get("from", "")
                message_body = msg.get("text", {}).get("body", "")
                message_id = msg.get("id", "")
                message_type = msg.get("type", "text")

                if not sender_phone or not message_body:
                    continue

                logger.info("WhatsApp from %s: %s", sender_phone, message_body[:100])

                # Route to conversational handler
                try:
                    await whatsapp.handle_incoming_message(
                        sender_phone=sender_phone,
                        message_body=message_body,
                        message_id=message_id,
                    )
                except Exception:
                    logger.exception("Error handling WhatsApp from %s", sender_phone)

    return {"status": "ok"}


@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    """
    WhatsApp webhook verification (GET challenge).
    Required by WhatsApp Cloud API during webhook registration.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.PHARMAPP_WEBHOOK_SECRET:
        return int(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


# ── Mercado Pago IPN ─────────────────────────────────────────────────

def _fetch_mp_payment(payment_id: str) -> dict | None:
    """Fetch payment details from MercadoPago API."""
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        logger.error("MERCADOPAGO_ACCESS_TOKEN not configured")
        return None
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    result = sdk.payment().get(payment_id)
    if result.get("status") == 200:
        return result.get("response", {})
    logger.error("MercadoPago payment fetch failed: %s", result)
    return None


@router.post("/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    if body.get("type") != "payment":
        return {"status": "ok"}

    # MercadoPago IPN sends {"type": "payment", "data": {"id": "12345"}}
    payment_id = body.get("data", {}).get("id")
    if not payment_id:
        logger.warning("MercadoPago webhook missing payment id")
        return {"status": "ok"}

    # Verify payment via MercadoPago API
    payment = _fetch_mp_payment(str(payment_id))
    if not payment:
        logger.error("Could not verify MercadoPago payment %s", payment_id)
        return {"status": "ok"}

    order_id = payment.get("external_reference")
    mp_status = payment.get("status")  # approved, rejected, pending, etc.

    if not order_id:
        logger.warning("MercadoPago payment %s has no external_reference", payment_id)
        return {"status": "ok"}

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning("Order not found for MercadoPago payment: %s", order_id)
        return {"status": "ok"}

    if mp_status == "approved":
        order.status = OrderStatus.confirmed
        order.payment_status = "approved"
        db.commit()

        # Record commission
        record_commission(db, order)

        # Record adherence refill
        try:
            record_refill_from_order(db, order)
        except Exception:
            logger.exception("Error recording refill for order %s", order.id)

        # Notify user via WhatsApp
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            try:
                await whatsapp.send_payment_confirmed(
                    user.phone_number, str(order.id)
                )
            except Exception:
                pass

    elif mp_status == "rejected":
        order.status = OrderStatus.cancelled
        order.payment_status = "rejected"
        db.commit()

    elif mp_status in ("pending", "in_process"):
        order.payment_status = mp_status
        db.commit()

    else:
        logger.info("MercadoPago payment %s status: %s", payment_id, mp_status)

    return {"status": "ok"}


# ── Transbank Webpay ─────────────────────────────────────────────────

@router.post("/transbank")
async def transbank_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Transbank return_url redirect (POST with token_ws)."""
    from transbank.webpay.webpay_plus.transaction import Transaction

    frontend_url = settings.FRONTEND_URL
    params = await request.form()
    token = params.get("token_ws")

    if not token:
        return RedirectResponse(url=f"{frontend_url}/?error=transbank_no_token", status_code=303)

    tx = Transaction()
    resp = tx.commit(token)

    buy_order = resp.get("buy_order", "")
    order = db.query(Order).filter(Order.id == buy_order).first() if buy_order else None

    if resp.get("status") == "AUTHORIZED" and order:
        order.status = OrderStatus.confirmed
        order.payment_status = "authorized"
        db.commit()

        # Record commission
        record_commission(db, order)

        # Record adherence refill
        try:
            record_refill_from_order(db, order)
        except Exception:
            logger.exception("Error recording refill for order %s", order.id)

        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            try:
                await whatsapp.send_payment_confirmed(
                    user.phone_number, str(order.id)
                )
            except Exception:
                pass

        return RedirectResponse(
            url=f"{frontend_url}/orders/{buy_order}?status=success", status_code=303
        )
    else:
        if order:
            order.payment_status = resp.get("status", "failed")
            db.commit()
        return RedirectResponse(
            url=f"{frontend_url}/orders/{buy_order}?status=failure", status_code=303
        )
