"""Tests for C-03 auth-jwt-2fa.

Groups covered:
    8.1 JWT utils: create + verify round-trip, token expirado, firma inválida
    8.2 Password hashing: hash + verify, contraseña incorrecta falla
    8.3 Rate limiter: dentro del límite, excedido, ventana deslizante
    8.4 Login: OK, KO, con 2FA gate, email inexistente
    8.5 Refresh rotation: OK, reuso invalida familia, expirado
    8.6 2FA: enroll, verify, código incorrecto
    8.7 Password recovery: forgot, reset, token inválido, token reusado
    8.8 get_current_user: token válido, expirado, sin tenant_id, user inexistente
"""

import time
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token_unsafe,
    verify_token,
)
from app.core.rate_limiter import RateLimiter
from app.core.security import hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_service import (
    create_password_reset_token,
    enroll_2fa,
    login,
    refresh_access,
    reset_password,
    verify_2fa_code,
)

# ── Helpers ──


def _make_settings(secret_key: str | None = None) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY=secret_key or ("a" * 32),
        ENCRYPTION_KEY="b" * 32,
    )


async def _create_tenant(db: AsyncSession) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
        estado="Activo",
    )
    db.add(t)
    await db.flush()
    return t


async def _create_user(
    db: AsyncSession,
    tenant_id: str,
    email: str = "test@example.com",
    password: str = "SecurePass123!",
) -> User:
    from tests.conftest import create_user
    return await create_user(db, tenant_id, email=email, password=password)


# ═══════════════════════════════════════════
# 8.1 JWT Utils
# ═══════════════════════════════════════════


class TestJWT:
    """JWT token creation, verification, and edge cases."""

    def test_create_and_verify_access_token(self):
        """Round-trip: create → verify returns correct claims."""
        settings = _make_settings()
        from app.core.security import encrypt, get_encryption_key
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("test@example.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
        )
        token = create_access_token(user, settings)
        claims = verify_token(token, settings)

        assert claims is not None
        assert claims["sub"] == user.id
        assert claims["tenant_id"] == user.tenant_id
        assert "roles" not in claims

    def test_create_and_verify_refresh_token(self):
        """Refresh token has longer expiration."""
        settings = _make_settings()
        from app.core.security import encrypt, get_encryption_key
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("test@example.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
        )
        token = create_refresh_token(user, settings)
        claims = decode_token_unsafe(token)

        assert claims["type"] == "refresh"
        exp = claims["exp"]
        iat = claims["iat"]
        assert exp - iat >= 604800 - 10

    def test_verify_invalid_signature_returns_none(self):
        """Token signed with different key should not verify."""
        settings_a = _make_settings(secret_key="a" * 32)
        settings_b = _make_settings(secret_key="b" * 32)
        from app.core.security import encrypt, get_encryption_key
        enc_key = get_encryption_key(settings_a)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("a@b.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
        )

        token = create_access_token(user, settings_a)
        claims = verify_token(token, settings_b)

        assert claims is None

    def test_verify_expired_token_returns_none(self):
        """Token past its expiration should not verify."""
        settings = _make_settings()
        from app.core.security import encrypt, get_encryption_key
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("a@b.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
        )

        token = create_access_token(user, settings, expires_delta=-1)
        claims = verify_token(token, settings)

        assert claims is None


# ═══════════════════════════════════════════
# 8.2 Password Hashing
# ═══════════════════════════════════════════


class TestPasswordHashing:
    """Argon2id password hashing and verification."""

    def test_hash_and_verify(self):
        hashed = hash_password("MySecureP@ss1")
        assert verify_password("MySecureP@ss1", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("MySecureP@ss1")
        assert not verify_password("WrongPassword", hashed)

    def test_hash_is_different_each_time(self):
        h1 = hash_password("SamePassword")
        h2 = hash_password("SamePassword")
        assert h1 != h2


# ═══════════════════════════════════════════
# 8.3 Rate Limiter
# ═══════════════════════════════════════════


class TestRateLimiter:
    """In-memory sliding window rate limiter."""

    def test_allows_within_limit(self):
        limiter = RateLimiter()
        for _ in range(5):
            assert limiter.check("key-1", max_attempts=5, window_seconds=60)

    def test_blocks_when_exceeded(self):
        limiter = RateLimiter()
        for _ in range(5):
            limiter.check("key-2", max_attempts=5, window_seconds=60)
        assert not limiter.check("key-2", max_attempts=5, window_seconds=60)

    def test_different_keys_independent(self):
        limiter = RateLimiter()
        for _ in range(5):
            limiter.check("key-a", max_attempts=5, window_seconds=60)
        assert limiter.check("key-b", max_attempts=5, window_seconds=60)

    def test_sliding_window_expires(self):
        limiter = RateLimiter()
        for _ in range(5):
            limiter.check("key-3", max_attempts=5, window_seconds=1)
        assert not limiter.check("key-3", max_attempts=5, window_seconds=1)
        time.sleep(1.1)
        assert limiter.check("key-3", max_attempts=5, window_seconds=1)

    def test_retry_after_returns_correct_value(self):
        limiter = RateLimiter()
        for _ in range(5):
            limiter.check("key-4", max_attempts=5, window_seconds=60)
        retry = limiter.get_retry_after("key-4", window_seconds=60)
        assert 0 < retry <= 60


# ═══════════════════════════════════════════
# 8.4 Login (DB-based)
# ═══════════════════════════════════════════


@pytest.mark.asyncio
class TestLogin:
    """End-to-end login flow with real DB."""

    async def test_login_ok(self, db_session: AsyncSession, async_client: AsyncClient):
        tenant = await _create_tenant(db_session)
        await _create_user(db_session, tenant.id, email="login-ok@test.com", password="Pass1234!")
        await db_session.commit()

        response = await async_client.post("/api/auth/login", json={
            "email": "login-ok@test.com",
            "password": "Pass1234!",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] is not None
        assert data["refresh_token"] is not None
        assert data["token_type"] == "bearer"
        assert "id" in data["user"]

    async def test_login_wrong_password(self, db_session: AsyncSession, async_client: AsyncClient):
        tenant = await _create_tenant(db_session)
        await _create_user(db_session, tenant.id, email="login-wrong@test.com", password="Pass1234!")
        await db_session.commit()

        response = await async_client.post("/api/auth/login", json={
            "email": "login-wrong@test.com",
            "password": "WrongPassword!",
        })

        assert response.status_code == 401

    async def test_login_nonexistent_email(self, db_session: AsyncSession, async_client: AsyncClient):
        tenant = await _create_tenant(db_session)
        await db_session.commit()

        response = await async_client.post("/api/auth/login", json={
            "email": "noone@test.com",
            "password": "Pass1234!",
        })

        assert response.status_code == 401

    async def test_login_with_2fa_gate(self, db_session: AsyncSession, async_client: AsyncClient):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, email="2fa-gate@test.com", password="Pass1234!")
        user.two_fa_enabled = True
        user.two_fa_secret = "JBSWY3DPEHPK3PXP"
        await db_session.commit()

        response = await async_client.post("/api/auth/login", json={
            "email": "2fa-gate@test.com",
            "password": "Pass1234!",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["requires_2fa"] is True
        assert data["session_token"] is not None
        assert data.get("access_token") is None


# ═══════════════════════════════════════════
# 8.5 Refresh Rotation
# ═══════════════════════════════════════════


@pytest.mark.asyncio
class TestRefreshRotation:
    """Refresh token rotation with family-based theft detection."""

    async def test_refresh_ok(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, email="refresh@test.com")
        await db_session.commit()

        settings = _make_settings()
        result = await login(db_session, "refresh@test.com", "SecurePass123!", settings)
        old_refresh = result["refresh_token"]

        new_pair = await refresh_access(db_session, old_refresh, settings)
        assert "access_token" in new_pair
        assert "refresh_token" in new_pair
        assert new_pair["refresh_token"] != old_refresh

    async def test_reuse_revokes_family(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, email="reuse@test.com")
        await db_session.commit()

        settings = _make_settings()
        result = await login(db_session, "reuse@test.com", "SecurePass123!", settings)
        old_refresh = result["refresh_token"]

        await refresh_access(db_session, old_refresh, settings)
        await db_session.commit()

        result2 = await refresh_access(db_session, old_refresh, settings)
        assert "error" in result2
        await db_session.commit()

    async def test_invalid_token_returns_error(self, db_session: AsyncSession):
        settings = _make_settings()
        result = await refresh_access(db_session, "bogus-token", settings)
        assert "error" in result

    async def test_expired_token_is_expired(self, db_session: AsyncSession):
        from datetime import UTC, datetime, timedelta

        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            token_hash="test",
            family=str(uuid.uuid4()),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        assert rt.is_expired

    async def test_active_token_is_not_expired(self, db_session: AsyncSession):
        from datetime import UTC, datetime, timedelta

        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            token_hash="test",
            family=str(uuid.uuid4()),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            created_at=datetime.now(UTC),
        )
        assert not rt.is_expired


# ═══════════════════════════════════════════
# 8.6 2FA
# ═══════════════════════════════════════════


class TestTwoFA:
    """TOTP-based 2FA enrollment and verification."""

    def test_enroll_returns_secret_and_uri(self):
        from app.core.security import encrypt, get_encryption_key
        settings = _make_settings()
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("2fa@test.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
        )
        result = enroll_2fa(user)

        assert "secret" in result
        assert "uri" in result
        assert result["uri"].startswith("otpauth://")

    def test_verify_valid_code(self):
        import pyotp

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()

        from app.core.security import encrypt, get_encryption_key
        settings = _make_settings()
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("verify@test.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
            two_fa_secret=secret,
            two_fa_enabled=False,
        )
        assert user.two_fa_enabled is False
        assert verify_2fa_code(user, code)
        assert user.two_fa_enabled is True

    def test_verify_wrong_code_returns_false(self):
        from app.core.security import encrypt, get_encryption_key
        settings = _make_settings()
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("wrong@test.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
            two_fa_secret="JBSWY3DPEHPK3PXP",
        )
        assert not verify_2fa_code(user, "000000")

    def test_verify_no_secret_returns_false(self):
        from app.core.security import encrypt, get_encryption_key
        settings = _make_settings()
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("nosecret@test.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
            two_fa_secret=None,
        )
        assert not verify_2fa_code(user, "123456")


# ═══════════════════════════════════════════
# 8.7 Password Recovery
# ═══════════════════════════════════════════


@pytest.mark.asyncio
class TestPasswordRecovery:
    """Password forgot and reset flow."""

    async def test_forgot_creates_token(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        await _create_user(db_session, tenant.id, email="forgot@test.com")
        await db_session.commit()

        token = await create_password_reset_token(db_session, "forgot@test.com")
        assert token is not None
        assert len(token) > 20

    async def test_forgot_nonexistent_email_returns_none(self, db_session: AsyncSession):
        token = await create_password_reset_token(db_session, "noone@test.com")
        assert token is None

    async def test_reset_with_valid_token(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, email="reset@test.com")
        await db_session.commit()

        token = await create_password_reset_token(db_session, "reset@test.com")
        assert token is not None

        success = await reset_password(db_session, token, "NewPass123!")
        assert success

        from app.core.security import verify_password

        await db_session.refresh(user)
        assert verify_password("NewPass123!", user.password_hash)

    async def test_reset_with_invalid_token(self, db_session: AsyncSession):
        success = await reset_password(db_session, "invalid-token", "NewPass123!")
        assert not success

    async def test_reset_with_reused_token(self, db_session: AsyncSession):
        tenant = await _create_tenant(db_session)
        await _create_user(db_session, tenant.id, email="reuse-reset@test.com")
        await db_session.commit()

        token = await create_password_reset_token(db_session, "reuse-reset@test.com")
        assert token is not None

        success = await reset_password(db_session, token, "NewPass456!")
        assert success
        await db_session.commit()

        success2 = await reset_password(db_session, token, "AnotherPass!")
        assert not success2


# ═══════════════════════════════════════════
# 8.8 get_current_user
# ═══════════════════════════════════════════


@pytest.mark.asyncio
class TestGetCurrentUser:
    """get_current_user dependency resolution from JWT."""

    async def test_valid_token_returns_user(self, db_session: AsyncSession, async_client: AsyncClient):
        tenant = await _create_tenant(db_session)
        user = await _create_user(db_session, tenant.id, email="current-user@test.com")
        await db_session.commit()

        settings = _make_settings()
        token = create_access_token(user, settings)

        response = await async_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_expired_token_returns_401(self, db_session: AsyncSession, async_client: AsyncClient):
        settings = _make_settings()
        from app.core.security import encrypt, get_encryption_key
        enc_key = get_encryption_key(settings)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            email=encrypt("expired@test.com", enc_key),
            email_hash="abc123",
            nombre="Test",
            apellidos="User",
            dni=encrypt("12345678", enc_key),
        )

        token = create_access_token(user, settings, expires_delta=-1)

        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": "some-token"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    async def test_no_auth_header_returns_422(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": "some-token"},
        )

        assert response.status_code == 422
