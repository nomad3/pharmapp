import asyncio
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.price import Price
from app.schemas.order import OrderCreate
from app.services.payment_service import create_mercadopago_preference, create_transbank_transaction
from app.services.adherence_service import apply_adherence_discount
from app.services import whatsapp

logger = logging.getLogger(__name__)


async def create_order(db: Session, user_id: str, phone_number: str, data: OrderCreate) -> Order:
    total = 0.0
    items = []
    for item_data in data.items:
        # Look up price — try by price_id first, fall back to medication+pharmacy match
        price = db.query(Price).filter(Price.id == item_data.price_id).first()
        if not price:
            price = db.query(Price).filter(
                Price.medication_id == item_data.medication_id,
                Price.pharmacy_id == data.pharmacy_id,
            ).first()
        if not price:
            raise HTTPException(status_code=404, detail=f"Price not found for medication {item_data.medication_id}")

        base_price = price.price * item_data.quantity

        # Apply adherence discount if enrolled
        try:
            discount_info = apply_adherence_discount(db, user_id, str(item_data.medication_id), base_price)
            subtotal = discount_info["final_price"]
        except Exception:
            subtotal = base_price

        total += subtotal
        items.append(OrderItem(
            medication_id=item_data.medication_id,
            price_id=price.id,
            quantity=item_data.quantity,
            subtotal=subtotal,
        ))

    order = Order(
        user_id=user_id,
        pharmacy_id=data.pharmacy_id,
        payment_provider=data.payment_provider,
        total=total,
    )
    db.add(order)
    db.flush()

    for item in items:
        item.order_id = order.id
        db.add(item)

    order_id_str = str(order.id)

    if data.payment_provider in ("mercadopago", "transbank"):
        try:
            if data.payment_provider == "mercadopago":
                order.payment_url = create_mercadopago_preference(order_id_str, items, total)
            elif data.payment_provider == "transbank":
                order.payment_url = create_transbank_transaction(order_id_str, total)
        except Exception as e:
            logger.warning("Payment provider error (order still created): %s", e)
        order.status = OrderStatus.payment_sent
    elif data.payment_provider == "cash_on_delivery":
        order.status = OrderStatus.confirmed
    elif data.payment_provider == "bank_transfer":
        order.status = OrderStatus.pending_transfer
    else:
        order.status = OrderStatus.payment_sent

    # Send WhatsApp for offline payments (fire-and-forget in background)
    if data.payment_provider == "cash_on_delivery":
        try:
            asyncio.ensure_future(
                whatsapp.send_cash_on_delivery_confirmation(phone_number, order_id_str, total)
            )
        except Exception:
            logger.warning("Failed to send cash-on-delivery WhatsApp for order %s", order_id_str)
    elif data.payment_provider == "bank_transfer":
        try:
            from app.models.site_setting import SiteSetting
            bank_rows = db.query(SiteSetting).filter(
                SiteSetting.key.in_(["bank_name", "bank_account_type", "bank_account_number",
                                     "bank_rut", "bank_holder_name", "bank_email"])
            ).all()
            bank_details = {r.key: r.value for r in bank_rows}
            asyncio.ensure_future(
                whatsapp.send_bank_transfer_details(phone_number, order_id_str, total, bank_details)
            )
        except Exception:
            logger.warning("Failed to send bank-transfer WhatsApp for order %s", order_id_str)

    db.commit()
    db.refresh(order)
    return order
