import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services import whatsapp

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

@router.post("/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    if body.get("type") == "payment":
        external_ref = body.get("data", {}).get("external_reference")
        if external_ref:
            order = db.query(Order).filter(Order.id == external_ref).first()
            if order:
                order.status = OrderStatus.confirmed
                order.payment_status = "approved"
                db.commit()

                # Notify user via WhatsApp
                user = db.query(User).filter(User.id == order.user_id).first()
                if user:
                    try:
                        await whatsapp.send_payment_confirmed(
                            user.phone_number, str(order.id)
                        )
                    except Exception:
                        pass
    return {"status": "ok"}


# ── Transbank Webpay ─────────────────────────────────────────────────

@router.post("/transbank")
async def transbank_webhook(request: Request, db: Session = Depends(get_db)):
    from transbank.webpay.webpay_plus.transaction import Transaction
    params = await request.form()
    token = params.get("token_ws")
    if token:
        tx = Transaction()
        resp = tx.commit(token)
        if resp.get("status") == "AUTHORIZED":
            order = db.query(Order).filter(Order.id == resp["buy_order"]).first()
            if order:
                order.status = OrderStatus.confirmed
                order.payment_status = "authorized"
                db.commit()

                user = db.query(User).filter(User.id == order.user_id).first()
                if user:
                    try:
                        await whatsapp.send_payment_confirmed(
                            user.phone_number, str(order.id)
                        )
                    except Exception:
                        pass
    return {"status": "ok"}
