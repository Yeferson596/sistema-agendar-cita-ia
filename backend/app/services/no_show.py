from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentStatus, Urgency

logger = logging.getLogger(__name__)

URGENCY_MAP = {Urgency.low: 0.0, Urgency.medium: 1.0, Urgency.high: 2.0}


def _sigmoid(z: float) -> float:
    if z > 30:
        return 1.0
    if z < -30:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


def _patient_no_show_rate(db: Session, patient_id: UUID) -> float:
    total = db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.patient_id == patient_id)
        .where(Appointment.status.in_([AppointmentStatus.completed, AppointmentStatus.no_show]))
    )
    if not total or total < 1:
        return 0.0
    no_shows = db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.patient_id == patient_id)
        .where(Appointment.status == AppointmentStatus.no_show)
    ) or 0
    return float(no_shows) / float(total)


def _specialty_no_show_rate(db: Session, specialty_id: UUID) -> float:
    denom = db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.specialty_id == specialty_id)
        .where(
            Appointment.status.in_(
                [AppointmentStatus.completed, AppointmentStatus.no_show, AppointmentStatus.cancelled]
            )
        )
    )
    if not denom or denom < 1:
        return 0.15
    ns = db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.specialty_id == specialty_id)
        .where(Appointment.status == AppointmentStatus.no_show)
    ) or 0
    return float(ns) / float(denom)


def _row_features(ap: Appointment, db: Session) -> list[float]:
    u = URGENCY_MAP.get(ap.urgency, 1.0)
    start = ap.start_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    hour = start.hour + start.minute / 60.0
    dow = float(start.weekday())
    pr = _patient_no_show_rate(db, ap.patient_id)
    sr = _specialty_no_show_rate(db, ap.specialty_id)
    return [u, hour, dow, pr, sr]


def _build_training(db: Session) -> tuple[list[list[float]], list[int]] | None:
    rows = db.execute(
        select(Appointment).where(
            Appointment.status.in_([AppointmentStatus.completed, AppointmentStatus.no_show])
        )
    ).scalars().all()
    if len(rows) < 8:
        return None
    X: list[list[float]] = []
    y: list[int] = []
    for ap in rows:
        X.append(_row_features(ap, db))
        y.append(1 if ap.status == AppointmentStatus.no_show else 0)
    if len(set(y)) < 2:
        return None
    return X, y


def _train_logistic(X: list[list[float]], y: list[int], epochs: int = 400, lr: float = 0.35) -> tuple[list[float], float]:
    m = len(X)
    n = len(X[0])
    w = [0.0] * n
    b = 0.0
    for _ in range(epochs):
        gw = [0.0] * n
        gb = 0.0
        for i in range(m):
            z = b + sum(w[j] * X[i][j] for j in range(n))
            p = _sigmoid(z)
            err = p - y[i]
            gb += err
            for j in range(n):
                gw[j] += err * X[i][j]
        gb /= m
        for j in range(n):
            gw[j] /= m
        b -= lr * gb
        for j in range(n):
            w[j] -= lr * gw[j]
    return w, b


def predict_no_show(
    db: Session,
    patient_id: UUID,
    specialty_id: UUID,
    urgency: Urgency,
    start_at: datetime,
) -> tuple[float, str, dict[str, Any]]:
    pr = _patient_no_show_rate(db, patient_id)
    sr = _specialty_no_show_rate(db, specialty_id)
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)
    hour = start_at.hour + start_at.minute / 60.0
    dow = float(start_at.weekday())
    u = URGENCY_MAP.get(urgency, 1.0)

    features = {
        "urgency_score": u,
        "hour": hour,
        "weekday": dow,
        "patient_no_show_rate": round(pr, 3),
        "specialty_no_show_rate": round(sr, 3),
    }

    train = _build_training(db)
    if train is not None:
        X, y = train
        try:
            w, b = _train_logistic(X, y)
            x_row = [u, hour, dow, pr, sr]
            z = b + sum(w[j] * x_row[j] for j in range(len(x_row)))
            prob = _sigmoid(z)
            prob = max(0.0, min(1.0, prob))
            reason = f"Regresión logística entrenada ({len(y)} citas históricas). Tasas paciente {pr:.0%}, especialidad {sr:.0%}."
            return prob, reason, features
        except Exception as e:
            logger.warning("logistic train failed: %s", e)

    base = 0.12 + 0.08 * sr + 0.25 * pr
    base += 0.04 * (u / 2.0)
    if hour < 9 or hour > 17:
        base += 0.05
    prob = max(0.02, min(0.92, base))
    reason = (
        f"Heurística con histórico agregado (pocos datos para entrenar). "
        f"Tasa paciente {pr:.0%}, especialidad {sr:.0%}."
    )
    return prob, reason, features
