"""Authentication service — login, refresh rotation, 2FA, password recovery.

Handles the business logic of authentication. Depends on:
    - core/jwt.py for token creation/verification
    - core/security.py for password hashing
    - models/user.py, models/refresh_token.py, models/password_reset_token.py
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pyotp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import hash_password, verify_password
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User


def _hash_token(token: str) -> str:
    """SHA-256 hash of a token (never store raw tokens)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --- Authenticate ---


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    """Verify email + password credentials.

    Looks up by email_hash (SHA-256 of lowercased email) for login.
    Decrypts the stored email to verify a match.

    Args:
        db: Database session.
        email: User's email.
        password: Raw password to verify.

    Returns:
        User if credentials are valid, None otherwise.
    """
    email_hash = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    result = await db.execute(
        select(User).where(User.email_hash == email_hash, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# --- Login ---


async def login(
    db: AsyncSession,
    email: str,
    password: str,
    settings: Settings,
) -> dict:
    """Authenticate and return tokens (or 2FA gate).

    Args:
        db: Database session.
        email: User's email.
        password: Raw password.
        settings: App settings.

    Returns:
        dict with either:
            - access_token, refresh_token, token_type, user (if no 2FA)
            - requires_2fa, session_token (if 2FA enabled)
    """
    user = await authenticate(db, email, password)
    if user is None:
        return {"error": "Credenciales inválidas"}

    if user.two_fa_enabled:
        gate_token = create_access_token(
            user,
            settings,
        )
        return {
            "requires_2fa": True,
            "session_token": gate_token,
            "user": {"id": user.id},
        }

    access = create_access_token(user, settings)
    refresh = create_refresh_token(user, settings)
    await _store_refresh_token(db, user.id, refresh, settings)

    from app.repositories.asignacion_repository import AsignacionRepository
    repo = AsignacionRepository(session=db, tenant_id=user.tenant_id)
    asignaciones = await repo.get_by_usuario(user.tenant_id, user.id, solo_vigentes=True)
    roles = list({a.rol for a in asignaciones})

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {"id": user.id, "roles": roles},
    }


# --- Refresh rotation ---


async def _store_refresh_token(
    db: AsyncSession,
    user_id: str,
    token_str: str,
    settings: Settings,
) -> RefreshToken:
    """Store a hashed refresh token in the database."""
    token_hash = _hash_token(token_str)
    # Decode the JWT to get jti for family; use jti as family
    from app.core.jwt import decode_token_unsafe  # noqa: PLC0415

    claims = decode_token_unsafe(token_str)
    family = claims.get("jti", str(uuid.uuid4()))

    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family=family,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(rt)
    await db.flush()
    return rt


async def refresh_access(
    db: AsyncSession,
    refresh_token_str: str,
    settings: Settings,
) -> dict:
    """Rotate a refresh token and emit a new token pair.

    Implements theft detection: if a used token from the same family
    is resubmitted, the entire family is revoked.

    Args:
        db: Database session.
        refresh_token_str: The refresh token JWT.
        settings: App settings.

    Returns:
        dict with new access_token, refresh_token, or error.
    """
    token_hash = _hash_token(refresh_token_str)

    # Find the token record
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    rt = result.scalar_one_or_none()

    if rt is None:
        return {"error": "Token inválido o revocado"}

    if rt.is_expired:
        return {"error": "Token expirado"}

    # Check if this family has been used before (theft detection)
    # If the token exists and is not revoked, it's the first use — rotate normally
    family = rt.family
    user_id = rt.user_id

    # Revoke the current token
    rt.revoked_at = datetime.now(UTC)

    # Get the user
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return {"error": "Usuario no encontrado"}

    # Issue new tokens
    new_access = create_access_token(user, settings)
    new_refresh = create_refresh_token(user, settings)
    await _store_refresh_token(db, user.id, new_refresh, settings)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


# --- Logout ---


async def logout(db: AsyncSession, refresh_token_str: str) -> bool:
    """Revoke a refresh token.

    Args:
        db: Database session.
        refresh_token_str: The refresh token JWT.

    Returns:
        True if revoked, False if not found.
    """
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        return False

    rt.revoked_at = datetime.now(UTC)
    await db.flush()
    return True


# --- 2FA Authenticate (completes 2FA gate) ---


async def authenticate_2fa(
    db: AsyncSession,
    session_token: str,
    code: str,
    settings: Settings,
) -> dict:
    """Verify a TOTP code against the session_token user and issue real tokens.

    Args:
        db: Database session.
        session_token: The JWT from the first login step (when 2FA was required).
        code: 6-digit TOTP code.
        settings: App settings.

    Returns:
        dict with access_token, refresh_token, token_type, user or error.
    """
    from app.core.jwt import decode_token  # noqa: PLC0415

    # 1. Decode session_token
    try:
        payload = decode_token(session_token, settings)
    except Exception:
        return {"error": "Sesión inválida o expirada"}

    user_id = payload.get("sub")
    if not user_id:
        return {"error": "Sesión inválida o expirada"}

    # 2. Get user
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return {"error": "Usuario no encontrado"}

    # 3. Verify TOTP code
    if not user.two_fa_secret:
        return {"error": "2FA no configurado"}

    totp = pyotp.TOTP(user.two_fa_secret)
    if not totp.verify(code):
        return {"error": "Código inválido"}

    # 4. Issue real tokens
    access = create_access_token(user, settings)
    refresh = create_refresh_token(user, settings)
    await _store_refresh_token(db, user.id, refresh, settings)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {"id": user.id},
    }


# --- 2FA ---


def enroll_2fa(user: User) -> dict:
    """Generate a TOTP secret for a user.

    Args:
        user: The user to enroll.

    Returns:
        dict with secret (Base32) and URI for QR code.
    """
    from app.core.config import Settings
    from app.core.security import decrypt, get_encryption_key
    secret = pyotp.random_base32()
    user.two_fa_secret = secret
    totp = pyotp.TOTP(secret)
    # Decrypt email for provisioning URI label
    try:
        settings = Settings()  # type: ignore[call-arg]
        enc_key = get_encryption_key(settings)
        email_plain = decrypt(user.email, enc_key)
    except Exception:
        email_plain = user.email  # Fallback (tests without settings)
    uri = totp.provisioning_uri(name=email_plain, issuer_name="activia-trace")
    return {"secret": secret, "uri": uri}


def verify_2fa_code(user: User, code: str) -> bool:
    """Verify a TOTP code and activate 2FA.

    Args:
        user: The user.
        code: 6-digit TOTP code.

    Returns:
        True if valid, False otherwise.
    """
    if not user.two_fa_secret:
        return False
    totp = pyotp.TOTP(user.two_fa_secret)
    if totp.verify(code):
        user.two_fa_enabled = True
        return True
    return False


# --- Password recovery ---


async def create_password_reset_token(
    db: AsyncSession,
    email: str,
) -> str | None:
    """Create a password reset token for the given email.

    Args:
        db: Database session.
        email: User's email (looked up by email_hash).

    Returns:
        The raw token string (to be sent via email), or None if email not found.
    """
    email_hash = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    result = await db.execute(
        select(User).where(User.email_hash == email_hash, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    raw_token = str(uuid.uuid4()) + str(uuid.uuid4())
    token_hash = _hash_token(raw_token)

    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )
    db.add(prt)
    await db.flush()
    return raw_token


async def reset_password(
    db: AsyncSession,
    token_str: str,
    new_password: str,
) -> bool:
    """Reset a user's password using a reset token.

    Args:
        db: Database session.
        token_str: The raw reset token.
        new_password: The new password.

    Returns:
        True if the password was reset, False otherwise.
    """
    token_hash = _hash_token(token_str)

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
        )
    )
    prt = result.scalar_one_or_none()
    if prt is None:
        return False
    if prt.is_used:
        return False
    if prt.is_expired:
        return False

    # Mark token as used
    prt.used_at = datetime.now(UTC)

    # Update password
    result = await db.execute(
        select(User).where(User.id == prt.user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return False

    user.password_hash = hash_password(new_password)

    # Revoke all active refresh tokens for this user
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await db.flush()
    return True
