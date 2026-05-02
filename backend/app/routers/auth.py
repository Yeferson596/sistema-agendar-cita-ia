from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, UserRole
from app.schemas import GoogleAuthIn, LoginIn, RegisterIn, TokenResponse, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/public-google-client-id")
def public_google_client_id():
    """ID público del cliente OAuth (el mismo que usa el frontend con Google)."""
    cid = (settings.google_client_id or "").strip()
    return {"client_id": cid if cid else None}


def _admin_emails() -> set[str]:
    return {e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()}


def _role_for_email(email: str) -> UserRole:
    return UserRole.admin if email.lower() in _admin_emails() else UserRole.patient


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterIn, db: Annotated[Session, Depends(get_db)]):
    exists = db.scalars(select(User).where(User.email == body.email)).first()
    if exists:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role=_role_for_email(body.email),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginIn, db: Annotated[Session, Depends(get_db)]):
    user = db.scalars(select(User).where(User.email == body.email)).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]):
    return UserOut.model_validate(user)


@router.post("/google", response_model=TokenResponse)
def google_auth(body: GoogleAuthIn, db: Annotated[Session, Depends(get_db)]):
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth no configurado (GOOGLE_CLIENT_ID)")
    try:
        info = google_id_token.verify_oauth2_token(
            body.id_token, google_requests.Request(), settings.google_client_id
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token de Google inválido")

    sub = info.get("sub")
    email = info.get("email")
    if not sub or not email:
        raise HTTPException(status_code=400, detail="Token sin email")

    user = db.scalars(select(User).where(User.google_sub == sub)).first()
    if not user:
        user = db.scalars(select(User).where(User.email == email)).first()
    if user:
        user.google_sub = sub
        user.display_name = user.display_name or info.get("name")
        user.photo_url = user.photo_url or info.get("picture")
        user.role = _role_for_email(email)
        db.commit()
        db.refresh(user)
    else:
        user = User(
            email=email,
            google_sub=sub,
            display_name=info.get("name"),
            photo_url=info.get("picture"),
            role=_role_for_email(email),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
