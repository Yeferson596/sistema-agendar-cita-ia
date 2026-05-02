from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import TriageIn, TriageOut, UrgencyEnum
from app.services.gemini_triage import perform_triage

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("", response_model=TriageOut)
def triage(
    body: TriageIn,
    _db: Annotated[Session, Depends(get_db)],
):
    data = perform_triage(body.description)
    return TriageOut(
        specialty=data["specialty"],
        urgency=UrgencyEnum(data["urgency"]),
        reasoning=data["reasoning"],
    )
