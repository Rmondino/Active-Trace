"""Tests for C-07 User model expansion and Asignacion model."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt, encrypt, get_encryption_key
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimeStampedMixin


async def _create_tenant(db: AsyncSession):
    from app.models.tenant import Tenant

    t = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
        estado="Activo",
    )
    db.add(t)
    await db.flush()
    return t


class TestUserModelExpanded:
    """User model has profile fields, encrypted email, email_hash, no roles JSONB."""

    async def test_user_has_new_profile_fields(self, db_session: AsyncSession):
        from app.core.security import get_encryption_key
        from app.models.user import User

        tenant = await _create_tenant(db_session)
        key = get_encryption_key(None) if hasattr(get_encryption_key, '__wrapped__') else None
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=encrypt("juan@example.com", enc_key),
            email_hash="abc123hash",
            password_hash="argon2hash",
            nombre="Juan",
            apellidos="Pérez",
            dni=encrypt("12345678", enc_key),
            cuil=encrypt("20-12345678-9", enc_key),
            cbu=encrypt("0000003100012345678901", enc_key),
            alias_cbu=encrypt("JUAN.PEREZ", enc_key),
            banco="Banco Test",
            regional="CABA",
            legajo="LEG-001",
            legajo_profesional="LP-001",
            facturador=True,
            estado="Activo",
        )
        db_session.add(user)
        await db_session.flush()

        assert user.nombre == "Juan"
        assert user.apellidos == "Pérez"
        assert user.dni is not None
        assert user.cuil is not None
        assert user.cbu is not None
        assert user.alias_cbu is not None
        assert user.banco == "Banco Test"
        assert user.regional == "CABA"
        assert user.legajo == "LEG-001"
        assert user.legajo_profesional == "LP-001"
        assert user.facturador is True
        assert user.estado == "Activo"
        assert user.email_hash == "abc123hash"

    async def test_user_email_roundtrip_encrypt_decrypt(self, db_session: AsyncSession):
        from app.core.config import Settings
        from app.core.security import decrypt, get_encryption_key
        from app.models.user import User

        tenant = await _create_tenant(db_session)
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)

        plain_email = "maria@test.com"
        encrypted = encrypt(plain_email, enc_key)
        import hashlib
        email_hash = hashlib.sha256(plain_email.lower().encode()).hexdigest()

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=encrypted,
            email_hash=email_hash,
            password_hash="argon2hash",
            nombre="María",
            apellidos="García",
            dni=encrypt("87654321", enc_key),
        )
        db_session.add(user)
        await db_session.flush()

        decrypted = decrypt(user.email, enc_key)
        assert decrypted == plain_email
        assert user.email_hash == email_hash

    async def test_user_no_roles_column(self, db_session: AsyncSession):
        from app.models.user import User

        assert not hasattr(User, "roles"), "User should NOT have a roles column"

    async def test_user_defaults(self, db_session: AsyncSession):
        from app.core.config import Settings
        from app.core.security import encrypt, get_encryption_key
        from app.models.user import User

        tenant = await _create_tenant(db_session)
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=encrypt("default@test.com", enc_key),
            email_hash="defhash",
            password_hash="argon2hash",
            nombre="Default",
            apellidos="User",
            dni=encrypt("00000000", enc_key),
        )
        db_session.add(user)
        await db_session.flush()

        assert user.estado == "Activo"
        assert user.facturador is False


class TestAsignacionModel:
    """Asignacion model creation and relationships."""

    async def test_create_asignacion(self, db_session: AsyncSession):
        from app.core.config import Settings
        from app.core.security import encrypt, get_encryption_key
        from app.models.asignacion import Asignacion
        from app.models.user import User

        tenant = await _create_tenant(db_session)
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email=encrypt("user@test.com", enc_key),
            email_hash="uhash",
            password_hash="argon2hash",
            nombre="Test",
            apellidos="User",
            dni=encrypt("11111111", enc_key),
        )
        db_session.add(user)
        await db_session.flush()

        from datetime import date
        asignacion = Asignacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            usuario_id=user.id,
            rol="PROFESOR",
            desde=date(2024, 1, 1),
            comisiones=["COM-A", "COM-B"],
        )
        db_session.add(asignacion)
        await db_session.flush()

        assert asignacion.id is not None
        assert asignacion.rol == "PROFESOR"
        assert asignacion.usuario_id == user.id
        assert asignacion.tenant_id == tenant.id
        assert asignacion.desde == date(2024, 1, 1)
        assert asignacion.hasta is None
        assert asignacion.comisiones == ["COM-A", "COM-B"]
        assert asignacion.deleted_at is None

    async def test_asignacion_with_full_context(self, db_session: AsyncSession):
        from app.core.config import Settings
        from app.core.security import encrypt, get_encryption_key
        from app.models.asignacion import Asignacion
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte
        from app.models.materia import Materia
        from app.models.user import User

        tenant = await _create_tenant(db_session)
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)

        user = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email=encrypt("full@test.com", enc_key), email_hash="fhash",
            password_hash="argon2hash", nombre="Full", apellidos="Context",
            dni=encrypt("22222222", enc_key),
        )
        db_session.add(user)

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="TUPAD", nombre="Tecnicatura")
        db_session.add(carrera)

        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2024", anio=2024, vig_desde="2024-01-01")
        db_session.add(cohorte)

        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="PROG1", nombre="Programación I")
        db_session.add(materia)
        await db_session.flush()

        from datetime import date
        asignacion = Asignacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            usuario_id=user.id,
            rol="COORDINADOR",
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            comisiones=["UNICA"],
            responsable_id=user.id,
            desde=date(2024, 1, 1),
            hasta=date(2024, 12, 31),
        )
        db_session.add(asignacion)
        await db_session.flush()

        assert asignacion.materia_id == materia.id
        assert asignacion.carrera_id == carrera.id
        assert asignacion.cohorte_id == cohorte.id
        assert asignacion.responsable_id == user.id
        assert asignacion.hasta == date(2024, 12, 31)
