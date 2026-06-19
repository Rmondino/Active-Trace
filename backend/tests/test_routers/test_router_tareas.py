"""Tests for tareas router endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.user import User
from app.models.tarea import Tarea
from tests.conftest import create_user


async def _create_tenant(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _seed_role_permiso(db_session, slug, codigo, alcance="global"):
    result = await db_session.execute(select(Rol).where(Rol.slug == slug))
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db_session.add(role)
        await db_session.flush()
    result = await db_session.execute(select(Permiso).where(Permiso.codigo == codigo))
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db_session.add(permiso)
        await db_session.flush()
    result = await db_session.execute(
        select(RolPermiso).where(RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id)
    )
    if result.scalar_one_or_none():
        return
    rp = RolPermiso(id=str(uuid.uuid4()), rol_id=role.id, permiso_id=permiso.id, alcance=alcance)
    db_session.add(rp)
    await db_session.flush()


def _build_app(db_session, settings, user):
    from app.core.config import get_settings
    from app.core.current_user import get_current_user
    from app.core.database import get_db_session

    app = FastAPI()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user

    async def _db_override():
        yield db_session
    app.dependency_overrides[get_db_session] = _db_override

    from app.routers.tareas import router as tareas_router
    app.include_router(tareas_router)
    return app


def _make_test_settings():
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestTareasRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        admin = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"admin-tarea-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        asignado = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"asig-tarea-{uuid.uuid4().hex[:8]}@test.com",
        )
        await _seed_role_permiso(db_session, "coordinador", "tareas:gestionar")
        return {"tenant_id": tenant.id, "admin": admin, "asignado_id": asignado.id}

    async def _seed_tarea(self, db_session, tenant_id, asignado_a, asignado_por, **overrides):
        defaults = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "asignado_a": asignado_a,
            "asignado_por": asignado_por,
            "descripcion": "Tarea de prueba",
        }
        defaults.update(overrides)
        tarea = Tarea(**defaults)
        db_session.add(tarea)
        await db_session.flush()
        return tarea

    # ── POST /api/tareas ──

    async def test_crear_tarea_201(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/tareas",
                json={
                    "asignado_a": seed["asignado_id"],
                    "descripcion": "Nueva tarea desde API",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["descripcion"] == "Nueva tarea desde API"
            assert data["asignado_a"] == seed["asignado_id"]

    async def test_crear_tarea_403_sin_permiso(self, db_session, test_settings):
        seed = await self._seed(db_session)
        # user without tareas:gestionar
        no_perm_user = await create_user(
            db_session, tenant_id=seed["tenant_id"],
            email=f"noperm-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, no_perm_user)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/tareas",
                json={"asignado_a": seed["asignado_id"], "descripcion": "Sin permiso"},
            )
            assert response.status_code == 403

    # ── GET /api/tareas ──

    async def test_listar_todas_admin(self, db_session, test_settings):
        seed = await self._seed(db_session)
        await self._seed_tarea(db_session, seed["tenant_id"], seed["asignado_id"], seed["admin"].id)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tareas")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    async def test_listar_todas_403_sin_permiso(self, db_session, test_settings):
        seed = await self._seed(db_session)
        no_perm_user = await create_user(
            db_session, tenant_id=seed["tenant_id"],
            email=f"noperm2-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, no_perm_user)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tareas")
            assert response.status_code == 403

    # ── GET /api/tareas/mias ──

    async def test_mis_tareas(self, db_session, test_settings):
        seed = await self._seed(db_session)
        # Create one task assigned to admin
        await self._seed_tarea(db_session, seed["tenant_id"], seed["admin"].id, seed["admin"].id)
        # Create one for another user
        await self._seed_tarea(db_session, seed["tenant_id"], seed["asignado_id"], seed["admin"].id)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tareas/mias")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    # ── GET /api/tareas/{id} ──

    async def test_detalle_tarea(self, db_session, test_settings):
        seed = await self._seed(db_session)
        tarea = await self._seed_tarea(db_session, seed["tenant_id"], seed["admin"].id, seed["admin"].id)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/tareas/{tarea.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == tarea.id
            assert "comentarios" in data

    # ── PATCH /api/tareas/{id}/estado ──

    async def test_cambiar_estado_valido(self, db_session, test_settings):
        seed = await self._seed(db_session)
        tarea = await self._seed_tarea(db_session, seed["tenant_id"], seed["admin"].id, seed["admin"].id)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/tareas/{tarea.id}/estado",
                json={"estado": "En progreso"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["estado"] == "En progreso"

    async def test_cambiar_estado_invalido_400(self, db_session, test_settings):
        seed = await self._seed(db_session)
        tarea = await self._seed_tarea(db_session, seed["tenant_id"], seed["admin"].id, seed["admin"].id)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/tareas/{tarea.id}/estado",
                json={"estado": "Resuelta"},
            )
            assert response.status_code == 400

    # ── POST /api/tareas/{id}/comentarios ──

    async def test_agregar_comentario_201(self, db_session, test_settings):
        seed = await self._seed(db_session)
        tarea = await self._seed_tarea(db_session, seed["tenant_id"], seed["admin"].id, seed["admin"].id)
        app = _build_app(db_session, test_settings, seed["admin"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/tareas/{tarea.id}/comentarios",
                json={"texto": "Un comentario desde la API"},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["texto"] == "Un comentario desde la API"

    # ── Multi-tenant ──

    async def test_multi_tenant_isolation(self, db_session, test_settings):
        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)

        admin1 = await create_user(
            db_session, tenant_id=t1.id,
            email=f"adm1-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        admin2 = await create_user(
            db_session, tenant_id=t2.id,
            email=f"adm2-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "tareas:gestionar")

        # Create tarea in t2
        t2_tarea = Tarea(
            id=str(uuid.uuid4()), tenant_id=t2.id,
            asignado_a=admin2.id, asignado_por=admin2.id,
            descripcion="T2 tarea",
        )
        db_session.add(t2_tarea)
        await db_session.flush()

        # Admin from t1 should see 0 tareas
        app = _build_app(db_session, test_settings, admin1)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/tareas")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
