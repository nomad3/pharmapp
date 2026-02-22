from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router
from app.models import Base
from app.core.database import engine
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(title="PharmApp API")

app.add_middleware(RateLimitMiddleware)
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
