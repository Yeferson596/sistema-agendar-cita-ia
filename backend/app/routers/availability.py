from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import get_or_create_specialty
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import SlotOut, UrgencyEnum
from app.services.availability import list_available_slots

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("", response_model=list[SlotOut])
def get_availability(
    specialty: str = Query(..., min_length=2),
    date_str: str = Query(..., alias="date", description="YYYY-MM-DD"),
    urgency: UrgencyEnum = Query(...),
    db: Annotated[Session, Depends(get_db)] = ...,
    _user: Annotated[User, Depends(get_current_user)] = ...,
):
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="date debe ser YYYY-MM-DD")
    spec = get_or_create_specialty(db, specialty)
    return list_available_slots(db, spec.id, d, urgency)
