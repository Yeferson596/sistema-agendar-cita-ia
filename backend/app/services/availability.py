from datetime import date, datetime, time, timedelta, timezone
from typing import List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Appointment, AppointmentStatus
from app.schemas import SlotOut, UrgencyEnum


def _combine_utc(d: date, hour: int, minute: int) -> datetime:
    dt = datetime.combine(d, time(hour=hour, minute=minute))
    return dt.replace(tzinfo=timezone.utc)


def _slot_priority_score(start: datetime, urgency: UrgencyEnum) -> float:
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    minutes = start.hour * 60 + start.minute
    if urgency == UrgencyEnum.high:
        return 10000.0 - float(minutes)
    if urgency == UrgencyEnum.medium:
        return 8000.0 - abs(float(minutes) - 10 * 60)
    return 4000.0 + float(minutes) * 0.5


def list_available_slots(
    db: Session,
    specialty_id: UUID,
    on_date: date,
    urgency: UrgencyEnum,
) -> List[SlotOut]:
    open_h = settings.clinic_open_hour
    close_h = settings.clinic_close_hour
    step = settings.slot_step_minutes
    duration = settings.appointment_duration_minutes

    day_start = datetime(on_date.year, on_date.month, on_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    rows = db.execute(
        select(Appointment).where(
            and_(
                Appointment.specialty_id == specialty_id,
                Appointment.status == AppointmentStatus.scheduled,
                Appointment.start_at >= day_start,
                Appointment.start_at < day_end,
            )
        )
    ).scalars().all()

    busy: list[tuple[datetime, datetime]] = []
    for ap in rows:
        s, e = ap.start_at, ap.end_at
        if s.tzinfo is None:
            s = s.replace(tzinfo=timezone.utc)
        if e.tzinfo is None:
            e = e.replace(tzinfo=timezone.utc)
        busy.append((s, e))

    slots: list[SlotOut] = []
    t = open_h * 60
    end_limit = close_h * 60
    while t + duration <= end_limit:
        h, m = divmod(t, 60)
        start = _combine_utc(on_date, h, m)
        end = start + timedelta(minutes=duration)

        conflict = False
        for bs, be in busy:
            if start < be and end > bs:
                conflict = True
                break
        if not conflict:
            score = _slot_priority_score(start, urgency)
            label = "Prioridad mañana" if urgency == UrgencyEnum.high and h < 12 else None
            slots.append(SlotOut(start_at=start, end_at=end, priority_score=score, label=label))
        t += step

    slots.sort(key=lambda s: s.priority_score, reverse=True)
    return slots
