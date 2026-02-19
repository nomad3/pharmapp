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

## Tech Stack

| Capa | Tecnología |
|------|------------|
| Frontend | React 18, React Router, Google Maps API, Axios |
| Backend | FastAPI (Python 3.11), SQLAlchemy, Pydantic |
| Base de datos | PostgreSQL 15 + PostGIS |
| Pagos | Mercado Pago SDK, Transbank SDK |
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

## Arquitectura

```
pharmapp/
├── backend/                    # FastAPI + PostgreSQL/PostGIS
│   ├── app/
│   │   ├── main.py            # App FastAPI, startup, CORS
│   │   ├── core/              # Config, database, security, deps
│   │   ├── models/            # 12 modelos SQLAlchemy
│   │   ├── schemas/           # Validación Pydantic
│   │   ├── api/v1/            # Routers (auth, medications, prices, orders, etc.)
│   │   ├── services/          # Lógica de negocio (geolocation, payments, ServiceTsunami)
│   │   ├── tasks/             # Triggers de scraping
│   │   └── seed.py            # Datos de ejemplo
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React 18 SPA
│   ├── src/
│   │   ├── api/               # Cliente Axios con interceptor JWT
│   │   ├── pages/             # 7 páginas (Home, Search, Detail, Login, Orders, Favorites, Map)
│   │   ├── components/        # SearchBar, PriceCard, PharmacyMap, WhatsAppButton, etc.
│   │   └── hooks/             # useGeolocation, useAuth
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

## Contribuciones

1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "Añadir nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abrir un Pull Request

## Licencia

MIT — ver [LICENSE](LICENSE) para más detalles.
