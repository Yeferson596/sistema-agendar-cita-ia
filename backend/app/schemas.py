import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class RoleEnum(str, Enum):
    patient = "patient"
    admin = "admin"


class UrgencyEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class StatusEnum(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no-show"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    photo_url: str | None
    role: RoleEnum
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthIn(BaseModel):
    id_token: str


class TriageIn(BaseModel):
    description: str = Field(min_length=3, max_length=8000)


class TriageOut(BaseModel):
    specialty: str
    urgency: UrgencyEnum
    reasoning: str


class AvailabilityQuery(BaseModel):
    specialty: str
    date: datetime
    urgency: UrgencyEnum


class SlotOut(BaseModel):
    start_at: datetime
    end_at: datetime
    priority_score: float
    label: str | None = None


class PredictNoShowIn(BaseModel):
    specialty: str
    urgency: UrgencyEnum
    start_at: datetime


class PredictNoShowOut(BaseModel):
    no_show_risk: float
    reasoning: str
    features: dict | None = None


class AppointmentCreate(BaseModel):
    specialty: str
    urgency: UrgencyEnum
    start_at: datetime
    description: str | None = None
    triage_reasoning: str | None = None


class AppointmentOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str | None
    patient_email: str | None
    specialty: str
    start_at: datetime
    end_at: datetime
    urgency: UrgencyEnum
    status: StatusEnum
    description: str | None
    triage_reasoning: str | None
    no_show_risk: float | None

    model_config = {"from_attributes": True}


class RiskAlertOut(BaseModel):
    appointment_id: uuid.UUID
    patient_name: str | None
    specialty: str
    start_at: datetime
    no_show_risk: float
    suggested_action: str
