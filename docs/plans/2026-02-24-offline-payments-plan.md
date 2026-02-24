# Offline Payments Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add cash-on-delivery and bank-transfer payment methods with admin manual verification.

**Architecture:** Extend existing PaymentProvider/OrderStatus enums, add a SiteSetting key-value model for bank details, add admin endpoints for payment confirmation and settings management. Frontend gets two new payment options at checkout and a bank details admin config page.

**Tech Stack:** FastAPI, SQLAlchemy, React, existing Axios client

---

### Task 1: Extend Order Model — New Enums

**Files:**
- Modify: `backend/app/models/order.py:6-16`

**Step 1: Add new enum values**

```python
class OrderStatus(str, enum.Enum):
    pending = "pending"
    payment_sent = "payment_sent"
    pending_transfer = "pending_transfer"
    confirmed = "confirmed"
    delivering = "delivering"
    awaiting_delivery_payment = "awaiting_delivery_payment"
    completed = "completed"
    cancelled = "cancelled"

class PaymentProvider(str, enum.Enum):
    mercadopago = "mercadopago"
    transbank = "transbank"
    cash_on_delivery = "cash_on_delivery"
    bank_transfer = "bank_transfer"
```

**Step 2: Commit**

```bash
git add backend/app/models/order.py
git commit -m "feat: add offline payment enums (cash_on_delivery, bank_transfer, pending_transfer, awaiting_delivery_payment)"
```

---

### Task 2: SiteSetting Model + Migration

**Files:**
- Create: `backend/app/models/site_setting.py`
- Modify: `backend/app/models/__init__.py` (if needed for import)

**Step 1: Create SiteSetting model**

```python
from sqlalchemy import Column, String, DateTime, func
from app.models.base import Base


class SiteSetting(Base):
    __tablename__ = "site_settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**Step 2: Commit**

```bash
git add backend/app/models/site_setting.py
git commit -m "feat: add SiteSetting key-value model for bank details"
```

---

### Task 3: Update Order Service — Offline Payment Logic

**Files:**
- Modify: `backend/app/services/order_service.py`

**Step 1: Update create_order to handle offline providers**

After the existing payment URL generation block (lines 61-67), add handling for cash_on_delivery and bank_transfer. The key change: these providers skip payment URL generation and set different initial statuses.

```python
# In create_order(), replace lines 60-73:

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

    db.commit()
    db.refresh(order)
    return order
```

**Step 2: Commit**

```bash
git add backend/app/services/order_service.py
git commit -m "feat: handle cash_on_delivery and bank_transfer in order creation"
```

---

### Task 4: Admin Settings API — Bank Details CRUD

**Files:**
- Create: `backend/app/api/v1/settings.py`
- Modify: `backend/app/api/v1/routes.py`

**Step 1: Create settings router**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.site_setting import SiteSetting
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])

BANK_KEYS = [
    "bank_name", "bank_account_type", "bank_account_number",
    "bank_rut", "bank_holder_name", "bank_email",
]


@router.get("/bank-details")
def get_bank_details(db: Session = Depends(get_db)):
    """Public endpoint — needed at checkout and order detail."""
    rows = db.query(SiteSetting).filter(SiteSetting.key.in_(BANK_KEYS)).all()
    return {row.key: row.value for row in rows}


class BankDetailsUpdate(BaseModel):
    bank_name: str = ""
    bank_account_type: str = ""
    bank_account_number: str = ""
    bank_rut: str = ""
    bank_holder_name: str = ""
    bank_email: str = ""


@router.put("/bank-details")
def update_bank_details(
    body: BankDetailsUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Admin-only — update bank transfer details."""
    for key in BANK_KEYS:
        value = getattr(body, key, "")
        existing = db.query(SiteSetting).filter(SiteSetting.key == key).first()
        if existing:
            existing.value = value
        else:
            db.add(SiteSetting(key=key, value=value))
    db.commit()
    return {"status": "ok"}
```

**Step 2: Register in routes.py**

Add to `backend/app/api/v1/routes.py`:
```python
from app.api.v1 import settings
# After the admin router include:
api_router.include_router(settings.router)
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/settings.py backend/app/api/v1/routes.py
git commit -m "feat: add bank details settings API (public GET, admin PUT)"
```

---

### Task 5: Admin Payment Confirmation Endpoints

**Files:**
- Modify: `backend/app/api/v1/orders.py:24-29` (VALID_TRANSITIONS)
- Modify: `backend/app/api/v1/orders.py` (add confirm/reject endpoints)

**Step 1: Update VALID_TRANSITIONS to include new statuses**

```python
VALID_TRANSITIONS = {
    OrderStatus.confirmed: [OrderStatus.delivering, OrderStatus.cancelled],
    OrderStatus.delivering: [OrderStatus.completed, OrderStatus.awaiting_delivery_payment, OrderStatus.cancelled],
    OrderStatus.awaiting_delivery_payment: [OrderStatus.completed, OrderStatus.cancelled],
    OrderStatus.pending: [OrderStatus.cancelled],
    OrderStatus.payment_sent: [OrderStatus.cancelled],
    OrderStatus.pending_transfer: [OrderStatus.confirmed, OrderStatus.cancelled],
}
```

**Step 2: Add confirm-payment and reject-payment endpoints**

Append to `backend/app/api/v1/orders.py`:

```python
@router.patch("/{order_id}/confirm-payment")
async def confirm_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    """Admin: confirm bank transfer payment."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending_transfer:
        raise HTTPException(status_code=400, detail="Order is not pending transfer")

    order.status = OrderStatus.confirmed
    order.payment_status = "verified"
    db.commit()

    user = db.query(User).filter(User.id == order.user_id).first()
    if user:
        try:
            await whatsapp.send_payment_confirmed(user.phone_number, str(order.id))
        except Exception:
            logger.warning("Failed to send WhatsApp for order %s payment confirmed", order.id)

    return {"id": str(order.id), "status": "confirmed", "message": "Payment confirmed"}


@router.patch("/{order_id}/reject-payment")
async def reject_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    """Admin: reject bank transfer (cancel order)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending_transfer:
        raise HTTPException(status_code=400, detail="Order is not pending transfer")

    order.status = OrderStatus.cancelled
    order.payment_status = "rejected"
    db.commit()

    return {"id": str(order.id), "status": "cancelled", "message": "Payment rejected"}
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/orders.py
git commit -m "feat: add confirm/reject payment endpoints and offline status transitions"
```

---

### Task 6: WhatsApp Messages for Offline Payments

**Files:**
- Modify: `backend/app/services/whatsapp.py`

**Step 1: Add two new WhatsApp message functions**

```python
async def send_cash_on_delivery_confirmation(phone_number: str, order_id: str, total: float) -> dict:
    message = (
        f"*Remedia* — Pedido recibido\n\n"
        f"Tu pedido #{order_id[:8]} fue recibido.\n"
        f"Total: ${int(total):,} CLP\n\n"
        f"Paga en efectivo al momento de la entrega."
    )
    return await _send_message(phone_number, message)


async def send_bank_transfer_details(
    phone_number: str, order_id: str, total: float, bank_details: dict
) -> dict:
    message = (
        f"*Remedia* — Datos para transferencia\n\n"
        f"Tu pedido #{order_id[:8]} esta pendiente de pago.\n"
        f"Total: ${int(total):,} CLP\n\n"
        f"Transfiere a:\n"
        f"Banco: {bank_details.get('bank_name', '-')}\n"
        f"Tipo: {bank_details.get('bank_account_type', '-')}\n"
        f"Cuenta: {bank_details.get('bank_account_number', '-')}\n"
        f"RUT: {bank_details.get('bank_rut', '-')}\n"
        f"Nombre: {bank_details.get('bank_holder_name', '-')}\n"
        f"Email: {bank_details.get('bank_email', '-')}\n\n"
        f"Tu pedido sera confirmado al verificar el pago."
    )
    return await _send_message(phone_number, message)
```

**Step 2: Call them from order_service.py after order creation**

Add to `backend/app/services/order_service.py`, after the status assignment block and before `db.commit()`:

```python
    # Send WhatsApp for offline payments (fire-and-forget in background)
    if data.payment_provider == "cash_on_delivery":
        try:
            import asyncio
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
            import asyncio
            asyncio.ensure_future(
                whatsapp.send_bank_transfer_details(phone_number, order_id_str, total, bank_details)
            )
        except Exception:
            logger.warning("Failed to send bank-transfer WhatsApp for order %s", order_id_str)
```

Add import at top of order_service.py:
```python
from app.services import whatsapp
```

**Step 3: Commit**

```bash
git add backend/app/services/whatsapp.py backend/app/services/order_service.py
git commit -m "feat: add WhatsApp messages for cash on delivery and bank transfer"
```

---

### Task 7: Frontend — Checkout Page Payment Options

**Files:**
- Modify: `frontend/src/pages/CheckoutPage.js:214-245` (payment method section)
- Modify: `frontend/src/pages/CheckoutPage.js:71-96` (handleConfirm)

**Step 1: Add 4 payment options (replace existing 2)**

Replace the payment-options div (lines 217-244) with:

```jsx
<div className="payment-options">
  <label className={`payment-option ${paymentProvider === "mercadopago" ? "selected" : ""}`}>
    <input type="radio" name="payment" value="mercadopago"
      checked={paymentProvider === "mercadopago"}
      onChange={e => setPaymentProvider(e.target.value)} />
    <div className="payment-option__content">
      <div className="payment-option__name">Mercado Pago</div>
      <div className="payment-option__desc">Tarjetas de credito/debito, transferencia</div>
    </div>
  </label>
  <label className={`payment-option ${paymentProvider === "transbank" ? "selected" : ""}`}>
    <input type="radio" name="payment" value="transbank"
      checked={paymentProvider === "transbank"}
      onChange={e => setPaymentProvider(e.target.value)} />
    <div className="payment-option__content">
      <div className="payment-option__name">Transbank Webpay</div>
      <div className="payment-option__desc">Tarjetas de credito/debito</div>
    </div>
  </label>
  <label className={`payment-option ${paymentProvider === "bank_transfer" ? "selected" : ""}`}>
    <input type="radio" name="payment" value="bank_transfer"
      checked={paymentProvider === "bank_transfer"}
      onChange={e => setPaymentProvider(e.target.value)} />
    <div className="payment-option__content">
      <div className="payment-option__name">Transferencia Bancaria</div>
      <div className="payment-option__desc">Transfiere a nuestra cuenta y confirmamos manualmente</div>
    </div>
  </label>
  <label className={`payment-option ${paymentProvider === "cash_on_delivery" ? "selected" : ""}`}>
    <input type="radio" name="payment" value="cash_on_delivery"
      checked={paymentProvider === "cash_on_delivery"}
      onChange={e => setPaymentProvider(e.target.value)} />
    <div className="payment-option__content">
      <div className="payment-option__name">Pago en Efectivo</div>
      <div className="payment-option__desc">Paga al momento de la entrega o retiro</div>
    </div>
  </label>
</div>
```

**Step 2: Update handleConfirm to handle non-redirect flows**

In the handleConfirm success handler (line 87-91), change to:

```javascript
if (fromCart) clearCart();
if (data.payment_url) {
  window.location.href = data.payment_url;
} else {
  // Offline payments — go to order detail with appropriate status
  const status = paymentProvider === "bank_transfer" ? "transfer" : "cash";
  navigate(`/orders/${data.id}?status=${status}`);
}
```

**Step 3: Update confirm button text**

Replace the button text (line 254):

```jsx
{loading ? "Procesando..." : (
  paymentProvider === "cash_on_delivery"
    ? `Confirmar pedido — $${Math.round(total).toLocaleString("es-CL")} CLP`
    : paymentProvider === "bank_transfer"
      ? `Confirmar pedido — $${Math.round(total).toLocaleString("es-CL")} CLP`
      : `Pagar $${Math.round(total).toLocaleString("es-CL")} CLP`
)}
```

**Step 4: Commit**

```bash
git add frontend/src/pages/CheckoutPage.js
git commit -m "feat: add bank transfer and cash on delivery payment options to checkout"
```

---

### Task 8: Frontend — Order Detail Page Updates

**Files:**
- Modify: `frontend/src/pages/OrderDetailPage.js`

**Step 1: Add bank transfer banner and bank details card**

After the existing payment status banners (line 84), add:

```jsx
{paymentStatus === "transfer" && (
  <div className="payment-banner payment-banner--pending">
    <span className="payment-banner__icon">&#127974;</span>
    <div>
      <div className="payment-banner__title">Transferencia pendiente</div>
      <div className="payment-banner__desc">
        Realiza la transferencia y tu pedido sera confirmado al verificar el pago.
      </div>
    </div>
  </div>
)}
{paymentStatus === "cash" && (
  <div className="payment-banner payment-banner--success">
    <span className="payment-banner__icon">&#128176;</span>
    <div>
      <div className="payment-banner__title">Pedido confirmado</div>
      <div className="payment-banner__desc">
        Paga ${order.total?.toLocaleString("es-CL")} CLP en efectivo al momento de la entrega.
      </div>
    </div>
  </div>
)}
```

**Step 2: Add bank details card component**

Add a `BankDetailsCard` inside OrderDetailPage that fetches and shows bank details when `order.payment_provider === "bank_transfer"`:

```jsx
function BankDetailsCard() {
  const [details, setDetails] = useState(null);
  useEffect(() => {
    client.get("/settings/bank-details")
      .then(({ data }) => setDetails(data))
      .catch(() => {});
  }, []);
  if (!details || Object.keys(details).length === 0) return null;

  const copy = (text) => { navigator.clipboard.writeText(text); };
  const fields = [
    { label: "Banco", key: "bank_name" },
    { label: "Tipo de cuenta", key: "bank_account_type" },
    { label: "N° de cuenta", key: "bank_account_number" },
    { label: "RUT", key: "bank_rut" },
    { label: "Titular", key: "bank_holder_name" },
    { label: "Email", key: "bank_email" },
  ];
  return (
    <div className="bank-details-card">
      <h3>Datos para transferencia</h3>
      {fields.map(f => details[f.key] ? (
        <div key={f.key} className="bank-detail-row">
          <span className="bank-detail-label">{f.label}</span>
          <span className="bank-detail-value">{details[f.key]}</span>
          <button className="bank-detail-copy" onClick={() => copy(details[f.key])} title="Copiar">
            &#128203;
          </button>
        </div>
      ) : null)}
    </div>
  );
}
```

Render it in the payment section when provider is bank_transfer:

```jsx
{order.payment_provider === "bank_transfer" && order.status === "pending_transfer" && (
  <BankDetailsCard />
)}
```

**Step 3: Update status timeline for offline payments**

Replace the hardcoded timeline steps (line 92) with dynamic steps based on payment_provider:

```jsx
{order.status !== "cancelled" && (() => {
  let steps;
  if (order.payment_provider === "cash_on_delivery") {
    steps = ["confirmed", "delivering", "awaiting_delivery_payment", "completed"];
  } else if (order.payment_provider === "bank_transfer") {
    steps = ["pending_transfer", "confirmed", "delivering", "completed"];
  } else {
    steps = ["pending", "payment_sent", "confirmed", "delivering", "completed"];
  }
  const stepLabels = {
    pending: "Pendiente",
    payment_sent: "Pago enviado",
    pending_transfer: "Esperando transferencia",
    confirmed: "Confirmado",
    delivering: "En camino",
    awaiting_delivery_payment: "Pago pendiente",
    completed: "Entregado",
  };
  const currentIdx = steps.indexOf(order.status);
  return (
    <div className="order-timeline">
      {steps.map((step, i) => (
        <div key={step} className={`timeline-step ${i <= currentIdx ? "timeline-step--active" : ""}`}>
          <div className="timeline-step__dot" />
          {i < steps.length - 1 && <div className="timeline-step__line" />}
          <div className="timeline-step__label">{stepLabels[step]}</div>
        </div>
      ))}
    </div>
  );
})()}
```

**Step 4: Update payment info section**

Replace the hardcoded provider name (line 158):

```jsx
const PROVIDER_LABELS = {
  mercadopago: "Mercado Pago",
  transbank: "Transbank Webpay",
  cash_on_delivery: "Pago en Efectivo",
  bank_transfer: "Transferencia Bancaria",
};
// In the payment section:
<div>Medio: {PROVIDER_LABELS[order.payment_provider] || order.payment_provider}</div>
```

**Step 5: Commit**

```bash
git add frontend/src/pages/OrderDetailPage.js
git commit -m "feat: update order detail for offline payments (bank details card, dynamic timeline)"
```

---

### Task 9: Frontend — Admin Orders Page Updates

**Files:**
- Modify: `frontend/src/pages/admin/AdminOrdersPage.js`

**Step 1: Add new statuses to STATUS_LABELS and filter dropdown**

```javascript
const STATUS_LABELS = {
  pending: "Pendiente",
  payment_sent: "Pago Enviado",
  pending_transfer: "Transferencia Pendiente",
  confirmed: "Confirmado",
  delivering: "En Camino",
  awaiting_delivery_payment: "Pago en Entrega",
  completed: "Entregado",
  cancelled: "Cancelado",
};
```

Add new options to the filter dropdown:
```jsx
<option value="pending_transfer">Transferencia Pendiente</option>
<option value="awaiting_delivery_payment">Pago en Entrega</option>
```

**Step 2: Add confirm/reject buttons for pending_transfer orders**

In the admin-actions div (after line 122), add:

```jsx
{o.status === "pending_transfer" && (
  <>
    <button
      className="btn btn--primary btn--sm"
      disabled={updating === o.id}
      onClick={() => confirmPayment(o.id)}
    >
      Confirmar Pago
    </button>
    <button
      className="btn btn--danger btn--sm"
      disabled={updating === o.id}
      onClick={() => rejectPayment(o.id)}
    >
      Rechazar
    </button>
  </>
)}
{o.status === "awaiting_delivery_payment" && (
  <button
    className="btn btn--primary btn--sm"
    disabled={updating === o.id}
    onClick={() => updateStatus(o.id, "completed")}
  >
    Pago Recibido
  </button>
)}
```

**Step 3: Add confirmPayment and rejectPayment functions**

```javascript
const confirmPayment = (orderId) => {
  setUpdating(orderId);
  client
    .patch(`/orders/${orderId}/confirm-payment`)
    .then(() => fetchOrders())
    .catch(console.error)
    .finally(() => setUpdating(null));
};

const rejectPayment = (orderId) => {
  setUpdating(orderId);
  client
    .patch(`/orders/${orderId}/reject-payment`)
    .then(() => fetchOrders())
    .catch(console.error)
    .finally(() => setUpdating(null));
};
```

**Step 4: Add provider labels in the table**

```javascript
const PROVIDER_LABELS = {
  mercadopago: "Mercado Pago",
  transbank: "Transbank",
  cash_on_delivery: "Efectivo",
  bank_transfer: "Transferencia",
};
// In the table cell:
<td>{PROVIDER_LABELS[o.payment_provider] || o.payment_provider || "-"}</td>
```

**Step 5: Commit**

```bash
git add frontend/src/pages/admin/AdminOrdersPage.js
git commit -m "feat: add payment confirm/reject actions and offline status filters to admin orders"
```

---

### Task 10: Frontend — Admin Settings Page (Bank Details)

**Files:**
- Create: `frontend/src/pages/admin/AdminSettingsPage.js`
- Modify: `frontend/src/App.js` (add route)
- Modify: `frontend/src/pages/admin/AdminDashboardPage.js:10-15` (add nav link)

**Step 1: Create AdminSettingsPage**

```jsx
import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import client from "../../api/client";
import { AdminNav } from "./AdminDashboardPage";

export default function AdminSettingsPage() {
  const [form, setForm] = useState({
    bank_name: "", bank_account_type: "", bank_account_number: "",
    bank_rut: "", bank_holder_name: "", bank_email: "",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    client.get("/settings/bank-details")
      .then(({ data }) => setForm(prev => ({ ...prev, ...data })))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      await client.put("/settings/bank-details", form);
      setMessage("Guardado correctamente");
    } catch {
      setMessage("Error al guardar");
    }
    setSaving(false);
  };

  const fields = [
    { key: "bank_name", label: "Nombre del banco", placeholder: "Ej: Banco Estado" },
    { key: "bank_account_type", label: "Tipo de cuenta", placeholder: "Ej: Cuenta Corriente" },
    { key: "bank_account_number", label: "Numero de cuenta", placeholder: "Ej: 123456789" },
    { key: "bank_rut", label: "RUT", placeholder: "Ej: 76.123.456-7" },
    { key: "bank_holder_name", label: "Nombre del titular", placeholder: "Ej: Remedia SpA" },
    { key: "bank_email", label: "Email de notificacion", placeholder: "Ej: pagos@remedia.cl" },
  ];

  return (
    <div className="admin-page">
      <Helmet>
        <title>Configuracion Admin | Remedia</title>
        <meta name="robots" content="noindex" />
      </Helmet>
      <div className="container">
        <h1 className="page-title">Configuracion</h1>
        <AdminNav />

        <div className="admin-settings-section">
          <h2>Datos Bancarios para Transferencia</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: 16 }}>
            Estos datos se muestran al usuario cuando elige pagar por transferencia bancaria.
          </p>
          {fields.map(f => (
            <div key={f.key} className="form-group">
              <label className="form-label">{f.label}</label>
              <input
                className="input"
                type="text"
                placeholder={f.placeholder}
                value={form[f.key]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
              />
            </div>
          ))}
          {message && (
            <div className={`checkout-${message.includes("Error") ? "error" : "success"}`} style={{ marginBottom: 12 }}>
              {message}
            </div>
          )}
          <button className="btn btn--primary" onClick={handleSave} disabled={saving}>
            {saving ? "Guardando..." : "Guardar datos bancarios"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Add route in App.js**

Import:
```javascript
import AdminSettingsPage from "./pages/admin/AdminSettingsPage";
```

Add route alongside other admin routes:
```jsx
<Route path="/admin/settings" element={<AdminSettingsPage />} />
```

**Step 3: Add "Configuracion" to AdminNav**

In `AdminDashboardPage.js`, add to the links array:
```javascript
{ to: "/admin/settings", label: "Configuracion" },
```

**Step 4: Commit**

```bash
git add frontend/src/pages/admin/AdminSettingsPage.js frontend/src/App.js frontend/src/pages/admin/AdminDashboardPage.js
git commit -m "feat: add admin settings page for bank details configuration"
```

---

### Task 11: CSS Styles for Bank Details + Offline Payments

**Files:**
- Modify: `frontend/src/App.css`

**Step 1: Add bank details card styles**

```css
/* Bank details card */
.bank-details-card {
  background: var(--primary-light);
  border: 1px solid var(--primary);
  border-radius: 12px;
  padding: 20px;
  margin-top: 12px;
}
.bank-details-card h3 {
  margin: 0 0 16px;
  color: var(--primary-dark);
  font-size: 16px;
}
.bank-detail-row {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.bank-detail-row:last-child { border-bottom: none; }
.bank-detail-label {
  flex: 0 0 140px;
  font-size: 13px;
  color: var(--text-secondary);
}
.bank-detail-value {
  flex: 1;
  font-weight: 600;
  font-size: 14px;
}
.bank-detail-copy {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.bank-detail-copy:hover { opacity: 1; }

/* Admin settings section */
.admin-settings-section {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border);
  padding: 24px;
  margin-top: 20px;
}
.admin-settings-section h2 {
  margin: 0 0 8px;
  font-size: 18px;
}
.form-group {
  margin-bottom: 16px;
}
.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

**Step 2: Commit**

```bash
git add frontend/src/App.css
git commit -m "style: add CSS for bank details card and admin settings form"
```

---

### Task 12: Database Migration + Rebuild & Test

**Step 1: Create the site_settings table via alembic or direct SQL**

Since the project uses SQLAlchemy models without a formal migration tool, the table will be auto-created if `Base.metadata.create_all` is called at startup, or we can add it manually. Check if `main.py` does auto-create:

If not, add to `backend/app/main.py` startup:
```python
from app.models.site_setting import SiteSetting  # noqa — ensure table created
```

**Step 2: Also update the PostgreSQL enum types**

Since PostgreSQL enums are strict, we need to add the new enum values. Add a startup event or manual SQL:

```python
# In backend/app/main.py, add to the startup event or after Base.metadata.create_all:
from sqlalchemy import text

@app.on_event("startup")
def add_enum_values():
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'pending_transfer'"))
        db.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'awaiting_delivery_payment'"))
        db.execute(text("ALTER TYPE paymentprovider ADD VALUE IF NOT EXISTS 'cash_on_delivery'"))
        db.execute(text("ALTER TYPE paymentprovider ADD VALUE IF NOT EXISTS 'bank_transfer'"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
```

**Step 3: Rebuild and test**

```bash
DB_PORT=5435 WEB_PORT=3002 docker-compose up --build --force-recreate -d
```

Verify:
```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/settings/bank-details
```

**Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: add enum migration and site_settings table creation on startup"
```
