from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.price import Price
from app.schemas.order import OrderCreate
from app.services.payment_service import create_mercadopago_preference, create_transbank_transaction
from app.services import whatsapp

async def create_order(db: Session, user_id: str, phone_number: str, data: OrderCreate) -> Order:
    total = 0.0
    items = []
    for item_data in data.items:
        price = db.query(Price).filter(Price.id == item_data.price_id).first()
        subtotal = price.price * item_data.quantity
        total += subtotal
        items.append(OrderItem(
            medication_id=item_data.medication_id,
            price_id=item_data.price_id,
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
    if data.payment_provider == "mercadopago":
        order.payment_url = create_mercadopago_preference(order_id_str, items, total)
    elif data.payment_provider == "transbank":
        order.payment_url = create_transbank_transaction(order_id_str, total)

    order.status = OrderStatus.payment_sent
    db.commit()
    db.refresh(order)

    try:
        await whatsapp.send_order_confirmation(
            phone_number, order_id_str, total, order.payment_url or ""
        )
    except Exception:
        pass  # Don't block order creation if WhatsApp fails

    return order
