from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def _engine_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, **_engine_args(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created when the database module is imported (helps tests and local runs)
import os
if not os.getenv("SKIP_DB_BOOTSTRAP"):
    # Import models to ensure they are registered with Base before creating tables
    try:
        import app.models  # noqa: F401
    except Exception:
        pass
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
