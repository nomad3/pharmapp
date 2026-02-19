# PharmApp Marketplace Design

**Date**: 2026-02-19
**Status**: Approved

## Product Vision

PharmApp is a medication marketplace for Chile that aggregates pricing from pharmacy chains and government data, helps users find the cheapest medicines near them, and completes purchases through a WhatsApp agent handling payment, delivery, and coordination.

## Decisions

| Area | Decision |
|---|---|
| Market | Chile — ISP drug registry, CENABAST, Cruz Verde, Salcobrand, Ahumada |
| Architecture | Thick PharmApp backend (own PostgreSQL + PostGIS). ServiceTsunami for agent orchestration, WhatsApp, and scraping only |
| Auth | Phone number + OTP via WhatsApp |
| Data sources | Web scraping pharmacy chain websites via ServiceTsunami's web_researcher agent |
| Frontend | React SPA, mobile-first, Google Maps, React Router |
| Geolocation | Browser Geolocation API + PostGIS server-side distance queries |
| WhatsApp | Full purchase loop — confirmation, payment link, delivery coordination |
| Payments | Mercado Pago + Transbank Webpay (user choice via WhatsApp agent) |
| Extras | Delivery tracking, user favorites, search history |

## Data Model

### Users & Auth

- `users` — id (uuid), phone_number (unique), name, comuna, location (geography point), created_at
- `otp_codes` — id, user_id (FK), code, expires_at, verified
- `delivery_addresses` — id, user_id (FK), label (home/work/etc), address, comuna, location (geography point), instructions

### Catalog (populated by scrapers)

- `medications` — id, name, active_ingredient, dosage, form (tablet/syrup/etc), lab, isp_registry_number, requires_prescription
- `pharmacies` — id, chain (cruz_verde/salcobrand/ahumada/etc), name, address, comuna, location (geography point), phone, hours
- `prices` — id, medication_id (FK), pharmacy_id (FK), price, in_stock, source_url, scraped_at

### Orders

- `orders` — id, user_id (FK), pharmacy_id (FK), status (pending/payment_sent/confirmed/delivering/completed/cancelled), payment_provider (mercadopago/transbank), payment_url, payment_status, total, created_at
- `order_items` — id, order_id (FK), medication_id (FK), price_id (FK), quantity, subtotal
- `order_deliveries` — id, order_id (FK), delivery_address_id (FK), rider_name, rider_phone, status (assigned/picked_up/in_transit/delivered), eta, delivered_at

### User Activity

- `user_favorites` — id, user_id (FK), medication_id (FK), created_at
- `search_history` — id, user_id (FK), query_text, location (geography point), results_count, created_at

## Backend Architecture

FastAPI structured app with own PostgreSQL + PostGIS:

```
backend/app/
├── main.py                    # FastAPI app, startup events
├── core/
│   ├── config.py              # Settings (DB, ServiceTsunami URL, payment keys)
│   ├── database.py            # SQLAlchemy + PostGIS engine/session
│   └── security.py            # OTP generation, JWT tokens
├── models/                    # SQLAlchemy models (all tables above)
├── schemas/                   # Pydantic request/response schemas
├── api/v1/
│   ├── auth.py                # POST /auth/otp/request, /auth/otp/verify
│   ├── medications.py         # GET /medications, /medications/search
│   ├── pharmacies.py          # GET /pharmacies/nearby
│   ├── prices.py              # GET /prices/compare
│   ├── orders.py              # POST /orders, GET /orders/{id}
│   ├── favorites.py           # GET/POST/DELETE /favorites
│   └── webhooks.py            # Payment provider callbacks
├── services/
│   ├── geolocation.py         # PostGIS distance queries
│   ├── price_engine.py        # Price comparison, ranking, best-deal logic
│   ├── order_service.py       # Order state machine
│   ├── payment_service.py     # Mercado Pago + Transbank integration
│   └── servicetsunami.py      # Client for ServiceTsunami API
└── tasks/
    └── scraping.py            # Triggers ServiceTsunami scraping pipelines
```

### Key API Endpoints

- `POST /api/v1/auth/otp/request` — send OTP via WhatsApp
- `POST /api/v1/auth/otp/verify` — verify OTP, return JWT
- `GET /api/v1/medications/search?q=&lat=&lng=&radius_km=` — search with geolocation
- `GET /api/v1/pharmacies/nearby?lat=&lng=&radius_km=` — nearby pharmacies
- `GET /api/v1/prices/compare?medication_id=&lat=&lng=` — price comparison ranked by price/distance
- `POST /api/v1/orders` — create order, initiate WhatsApp purchase flow
- `GET /api/v1/orders/{id}` — order status + delivery tracking
- `POST /api/v1/webhooks/mercadopago` — Mercado Pago IPN callback
- `POST /api/v1/webhooks/transbank` — Transbank callback
- `GET/POST/DELETE /api/v1/favorites` — user favorites
- `GET /api/v1/search-history` — user search history

## Frontend Architecture

React SPA, mobile-first, Google Maps:

```
frontend/src/
├── App.js                      # Routes setup (React Router)
├── api/
│   └── client.js               # Axios instance, auth interceptor
├── pages/
│   ├── HomePage.js             # Search bar + geolocation prompt
│   ├── SearchResultsPage.js    # Medication list with price comparison
│   ├── PharmacyMapPage.js      # Nearby pharmacies on Google Map
│   ├── MedicationDetailPage.js # Single medication, all pharmacy prices sorted
│   ├── OrderPage.js            # Order summary before WhatsApp handoff
│   ├── OrderHistoryPage.js     # Past orders + delivery status tracking
│   ├── FavoritesPage.js        # Saved medications
│   └── LoginPage.js            # Phone number input + OTP verification
├── components/
│   ├── SearchBar.js            # Medication search with autocomplete
│   ├── PriceCard.js            # Pharmacy + price + distance display
│   ├── PharmacyMap.js          # Google Maps component
│   ├── WhatsAppButton.js       # "Buy via WhatsApp" CTA
│   └── OrderStatusBadge.js     # Order state display
└── hooks/
    ├── useGeolocation.js       # Browser geolocation hook
    └── useAuth.js              # Auth state + OTP flow
```

New dependencies: react-router-dom, @react-google-maps/api.

## ServiceTsunami Integration

PharmApp calls ServiceTsunami (`../servicetsunami-agents`) for three things:

### 1. Web Scraping Pipelines

- PharmApp triggers ServiceTsunami data pipelines on a schedule
- ServiceTsunami's web_researcher agent scrapes Cruz Verde, Salcobrand, Ahumada
- Scraped data lands in Databricks Bronze layer
- PharmApp pulls cleaned data and writes to its own PostgreSQL

### 2. WhatsApp Messaging

All WhatsApp communication goes through ServiceTsunami's SkillRouter + OpenClaw:

- **OTP delivery**: PharmApp backend generates code, calls ServiceTsunami to send it via WhatsApp
- **Purchase flow**: After order creation, ServiceTsunami agent manages the WhatsApp conversation:
  1. Sends order confirmation message
  2. Offers payment method choice (Mercado Pago / Transbank)
  3. Sends payment link
  4. Confirms payment received
  5. Asks for delivery address or offers pharmacy pickup
  6. Sends delivery status updates
  7. Confirms order completion

### 3. Conversational Search (enhancement)

Optional: users can search medications by messaging the PharmApp WhatsApp number directly. ServiceTsunami agent queries PharmApp's API and returns results in chat.

### Integration Points

ServiceTsunami endpoints used:
- `POST /api/v1/auth/login` — get JWT for PharmApp's tenant
- `POST /api/v1/skill-configs` — configure WhatsApp skill
- `POST /api/v1/chat/sessions` + `/{id}/messages` — trigger WhatsApp conversations
- `POST /api/v1/data_pipelines` — create/trigger scraping pipelines
- `POST /api/v1/datasets/ingest` — push scraped data for processing

## Payment Integration

### Mercado Pago

1. PharmApp creates payment preference via Mercado Pago SDK
2. Gets checkout URL
3. WhatsApp agent sends URL to user
4. User pays on Mercado Pago hosted checkout
5. IPN webhook hits `/api/v1/webhooks/mercadopago`
6. Order status updated

### Transbank Webpay

1. PharmApp creates transaction via Transbank SDK
2. Gets Webpay redirect URL
3. WhatsApp agent sends URL to user
4. User pays on Transbank hosted page
5. Return URL callback hits `/api/v1/webhooks/transbank`
6. Order status updated

WhatsApp agent offers the user a choice between providers before generating the link.

## Docker Compose (Development)

Updated to include PostgreSQL + PostGIS:

```yaml
services:
  db:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_DB: pharmapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
  backend:
    build: ./backend
    depends_on: [db]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/pharmapp
      SERVICETSUNAMI_API_URL: http://host.docker.internal:8001
      SERVICETSUNAMI_API_KEY: ...
  frontend:
    build: ./frontend
    depends_on: [backend]
    ports:
      - "3000:80"
```
