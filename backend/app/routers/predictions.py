from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import get_or_create_specialty
from app.database import get_db
from app.deps import get_current_user
from app.models import Urgency, User
from app.schemas import PredictNoShowIn, PredictNoShowOut
from app.services.no_show import predict_no_show

router = APIRouter(prefix="/predict-no-show", tags=["predictions"])


@router.post("", response_model=PredictNoShowOut)
def predict(
    body: PredictNoShowIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    spec = get_or_create_specialty(db, body.specialty)
    urg = Urgency(body.urgency.value)
    risk, reasoning, feats = predict_no_show(db, user.id, spec.id, urg, body.start_at)
    return PredictNoShowOut(no_show_risk=risk, reasoning=reasoning, features=feats)
