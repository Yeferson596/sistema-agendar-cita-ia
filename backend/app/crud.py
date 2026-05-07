from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Specialty


def get_or_create_specialty(db: Session, name: str) -> Specialty:
    key = name.strip()
    existing = db.scalars(
        select(Specialty).where(func.lower(Specialty.name) == func.lower(key))
    ).first()
    if existing:
        return existing
    row = Specialty(name=key, description=None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
