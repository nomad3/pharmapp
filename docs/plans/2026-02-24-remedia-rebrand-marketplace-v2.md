# Remedia — Rebrand & Marketplace V2

**Date:** 2026-02-24
**Status:** Approved

---

## Overview

Rebrand PharmApp → **Remedia** with a new visual identity (Teal + Amber palette), then build four feature areas to make the marketplace production-ready: Admin Dashboard, Search & Discovery, User Profile, and Production Hardening.

---

## 1. Rebrand to Remedia

### Text Changes
- All "PharmApp" references → "Remedia" across frontend and backend
- WhatsApp message templates: update all 15+ templates in `whatsapp.py`
- FastAPI app title: `PharmApp API` → `Remedia API`
- Frontend: navbar brand, page titles (Helmet), footer, error messages
- README, CLAUDE.md, docker-compose labels

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary` | `#0D9488` Deep Teal | Nav, buttons, trust elements |
| `--color-accent` | `#D97706` Amber | Price badges, deals, CTAs, "Mejor precio" |
| `--color-dark` | `#134E4A` Dark Teal | Headings, nav background |
| `--color-bg-light` | `#F0FDFA` Teal Wash | Page backgrounds |
| `--color-bg-warm` | `#FFFBEB` Amber Wash | Deal cards, highlights |
| `--color-success` | `#10B981` Emerald | Confirmations, in-stock |
| `--color-danger` | `#EF4444` Red | Errors, out-of-stock |
| `--color-text` | `#1F2937` Dark Gray | Body text |
| `--color-text-light` | `#6B7280` Gray | Secondary text |

### Implementation Approach
- Define CSS custom properties (variables) in `:root` so colors are centralized
- Replace all hardcoded hex values in App.css with CSS variables
- Update component inline styles to use the variables
- Navbar: dark teal background (`--color-dark`), white text
- "Mejor precio" badge: amber background
- CTA buttons: teal primary, amber for purchase actions
- Card backgrounds: white, page backgrounds: teal wash

---

## 2. Admin Dashboard

### Access Control
- Add `is_admin: bool = False` column to User model
- Add `require_admin` dependency in FastAPI
- Frontend: `/admin/*` routes protected by admin check
- Admin nav only visible to admin users

### Pages

#### 2a. Orders Management (`/admin/orders`)
- Table: order ID, user phone, status, total, payment provider, created_at
- Filters: status dropdown, date range picker
- Click row → order detail with items, status timeline
- Status update buttons: "Mark Delivering", "Mark Completed", "Cancel"
- Each status change sends WhatsApp notification (already built)

#### 2b. Users (`/admin/users`)
- Table: phone, created_at, order count, total spent
- Search by phone number
- Click → user detail: order history, favorites, price alerts

#### 2c. Scraping Monitor (`/admin/scraping`)
- Cards per chain: last run status, products found, prices upserted, errors
- "Run Now" button per chain (calls existing `/scraping/catalog` endpoint)
- Recent runs table (uses existing `/scraping/runs` endpoint)
- Next scheduled run time (from `/scraping/schedule`)

#### 2d. System Dashboard (`/admin/dashboard`)
- Summary cards: total users, total orders (today/week/month), revenue, active medications
- Recent orders list (last 10)
- Payment success rate (approved / total)
- Scraping health (last run age, error rate)

### Backend Endpoints
- `GET /admin/stats` — aggregate stats (users, orders, revenue, medications)
- `GET /admin/users` — paginated user list with order counts
- `GET /admin/users/{id}` — user detail with orders
- Order endpoints already exist (`GET /orders/admin/all`, `PATCH /orders/{id}/status`)

---

## 3. Search & Discovery

### 3a. Search Filters
- Filter panel on search results page (collapsible on mobile)
- Filters:
  - **Drug form**: tablet, capsule, liquid, cream, injectable, other (from medication.form field)
  - **Requires prescription**: Yes / No / All
  - **Pharmacy chain**: checkboxes for Cruz Verde, Salcobrand, Ahumada, Dr. Simi
  - **Price range**: min/max slider or inputs
- Filters applied as query params: `?q=losartan&form=tablet&prescription=false&chain=cruz_verde&price_min=1000&price_max=5000`
- Backend: add filter params to `/medications/search` endpoint

### 3b. Active Ingredient Search Cleanup
- Clean Cenabast-style prefixes ("1-aciclovir" → "aciclovir") in search matching
- Add `cleaned_ingredient` computed field or clean on search query time
- Search should match both `name` and `active_ingredient` (cleaned)

### 3c. Shopping Cart
- Cart state in React context (localStorage-persisted)
- Cart model: `[{medication_id, pharmacy_id, price_id, quantity, price, name, pharmacy_name}]`
- Add to cart button on medication detail page (alongside "Comprar" which is instant checkout)
- Cart icon in navbar with item count badge
- Cart page (`/cart`): list items, adjust quantities, remove, total, proceed to checkout
- Checkout: create order with multiple OrderItems

### 3d. Autocomplete Search
- Debounced search-as-you-type (300ms debounce)
- `GET /medications/autocomplete?q=para` → returns top 8 name matches
- Dropdown below search input showing suggestions
- Click suggestion → navigate to medication detail

---

## 4. User Profile & Settings

### 4a. Profile Page (`/profile`)
- View phone number (read-only, change requires new OTP)
- Delivery addresses: list, add new, edit, delete, set default
- Backend: `GET/POST/PUT/DELETE /users/addresses`
- Address model already exists (DeliveryAddress)

### 4b. Notification Preferences
- Toggle WhatsApp notifications per type:
  - Order updates (default: on)
  - Price alerts (default: on)
  - Refill reminders (default: on)
  - Promotions (default: off)
- Backend: add `notification_prefs: JSON` column to User model
- Check prefs before sending each WhatsApp message

### 4c. Order History Improvements
- Filter orders by date range
- "Re-order" button → pre-fills cart with same items
- Show payment method used

---

## 5. Production Hardening

### 5a. JWT Token Refresh
- `POST /auth/refresh` — accepts current valid JWT, returns new one
- Frontend Axios interceptor: on 401, try refresh, retry request
- Refresh window: tokens valid for 24h, refresh allowed within last 2h

### 5b. Health Check
- `GET /health` — returns:
  - DB connectivity (ping)
  - Last scrape run age (warn if >36h)
  - Redis connectivity (if applicable)
- Used by Docker healthcheck and monitoring

### 5c. Structured Logging
- JSON-formatted logs with: timestamp, level, message, request_id, user_id
- Add request_id middleware (UUID per request in header)
- Log all API requests (method, path, status, duration)

### 5d. Error Tracking
- Sentry SDK for backend (FastAPI integration)
- Sentry SDK for frontend (React error boundary)
- Environment-based DSN (only active in production)

---

## Implementation Order

1. **Rebrand** (touches everything, do first to avoid merge conflicts)
2. **Admin Dashboard** (operate the marketplace)
3. **Search & Discovery** (improve user conversion)
4. **User Profile** (polish user experience)
5. **Production Hardening** (prepare for launch)

---

## Files Impact

### Modified (major):
- `frontend/src/App.css` — full color palette swap + CSS variables
- `frontend/src/App.js` — new routes (/admin/*, /cart, /profile), cart context
- `frontend/src/pages/*.js` — rebrand text, color updates
- `backend/app/services/whatsapp.py` — all message templates rebrand
- `backend/app/main.py` — title, health endpoint
- `backend/app/models/user.py` — is_admin, notification_prefs
- `backend/app/api/v1/medications.py` — search filters, autocomplete
- `backend/app/core/security.py` — refresh token logic

### New:
- `frontend/src/pages/admin/` — AdminDashboard, AdminOrders, AdminUsers, AdminScraping
- `frontend/src/pages/CartPage.js` — shopping cart
- `frontend/src/pages/ProfilePage.js` — user profile
- `frontend/src/context/CartContext.js` — cart state management
- `frontend/src/components/SearchFilters.js` — filter panel
- `frontend/src/components/Autocomplete.js` — search suggestions
- `backend/app/api/v1/admin.py` — admin endpoints
- `backend/app/core/deps.py` — require_admin dependency
- `backend/app/middleware/request_id.py` — request ID middleware
