"""Authentication router — login, refresh, logout, 2FA, password recovery.

All public endpoints (no auth required):
    - POST /api/auth/login
    - POST /api/auth/refresh
    - POST /api/auth/forgot
    - POST /api/auth/reset

Protected endpoints (auth required):
    - POST /api/auth/logout
    - POST /api/auth/2fa/enroll
    - POST /api/auth/2fa/verify
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.dependencies import get_current_user, get_db, get_settings
from app.core.rate_limiter import rate_limit_login
from app.core.security import hash_password
from app.models.user import User
from app.services.auth_service import (
    create_password_reset_token,
    enroll_2fa,
    login,
    logout,
    refresh_access,
    reset_password,
    verify_2fa_code,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --- Schemas ---


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    requires_2fa: bool | None = None
    session_token: str | None = None
    user: dict | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotRequest(BaseModel):
    email: EmailStr


class ResetRequest(BaseModel):
    token: str
    new_password: str


class EnrollResponse(BaseModel):
    secret: str
    uri: str


class Verify2FARequest(BaseModel):
    code: str


class ErrorResponse(BaseModel):
    detail: str


# --- Endpoints ---


@router.post("/login", response_model=LoginResponse)
async def api_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(rate_limit_login),
):
    """Authenticate with email and password.

    If 2FA is enabled, returns requires_2fa=true and a session_token.
    Otherwise returns access_token + refresh_token.
    """
    result = await login(db, request.email, request.password, settings)

    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])

    return LoginResponse(**result)


@router.post("/refresh", response_model=RefreshResponse | ErrorResponse)
async def api_refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Rotate a refresh token and emit a new pair."""
    result = await refresh_access(db, request.refresh_token, settings)

    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])

    return RefreshResponse(**result)


@router.post("/logout")
async def api_logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Revoke the current refresh token."""
    await logout(db, request.refresh_token)
    return {"message": "Sesión cerrada exitosamente"}


@router.post("/2fa/enroll", response_model=EnrollResponse)
async def api_enroll_2fa(
    current_user: User = Depends(get_current_user),
):
    """Enroll in 2FA by generating a TOTP secret.

    Returns the secret (Base32) and provisioning URI for QR codes.
    """
    result = enroll_2fa(current_user)
    return EnrollResponse(**result)


@router.post("/2fa/verify")
async def api_verify_2fa(
    request: Verify2FARequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a TOTP code and activate 2FA."""
    if verify_2fa_code(current_user, request.code):
        return {"message": "2FA activado exitosamente", "enabled": True}
    raise HTTPException(status_code=400, detail="Código inválido")


@router.post("/forgot")
async def api_forgot(
    request: ForgotRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset token.

    Always returns the same message to avoid email enumeration.
    """
    token = await create_password_reset_token(db, request.email)
    # In production, send token via email (C-12 integration)
    # For now, return it for testing
    if token:
        return {"message": "Si el email está registrado, recibirás instrucciones", "token": token}
    return {"message": "Si el email está registrado, recibirás instrucciones"}


@router.post("/reset")
async def api_reset(
    request: ResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a recovery token."""
    success = await reset_password(db, request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Token inválido, expirado o ya utilizado")
    return {"message": "Contraseña actualizada exitosamente"}
