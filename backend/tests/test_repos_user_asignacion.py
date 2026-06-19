"""Tests for UserRepository and AsignacionRepository (C-07)."""
import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


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


class TestUserRepository:
    """UserRepository CRUD and search methods."""

    async def test_create_user(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib
        email_hash = hashlib.sha256("test@example.com".encode()).hexdigest()

        user = await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("test@example.com", enc_key),
            "email_hash": email_hash,
            "password_hash": "argon2hash",
            "nombre": "Test",
            "apellidos": "User",
            "dni": encrypt("12345678", enc_key),
        })
        assert user.id is not None
        assert user.nombre == "Test"
        assert user.email_hash == email_hash

    async def test_get_by_email_hash(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib
        email_hash = hashlib.sha256("findme@test.com".encode()).hexdigest()

        await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("findme@test.com", enc_key),
            "email_hash": email_hash,
            "password_hash": "argon2hash",
            "nombre": "Find",
            "apellidos": "Me",
            "dni": encrypt("00000000", enc_key),
        })

        found = await repo.get_by_email_hash(tenant.id, email_hash)
        assert found is not None
        assert found.nombre == "Find"

    async def test_get_by_email_hash_not_found(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        found = await repo.get_by_email_hash(tenant.id, "nonexistenthash")
        assert found is None

    async def test_get_by_legajo(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib

        await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("legajo@test.com", enc_key),
            "email_hash": hashlib.sha256("legajo@test.com".encode()).hexdigest(),
            "password_hash": "argon2hash",
            "nombre": "Legajo",
            "apellidos": "User",
            "dni": encrypt("00000000", enc_key),
            "legajo": "LEG-001",
        })

        found = await repo.get_by_legajo(tenant.id, "LEG-001")
        assert found is not None
        assert found.legajo == "LEG-001"

    async def test_get_by_legajo_not_found(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        found = await repo.get_by_legajo(tenant.id, "NO-EXISTE")
        assert found is None

    async def test_search_by_nombre(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib

        await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("search@test.com", enc_key),
            "email_hash": hashlib.sha256("search@test.com".encode()).hexdigest(),
            "password_hash": "argon2hash",
            "nombre": "Searchable",
            "apellidos": "Name",
            "dni": encrypt("00000000", enc_key),
        })

        results = await repo.search(tenant.id, "Searchable")
        assert len(results) >= 1

    async def test_search_by_apellidos(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib

        await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("last@test.com", enc_key),
            "email_hash": hashlib.sha256("last@test.com".encode()).hexdigest(),
            "password_hash": "argon2hash",
            "nombre": "Test",
            "apellidos": "González",
            "dni": encrypt("00000000", enc_key),
        })

        results = await repo.search(tenant.id, "González")
        assert len(results) >= 1

    async def test_search_empty_results(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        results = await repo.search(tenant.id, "NoMatch123XYZ")
        assert results == []

    async def test_exists_by_email_hash_true(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib
        email_hash = hashlib.sha256("exists@test.com".encode()).hexdigest()

        await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("exists@test.com", enc_key),
            "email_hash": email_hash,
            "password_hash": "argon2hash",
            "nombre": "Exists",
            "apellidos": "User",
            "dni": encrypt("00000000", enc_key),
        })

        assert await repo.exists_by_email_hash(tenant.id, email_hash) is True

    async def test_exists_by_email_hash_false(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        assert await repo.exists_by_email_hash(tenant.id, "nonexistenthash") is False

    async def test_exists_by_email_hash_exclude_id(self, db_session: AsyncSession):
        from app.repositories.user_repository import UserRepository

        tenant = await _create_tenant(db_session)
        repo = UserRepository(session=db_session, tenant_id=tenant.id)
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib
        email_hash = hashlib.sha256("exclude@test.com".encode()).hexdigest()

        user = await repo.create({
            "id": str(uuid.uuid4()),
            "email": encrypt("exclude@test.com", enc_key),
            "email_hash": email_hash,
            "password_hash": "argon2hash",
            "nombre": "Exclude",
            "apellidos": "Me",
            "dni": encrypt("00000000", enc_key),
        })

        assert await repo.exists_by_email_hash(tenant.id, email_hash, exclude_id=user.id) is False
        assert await repo.exists_by_email_hash(tenant.id, email_hash, exclude_id=str(uuid.uuid4())) is True


class TestAsignacionRepository:
    """AsignacionRepository CRUD and vigencia filtering."""

    async def _seed_user(self, db, tenant_id):
        from app.core.security import encrypt, get_encryption_key
        from app.core.config import Settings
        settings = Settings(_env_file=None, DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test", SECRET_KEY="a"*32, ENCRYPTION_KEY="b"*32)
        enc_key = get_encryption_key(settings)
        import hashlib
        from app.models.user import User

        u = User(
            id=str(uuid.uuid4()), tenant_id=tenant_id,
            email=encrypt("asig@test.com", enc_key),
            email_hash=hashlib.sha256("asig@test.com".encode()).hexdigest(),
            password_hash="argon2hash", nombre="Asig", apellidos="User",
            dni=encrypt("00000000", enc_key),
        )
        db.add(u)
        await db.flush()
        return u

    async def test_create_asignacion(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await _create_tenant(db_session)
        user = await self._seed_user(db_session, tenant.id)
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)

        asig = await repo.create({
            "id": str(uuid.uuid4()),
            "usuario_id": user.id,
            "rol": "PROFESOR",
            "desde": date(2024, 1, 1),
        })
        assert asig.id is not None
        assert asig.rol == "PROFESOR"

    async def test_get_vigentes(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await _create_tenant(db_session)
        user = await self._seed_user(db_session, tenant.id)
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)

        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "PROFESOR", "desde": date(2020, 1, 1), "hasta": None,
        })
        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "TUTOR", "desde": date(2020, 1, 1), "hasta": date(2020, 12, 31),
        })

        vigentes = await repo.get_vigentes(tenant.id)
        assert len(vigentes) >= 1
        roles = [a.rol for a in vigentes]
        assert "PROFESOR" in roles
        assert "TUTOR" not in roles

    async def test_get_by_usuario(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await _create_tenant(db_session)
        user = await self._seed_user(db_session, tenant.id)
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)

        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "PROFESOR", "desde": date(2020, 1, 1),
        })
        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "COORDINADOR", "desde": date(2020, 1, 1),
        })

        results = await repo.get_by_usuario(tenant.id, user.id)
        assert len(results) == 2

        results_vigentes = await repo.get_by_usuario(tenant.id, user.id, solo_vigentes=True)
        assert len(results_vigentes) == 2

    async def test_get_by_usuario_no_match(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await _create_tenant(db_session)
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)
        results = await repo.get_by_usuario(tenant.id, str(uuid.uuid4()))
        assert results == []

    async def test_get_by_materia(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository
        from app.models.materia import Materia

        tenant = await _create_tenant(db_session)
        user = await self._seed_user(db_session, tenant.id)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MATE", nombre="Matemáticas")
        db_session.add(materia)
        await db_session.flush()

        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)
        asig = await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "PROFESOR", "desde": date(2020, 1, 1),
            "materia_id": materia.id,
        })

        results = await repo.get_by_materia(tenant.id, materia.id)
        assert len(results) == 1
        assert results[0].id == asig.id

    async def test_get_by_rol(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await _create_tenant(db_session)
        user = await self._seed_user(db_session, tenant.id)
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)

        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "TUTOR", "desde": date(2020, 1, 1),
        })

        results = await repo.get_by_rol(tenant.id, "TUTOR")
        assert len(results) == 1

        results_no_match = await repo.get_by_rol(tenant.id, "ADMIN")
        assert results_no_match == []

    async def test_get_active_role_slugs(self, db_session: AsyncSession):
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await _create_tenant(db_session)
        user = await self._seed_user(db_session, tenant.id)
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)

        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "PROFESOR", "desde": date(2020, 1, 1),
        })
        await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": user.id,
            "rol": "COORDINADOR", "desde": date(2020, 1, 1),
            "hasta": date(2020, 12, 31),
        })

        slugs = await repo.get_active_role_slugs(tenant.id, user.id)
        assert "profesor" in slugs
        assert "coordinador" not in slugs
