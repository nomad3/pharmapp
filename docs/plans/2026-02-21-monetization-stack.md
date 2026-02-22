# PharmApp Monetization Stack

**Date**: 2026-02-21
**Status**: Approved

## Context

PharmApp has a working marketplace with 834 medications, 795 pharmacies, 129K prices, plus rich government data (680K Cenabast invoices, 64K BMS distribution records, 11K purchase orders, 2.9K adjudications). The analytics dashboard, WhatsApp order flow, and payment integrations (MercadoPago + Transbank) are all functional.

**Goal:** Build 4 layered revenue streams on top of existing infrastructure, ordered by time-to-revenue.

## Revenue Streams

| Phase | Stream | Revenue Model | Timeline |
|-------|--------|--------------|----------|
| 1 | Premium Data API | $500-5K/mo per client (Stripe) | Week 1-2 |
| 2 | Pharmacy Commissions | 2-5% per order | Week 3-4 |
| 3 | B2B Analytics SaaS | $5-20K/yr per client | Week 5-8 |
| 4 | Consumer Freemium | $2-5/mo per user | Week 9-12 |

## Decisions

| Area | Decision |
|------|----------|
| Billing | Stripe (checkout sessions, customer portal, webhooks) |
| API Auth | `X-API-Key` header with SHA-256 hashed keys, `pa_live_` prefix |
| Rate Limiting | In-memory sliding window (no Redis) |
| Multi-tenancy | Organization model with member roles (owner/admin/analyst/viewer) |
| Subscriptions | Tiered: free/pro/enterprise (B2B) and free/premium (consumer) |
| Commissions | Automatic recording on payment webhook confirmation |
| Premium Gating | Component wrapper (`PremiumGate`) for frontend feature gating |

---

## Phase 1: Premium Data API (Week 1-2) — FASTEST REVENUE

Wrap existing analytics endpoints behind API key auth with Stripe billing. Pharma companies pay $500-5K/mo for programmatic access to Chilean pharma market intelligence.

### 1.1 New Models

| Table | Key Fields |
|-------|-----------|
| `organizations` | name, slug, type (pharma/pharmacy/institution/api_consumer), stripe_customer_id |
| `org_members` | org_id FK, user_id FK, role (owner/admin/analyst/viewer) |
| `subscriptions` | org_id FK, tier (free/pro/enterprise), status (active/canceled/past_due), stripe_subscription_id, current_period_start, current_period_end |
| `api_keys` | org_id FK, name, key_prefix (8 chars for display), key_hash (SHA-256), is_active |
| `api_usage` | api_key_id FK, endpoint, method, status_code, response_time_ms, timestamp |

### 1.2 API Key Design

- Format: `pa_live_` + 32 hex chars (e.g., `pa_live_a1b2c3d4e5f6...`)
- On creation: return plaintext ONCE, store only SHA-256 hash in DB
- Auth flow: `X-API-Key` header → hash lookup → load org → check subscription tier → check rate limits
- Display: show only `key_prefix` (first 8 chars) in management UI

### 1.3 Rate Limiting

| Tier | Req/day | Req/min | Price |
|------|---------|---------|-------|
| Free | 100 | 10 | $0 |
| Pro | 10,000 | 100 | $500/mo |
| Enterprise | Unlimited | 1,000 | $5,000/mo |

Implementation: In-memory sliding window counter in middleware at `backend/app/middleware/rate_limit.py`. No Redis dependency. Counters reset on process restart (acceptable for MVP).

### 1.4 New Endpoints

**Billing** (`/api/v1/billing/`):
- `POST /billing/checkout` — Create Stripe checkout session for pro/enterprise
- `POST /billing/webhook` — Handle Stripe events (subscription created/updated/deleted)
- `POST /billing/portal` — Create Stripe customer portal session

**Organizations** (`/api/v1/organizations/`):
- `POST /organizations/` — Create org (auto-assigns creator as owner)
- `GET /organizations/{slug}` — Get org details
- `PUT /organizations/{slug}` — Update org
- `POST /organizations/{slug}/members` — Invite member
- `GET /organizations/{slug}/members` — List members
- `DELETE /organizations/{slug}/members/{user_id}` — Remove member

**API Keys** (`/api/v1/api-keys/`):
- `POST /api-keys/` — Generate new key (returns plaintext once)
- `GET /api-keys/` — List keys (prefix only)
- `DELETE /api-keys/{id}` — Revoke key
- `GET /api-keys/{id}/usage` — Usage statistics

**Data API** (`/api/v1/data/`):
- `GET /data/prices` — Medication price data with filters
- `GET /data/market-share` — Market share analysis
- `GET /data/procurement` — Government procurement data
- `GET /data/trends` — Sales and pricing trends
- `GET /data/institutions` — Institution-level data
- `GET /data/regions` — Regional distribution data
- `POST /data/export` — CSV export of any dataset

### 1.5 Dependencies & Config

Add to `backend/requirements.txt`:
```
stripe
```

Add to `backend/app/core/config.py`:
```python
STRIPE_SECRET_KEY: str = ""
STRIPE_WEBHOOK_SECRET: str = ""
STRIPE_PRICE_ID_PRO: str = ""
STRIPE_PRICE_ID_ENTERPRISE: str = ""
```

New dependency `get_api_key` in `backend/app/core/deps.py` — extracts `X-API-Key` header, validates against DB, returns org with subscription info.

### 1.6 Frontend

- `frontend/src/pages/PricingPage.js` — 3-tier pricing cards with Stripe checkout buttons
- Add `/pricing` route to `App.js`
- Add "Pricing" nav link to `Layout.js`

---

## Phase 2: Pharmacy Commissions (Week 3-4) — SCALES WITH ORDERS

Track 2-5% commission per order. Triggers automatically when payment confirms.

### 2.1 New Models

| Table | Key Fields |
|-------|-----------|
| `pharmacy_partners` | pharmacy_id FK (unique), commission_rate (default 0.03), is_active, contact_name, contact_email, contact_phone |
| `commissions` | order_id FK (unique), pharmacy_partner_id FK, order_total, commission_rate, commission_amount, status (pending/invoiced/paid) |

### 2.2 Commission Service

`backend/app/services/commission_service.py`:
- `record_commission(db, order)` — Look up pharmacy partner by `order.pharmacy_id`, calculate `order.total * commission_rate`, create Commission record with status `pending`
- Called from both MercadoPago and Transbank webhook handlers after `order.status = confirmed`

### 2.3 Endpoints

`backend/app/api/v1/commissions.py`:
- `GET /commissions/summary` — Monthly totals grouped by pharmacy partner
- `GET /commissions/` — List commissions with date/status/pharmacy filters
- `GET /commissions/export` — CSV export

### 2.4 Modifications

- `backend/app/api/v1/webhooks.py` — Add `commission_service.record_commission(db, order)` call after payment confirmation in both MercadoPago and Transbank handlers
- `frontend/src/pages/PharmacyPartnerPage.js` — Commission dashboard showing partner earnings

---

## Phase 3: B2B Analytics SaaS Dashboard (Week 5-8) — $5-20K/yr PER CLIENT

Polish the existing analytics dashboard into a multi-tenant SaaS product for pharma companies.

### 3.1 New Frontend Pages

| File | Purpose |
|------|---------|
| `frontend/src/pages/OrgDashboardPage.js` | Org-scoped analytics (extends existing AnalyticsDashboardPage patterns) |
| `frontend/src/pages/OrgSettingsPage.js` | Manage members, roles, billing portal link |
| `frontend/src/pages/ApiKeysPage.js` | Key management UI + usage charts |
| `frontend/src/pages/BillingPage.js` | Stripe customer portal redirect |

### 3.2 New Frontend Components

| File | Purpose |
|------|---------|
| `frontend/src/components/OrgSidebar.js` | Org navigation sidebar (dashboard/settings/keys/billing) |
| `frontend/src/components/UsageChart.js` | API usage visualization (Recharts) |
| `frontend/src/hooks/useOrg.js` | Org context hook (current org, membership, tier) |

### 3.3 Modifications

- `frontend/src/pages/AnalyticsDashboardPage.js` — Add export buttons, advanced filters, "Upgrade" CTAs for free-tier users
- `frontend/src/hooks/useAuth.js` — Store org memberships and subscription tier
- `frontend/src/api/client.js` — Add `X-Org-Id` header when in org context
- `frontend/src/App.js` — Add `/org/:slug/*` routes
- `frontend/src/components/Layout.js` — Org switcher dropdown in header

---

## Phase 4: Consumer Freemium (Week 9-12) — $2-5/mo PER USER

Premium consumer features on top of the free marketplace.

### 4.1 New Models

| Table | Key Fields |
|-------|-----------|
| `user_subscriptions` | user_id FK (unique), tier (free/premium), stripe_subscription_id, current_period_end |
| `price_alerts` | user_id FK, medication_id FK, target_price, is_active, last_notified_at |

### 4.2 Premium Features

| Feature | Description | Gate |
|---------|------------|------|
| Price alerts | Set target price → WhatsApp notification when price drops | Premium |
| Price history charts | Historical price trends per medication | Premium |
| Generic alternatives | Show cheaper generic options for brand-name drugs | Premium |
| Prescription management | Photo upload, linked medications | Premium |

### 4.3 New Files

| File | Purpose |
|------|---------|
| `backend/app/services/premium_service.py` | Price alert checking (cron-compatible), generic drug lookup |
| `backend/app/api/v1/premium.py` | Alert CRUD, price history, generic alternatives endpoints |
| `backend/app/schemas/premium.py` | Request/response schemas for premium features |
| `frontend/src/pages/PremiumPage.js` | Feature showcase + Stripe checkout |
| `frontend/src/components/PremiumGate.js` | Wrapper that shows upgrade CTA for gated features |
| `frontend/src/components/charts/PriceHistoryChart.js` | Recharts line chart for price trends |

### 4.4 Modifications

- `frontend/src/pages/MedicationDetailPage.js` — Add price history chart, alert button, generics section (behind PremiumGate)
- `frontend/src/pages/FavoritesPage.js` — Alert management for premium users
- `backend/app/core/deps.py` — Add `require_premium_user` dependency

---

## Files Summary

### New Files (34 total)

**Phase 1 — API + Billing (16 files):**
- `backend/app/models/organization.py`
- `backend/app/models/org_member.py`
- `backend/app/models/subscription.py`
- `backend/app/models/api_key.py`
- `backend/app/models/api_usage.py`
- `backend/app/schemas/organization.py`
- `backend/app/schemas/billing.py`
- `backend/app/schemas/api_key.py`
- `backend/app/services/stripe_service.py`
- `backend/app/middleware/__init__.py`
- `backend/app/middleware/rate_limit.py`
- `backend/app/api/v1/billing.py`
- `backend/app/api/v1/organizations.py`
- `backend/app/api/v1/api_keys.py`
- `backend/app/api/v1/data_api.py`
- `frontend/src/pages/PricingPage.js`

**Phase 2 — Commissions (5 files):**
- `backend/app/models/pharmacy_partner.py`
- `backend/app/models/commission.py`
- `backend/app/schemas/commission.py`
- `backend/app/services/commission_service.py`
- `backend/app/api/v1/commissions.py`

**Phase 3 — B2B SaaS (7 files):**
- `frontend/src/pages/OrgDashboardPage.js`
- `frontend/src/pages/OrgSettingsPage.js`
- `frontend/src/pages/ApiKeysPage.js`
- `frontend/src/pages/BillingPage.js`
- `frontend/src/components/OrgSidebar.js`
- `frontend/src/components/UsageChart.js`
- `frontend/src/hooks/useOrg.js`

**Phase 4 — Consumer Premium (6 files):**
- `backend/app/models/user_subscription.py`
- `backend/app/models/price_alert.py`
- `backend/app/schemas/premium.py`
- `backend/app/services/premium_service.py`
- `backend/app/api/v1/premium.py`
- `frontend/src/pages/PremiumPage.js`

### Modified Files (13 total)

- `backend/requirements.txt` — Add `stripe`
- `backend/app/models/__init__.py` — Register all new models
- `backend/app/core/config.py` — Stripe config vars
- `backend/app/core/deps.py` — `get_api_key`, `get_current_org_member`, `require_premium_user`
- `backend/app/api/v1/routes.py` — Include 6 new routers
- `backend/app/api/v1/webhooks.py` — Commission recording on payment confirm
- `backend/app/main.py` — Rate limit middleware
- `frontend/src/App.js` — New routes
- `frontend/src/components/Layout.js` — Pricing link, org switcher
- `frontend/src/hooks/useAuth.js` — Org memberships + tier
- `frontend/src/api/client.js` — `X-Org-Id` header
- `frontend/src/pages/AnalyticsDashboardPage.js` — Export, filters, upgrade CTAs
- `frontend/src/pages/MedicationDetailPage.js` — Premium features

---

## Verification

1. **Phase 1**: `curl -H "X-API-Key: pa_live_xxx" localhost:8000/api/v1/data/market-share` → JSON with market share data. Without key → 401. Exceed rate limit → 429.
2. **Phase 2**: Create order → confirm payment → check `commissions` table has new record with correct amount.
3. **Phase 3**: Login as org member → see org dashboard with scoped data and export buttons.
4. **Phase 4**: Premium user on MedicationDetailPage → price history chart renders. Set alert → WhatsApp notification when price drops.
