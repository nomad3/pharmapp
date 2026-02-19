from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order, OrderStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

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
    return {"status": "ok"}

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
    return {"status": "ok"}
