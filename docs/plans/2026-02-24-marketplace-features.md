# Marketplace Features: Payments, Orders, Alerts & Scheduling

## Context

PharmApp has 11,626 medications, 140,249 prices, and 2,706 pharmacies across 4 chains. The data layer is solid but the **purchase flow is broken**: MercadoPago webhook reads wrong fields, `price_id` bug in frontend sends pharmacy_id instead, notification_url points to frontend, and no credentials are configured. Beyond fixing payments, we need order management, price alerts, and auto-scheduled scraping to complete the marketplace.

---

## Task 1: Fix MercadoPago Checkout Flow (End-to-End)

### 1a. Fix frontend `price_id` bug

**Modify** `frontend/src/pages/MedicationDetailPage.js`:
- In `handleBuy(priceItem)`, add `price_id: priceItem.price_id` to the URLSearchParams
  - The `/prices/compare-transparent` endpoint already returns `price_id` in each item (check and confirm)

**Modify** `frontend/src/pages/CheckoutPage.js`:
- Read `price_id` from searchParams
- Fix line 65: change `price_id: pharmacyId` to `price_id: priceId` (the actual Price record UUID)

### 1b. Fix `payment_service.py` notification_url

**Modify** `backend/app/core/config.py`:
- Add `BACKEND_PUBLIC_URL: str = "http://localhost:8000"` setting

**Modify** `backend/app/services/payment_service.py`:
- Change `notification_url` from `{base_url}/api/v1/webhooks/mercadopago` to `{settings.BACKEND_PUBLIC_URL}/api/v1/webhooks/mercadopago`
- Keep `back_urls` pointing to `FRONTEND_URL` (those are user-facing redirects)
- Fix Transbank `return_url`: should point to a **frontend** return page, not the webhook endpoint
  - Change to `{base_url}/orders/{order_id}?status=transbank&token_ws=` (user-facing)
  - Add a separate Transbank commit endpoint in webhooks (below)

### 1c. Fix MercadoPago webhook to verify payment via API

**Modify** `backend/app/api/v1/webhooks.py`:
- MercadoPago IPN sends `{"type": "payment", "data": {"id": "12345"}}` — the `id` is the **payment ID**, NOT external_reference
- Fix webhook to:
  1. Extract `payment_id` from `body["data"]["id"]`
  2. Call MercadoPago API: `GET /v1/payments/{payment_id}` to get full payment details
  3. Read `external_reference` (our order_id) from the API response
  4. Read `status` from the API response ("approved", "rejected", "pending", etc.)
  5. Only update order to `confirmed` if status == "approved"
  6. Handle "rejected" → set order status to `cancelled`, payment_status to "rejected"
- Add helper `_fetch_mp_payment(payment_id: str)` that uses `mercadopago.SDK` to query payment

### 1d. Add Transbank return flow

**Modify** `backend/app/api/v1/webhooks.py`:
- Change Transbank endpoint to handle the **return_url** redirect (GET request from user's browser)
- After `tx.commit(token)`, redirect user to frontend order page:
  - If AUTHORIZED: redirect to `/orders/{order_id}?status=success`
  - If not: redirect to `/orders/{order_id}?status=failure`

### 1e. Configure test credentials

**Modify** `backend/.env.example` (or `.env`):
- Add MercadoPago test access token placeholder
- Document: users need `MERCADOPAGO_ACCESS_TOKEN=TEST-xxx` for sandbox

**Modify** `backend/app/core/config.py`:
- Fix `FRONTEND_URL` default: keep as `http://localhost:3000` (it's overridable via .env)

---

## Task 2: Order Status Management

### 2a. Admin order endpoints

**Modify** `backend/app/api/v1/orders.py`:
- Add `PATCH /orders/{order_id}/status` endpoint:
  - Body: `{"status": "delivering" | "completed" | "cancelled"}`
  - Validates transition: only allow valid status transitions
  - Valid transitions: `confirmed → delivering → completed`, any → `cancelled`
  - On status change, send WhatsApp notification via `whatsapp.send_order_status_update()`
- Add `GET /orders/` — list all orders for admin (query by status filter)
- Add `GET /orders/{order_id}` — get single order with items

### 2b. Order status WhatsApp notifications

**Modify** `backend/app/services/whatsapp.py`:
- Add `send_order_status_update(phone, order_id, new_status)` function
- Messages:
  - `delivering`: "Tu pedido #{order_id} esta en camino"
  - `completed`: "Tu pedido #{order_id} fue entregado"
  - `cancelled`: "Tu pedido #{order_id} fue cancelado"

### 2c. Frontend order status page

**Modify** `frontend/src/pages/OrderStatusPage.js` (or create if missing):
- Show order details, items, payment status
- Poll for status updates or use the `status` query param from payment redirect
- Show status timeline: pending → payment_sent → confirmed → delivering → completed

---

## Task 3: Price Alerts (Scheduled Job)

### 3a. Add APScheduler

**Modify** `backend/requirements.txt`:
- Add `apscheduler>=3.10`

**Modify** `backend/app/main.py`:
- Add scheduler startup on `@app.on_event("startup")`:
  ```python
  from apscheduler.schedulers.asyncio import AsyncIOScheduler
  scheduler = AsyncIOScheduler()
  scheduler.add_job(check_price_alerts, "interval", hours=6)
  scheduler.add_job(run_scheduled_scrape, "cron", hour=3)  # Task 4
  scheduler.start()
  ```

### 3b. Price alert checker

**Create** `backend/app/tasks/price_alerts.py`:
- `async def check_price_alerts()`:
  1. Create own DB session
  2. Query all active PriceAlerts where `is_active=True`
  3. For each alert, find minimum current price for that medication
  4. If min price <= target_price and (last_notified_at is None or > 24h ago):
     - Send WhatsApp notification via `whatsapp.send_price_alert(phone, medication_name, price, pharmacy_name)`
     - Update `last_notified_at`
  5. Commit

### 3c. WhatsApp price alert message

**Modify** `backend/app/services/whatsapp.py`:
- Add `send_price_alert(phone, medication_name, current_price, pharmacy_name)` function

---

## Task 4: Auto-Scheduled Scraping

### 4a. Scheduled catalog + price scrape

Uses the scheduler from Task 3a.

**Create** `backend/app/tasks/scheduled.py`:
- `async def run_scheduled_scrape()`:
  1. Run catalog scrape for all chains (reuses `run_catalog_scrape_with_session`)
  2. Log results
  3. This runs daily at 3 AM (configured in scheduler)

### 4b. API endpoint for manual schedule info

**Modify** `backend/app/api/v1/scraping.py`:
- Add `GET /scraping/schedule` — returns next scheduled run time and last run info

---

## Task 5: WhatsApp Purchase Flow

### 5a. Conversational purchase handler

**Modify** `backend/app/services/whatsapp.py`:
- Enhance `handle_incoming_message()` to support purchase flow:
  - "comprar {medication}" → search medication, show cheapest 3 options
  - User picks option → create order, send payment link
  - After payment confirmed (webhook) → send delivery updates
- This requires ServiceTsunami integration via existing `servicetsunami.py` client

### 5b. Message templates

**Modify** `backend/app/services/whatsapp.py`:
- Add message templates for:
  - Price comparison results (medication search response)
  - Payment link delivery
  - Payment confirmed
  - Order status updates (delivering, completed)

---

## Files Summary

### Modified:
| File | Task | Changes |
|------|------|---------|
| `frontend/src/pages/MedicationDetailPage.js` | 1a | Pass `price_id` in handleBuy |
| `frontend/src/pages/CheckoutPage.js` | 1a | Fix `price_id` bug |
| `backend/app/core/config.py` | 1b | Add `BACKEND_PUBLIC_URL` |
| `backend/app/services/payment_service.py` | 1b | Fix notification_url, Transbank return_url |
| `backend/app/api/v1/webhooks.py` | 1c,1d | Fix MP webhook, fix Transbank return flow |
| `backend/app/api/v1/orders.py` | 2a | Admin order status endpoints |
| `backend/app/services/whatsapp.py` | 2b,3c,5 | Order status, price alert, purchase flow messages |
| `frontend/src/pages/OrderStatusPage.js` | 2c | Order status display |
| `backend/requirements.txt` | 3a | Add apscheduler |
| `backend/app/main.py` | 3a | Scheduler startup |
| `backend/app/api/v1/scraping.py` | 4b | Schedule info endpoint |

### New:
| File | Task | Purpose |
|------|------|---------|
| `backend/app/tasks/price_alerts.py` | 3b | Price alert checker job |
| `backend/app/tasks/scheduled.py` | 4a | Scheduled scraping job |

---

## Verification

1. **Checkout flow**: Navigate to medication → click "Comprar" → verify `price_id` sent correctly → order created with payment_url
2. **MercadoPago sandbox**: Create order with mercadopago provider → redirect to MP checkout → complete test payment → webhook fires → order status = confirmed
3. **Order management**: `PATCH /orders/{id}/status` with `{"status": "delivering"}` → verify status updated
4. **Price alerts**: Create alert for medication at high target price → run `check_price_alerts()` manually → verify WhatsApp notification sent
5. **Scheduled scraping**: Verify scheduler starts on app boot → check logs for "Scheduled scrape" entries
6. Build: `DB_PORT=5435 WEB_PORT=3002 docker-compose up --build -d`
