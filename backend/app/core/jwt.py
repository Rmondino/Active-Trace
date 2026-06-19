"""JWT token creation and verification utilities.

Uses HS256 with SECRET_KEY. Tokens include standard claims (sub, exp, iat, jti)
plus custom claim (tenant_id).

Refresh tokens are longer-lived (7 days) and participate in rotation protocol.
"""

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import Settings
from app.models.user import User


def create_access_token(user: User, settings: Settings, expires_delta: int | None = None) -> str:
    """Create a short-lived JWT access token.

    Args:
        user: The authenticated user.
        settings: App settings (uses SECRET_KEY and ACCESS_TOKEN_EXPIRE_MINUTES).
        expires_delta: Minutes until expiration. Override for testing (negative = expired).

    Returns:
        Encoded JWT string.
    """
    delta = (
        timedelta(minutes=expires_delta)
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    now = datetime.now(UTC)
    payload = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "exp": now + delta,
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user: User, settings: Settings) -> str:
    """Create a long-lived JWT refresh token (7 days).

    Args:
        user: The authenticated user.
        settings: App settings (uses SECRET_KEY).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "exp": now + timedelta(days=7),
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str, settings: Settings) -> dict | None:
    """Verify a JWT and return its claims.

    Args:
        token: The JWT string to verify.
        settings: App settings (uses SECRET_KEY).

    Returns:
        Decoded claims dictionary, or None if the token is invalid/expired.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "jti", "sub"]},
        )
    except JWTError:
        return None


def decode_token(token: str, settings: Settings) -> dict:
    """Decode and verify a JWT, raising on invalid/expired.

    Args:
        token: The JWT string to verify.
        settings: App settings (uses SECRET_KEY).

    Returns:
        Decoded claims dictionary.

    Raises:
        JWTError: If the token is invalid, expired, or has a bad signature.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "jti", "sub"]},
    )


def decode_token_unsafe(token: str) -> dict:
    """Decode a JWT without verifying signature (debugging only).

    Args:
        token: The JWT string.

    Returns:
        Decoded claims dictionary (unverified).
    """
    return jwt.get_unverified_claims(token)
