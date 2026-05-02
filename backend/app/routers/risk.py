from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_admin
from app.models import Appointment, AppointmentStatus, User
from app.schemas import RiskAlertOut

router = APIRouter(prefix="/risk-alerts", tags=["risk"])


@router.get("", response_model=list[RiskAlertOut])
def risk_alerts(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
    threshold: float = 0.55,
):
    rows = (
        db.execute(
            select(Appointment)
            .options(joinedload(Appointment.specialty))
            .where(Appointment.status == AppointmentStatus.scheduled)
            .where(Appointment.no_show_risk.is_not(None))
            .where(Appointment.no_show_risk >= threshold)
            .order_by(Appointment.start_at.asc())
        )
        .unique()
        .scalars()
        .all()
    )

    out: list[RiskAlertOut] = []
    for ap in rows:
        patient = db.get(User, ap.patient_id)
        risk = float(ap.no_show_risk or 0)
        if risk >= 0.75:
            action = "Sugerido: liberar cupo alternativo y ofrecer recordatorio activo; evaluar sobrecupo controlado en franja cercana."
        elif risk >= 0.55:
            action = "Sugerido: contacto de confirmación y lista de espera para reasignar el hueco si cancela."
        else:
            action = "Monitoreo estándar."
        spec_name = ap.specialty.name if ap.specialty else ""
        out.append(
            RiskAlertOut(
                appointment_id=ap.id,
                patient_name=patient.display_name if patient else None,
                specialty=spec_name,
                start_at=ap.start_at,
                no_show_risk=risk,
                suggested_action=action,
            )
        )
    return out
