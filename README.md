# PharmApp — Marketplace de Medicamentos

PharmApp es un marketplace de medicamentos para Chile que agrega precios de cadenas de farmacias (Cruz Verde, Salcobrand, Ahumada, Dr. Simi) y datos gubernamentales (ISP, CENABAST), ayudando a los usuarios a encontrar los medicamentos más baratos cerca de ellos y completar compras a través de un agente de WhatsApp.

## Características

- **Búsqueda de medicamentos** por nombre o principio activo
- **Comparación de precios** en farmacias cercanas ordenados por precio y distancia
- **Geolocalización** con Google Maps para encontrar farmacias cercanas
- **Compra por WhatsApp** — agente que maneja pago, delivery y coordinación
- **Pagos duales** — Mercado Pago y Transbank Webpay
- **Autenticación por teléfono** — OTP enviado por WhatsApp
- **Favoritos e historial** de búsquedas
- **Seguimiento de pedidos** con estados en tiempo real
- **Market Intelligence** — dashboard analytics con datos BMS y Cenabast

## Monetización

PharmApp implementa 4 flujos de revenue:

| Fase | Stream | Modelo |
|------|--------|--------|
| 1 | **Premium Data API** | API key auth + Stripe billing ($500-5K/mo) |
| 2 | **Comisiones de farmacias** | 2-5% por orden confirmada |
| 3 | **B2B Analytics SaaS** | Dashboard multi-tenant para empresas pharma |
| 4 | **Consumer Freemium** | Alertas de precio, historial, genéricos ($2-5/mo) |

### Data API

Acceso programático a inteligencia de mercado farmacéutico chileno:

```bash
# Autenticación por API key
curl -H "X-API-Key: pa_live_xxx" localhost:8000/api/v1/data/market-share

# Endpoints disponibles
GET /api/v1/data/prices         # Precios de medicamentos
GET /api/v1/data/market-share   # Participación de mercado
GET /api/v1/data/procurement    # Datos de procurement público
GET /api/v1/data/trends         # Tendencias de ventas
GET /api/v1/data/institutions   # Datos por institución
GET /api/v1/data/regions        # Distribución regional
POST /api/v1/data/export        # Export CSV
```

Rate limits por tier: Free (100/día), Pro (10K/día), Enterprise (ilimitado).

## Tech Stack

| Capa | Tecnología |
|------|------------|
| Frontend | React 18, React Router, Recharts, Google Maps API, Axios |
| Backend | FastAPI (Python 3.11), SQLAlchemy, Pydantic |
| Base de datos | PostgreSQL 15 + PostGIS |
| Pagos | Mercado Pago SDK, Transbank SDK, Stripe |
| Orquestación | ServiceTsunami (agentes IA, WhatsApp, scraping) |
| Infraestructura | Docker Compose |

## Requisitos Previos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose
- [Node.js 16+](https://nodejs.org/) y npm
- [Python 3.11+](https://www.python.org/downloads/)

## Instalación y Uso

```bash
# Clonar el repositorio
git clone https://github.com/nomad3/pharmapp.git
cd pharmapp

# Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env con tus API keys

# Levantar todos los servicios
docker-compose up --build

# Sembrar datos de ejemplo
docker-compose exec backend python -m app.seed
```

### Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs

### Puertos personalizados

```bash
DB_PORT=5434 API_PORT=8001 WEB_PORT=3001 docker-compose up --build
```

## API Endpoints

### Marketplace

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/v1/auth/otp/request` | No | Enviar OTP por WhatsApp |
| POST | `/api/v1/auth/otp/verify` | No | Verificar OTP, obtener JWT |
| GET | `/api/v1/medications/` | No | Listar medicamentos |
| GET | `/api/v1/medications/search?q=` | No | Buscar por nombre/principio activo |
| GET | `/api/v1/pharmacies/nearby?lat=&lng=&radius_km=` | No | Farmacias cercanas (PostGIS) |
| GET | `/api/v1/prices/compare?medication_id=&lat=&lng=` | No | Comparar precios |
| POST | `/api/v1/orders/` | JWT | Crear pedido + pago |
| GET | `/api/v1/orders/{id}` | JWT | Estado del pedido |
| POST | `/api/v1/webhooks/mercadopago` | No | Callback Mercado Pago |
| POST | `/api/v1/webhooks/transbank` | No | Callback Transbank |
| GET/POST/DELETE | `/api/v1/favorites/` | JWT | Favoritos del usuario |
| GET | `/api/v1/search-history/` | JWT | Historial de búsquedas |

### Monetización

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/v1/billing/checkout` | JWT | Crear sesión Stripe checkout |
| POST | `/api/v1/billing/webhook` | No | Webhook de Stripe |
| POST | `/api/v1/billing/portal` | JWT | Portal de facturación Stripe |
| POST | `/api/v1/organizations/` | JWT | Crear organización |
| GET | `/api/v1/organizations/{slug}` | JWT | Detalle de organización |
| POST | `/api/v1/api-keys/` | JWT | Generar API key |
| GET | `/api/v1/api-keys/` | JWT | Listar API keys |
| GET | `/api/v1/data/*` | API Key | Endpoints de datos (ver arriba) |
| GET | `/api/v1/commissions/summary` | JWT | Resumen de comisiones |
| GET | `/api/v1/commissions/` | JWT | Listar comisiones |
| GET | `/api/v1/premium/status` | JWT | Estado de suscripción premium |
| POST | `/api/v1/premium/alerts` | JWT+Premium | Crear alerta de precio |
| GET | `/api/v1/premium/price-history/{id}` | JWT+Premium | Historial de precios |
| GET | `/api/v1/premium/generics/{id}` | JWT+Premium | Alternativas genéricas |

## Arquitectura

```
pharmapp/
├── backend/                    # FastAPI + PostgreSQL/PostGIS
│   ├── app/
│   │   ├── main.py            # App FastAPI, startup, CORS, rate limiting
│   │   ├── core/              # Config, database, security, deps
│   │   ├── models/            # 21 modelos SQLAlchemy
│   │   ├── schemas/           # Validación Pydantic
│   │   ├── api/v1/            # Routers (auth, medications, prices, orders, billing, data, etc.)
│   │   ├── services/          # Lógica de negocio (payments, analytics, stripe, commissions, premium)
│   │   ├── middleware/        # Rate limiting por tier
│   │   ├── tasks/             # Triggers de scraping
│   │   └── seed.py            # Datos de ejemplo
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React 18 SPA
│   ├── src/
│   │   ├── api/               # Cliente Axios con interceptor JWT + Org headers
│   │   ├── pages/             # 14 páginas (Home, Search, Detail, Login, Orders, Favorites, Map,
│   │   │                      #   Analytics, Pricing, Premium, OrgDashboard, OrgSettings, ApiKeys, Billing)
│   │   ├── components/        # SearchBar, PriceCard, OrgSidebar, PremiumGate, UsageChart, etc.
│   │   └── hooks/             # useGeolocation, useAuth, useOrg
│   ├── nginx.conf             # Proxy /api/v1 → backend, SPA fallback
│   └── Dockerfile
├── docker-compose.yml          # db + backend + frontend
└── docs/plans/                 # Documentos de diseño e implementación
```

## Integración con ServiceTsunami

PharmApp utiliza [ServiceTsunami](../servicetsunami-agents) como motor de orquestación de agentes:

- **WhatsApp OTP** — Envío de códigos de verificación
- **Flujo de compra WhatsApp** — Confirmación, link de pago, coordinación de delivery
- **Pipelines de scraping** — Agente web_researcher extrae precios de sitios de farmacias
- **Búsqueda conversacional** — Búsqueda de medicamentos por chat de WhatsApp
- **Alertas de precio** — Notificación WhatsApp cuando el precio baja al objetivo del usuario

## Variables de Entorno

```bash
# Base
DATABASE_URL=postgresql://postgres:postgres@db:5432/pharmapp
SECRET_KEY=your-secret-key

# ServiceTsunami
SERVICETSUNAMI_API_URL=http://localhost:8001
SERVICETSUNAMI_EMAIL=
SERVICETSUNAMI_PASSWORD=

# Payments
MERCADOPAGO_ACCESS_TOKEN=
TRANSBANK_COMMERCE_CODE=
TRANSBANK_API_KEY=
GOOGLE_MAPS_API_KEY=

# Stripe (monetización)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID_PRO=
STRIPE_PRICE_ID_ENTERPRISE=
STRIPE_PRICE_ID_PREMIUM=
```

## Contribuciones

1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "Añadir nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abrir un Pull Request

## Licencia

MIT — ver [LICENSE](LICENSE) para más detalles.
