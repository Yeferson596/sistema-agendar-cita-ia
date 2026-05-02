from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.config import settings
from app.crud import get_or_create_specialty
from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import Appointment, AppointmentStatus, Urgency, User, UserRole
from app.schemas import AppointmentCreate, AppointmentOut, PredictNoShowOut, StatusEnum, UrgencyEnum
from app.services.no_show import predict_no_show

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _to_out(ap: Appointment, patient: User | None) -> AppointmentOut:
    spec_name = ap.specialty.name if ap.specialty else ""
    return AppointmentOut(
        id=ap.id,
        patient_id=ap.patient_id,
        patient_name=patient.display_name if patient else None,
        patient_email=patient.email if patient else None,
        specialty=spec_name,
        start_at=ap.start_at,
        end_at=ap.end_at,
        urgency=UrgencyEnum(ap.urgency.value),
        status=StatusEnum(ap.status.value),
        description=ap.description,
        triage_reasoning=ap.triage_reasoning,
        no_show_risk=ap.no_show_risk,
    )


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    q = (
        select(Appointment)
        .options(joinedload(Appointment.specialty))
        .order_by(Appointment.start_at.desc())
    )
    if user.role != UserRole.admin:
        q = q.where(Appointment.patient_id == user.id)
    rows = db.execute(q).unique().scalars().all()
    out: list[AppointmentOut] = []
    for ap in rows:
        pat = db.get(User, ap.patient_id)
        out.append(_to_out(ap, pat))
    return out


@router.post("", response_model=AppointmentOut)
def create_appointment(
    body: AppointmentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Los administradores no crean citas desde este endpoint")

    spec = get_or_create_specialty(db, body.specialty)
    urg = Urgency(body.urgency.value)
    end = body.start_at + timedelta(minutes=settings.appointment_duration_minutes)

    overlap = db.scalars(
        select(Appointment)
        .where(
            Appointment.specialty_id == spec.id,
            Appointment.status == AppointmentStatus.scheduled,
            Appointment.start_at < end,
            Appointment.end_at > body.start_at,
        )
        .limit(1)
    ).first()
    if overlap:
        raise HTTPException(status_code=409, detail="El horario ya no está disponible")

    risk, _, _ = predict_no_show(db, user.id, spec.id, urg, body.start_at)

    ap = Appointment(
        patient_id=user.id,
        specialty_id=spec.id,
        start_at=body.start_at,
        end_at=end,
        urgency=urg,
        status=AppointmentStatus.scheduled,
        description=body.description,
        triage_reasoning=body.triage_reasoning,
        no_show_risk=risk,
    )
    db.add(ap)
    db.commit()
    ap = db.execute(
        select(Appointment).options(joinedload(Appointment.specialty)).where(Appointment.id == ap.id)
    ).scalar_one()
    return _to_out(ap, user)


@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(
    appointment_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    ap = db.get(Appointment, appointment_id)
    if not ap:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if user.role != UserRole.admin and ap.patient_id != user.id:
        raise HTTPException(status_code=403, detail="No autorizado")
    db.delete(ap)
    db.commit()
    return Response(status_code=204)


@router.get("/{appointment_id}/prediction", response_model=PredictNoShowOut)
def get_prediction(
    appointment_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_admin)],
):
    ap = db.get(Appointment, appointment_id)
    if not ap:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    risk, reasoning, feats = predict_no_show(db, ap.patient_id, ap.specialty_id, ap.urgency, ap.start_at)
    return PredictNoShowOut(no_show_risk=risk, reasoning=reasoning, features=feats)
