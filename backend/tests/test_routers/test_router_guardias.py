"""Tests for guardias router endpoints."""

import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.user import User
from tests.conftest import create_user


async def _create_tenant(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test",
        estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _seed_role_permiso(db_session, slug, codigo, alcance="global"):
    result = await db_session.execute(
        select(Rol).where(Rol.slug == slug)
    )
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db_session.add(role)
        await db_session.flush()
    result = await db_session.execute(
        select(Permiso).where(Permiso.codigo == codigo)
    )
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db_session.add(permiso)
        await db_session.flush()
    result = await db_session.execute(
        select(RolPermiso).where(
            RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id
        )
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

    from app.routers.guardias import router as guardias_router
    app.include_router(guardias_router)
    return app


def _make_test_settings():
    from app.core.config import Settings
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestGuardiasRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="MAT-GUA-R", nombre="Programación I")
        db_session.add(materia)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"gua-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "encuentros:gestionar")
        asignacion = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            usuario_id=user.id, rol="PROFESOR",
            materia_id=materia.id, desde=date(2026, 1, 1),
        )
        db_session.add(asignacion)
        await db_session.flush()
        return {"tenant_id": tenant.id, "materia_id": materia.id,
                "user": user, "asignacion_id": asignacion.id}

    # ── 403 ──

    async def test_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"no-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/guardias", json={})
        assert response.status_code == 403

    # ── Registrar ──

    async def test_registrar_201(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/guardias", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "dia": "Lunes",
                "horario": "14:00-14:45",
            })
        assert response.status_code == 201
        data = response.json()
        assert data["dia"] == "Lunes"
        assert data["horario"] == "14:00-14:45"
        assert data["estado"] == "Pendiente"

    # ── Listar ──

    async def test_listar_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/guardias", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "dia": "Lunes", "horario": "14:00-14:45",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/guardias", params={
                "materia_id": seed["materia_id"],
            })
        assert response.status_code == 200
        data = response.json()
        assert len(data["guardias"]) == 1
        assert data["guardias"][0]["dia"] == "Lunes"

    async def test_listar_sin_filtro_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/guardias")
        assert response.status_code == 200

    # ── Exportar ──

    async def test_exportar_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/guardias", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "dia": "Lunes", "horario": "14:00-14:45",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/guardias/export")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(response.content) > 0
