# Offline Payment Methods — Design Document

**Date:** 2026-02-24
**Status:** Approved

## Overview

Add two offline payment methods to Remedia: cash on delivery and bank transfer with manual verification. These complement the existing MercadoPago and Transbank online payment options.

## New Payment Providers

Add to `PaymentProvider` enum:
- `cash_on_delivery` — pay cash when order is delivered or picked up
- `bank_transfer` — transfer to fixed bank account, admin manually verifies

## New Order Statuses

Add to `OrderStatus` enum:
- `pending_transfer` — bank transfer order waiting for user to transfer and admin to verify
- `awaiting_delivery_payment` — cash on delivery order delivered but cash not yet collected

## Flow: Cash on Delivery

```
User selects "Pago en efectivo" at checkout
  → Order created (status: confirmed, no payment gate)
  → WhatsApp: "Tu pedido fue recibido. Paga $X al momento de la entrega"
  → Admin assigns delivery → status: delivering
  → Rider delivers → status: awaiting_delivery_payment
  → Cash collected → status: completed
```

Available for both pharmacy pickup and home delivery.

## Flow: Bank Transfer

```
User selects "Transferencia bancaria" at checkout
  → Order created (status: pending_transfer)
  → Bank details shown on confirmation page
  → WhatsApp: "Transfiere $X a: [bank details]. Tu pedido sera confirmado al verificar el pago"
  → User transfers at their convenience
  → Admin sees order in pending transfers filter
  → Admin clicks "Confirmar Pago" → status: confirmed
  → Normal delivery flow continues
```

## Bank Details Storage

New `SiteSetting` model — generic key-value table for site configuration:

```python
class SiteSetting(Base):
    key = Column(String, primary_key=True)      # e.g. "bank_name", "bank_account"
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

Bank detail keys:
- `bank_name` — e.g. "Banco Estado"
- `bank_account_type` — e.g. "Cuenta Corriente"
- `bank_account_number` — e.g. "123456789"
- `bank_rut` — e.g. "76.123.456-7"
- `bank_holder_name` — e.g. "Remedia SpA"
- `bank_email` — e.g. "pagos@remedia.cl"

## API Endpoints

### Public
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/settings/bank-details` | Returns bank details for checkout display |

### Admin
| Method | Path | Description |
|--------|------|-------------|
| PUT | `/api/v1/admin/settings/bank-details` | Update bank details |
| PATCH | `/api/v1/orders/{id}/confirm-payment` | Confirm bank transfer payment |
| PATCH | `/api/v1/orders/{id}/reject-payment` | Reject bank transfer (cancel order) |

## Frontend Changes

### CheckoutPage
- 4 payment method radio buttons: MercadoPago, Transbank, Transferencia Bancaria, Pago en Efectivo
- For cash/transfer: no redirect to external payment gateway
- For transfer: show bank details card on order confirmation with copy-to-clipboard per field

### OrderDetailPage
- Updated status timeline with new statuses
- `pending_transfer`: show bank details card + "Esperando verificacion de pago"
- `awaiting_delivery_payment`: show "Pago pendiente al momento de entrega"

### Admin Orders Page
- "Confirmar Pago" button (green) for `pending_transfer` orders
- "Rechazar" button (red) for `pending_transfer` orders
- Filter preset: "Pendientes de verificacion" showing only `pending_transfer` orders

### Admin Settings (new)
- "Configuracion" tab in admin nav
- Bank details form: bank name, account type, account number, RUT, holder, email
- Save button calls PUT `/api/v1/admin/settings/bank-details`

## WhatsApp Messages

**Cash on delivery:**
```
*Remedia* — Pedido recibido

Tu pedido #{{order_id}} fue recibido.
Total: ${{total}} CLP

Paga en efectivo al momento de la entrega.
```

**Bank transfer:**
```
*Remedia* — Datos para transferencia

Tu pedido #{{order_id}} esta pendiente de pago.
Total: ${{total}} CLP

Transfiere a:
Banco: {{bank_name}}
Tipo: {{bank_account_type}}
Cuenta: {{bank_account_number}}
RUT: {{bank_rut}}
Nombre: {{bank_holder_name}}
Email: {{bank_email}}

Tu pedido sera confirmado al verificar el pago.
```

## Updated Status Flow

```
                    ┌─── MercadoPago/Transbank ───┐
                    │                              │
                    │  pending → payment_sent → confirmed → delivering → completed
                    │                              │
                    ├─── Cash on Delivery ─────────┤
                    │                              │
                    │  confirmed → delivering → awaiting_delivery_payment → completed
                    │                              │
                    └─── Bank Transfer ────────────┘
                                                   │
                       pending_transfer → confirmed → delivering → completed
```
