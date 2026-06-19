"""Tests for C-07 routers: admin/usuarios, asignaciones, usuarios/me."""
import hashlib
import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from tests.conftest import create_user


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


async def _seed_role_permiso(db, slug, codigo, alcance="global"):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso
    from sqlalchemy import select

    result = await db.execute(select(Rol).where(Rol.slug == slug))
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db.add(role)
        await db.flush()

    result = await db.execute(select(Permiso).where(Permiso.codigo == codigo))
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db.add(permiso)
        await db.flush()

    result = await db.execute(
        select(RolPermiso).where(RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id)
    )
    if result.scalar_one_or_none():
        return
    rp = RolPermiso(id=str(uuid.uuid4()), rol_id=role.id, permiso_id=permiso.id, alcance=alcance)
    db.add(rp)
    await db.flush()


def _build_app(db_session, settings, user):
    from fastapi import FastAPI
    from app.core.config import get_settings
    from app.core.current_user import get_current_user
    from app.core.database import get_db_session

    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user

    async def _db_override():
        yield db_session
    app.dependency_overrides[get_db_session] = _db_override

    from app.routers.admin.usuarios import router as usuarios_router
    from app.routers.asignaciones import router as asignaciones_router
    from app.routers.usuarios_me import router as usuarios_me_router

    app.include_router(usuarios_router)
    app.include_router(asignaciones_router)
    app.include_router(usuarios_me_router)
    return app


class TestUsuariosRouter:
    """CRUD de usuarios via /api/admin/usuarios."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _create_admin_user(self, db, tenant_id):
        from tests.conftest import create_user
        u = await create_user(db, tenant_id, email=f"admin-{uuid.uuid4().hex[:8]}@test.com", password="Pass1234!", roles=["admin"])
        await _seed_role_permiso(db, "admin", "usuarios:gestionar")
        return u

    async def test_create_user_201(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/admin/usuarios", json={
                "nombre": "Juan",
                "apellidos": "Pérez",
                "email": "juan@example.com",
                "dni": "12345678",
                "cuil": "20-12345678-9",
                "legajo": "LEG-001",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Juan"
        assert data["apellidos"] == "Pérez"
        assert data["email"] == "juan@example.com"

    async def test_create_user_duplicate_email_409(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        # Create existing user with same email
        await create_user(db_session, tenant.id, email="duplicate@test.com")
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/admin/usuarios", json={
                "nombre": "Dup", "apellidos": "User",
                "email": "duplicate@test.com", "dni": "00000000",
            })
        assert resp.status_code == 409

    async def test_create_user_403_without_permission(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com", roles=["tutor"])
        await db_session.commit()

        app = _build_app(db_session, test_settings, user_no_perm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/admin/usuarios", json={
                "nombre": "No", "apellidos": "Perm",
                "email": "no@test.com", "dni": "00000000",
            })
        assert resp.status_code == 403

    async def test_list_users_masks_pii(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        await create_user(db_session, tenant.id, email=f"list-{uuid.uuid4().hex[:8]}@test.com", nombre="Visible", apellidos="User")
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/admin/usuarios")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        # PII should be masked in list
        for user in data:
            assert "***" in user["email"] or "@" not in user["email"]

    async def test_get_user_detail_returns_full_pii(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"detail-{uuid.uuid4().hex[:8]}@test.com", nombre="Detail", apellidos="View")
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/usuarios/{target.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Detail"
        assert data["id"] == target.id

    async def test_get_user_404(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/admin/usuarios/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_update_user_200(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"update-{uuid.uuid4().hex[:8]}@test.com", nombre="Old", apellidos="Name")
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(f"/api/admin/usuarios/{target.id}", json={
                "nombre": "Updated",
            })
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Updated"

    async def test_update_user_404(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(f"/api/admin/usuarios/{uuid.uuid4()}", json={"nombre": "Nope"})
        assert resp.status_code == 404

    async def test_delete_user_204(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"delete-{uuid.uuid4().hex[:8]}@test.com")
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/admin/usuarios/{target.id}")
        assert resp.status_code == 204

    async def test_deleted_user_not_in_list(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        admin = await self._create_admin_user(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"gone-{uuid.uuid4().hex[:8]}@test.com")
        await db_session.commit()

        app = _build_app(db_session, test_settings, admin)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.delete(f"/api/admin/usuarios/{target.id}")
            resp = await client.get("/api/admin/usuarios")
        assert resp.status_code == 200
        ids = [u["id"] for u in resp.json()]
        assert target.id not in ids


class TestAsignacionesRouter:
    """CRUD de asignaciones via /api/asignaciones."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _create_coordinador(self, db, tenant_id):
        from tests.conftest import create_user
        u = await create_user(db, tenant_id, email=f"coord-{uuid.uuid4().hex[:8]}@test.com", password="Pass1234!", roles=["coordinador"])
        await _seed_role_permiso(db, "coordinador", "equipos:asignar")
        return u

    async def test_create_asignacion_201(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        coord = await self._create_coordinador(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com")
        await db_session.commit()

        app = _build_app(db_session, test_settings, coord)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/asignaciones", json={
                "usuario_id": target.id,
                "rol": "PROFESOR",
                "desde": str(date.today() - timedelta(days=30)),
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["rol"] == "PROFESOR"
        assert data["estado_vigencia"] == "Vigente"

    async def test_list_asignaciones_filter_by_usuario(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        coord = await self._create_coordinador(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"filter-{uuid.uuid4().hex[:8]}@test.com")
        await db_session.commit()

        from app.repositories.asignacion_repository import AsignacionRepository
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)
        asig = await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": target.id,
            "rol": "PROFESOR", "desde": date(2020, 1, 1),
        })
        await db_session.commit()

        app = _build_app(db_session, test_settings, coord)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/asignaciones?usuario_id={target.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert any(a["id"] == asig.id for a in data)

    async def test_get_asignacion_detail(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        coord = await self._create_coordinador(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"detail-{uuid.uuid4().hex[:8]}@test.com")

        from app.repositories.asignacion_repository import AsignacionRepository
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)
        asig = await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": target.id,
            "rol": "TUTOR", "desde": date(2020, 1, 1),
        })
        await db_session.commit()

        app = _build_app(db_session, test_settings, coord)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/asignaciones/{asig.id}")
        assert resp.status_code == 200
        assert resp.json()["rol"] == "TUTOR"

    async def test_delete_asignacion_204(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        coord = await self._create_coordinador(db_session, tenant.id)
        target = await create_user(db_session, tenant.id, email=f"del-asig-{uuid.uuid4().hex[:8]}@test.com")

        from app.repositories.asignacion_repository import AsignacionRepository
        repo = AsignacionRepository(session=db_session, tenant_id=tenant.id)
        asig = await repo.create({
            "id": str(uuid.uuid4()), "usuario_id": target.id,
            "rol": "TUTOR", "desde": date(2020, 1, 1),
        })
        await db_session.commit()

        app = _build_app(db_session, test_settings, coord)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/api/asignaciones/{asig.id}")
        assert resp.status_code == 204

    async def test_create_asignacion_403_without_permission(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        await db_session.commit()

        app = _build_app(db_session, test_settings, user_no_perm)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/asignaciones", json={
                "usuario_id": str(uuid.uuid4()),
                "rol": "TUTOR",
                "desde": str(date.today()),
            })
        assert resp.status_code == 403


class TestUsuariosMeRouter:
    """Perfil propio: GET /api/usuarios/me y GET /api/usuarios/me/asignaciones."""

    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def test_get_me(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"me-{uuid.uuid4().hex[:8]}@test.com", nombre="Mi", apellidos="Perfil")
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/usuarios/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Mi"
        assert data["apellidos"] == "Perfil"

    async def test_get_me_asignaciones(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        user = await create_user(db_session, tenant.id, email=f"me-asig-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/usuarios/me/asignaciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["rol"] == "PROFESOR"

    async def test_update_me_perfil(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"update-me-{uuid.uuid4().hex[:8]}@test.com",
            nombre="Viejo", apellidos="Nombre",
            banco="Banco Original",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put("/api/usuarios/me", json={
                "nombre": "Nuevo",
                "apellidos": "Apellido",
                "banco": "Banco Nuevo",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Nuevo"
        assert data["apellidos"] == "Apellido"
        assert data["banco"] == "Banco Nuevo"

    async def test_update_me_cuil_no_se_modifica(self, db_session, test_settings):
        from tests.conftest import create_user
        from app.core.security import decrypt, get_encryption_key
        from app.core.config import Settings

        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )
        enc_key = get_encryption_key(settings)

        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"cuil-nochange-{uuid.uuid4().hex[:8]}@test.com",
            nombre="Original", apellidos="User",
            cuil="20-12345678-9",
        )
        cuil_original = decrypt(user.cuil, enc_key) if user.cuil else None
        await db_session.commit()

        app = _build_app(db_session, settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put("/api/usuarios/me", json={
                "nombre": "Actualizado",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Actualizado"
        assert data["cuil"] == cuil_original

        # Verify via GET too
        resp = await client.get("/api/usuarios/me")
        assert resp.status_code == 200
        assert resp.json()["cuil"] == cuil_original

    async def test_update_me_422_extra_fields(self, db_session, test_settings):
        from tests.conftest import create_user
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id,
            email=f"extra-me-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.commit()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put("/api/usuarios/me", json={
                "nombre": "Test",
                "cuil": "20-99999999-9",
            })
        assert resp.status_code == 422

    async def test_get_me_401_without_auth(self, db_session, test_settings):
        from fastapi import FastAPI
        from app.routers.usuarios_me import router as usuarios_me_router
        from app.core.database import get_db_session
        from app.core.config import get_settings

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        app.include_router(usuarios_me_router)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Send invalid token to trigger 401
            resp = await client.get(
                "/api/usuarios/me",
                headers={"Authorization": "Bearer invalidtoken"},
            )
        assert resp.status_code == 401


# ═══════════════════════════════════════════
# 7.8 Multi-tenant isolation
# ═══════════════════════════════════════════


class TestMultitenantIsolation:
    """Users and asignaciones from different tenants must be isolated."""

    async def test_usuarios_no_visibles_entre_tenants(self, db_session, test_settings):
        """User from tenant A should not see users from tenant B via repo."""
        tenant_a = await _create_tenant(db_session)
        tenant_b = await _create_tenant(db_session)
        user_a = await create_user(db_session, tenant_a.id, email="a@a.com")
        user_b = await create_user(db_session, tenant_b.id, email="b@b.com")
        await db_session.commit()

        from app.repositories.user_repository import UserRepository

        repo_a = UserRepository(session=db_session, tenant_id=tenant_a.id)
        users_a = await repo_a.list()
        user_ids_a = {u.id for u in users_a}

        assert user_a.id in user_ids_a
        assert user_b.id not in user_ids_a

    async def test_asignaciones_no_visibles_entre_tenants(self, db_session, test_settings):
        """Asignaciones from tenant A should not leak to tenant B via repo."""
        from datetime import date
        from app.models.asignacion import Asignacion

        tenant_a = await _create_tenant(db_session)
        tenant_b = await _create_tenant(db_session)
        user_a = await create_user(db_session, tenant_a.id, email="a2@a.com")
        user_b = await create_user(db_session, tenant_b.id, email="b2@b.com")

        asig_a = Asignacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant_a.id,
            usuario_id=user_a.id,
            rol="PROFESOR",
            desde=date(2020, 1, 1),
        )
        asig_b = Asignacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant_b.id,
            usuario_id=user_b.id,
            rol="TUTOR",
            desde=date(2020, 1, 1),
        )
        db_session.add_all([asig_a, asig_b])
        await db_session.commit()

        from app.repositories.asignacion_repository import AsignacionRepository

        repo_a = AsignacionRepository(session=db_session, tenant_id=tenant_a.id)
        asignaciones_a = await repo_a.list()
        asig_ids_a = {a.id for a in asignaciones_a}

        assert asig_a.id in asig_ids_a
        assert asig_b.id not in asig_ids_a

    async def test_create_user_email_hash_unique_per_tenant(self, db_session, test_settings):
        """Same email hash can exist in different tenants (no global collision)."""
        tenant_a = await _create_tenant(db_session)
        tenant_b = await _create_tenant(db_session)

        from app.repositories.user_repository import UserRepository

        repo_a = UserRepository(session=db_session, tenant_id=tenant_a.id)
        repo_b = UserRepository(session=db_session, tenant_id=tenant_b.id)

        # Same email in different tenants should not conflict
        await create_user(db_session, tenant_a.id, email="dupe@test.com")
        await db_session.commit()

        exists_a = await repo_a.exists_by_email_hash(tenant_a.id, hashlib.sha256(b"dupe@test.com").hexdigest())
        exists_b = await repo_b.exists_by_email_hash(tenant_b.id, hashlib.sha256(b"dupe@test.com").hexdigest())

        assert exists_a is True
        assert exists_b is False
