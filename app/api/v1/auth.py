from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_db
from app.core.emailer import send_email
from app.core.reset_tokens import generate_reset_token, hash_token
from app.core.security import verify_password, create_access_token, hash_password
from app.models.password_reset import PasswordResetToken
from app.models.user import User, Role
from app.schemas.auth import TokenOut, RegisterCustomerIn
from app.schemas.password_reset import ForgotPasswordIn, ResetPasswordIn

router = APIRouter(prefix="/auth")

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == form.username)
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(sub=str(user.id), role=user.role.value)
    return TokenOut(access_token=token)

@router.post("/register", response_model=TokenOut)
def register_customer(payload: RegisterCustomerIn, db: Session = Depends(get_db)):
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "Email already exists")

    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=hash_password(payload.password),
        phone_e164=payload.phone_e164,
        role=Role.CUSTOMER,
        is_active=True,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(sub=str(user.id), role=user.role.value)
        return TokenOut(access_token=token)
    except:
        db.rollback()
        raise

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    """
    Siempre responde 200 para no filtrar si el email existe.
    Si existe, envía email con link.
    """
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not user.is_active:
        return {"ok": True}

    raw_token = generate_reset_token()
    token_h = hash_token(raw_token)

    tz = ZoneInfo(settings.TIMEZONE)
    expires_at = datetime.now(tz) + timedelta(minutes=settings.RESET_TOKEN_TTL_MINUTES)

    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=token_h,
        expires_at=expires_at,
        used=False,
    ))
    db.commit()

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>Recuperar contraseña</h2>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p>Haz click aquí para continuar (válido por {settings.RESET_TOKEN_TTL_MINUTES} minutos):</p>
        <p><a href="{reset_link}">Restablecer contraseña</a></p>
        <p>Si no fuiste tú, puedes ignorar este correo.</p>
      </body>
    </html>
    """

    try:
        send_email(to_email=user.email, subject="Recuperar contraseña", html_body=html)
    except Exception:
        # No filtramos detalles; en logs del servidor verás el error real
        # (Si quieres, aquí agregamos logging)
        return {"ok": True}

    return {"ok": True}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(tz)

    token_h = hash_token(payload.token)

    prt = db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_h)
    ).scalar_one_or_none()

    if not prt or prt.used or prt.expires_at < now:
        raise HTTPException(400, "Invalid or expired token")

    user = db.get(User, prt.user_id)
    if not user or not user.is_active:
        raise HTTPException(400, "User not found or inactive")

    user.hashed_password = hash_password(payload.new_password)
    prt.used = True

    db.commit()
    return {"ok": True}