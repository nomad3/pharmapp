# PharmApp Marketplace Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform PharmApp from scaffolding into a full medication marketplace for Chile with geolocation-based price comparison, WhatsApp purchase flow via ServiceTsunami, and Mercado Pago + Transbank payments.

**Architecture:** Thick FastAPI backend with own PostgreSQL+PostGIS database for domain data (medications, pharmacies, prices, orders, users). ServiceTsunami is called only for WhatsApp messaging (OTP + purchase flow), web scraping pipelines, and agent orchestration. React frontend is mobile-first SPA with Google Maps.

**Tech Stack:** FastAPI, SQLAlchemy, PostGIS, Pydantic, React 18, React Router, Google Maps API, Axios, Docker Compose, Mercado Pago SDK, Transbank SDK

**Design doc:** `docs/plans/2026-02-19-marketplace-design.md`

---

## Phase 1: Backend Foundation

### Task 1: Update dependencies and project config

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`

**Step 1: Update requirements.txt**

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
geoalchemy2
psycopg2-binary
python-jose[cryptography]
passlib[bcrypt]
httpx
mercadopago
transbank-sdk
alembic
```

**Step 2: Create config.py with pydantic-settings**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/pharmapp"
    SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    OTP_EXPIRATION_MINUTES: int = 5
    SERVICETSUNAMI_API_URL: str = "http://localhost:8001"
    SERVICETSUNAMI_EMAIL: str = ""
    SERVICETSUNAMI_PASSWORD: str = ""
    MERCADOPAGO_ACCESS_TOKEN: str = ""
    TRANSBANK_COMMERCE_CODE: str = ""
    TRANSBANK_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 3: Create `__init__.py`**

Empty file at `backend/app/core/__init__.py`.

**Step 4: Commit**

```bash
git add backend/requirements.txt backend/app/core/
git commit -m "feat: add backend dependencies and config module"
```

---

### Task 2: Database engine and session setup

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`

**Step 1: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2: Create base model**

```python
# backend/app/models/base.py
import uuid
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Step 3: Create models `__init__.py`**

```python
# backend/app/models/__init__.py
from app.models.base import Base
```

**Step 4: Commit**

```bash
git add backend/app/core/database.py backend/app/models/
git commit -m "feat: add SQLAlchemy database engine and base model"
```

---

### Task 3: User and OTP models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/otp.py`
- Create: `backend/app/models/delivery_address.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Create user model**

```python
# backend/app/models/user.py
from sqlalchemy import Column, String
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class User(TimestampMixin, Base):
    __tablename__ = "users"
    phone_number = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    comuna = Column(String, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
```

**Step 2: Create OTP model**

```python
# backend/app/models/otp.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class OtpCode(TimestampMixin, Base):
    __tablename__ = "otp_codes"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified = Column(Boolean, default=False)
```

**Step 3: Create delivery address model**

```python
# backend/app/models/delivery_address.py
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class DeliveryAddress(TimestampMixin, Base):
    __tablename__ = "delivery_addresses"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    label = Column(String, default="home")
    address = Column(String, nullable=False)
    comuna = Column(String, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    instructions = Column(Text, nullable=True)
```

**Step 4: Update models/__init__.py**

```python
from app.models.base import Base
from app.models.user import User
from app.models.otp import OtpCode
from app.models.delivery_address import DeliveryAddress
```

**Step 5: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add user, OTP, and delivery address models"
```

---

### Task 4: Catalog models (medications, pharmacies, prices)

**Files:**
- Create: `backend/app/models/medication.py`
- Create: `backend/app/models/pharmacy.py`
- Create: `backend/app/models/price.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Create medication model**

```python
# backend/app/models/medication.py
from sqlalchemy import Column, String, Boolean
from app.models.base import Base, TimestampMixin

class Medication(TimestampMixin, Base):
    __tablename__ = "medications"
    name = Column(String, nullable=False, index=True)
    active_ingredient = Column(String, nullable=True, index=True)
    dosage = Column(String, nullable=True)
    form = Column(String, nullable=True)  # tablet, syrup, injection, etc.
    lab = Column(String, nullable=True)
    isp_registry_number = Column(String, nullable=True, unique=True)
    requires_prescription = Column(Boolean, default=False)
```

**Step 2: Create pharmacy model**

```python
# backend/app/models/pharmacy.py
from sqlalchemy import Column, String
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class Pharmacy(TimestampMixin, Base):
    __tablename__ = "pharmacies"
    chain = Column(String, nullable=False, index=True)  # cruz_verde, salcobrand, ahumada
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    comuna = Column(String, nullable=False, index=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    phone = Column(String, nullable=True)
    hours = Column(String, nullable=True)
```

**Step 3: Create price model**

```python
# backend/app/models/price.py
from sqlalchemy import Column, Float, Boolean, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class Price(TimestampMixin, Base):
    __tablename__ = "prices"
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False, index=True)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
    source_url = Column(String, nullable=True)
    scraped_at = Column(DateTime(timezone=True), nullable=True)
```

**Step 4: Update models/__init__.py to include all catalog models**

```python
from app.models.base import Base
from app.models.user import User
from app.models.otp import OtpCode
from app.models.delivery_address import DeliveryAddress
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
```

**Step 5: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add medication, pharmacy, and price catalog models"
```

---

### Task 5: Order models

**Files:**
- Create: `backend/app/models/order.py`
- Create: `backend/app/models/order_item.py`
- Create: `backend/app/models/order_delivery.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Create order model**

```python
# backend/app/models/order.py
import enum
from sqlalchemy import Column, String, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class OrderStatus(str, enum.Enum):
    pending = "pending"
    payment_sent = "payment_sent"
    confirmed = "confirmed"
    delivering = "delivering"
    completed = "completed"
    cancelled = "cancelled"

class PaymentProvider(str, enum.Enum):
    mercadopago = "mercadopago"
    transbank = "transbank"

class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pharmacy_id = Column(UUID(as_uuid=True), ForeignKey("pharmacies.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    payment_provider = Column(Enum(PaymentProvider), nullable=True)
    payment_url = Column(String, nullable=True)
    payment_status = Column(String, nullable=True)
    total = Column(Float, nullable=False, default=0)
```

**Step 2: Create order_item model**

```python
# backend/app/models/order_item.py
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class OrderItem(TimestampMixin, Base):
    __tablename__ = "order_items"
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False)
    price_id = Column(UUID(as_uuid=True), ForeignKey("prices.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False)
```

**Step 3: Create order_delivery model**

```python
# backend/app/models/order_delivery.py
import enum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class DeliveryStatus(str, enum.Enum):
    assigned = "assigned"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"

class OrderDelivery(TimestampMixin, Base):
    __tablename__ = "order_deliveries"
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, unique=True)
    delivery_address_id = Column(UUID(as_uuid=True), ForeignKey("delivery_addresses.id"), nullable=False)
    rider_name = Column(String, nullable=True)
    rider_phone = Column(String, nullable=True)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.assigned)
    eta = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
```

**Step 4: Update models/__init__.py**

Add imports for `Order`, `OrderItem`, `OrderDelivery`.

**Step 5: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add order, order item, and delivery models"
```

---

### Task 6: User activity models (favorites, search history)

**Files:**
- Create: `backend/app/models/user_favorite.py`
- Create: `backend/app/models/search_history.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Create user_favorite model**

```python
# backend/app/models/user_favorite.py
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin

class UserFavorite(TimestampMixin, Base):
    __tablename__ = "user_favorites"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "medication_id"),)
```

**Step 2: Create search_history model**

```python
# backend/app/models/search_history.py
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from app.models.base import Base, TimestampMixin

class SearchHistory(TimestampMixin, Base):
    __tablename__ = "search_history"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    query_text = Column(String, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    results_count = Column(Integer, default=0)
```

**Step 3: Update models/__init__.py with all models**

**Step 4: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add user favorites and search history models"
```

---

### Task 7: Pydantic schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/medication.py`
- Create: `backend/app/schemas/pharmacy.py`
- Create: `backend/app/schemas/price.py`
- Create: `backend/app/schemas/order.py`
- Create: `backend/app/schemas/favorite.py`

**Step 1: Create auth schemas**

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel

class OtpRequest(BaseModel):
    phone_number: str

class OtpVerify(BaseModel):
    phone_number: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    phone_number: str
    name: str | None
    comuna: str | None

    class Config:
        from_attributes = True
```

**Step 2: Create medication schemas**

```python
# backend/app/schemas/medication.py
from pydantic import BaseModel

class MedicationOut(BaseModel):
    id: str
    name: str
    active_ingredient: str | None
    dosage: str | None
    form: str | None
    lab: str | None
    isp_registry_number: str | None
    requires_prescription: bool

    class Config:
        from_attributes = True
```

**Step 3: Create pharmacy schemas**

```python
# backend/app/schemas/pharmacy.py
from pydantic import BaseModel

class PharmacyOut(BaseModel):
    id: str
    chain: str
    name: str
    address: str
    comuna: str
    phone: str | None
    hours: str | None
    distance_km: float | None = None

    class Config:
        from_attributes = True
```

**Step 4: Create price schemas**

```python
# backend/app/schemas/price.py
from pydantic import BaseModel
from app.schemas.pharmacy import PharmacyOut

class PriceOut(BaseModel):
    id: str
    medication_id: str
    pharmacy_id: str
    price: float
    in_stock: bool
    scraped_at: str | None

    class Config:
        from_attributes = True

class PriceCompareItem(BaseModel):
    price: float
    in_stock: bool
    pharmacy: PharmacyOut
    distance_km: float | None = None
```

**Step 5: Create order schemas**

```python
# backend/app/schemas/order.py
from pydantic import BaseModel

class OrderItemCreate(BaseModel):
    medication_id: str
    price_id: str
    quantity: int = 1

class OrderCreate(BaseModel):
    pharmacy_id: str
    items: list[OrderItemCreate]
    payment_provider: str  # "mercadopago" or "transbank"
    delivery_address_id: str | None = None

class OrderOut(BaseModel):
    id: str
    status: str
    payment_provider: str | None
    payment_url: str | None
    total: float
    created_at: str

    class Config:
        from_attributes = True
```

**Step 6: Create favorite schemas**

```python
# backend/app/schemas/favorite.py
from pydantic import BaseModel

class FavoriteCreate(BaseModel):
    medication_id: str

class FavoriteOut(BaseModel):
    id: str
    medication_id: str
    created_at: str

    class Config:
        from_attributes = True
```

**Step 7: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic request/response schemas"
```

---

### Task 8: Security module (JWT + OTP)

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/deps.py`

**Step 1: Create security.py**

```python
# backend/app/core/security.py
import random
import string
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import settings

def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
```

**Step 2: Create deps.py (FastAPI dependencies)**

```python
# backend/app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

**Step 3: Commit**

```bash
git add backend/app/core/
git commit -m "feat: add JWT and OTP security module with auth dependency"
```

---

### Task 9: ServiceTsunami client

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/servicetsunami.py`

**Step 1: Create the ServiceTsunami HTTP client**

```python
# backend/app/services/servicetsunami.py
import httpx
from app.core.config import settings

class ServiceTsunamiClient:
    def __init__(self):
        self.base_url = settings.SERVICETSUNAMI_API_URL
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                data={
                    "username": settings.SERVICETSUNAMI_EMAIL,
                    "password": settings.SERVICETSUNAMI_PASSWORD,
                },
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    async def send_whatsapp(self, phone_number: str, message: str) -> dict:
        """Send a WhatsApp message via ServiceTsunami SkillRouter."""
        async with httpx.AsyncClient() as client:
            # Create a chat session for this interaction
            headers = await self._headers()
            session_resp = await client.post(
                f"{self.base_url}/api/v1/chat/sessions",
                headers=headers,
                json={"title": f"WhatsApp to {phone_number}"},
            )
            session_resp.raise_for_status()
            session_id = session_resp.json()["id"]

            # Send the message through the agent
            msg_resp = await client.post(
                f"{self.base_url}/api/v1/chat/sessions/{session_id}/messages",
                headers=headers,
                json={"content": f"Send WhatsApp to {phone_number}: {message}"},
            )
            msg_resp.raise_for_status()
            return msg_resp.json()

    async def trigger_scraping_pipeline(self, pipeline_id: str) -> dict:
        """Trigger a scraping pipeline execution."""
        async with httpx.AsyncClient() as client:
            headers = await self._headers()
            resp = await client.post(
                f"{self.base_url}/api/v1/data_pipelines/{pipeline_id}/execute",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

tsunami_client = ServiceTsunamiClient()
```

**Step 2: Commit**

```bash
git add backend/app/services/
git commit -m "feat: add ServiceTsunami HTTP client for WhatsApp and scraping"
```

---

## Phase 2: API Routes

### Task 10: Auth routes (OTP request + verify)

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/routes.py`
- Modify: `backend/app/main.py`

**Step 1: Create auth router**

```python
# backend/app/api/v1/auth.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import generate_otp, create_access_token
from app.models.user import User
from app.models.otp import OtpCode
from app.schemas.auth import OtpRequest, OtpVerify, Token
from app.services.servicetsunami import tsunami_client

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/otp/request")
async def request_otp(body: OtpRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == body.phone_number).first()
    if not user:
        user = User(phone_number=body.phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)

    code = generate_otp()
    otp = OtpCode(
        user_id=user.id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(otp)
    db.commit()

    await tsunami_client.send_whatsapp(
        body.phone_number,
        f"Tu código de verificación PharmApp es: {code}"
    )
    return {"message": "OTP sent via WhatsApp"}

@router.post("/otp/verify", response_model=Token)
def verify_otp(body: OtpVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == body.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user.id,
            OtpCode.code == body.code,
            OtpCode.verified == False,
            OtpCode.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp.verified = True
    db.commit()

    token = create_access_token(str(user.id))
    return Token(access_token=token)
```

**Step 2: Create routes.py (router aggregator)**

```python
# backend/app/api/v1/routes.py
from fastapi import APIRouter
from app.api.v1 import auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
```

**Step 3: Rewrite main.py**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router
from app.models import Base
from app.core.database import engine

app = FastAPI(title="PharmApp API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
```

**Step 4: Commit**

```bash
git add backend/app/
git commit -m "feat: add auth routes with OTP request and verify via WhatsApp"
```

---

### Task 11: Medications and pharmacies routes

**Files:**
- Create: `backend/app/api/v1/medications.py`
- Create: `backend/app/api/v1/pharmacies.py`
- Create: `backend/app/services/geolocation.py`
- Modify: `backend/app/api/v1/routes.py`

**Step 1: Create geolocation service**

```python
# backend/app/services/geolocation.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint

def make_point(lng: float, lat: float):
    return func.ST_SetSRID(ST_MakePoint(lng, lat), 4326)

def nearby_query(db: Session, model, lat: float, lng: float, radius_km: float):
    """Return query filtered by distance with distance_km column."""
    user_point = make_point(lng, lat)
    distance = ST_Distance(model.location, func.cast(user_point, Geography)).label("distance_m")
    return (
        db.query(model, distance)
        .filter(ST_DWithin(model.location, func.cast(user_point, Geography), radius_km * 1000))
        .order_by(distance)
    )
```

**Step 2: Create medications router**

```python
# backend/app/api/v1/medications.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.medication import Medication
from app.schemas.medication import MedicationOut

router = APIRouter(prefix="/medications", tags=["medications"])

@router.get("/", response_model=list[MedicationOut])
def list_medications(db: Session = Depends(get_db)):
    return db.query(Medication).all()

@router.get("/search", response_model=list[MedicationOut])
def search_medications(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    return (
        db.query(Medication)
        .filter(
            Medication.name.ilike(f"%{q}%")
            | Medication.active_ingredient.ilike(f"%{q}%")
        )
        .limit(50)
        .all()
    )
```

**Step 3: Create pharmacies router**

```python
# backend/app/api/v1/pharmacies.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pharmacy import Pharmacy
from app.schemas.pharmacy import PharmacyOut
from app.services.geolocation import nearby_query

router = APIRouter(prefix="/pharmacies", tags=["pharmacies"])

@router.get("/nearby", response_model=list[PharmacyOut])
def nearby_pharmacies(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(default=5.0),
    db: Session = Depends(get_db),
):
    results = nearby_query(db, Pharmacy, lat, lng, radius_km).limit(50).all()
    pharmacies = []
    for pharmacy, distance_m in results:
        out = PharmacyOut.model_validate(pharmacy)
        out.distance_km = round(distance_m / 1000, 2)
        pharmacies.append(out)
    return pharmacies
```

**Step 4: Add routes to routes.py**

```python
from app.api.v1 import auth, medications, pharmacies
api_router.include_router(medications.router)
api_router.include_router(pharmacies.router)
```

**Step 5: Commit**

```bash
git add backend/app/
git commit -m "feat: add medication search and nearby pharmacy endpoints with PostGIS"
```

---

### Task 12: Price comparison route

**Files:**
- Create: `backend/app/api/v1/prices.py`
- Create: `backend/app/services/price_engine.py`
- Modify: `backend/app/api/v1/routes.py`

**Step 1: Create price engine service**

```python
# backend/app/services/price_engine.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance
from app.models.price import Price
from app.models.pharmacy import Pharmacy
from app.services.geolocation import make_point

def compare_prices(db: Session, medication_id: str, lat: float, lng: float, radius_km: float = 10.0):
    """Return prices for a medication at nearby pharmacies, sorted by price."""
    user_point = make_point(lng, lat)
    distance = ST_Distance(Pharmacy.location, func.cast(user_point, Geography)).label("distance_m")

    results = (
        db.query(Price, Pharmacy, distance)
        .join(Pharmacy, Price.pharmacy_id == Pharmacy.id)
        .filter(
            Price.medication_id == medication_id,
            Price.in_stock == True,
            ST_Distance(Pharmacy.location, func.cast(user_point, Geography)) <= radius_km * 1000,
        )
        .order_by(Price.price.asc())
        .all()
    )
    return results
```

**Step 2: Create prices router**

```python
# backend/app/api/v1/prices.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.price import PriceCompareItem
from app.schemas.pharmacy import PharmacyOut
from app.services.price_engine import compare_prices

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/compare", response_model=list[PriceCompareItem])
def compare(
    medication_id: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(default=10.0),
    db: Session = Depends(get_db),
):
    results = compare_prices(db, medication_id, lat, lng, radius_km)
    items = []
    for price, pharmacy, distance_m in results:
        pharmacy_out = PharmacyOut.model_validate(pharmacy)
        pharmacy_out.distance_km = round(distance_m / 1000, 2)
        items.append(PriceCompareItem(
            price=price.price,
            in_stock=price.in_stock,
            pharmacy=pharmacy_out,
            distance_km=pharmacy_out.distance_km,
        ))
    return items
```

**Step 3: Add to routes.py**

**Step 4: Commit**

```bash
git add backend/app/
git commit -m "feat: add price comparison endpoint with distance ranking"
```

---

### Task 13: Orders route + payment service

**Files:**
- Create: `backend/app/services/payment_service.py`
- Create: `backend/app/services/order_service.py`
- Create: `backend/app/api/v1/orders.py`
- Create: `backend/app/api/v1/webhooks.py`
- Modify: `backend/app/api/v1/routes.py`

**Step 1: Create payment service**

```python
# backend/app/services/payment_service.py
import mercadopago
from transbank.webpay.webpay_plus.transaction import Transaction
from app.core.config import settings

def create_mercadopago_preference(order_id: str, items: list, total: float) -> str:
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    preference_data = {
        "items": [{"title": "Medicamentos PharmApp", "quantity": 1, "unit_price": total}],
        "external_reference": order_id,
        "back_urls": {
            "success": f"https://pharmapp.cl/orders/{order_id}?status=success",
            "failure": f"https://pharmapp.cl/orders/{order_id}?status=failure",
        },
        "notification_url": f"https://pharmapp.cl/api/v1/webhooks/mercadopago",
    }
    result = sdk.preference().create(preference_data)
    return result["response"]["init_point"]

def create_transbank_transaction(order_id: str, total: float) -> str:
    tx = Transaction()
    resp = tx.create(
        buy_order=order_id[:26],
        session_id=order_id[:61],
        amount=total,
        return_url=f"https://pharmapp.cl/api/v1/webhooks/transbank",
    )
    return resp["url"] + "?token_ws=" + resp["token"]
```

**Step 2: Create order service**

```python
# backend/app/services/order_service.py
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.price import Price
from app.schemas.order import OrderCreate
from app.services.payment_service import create_mercadopago_preference, create_transbank_transaction
from app.services.servicetsunami import tsunami_client

async def create_order(db: Session, user_id: str, phone_number: str, data: OrderCreate) -> Order:
    # Calculate total
    total = 0.0
    items = []
    for item_data in data.items:
        price = db.query(Price).filter(Price.id == item_data.price_id).first()
        subtotal = price.price * item_data.quantity
        total += subtotal
        items.append(OrderItem(
            medication_id=item_data.medication_id,
            price_id=item_data.price_id,
            quantity=item_data.quantity,
            subtotal=subtotal,
        ))

    order = Order(
        user_id=user_id,
        pharmacy_id=data.pharmacy_id,
        payment_provider=data.payment_provider,
        total=total,
    )
    db.add(order)
    db.flush()

    for item in items:
        item.order_id = order.id
        db.add(item)

    # Generate payment URL
    order_id_str = str(order.id)
    if data.payment_provider == "mercadopago":
        order.payment_url = create_mercadopago_preference(order_id_str, items, total)
    elif data.payment_provider == "transbank":
        order.payment_url = create_transbank_transaction(order_id_str, total)

    order.status = OrderStatus.payment_sent
    db.commit()
    db.refresh(order)

    # Notify user via WhatsApp with payment link
    await tsunami_client.send_whatsapp(
        phone_number,
        f"Tu pedido PharmApp #{order_id_str[:8]} por ${total:,.0f} está listo. "
        f"Paga aquí: {order.payment_url}"
    )

    return order
```

**Step 3: Create orders router**

```python
# backend/app/api/v1/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_service import create_order

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderOut)
async def create(
    body: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = await create_order(db, str(user.id), user.phone_number, body)
    return order

@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
```

**Step 4: Create webhooks router**

```python
# backend/app/api/v1/webhooks.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.order import Order, OrderStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    if body.get("type") == "payment":
        external_ref = body.get("data", {}).get("external_reference")
        if external_ref:
            order = db.query(Order).filter(Order.id == external_ref).first()
            if order:
                order.status = OrderStatus.confirmed
                order.payment_status = "approved"
                db.commit()
    return {"status": "ok"}

@router.post("/transbank")
async def transbank_webhook(request: Request, db: Session = Depends(get_db)):
    from transbank.webpay.webpay_plus.transaction import Transaction
    params = await request.form()
    token = params.get("token_ws")
    if token:
        tx = Transaction()
        resp = tx.commit(token)
        if resp.get("status") == "AUTHORIZED":
            order = db.query(Order).filter(Order.id == resp["buy_order"]).first()
            if order:
                order.status = OrderStatus.confirmed
                order.payment_status = "authorized"
                db.commit()
    return {"status": "ok"}
```

**Step 5: Add both routers to routes.py**

**Step 6: Commit**

```bash
git add backend/app/
git commit -m "feat: add orders, payments (Mercado Pago + Transbank), and webhooks"
```

---

### Task 14: Favorites and search history routes

**Files:**
- Create: `backend/app/api/v1/favorites.py`
- Create: `backend/app/api/v1/search_history.py`
- Modify: `backend/app/api/v1/routes.py`

**Step 1: Create favorites router**

```python
# backend/app/api/v1/favorites.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.user_favorite import UserFavorite
from app.schemas.favorite import FavoriteCreate, FavoriteOut

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.get("/", response_model=list[FavoriteOut])
def list_favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UserFavorite).filter(UserFavorite.user_id == user.id).all()

@router.post("/", response_model=FavoriteOut, status_code=201)
def add_favorite(body: FavoriteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fav = UserFavorite(user_id=user.id, medication_id=body.medication_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav

@router.delete("/{favorite_id}", status_code=204)
def remove_favorite(favorite_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fav = db.query(UserFavorite).filter(UserFavorite.id == favorite_id, UserFavorite.user_id == user.id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
```

**Step 2: Create search history router**

```python
# backend/app/api/v1/search_history.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.search_history import SearchHistory

router = APIRouter(prefix="/search-history", tags=["search-history"])

@router.get("/")
def get_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(50)
        .all()
    )
```

**Step 3: Add to routes.py, commit**

```bash
git add backend/app/
git commit -m "feat: add favorites and search history endpoints"
```

---

## Phase 3: Docker & Infrastructure

### Task 15: Update Docker Compose with PostGIS

**Files:**
- Modify: `docker-compose.yml`
- Modify: `backend/Dockerfile`
- Create: `backend/.env.example`

**Step 1: Rewrite docker-compose.yml**

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.4
    container_name: pharmapp_db
    environment:
      POSTGRES_DB: pharmapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "${DB_PORT:-5433}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - pharmapp_net

  backend:
    build:
      context: ./backend
    container_name: pharmapp_backend
    ports:
      - "${API_PORT:-8000}:8000"
    depends_on:
      - db
    env_file:
      - ./backend/.env
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/pharmapp
    networks:
      - pharmapp_net

  frontend:
    build:
      context: ./frontend
    container_name: pharmapp_frontend
    ports:
      - "${WEB_PORT:-3000}:80"
    depends_on:
      - backend
    networks:
      - pharmapp_net

volumes:
  pgdata:

networks:
  pharmapp_net:
    driver: bridge
```

**Step 2: Update backend Dockerfile to install PostGIS deps**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 3: Create .env.example**

```
DATABASE_URL=postgresql://postgres:postgres@db:5432/pharmapp
SECRET_KEY=change-me-in-production
SERVICETSUNAMI_API_URL=http://host.docker.internal:8001
SERVICETSUNAMI_EMAIL=
SERVICETSUNAMI_PASSWORD=
MERCADOPAGO_ACCESS_TOKEN=
TRANSBANK_COMMERCE_CODE=
TRANSBANK_API_KEY=
GOOGLE_MAPS_API_KEY=
```

**Step 4: Commit**

```bash
git add docker-compose.yml backend/Dockerfile backend/.env.example
git commit -m "feat: add PostGIS database and update Docker Compose for development"
```

---

### Task 16: Seed data script

**Files:**
- Create: `backend/app/seed.py`

**Step 1: Create seed script with Chilean pharmacy data**

```python
# backend/app/seed.py
"""Seed the database with sample Chilean pharmacy and medication data."""
from app.core.database import SessionLocal
from app.models import Base
from app.core.database import engine
from app.models.medication import Medication
from app.models.pharmacy import Pharmacy
from app.models.price import Price
from geoalchemy2.elements import WKTElement

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Medication).count() > 0:
        print("Database already seeded")
        db.close()
        return

    # Sample medications
    meds = [
        Medication(name="Paracetamol 500mg", active_ingredient="Paracetamol", dosage="500mg", form="comprimido", lab="Chile Lab", requires_prescription=False),
        Medication(name="Ibuprofeno 400mg", active_ingredient="Ibuprofeno", dosage="400mg", form="comprimido", lab="Saval", requires_prescription=False),
        Medication(name="Amoxicilina 500mg", active_ingredient="Amoxicilina", dosage="500mg", form="cápsula", lab="Bagó", requires_prescription=True),
        Medication(name="Losartán 50mg", active_ingredient="Losartán", dosage="50mg", form="comprimido", lab="Andrómaco", requires_prescription=True),
        Medication(name="Omeprazol 20mg", active_ingredient="Omeprazol", dosage="20mg", form="cápsula", lab="Mintlab", requires_prescription=False),
    ]
    db.add_all(meds)
    db.flush()

    # Sample pharmacies in Santiago
    pharmacies = [
        Pharmacy(chain="cruz_verde", name="Cruz Verde Providencia", address="Av. Providencia 1234", comuna="Providencia", location=WKTElement("POINT(-70.6109 -33.4264)", srid=4326), phone="+56222345678"),
        Pharmacy(chain="salcobrand", name="Salcobrand Las Condes", address="Av. Apoquindo 4500", comuna="Las Condes", location=WKTElement("POINT(-70.5790 -33.4103)", srid=4326), phone="+56223456789"),
        Pharmacy(chain="ahumada", name="Farmacias Ahumada Centro", address="Paseo Ahumada 312", comuna="Santiago", location=WKTElement("POINT(-70.6506 -33.4378)", srid=4326), phone="+56224567890"),
        Pharmacy(chain="dr_simi", name="Dr. Simi Maipú", address="Av. Pajaritos 2100", comuna="Maipú", location=WKTElement("POINT(-70.7574 -33.5100)", srid=4326), phone="+56225678901"),
    ]
    db.add_all(pharmacies)
    db.flush()

    # Sample prices
    import random
    for med in meds:
        for pharm in pharmacies:
            db.add(Price(
                medication_id=med.id,
                pharmacy_id=pharm.id,
                price=round(random.uniform(800, 15000), 0),  # CLP
                in_stock=random.choice([True, True, True, False]),
            ))

    db.commit()
    db.close()
    print("Seeded database with sample data")

if __name__ == "__main__":
    seed()
```

**Step 2: Commit**

```bash
git add backend/app/seed.py
git commit -m "feat: add seed script with Chilean pharmacy and medication data"
```

---

## Phase 4: Frontend

### Task 17: Install frontend dependencies and setup routing

**Files:**
- Modify: `frontend/package.json` (via npm install)
- Modify: `frontend/src/App.js`
- Create: `frontend/src/api/client.js`

**Step 1: Install dependencies**

```bash
cd frontend && npm install react-router-dom @react-google-maps/api
```

**Step 2: Create API client with auth interceptor**

```javascript
// frontend/src/api/client.js
import axios from "axios";

const client = axios.create({ baseURL: "/api/v1" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default client;
```

**Step 3: Rewrite App.js with React Router**

```javascript
// frontend/src/App.js
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchResultsPage from "./pages/SearchResultsPage";
import MedicationDetailPage from "./pages/MedicationDetailPage";
import LoginPage from "./pages/LoginPage";
import OrderHistoryPage from "./pages/OrderHistoryPage";
import FavoritesPage from "./pages/FavoritesPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchResultsPage />} />
        <Route path="/medication/:id" element={<MedicationDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/orders" element={<OrderHistoryPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: add React Router, API client, and route structure"
```

---

### Task 18: Geolocation hook and auth hook

**Files:**
- Create: `frontend/src/hooks/useGeolocation.js`
- Create: `frontend/src/hooks/useAuth.js`

**Step 1: Create useGeolocation hook**

```javascript
// frontend/src/hooks/useGeolocation.js
import { useState, useEffect } from "react";

export default function useGeolocation() {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported");
      setLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLoading(false);
      },
      (err) => {
        setError(err.message);
        setLoading(false);
      }
    );
  }, []);

  return { location, error, loading };
}
```

**Step 2: Create useAuth hook**

```javascript
// frontend/src/hooks/useAuth.js
import { useState, useCallback } from "react";
import client from "../api/client";

export default function useAuth() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("token");
    return token ? { token } : null;
  });

  const requestOtp = useCallback(async (phoneNumber) => {
    await client.post("/auth/otp/request", { phone_number: phoneNumber });
  }, []);

  const verifyOtp = useCallback(async (phoneNumber, code) => {
    const { data } = await client.post("/auth/otp/verify", {
      phone_number: phoneNumber,
      code,
    });
    localStorage.setItem("token", data.access_token);
    setUser({ token: data.access_token });
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  return { user, requestOtp, verifyOtp, logout };
}
```

**Step 3: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add geolocation and auth hooks"
```

---

### Task 19: HomePage with search bar

**Files:**
- Create: `frontend/src/pages/HomePage.js`
- Create: `frontend/src/components/SearchBar.js`

**Step 1: Create SearchBar component**

```javascript
// frontend/src/components/SearchBar.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <form onSubmit={handleSearch} className="search-bar">
      <input
        type="text"
        placeholder="Buscar medicamento..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button type="submit">Buscar</button>
    </form>
  );
}
```

**Step 2: Create HomePage**

```javascript
// frontend/src/pages/HomePage.js
import React from "react";
import SearchBar from "../components/SearchBar";
import useGeolocation from "../hooks/useGeolocation";

export default function HomePage() {
  const { location, error, loading } = useGeolocation();

  return (
    <div className="home-page">
      <h1>PharmApp</h1>
      <p>Encuentra los medicamentos más baratos cerca de ti</p>
      <SearchBar />
      {loading && <p>Obteniendo tu ubicación...</p>}
      {error && <p>No pudimos obtener tu ubicación: {error}</p>}
      {location && <p>Ubicación detectada</p>}
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add HomePage with search bar and geolocation"
```

---

### Task 20: SearchResultsPage and PriceCard

**Files:**
- Create: `frontend/src/pages/SearchResultsPage.js`
- Create: `frontend/src/components/PriceCard.js`

**Step 1: Create PriceCard component**

```javascript
// frontend/src/components/PriceCard.js
import React from "react";

export default function PriceCard({ price, pharmacy, distanceKm }) {
  return (
    <div className="price-card">
      <div className="price-card-header">
        <span className="pharmacy-chain">{pharmacy.chain}</span>
        <span className="price">${price.toLocaleString("es-CL")}</span>
      </div>
      <p className="pharmacy-name">{pharmacy.name}</p>
      <p className="pharmacy-address">{pharmacy.address}</p>
      {distanceKm && <p className="distance">{distanceKm} km</p>}
    </div>
  );
}
```

**Step 2: Create SearchResultsPage**

```javascript
// frontend/src/pages/SearchResultsPage.js
import React, { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import client from "../api/client";

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!q) return;
    client.get(`/medications/search?q=${encodeURIComponent(q)}`)
      .then(({ data }) => setResults(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [q]);

  if (loading) return <p>Buscando "{q}"...</p>;

  return (
    <div className="search-results">
      <h2>Resultados para "{q}"</h2>
      {results.length === 0 && <p>No se encontraron medicamentos</p>}
      <ul>
        {results.map((med) => (
          <li key={med.id}>
            <Link to={`/medication/${med.id}`}>
              <strong>{med.name}</strong> — {med.active_ingredient} {med.dosage}
              {med.requires_prescription && <span className="rx-badge">Receta</span>}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add search results page and price card component"
```

---

### Task 21: MedicationDetailPage with price comparison and WhatsApp button

**Files:**
- Create: `frontend/src/pages/MedicationDetailPage.js`
- Create: `frontend/src/components/WhatsAppButton.js`

**Step 1: Create WhatsAppButton**

```javascript
// frontend/src/components/WhatsAppButton.js
import React from "react";

export default function WhatsAppButton({ onClick, disabled }) {
  return (
    <button className="whatsapp-button" onClick={onClick} disabled={disabled}>
      Comprar por WhatsApp
    </button>
  );
}
```

**Step 2: Create MedicationDetailPage**

```javascript
// frontend/src/pages/MedicationDetailPage.js
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PriceCard from "../components/PriceCard";
import WhatsAppButton from "../components/WhatsAppButton";

export default function MedicationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { location } = useGeolocation();
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!location) return;
    client.get(`/prices/compare?medication_id=${id}&lat=${location.lat}&lng=${location.lng}`)
      .then(({ data }) => setPrices(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id, location]);

  const handleBuy = async (priceItem) => {
    const token = localStorage.getItem("token");
    if (!token) { navigate("/login"); return; }
    try {
      const { data } = await client.post("/orders", {
        pharmacy_id: priceItem.pharmacy.id,
        items: [{ medication_id: id, price_id: priceItem.pharmacy.id, quantity: 1 }],
        payment_provider: "mercadopago",
      });
      if (data.payment_url) window.location.href = data.payment_url;
    } catch (err) {
      console.error("Error creating order:", err);
    }
  };

  if (loading) return <p>Comparando precios...</p>;

  return (
    <div className="medication-detail">
      <h2>Comparación de precios</h2>
      {prices.map((item, i) => (
        <div key={i}>
          <PriceCard price={item.price} pharmacy={item.pharmacy} distanceKm={item.distance_km} />
          <WhatsAppButton onClick={() => handleBuy(item)} />
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: add medication detail page with price comparison and WhatsApp buy button"
```

---

### Task 22: LoginPage (phone + OTP)

**Files:**
- Create: `frontend/src/pages/LoginPage.js`

**Step 1: Create LoginPage**

```javascript
// frontend/src/pages/LoginPage.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

export default function LoginPage() {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [error, setError] = useState(null);
  const { requestOtp, verifyOtp } = useAuth();
  const navigate = useNavigate();

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    try {
      await requestOtp(phone);
      setOtpSent(true);
    } catch { setError("Error enviando código"); }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    try {
      await verifyOtp(phone, code);
      navigate("/");
    } catch { setError("Código inválido o expirado"); }
  };

  return (
    <div className="login-page">
      <h2>Iniciar sesión</h2>
      {error && <p className="error">{error}</p>}
      {!otpSent ? (
        <form onSubmit={handleRequestOtp}>
          <input type="tel" placeholder="+56 9 1234 5678" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <button type="submit">Enviar código por WhatsApp</button>
        </form>
      ) : (
        <form onSubmit={handleVerify}>
          <p>Código enviado a {phone}</p>
          <input type="text" placeholder="123456" maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} />
          <button type="submit">Verificar</button>
        </form>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/pages/LoginPage.js
git commit -m "feat: add login page with phone + WhatsApp OTP flow"
```

---

### Task 23: OrderHistoryPage and FavoritesPage

**Files:**
- Create: `frontend/src/pages/OrderHistoryPage.js`
- Create: `frontend/src/pages/FavoritesPage.js`
- Create: `frontend/src/components/OrderStatusBadge.js`

**Step 1: Create OrderStatusBadge**

```javascript
// frontend/src/components/OrderStatusBadge.js
import React from "react";

const STATUS_LABELS = {
  pending: "Pendiente",
  payment_sent: "Pago enviado",
  confirmed: "Confirmado",
  delivering: "En camino",
  completed: "Completado",
  cancelled: "Cancelado",
};

export default function OrderStatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{STATUS_LABELS[status] || status}</span>;
}
```

**Step 2: Create OrderHistoryPage**

```javascript
// frontend/src/pages/OrderHistoryPage.js
import React, { useEffect, useState } from "react";
import client from "../api/client";
import OrderStatusBadge from "../components/OrderStatusBadge";

export default function OrderHistoryPage() {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    client.get("/orders").then(({ data }) => setOrders(data)).catch(console.error);
  }, []);

  return (
    <div className="order-history">
      <h2>Mis pedidos</h2>
      {orders.map((order) => (
        <div key={order.id} className="order-card">
          <p>Pedido #{order.id.slice(0, 8)}</p>
          <p>Total: ${order.total.toLocaleString("es-CL")}</p>
          <OrderStatusBadge status={order.status} />
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Create FavoritesPage**

```javascript
// frontend/src/pages/FavoritesPage.js
import React, { useEffect, useState } from "react";
import client from "../api/client";

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    client.get("/favorites").then(({ data }) => setFavorites(data)).catch(console.error);
  }, []);

  const removeFavorite = async (id) => {
    await client.delete(`/favorites/${id}`);
    setFavorites(favorites.filter((f) => f.id !== id));
  };

  return (
    <div className="favorites-page">
      <h2>Mis favoritos</h2>
      {favorites.map((fav) => (
        <div key={fav.id}>
          <span>{fav.medication_id}</span>
          <button onClick={() => removeFavorite(fav.id)}>Eliminar</button>
        </div>
      ))}
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: add order history and favorites pages"
```

---

### Task 24: Google Maps pharmacy map component

**Files:**
- Create: `frontend/src/components/PharmacyMap.js`
- Create: `frontend/src/pages/PharmacyMapPage.js`
- Modify: `frontend/src/App.js` (add route)

**Step 1: Create PharmacyMap component**

```javascript
// frontend/src/components/PharmacyMap.js
import React from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

const containerStyle = { width: "100%", height: "400px" };

export default function PharmacyMap({ center, pharmacies }) {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "",
  });

  if (!isLoaded) return <p>Cargando mapa...</p>;

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={14}>
      {pharmacies.map((p) => (
        <Marker
          key={p.id}
          position={{ lat: p.lat, lng: p.lng }}
          title={`${p.name} - ${p.chain}`}
        />
      ))}
    </GoogleMap>
  );
}
```

**Step 2: Create PharmacyMapPage**

```javascript
// frontend/src/pages/PharmacyMapPage.js
import React, { useEffect, useState } from "react";
import client from "../api/client";
import useGeolocation from "../hooks/useGeolocation";
import PharmacyMap from "../components/PharmacyMap";

export default function PharmacyMapPage() {
  const { location } = useGeolocation();
  const [pharmacies, setPharmacies] = useState([]);

  useEffect(() => {
    if (!location) return;
    client.get(`/pharmacies/nearby?lat=${location.lat}&lng=${location.lng}&radius_km=5`)
      .then(({ data }) => setPharmacies(data))
      .catch(console.error);
  }, [location]);

  if (!location) return <p>Obteniendo ubicación...</p>;

  return (
    <div className="pharmacy-map-page">
      <h2>Farmacias cercanas</h2>
      <PharmacyMap center={location} pharmacies={pharmacies} />
    </div>
  );
}
```

**Step 3: Add `/map` route to App.js**

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Google Maps pharmacy map page"
```

---

### Task 25: Update Nginx config and frontend Dockerfile

**Files:**
- Modify: `frontend/nginx.conf`
- Modify: `frontend/Dockerfile`

**Step 1: Update nginx.conf to proxy `/api/v1` to backend**

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location /api/v1 {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Step 2: Update frontend Dockerfile for Google Maps env var**

Add `ARG REACT_APP_GOOGLE_MAPS_API_KEY` before the build step so the key is available at build time.

**Step 3: Commit**

```bash
git add frontend/nginx.conf frontend/Dockerfile
git commit -m "feat: update Nginx proxy for /api/v1 and SPA routing"
```

---

## Phase 5: Scraping Pipeline Integration

### Task 26: Create scraping pipeline trigger service

**Files:**
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/scraping.py`

**Step 1: Create scraping trigger**

```python
# backend/app/tasks/scraping.py
"""Triggers ServiceTsunami scraping pipelines for pharmacy price data."""
from app.services.servicetsunami import tsunami_client

PIPELINE_IDS = {
    "cruz_verde": None,  # Set after creating pipelines in ServiceTsunami
    "salcobrand": None,
    "ahumada": None,
}

async def trigger_all_scrapers():
    """Trigger all pharmacy scraping pipelines."""
    results = {}
    for chain, pipeline_id in PIPELINE_IDS.items():
        if pipeline_id:
            result = await tsunami_client.trigger_scraping_pipeline(pipeline_id)
            results[chain] = result
    return results
```

**Step 2: Add a manual trigger endpoint (admin-only for now)**

Add to `backend/app/api/v1/routes.py`:

```python
@api_router.post("/admin/trigger-scraping")
async def trigger_scraping():
    from app.tasks.scraping import trigger_all_scrapers
    return await trigger_all_scrapers()
```

**Step 3: Commit**

```bash
git add backend/app/tasks/ backend/app/api/v1/routes.py
git commit -m "feat: add scraping pipeline trigger for pharmacy price data"
```

---

## Phase 6: Final Integration

### Task 27: Update CLAUDE.md with new architecture

**Files:**
- Modify: `CLAUDE.md`

Update to reflect the new backend structure, new commands, new environment variables, and the complete architecture.

**Step 1: Update CLAUDE.md**

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with marketplace architecture"
```

---

### Task 28: End-to-end smoke test

**Step 1: Start the stack**

```bash
docker-compose up --build
```

**Step 2: Verify backend health**

```bash
curl http://localhost:8000/docs  # Swagger UI loads
```

**Step 3: Seed data**

```bash
docker-compose exec backend python -m app.seed
```

**Step 4: Test medication search**

```bash
curl "http://localhost:8000/api/v1/medications/search?q=paracetamol"
```

**Step 5: Test price comparison (Santiago coords)**

```bash
curl "http://localhost:8000/api/v1/prices/compare?medication_id=<id>&lat=-33.4264&lng=-70.6109"
```

**Step 6: Test frontend loads**

```bash
curl http://localhost:3000  # React SPA loads
```

**Step 7: Commit any fixes found during testing**
