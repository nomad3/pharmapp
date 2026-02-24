import mercadopago
from transbank.webpay.webpay_plus.transaction import Transaction
from app.core.config import settings


def create_mercadopago_preference(order_id: str, items: list, total: float) -> str:
    frontend_url = settings.FRONTEND_URL
    backend_url = settings.BACKEND_PUBLIC_URL
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    preference_data = {
        "items": [{"title": "Medicamentos PharmApp", "quantity": 1, "unit_price": total}],
        "external_reference": order_id,
        "back_urls": {
            "success": f"{frontend_url}/orders/{order_id}?status=success",
            "failure": f"{frontend_url}/orders/{order_id}?status=failure",
            "pending": f"{frontend_url}/orders/{order_id}?status=pending",
        },
        "notification_url": f"{backend_url}/api/v1/webhooks/mercadopago",
        "auto_return": "approved",
    }
    result = sdk.preference().create(preference_data)
    return result["response"]["init_point"]


def create_transbank_transaction(order_id: str, total: float) -> str:
    frontend_url = settings.FRONTEND_URL
    tx = Transaction()
    resp = tx.create(
        buy_order=order_id[:26],
        session_id=order_id[:61],
        amount=total,
        return_url=f"{frontend_url}/orders/{order_id}?status=transbank",
    )
    return resp["url"] + "?token_ws=" + resp["token"]
