import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import appointments, auth, availability, predictions, rag, risk, triage


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not os.getenv("SKIP_DB_BOOTSTRAP"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MediFlow API", version="1.0.0", lifespan=lifespan)

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
app.include_router(rag.router)
app.include_router(appointments.router)
app.include_router(risk.router)


@app.get("/health")
def health():
    return {"status": "ok"}
