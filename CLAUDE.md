# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Remedia is a medication marketplace for Chile that helps people find the cheapest legal medicines near them. It aggregates pricing from pharmacy chains (Cruz Verde, Salcobrand, Ahumada, Dr. Simi) and government data (ISP, CENABAST), and completes purchases through a WhatsApp agent handling payment, delivery, and coordination.

Uses **ServiceTsunami** (`../servicetsunami-agents`) as the agent orchestration engine for WhatsApp messaging, web scraping pipelines, and AI agent interactions.

## Build & Run Commands

```bash
# Full stack with Docker (primary way to run)
docker-compose up --build

# Start with custom ports
DB_PORT=5433 API_PORT=8000 WEB_PORT=3000 docker-compose up --build

# Frontend dev server
cd frontend && npm start

# Backend standalone
cd backend && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Seed database with sample data
docker-compose exec backend python -m app.seed

# Frontend tests
cd frontend && npm test
```

## Architecture

**Backend** (`/backend`): FastAPI (Python 3.11) with own PostgreSQL + PostGIS database.
- Entry: `app/main.py` → includes `api/v1/routes.py` which aggregates all routers
- Config: `app/core/config.py` (pydantic-settings, loads from `.env`)
- Auth: Phone + OTP via WhatsApp, JWT tokens (`app/core/security.py`, `app/core/deps.py`)
- Models: 12 SQLAlchemy models in `app/models/` (users, medications, pharmacies, prices, orders, favorites, search history)
- Schemas: Pydantic validation in `app/schemas/`
- Services: `app/services/` — geolocation (PostGIS), price_engine, order_service, payment_service, servicetsunami client
- Scraping: `app/tasks/scraping.py` triggers ServiceTsunami pipelines

**Frontend** (`/frontend`): React 18 SPA, mobile-first.
- React Router for navigation (7 routes)
- Hooks: `useGeolocation` (browser GPS), `useAuth` (OTP flow + JWT)
- API client: `src/api/client.js` (Axios with auth interceptor)
- Google Maps for pharmacy locations
- Nginx proxy: `/api/v1` → backend:8000, SPA fallback

**Docker Compose**: 3 services — `db` (PostGIS 15), `backend` (FastAPI), `frontend` (React + Nginx)

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/otp/request` | No | Send OTP via WhatsApp |
| POST | `/api/v1/auth/otp/verify` | No | Verify OTP, get JWT |
| GET | `/api/v1/medications/` | No | List medications |
| GET | `/api/v1/medications/search?q=` | No | Search by name/ingredient |
| GET | `/api/v1/pharmacies/nearby?lat=&lng=&radius_km=` | No | Nearby pharmacies (PostGIS) |
| GET | `/api/v1/prices/compare?medication_id=&lat=&lng=` | No | Price comparison ranked by price |
| POST | `/api/v1/orders/` | JWT | Create order + payment |
| GET | `/api/v1/orders/{id}` | JWT | Order status |
| POST | `/api/v1/webhooks/mercadopago` | No | MercadoPago IPN |
| POST | `/api/v1/webhooks/transbank` | No | Transbank callback |
| GET/POST/DELETE | `/api/v1/favorites/` | JWT | User favorites |
| GET | `/api/v1/search-history/` | JWT | Search history |
| POST | `/api/v1/admin/trigger-scraping` | No | Trigger scraping pipelines |

## ServiceTsunami Integration

Remedia calls ServiceTsunami (`../servicetsunami-agents`) via `app/services/servicetsunami.py`:
- **WhatsApp OTP**: Sends verification codes through ServiceTsunami's SkillRouter
- **WhatsApp purchase flow**: Order confirmation, payment link delivery, delivery coordination
- **Scraping pipelines**: Triggers web_researcher agent to scrape pharmacy chain websites
- Auth: form-encoded login to get JWT, then Bearer token for all calls
- Endpoints used: `/api/v1/auth/login`, `/api/v1/chat/sessions`, `/api/v1/chat/sessions/{id}/messages`, `/api/v1/data_pipelines/{id}/execute`

## Payments

Dual payment provider support:
- **Mercado Pago**: SDK creates payment preference, returns checkout URL
- **Transbank Webpay**: SDK creates transaction, returns redirect URL
- WhatsApp agent sends payment link to user
- Webhooks update order status on payment completion

## Key Conventions

- Python 3.11, JavaScript (no TypeScript)
- SQLAlchemy models with UUID primary keys and TimestampMixin (created_at, updated_at)
- PostGIS geography columns for all location data (SRID 4326)
- Pydantic schemas with `from_attributes = True` for ORM serialization
- FastAPI dependency injection for DB sessions and auth
- Environment config via pydantic-settings + `.env` file
- Prices in CLP (Chilean pesos)
- Branch convention: `feature/` prefix for new work

## Access Points

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ServiceTsunami: http://localhost:8001

## Design & Plans

- Design doc: `docs/plans/2026-02-19-marketplace-design.md`
- Implementation plan: `docs/plans/2026-02-19-marketplace-implementation-plan.md`
