import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
import app.models  # ensure ORM models are registered
from app.routers import appointments, auth, availability, predictions, risk, triage, metrics
from app.agent.router import router as agent_router
from app.middleware.observability import observability_middleware
from app.middleware.sanitizer import sanitizer_middleware
from app.middleware.rate_limit import rate_limit_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not os.getenv("SKIP_DB_BOOTSTRAP"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MediFlow API", version="1.0.0", lifespan=lifespan)

# Ensure DB tables exist when module is imported (helps tests and sync clients)
if not os.getenv("SKIP_DB_BOOTSTRAP"):
    Base.metadata.create_all(bind=engine)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(triage.router)
app.include_router(availability.router)
app.include_router(predictions.router)
app.include_router(agent_router)
app.include_router(appointments.router)
app.include_router(risk.router)
app.include_router(metrics.router)

# Register middlewares
app.middleware('http')(sanitizer_middleware)
app.middleware('http')(rate_limit_middleware)
app.middleware('http')(observability_middleware)


@app.get("/health")
def health():
    return {"status": "ok"}
