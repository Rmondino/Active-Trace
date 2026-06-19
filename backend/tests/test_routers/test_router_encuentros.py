"""Tests for encuentros router endpoints."""

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

    from app.routers.encuentros import router as encuentros_router
    app.include_router(encuentros_router)
    return app


def _make_test_settings():
    from app.core.config import Settings
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestEncuentrosRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="MAT-ENC-R", nombre="Programación I")
        db_session.add(materia)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"enc-{uuid.uuid4().hex[:8]}@test.com",
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
            response = await client.post("/api/encuentros/slots", json={})
        assert response.status_code == 403

    # ── CRUD slots ──

    async def test_crear_slot_201(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "Clase 1",
                "hora": "18:00",
                "cant_semanas": 0,
                "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01",
                "vig_hasta": "2026-03-31",
            })
        assert response.status_code == 201
        data = response.json()
        assert "slot" in data
        assert "instancias" in data
        assert len(data["instancias"]) == 1

    async def test_listar_slots_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "C1", "hora": "18:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/encuentros/slots", params={
                "materia_id": seed["materia_id"],
            })
        assert response.status_code == 200
        data = response.json()
        assert len(data["slots"]) == 1
        assert data["slots"][0]["titulo"] == "C1"

    async def test_detalle_slot_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "C1", "hora": "18:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })
            slot_id = create_resp.json()["slot"]["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/encuentros/slots/{slot_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["slot"]["titulo"] == "C1"
        assert len(data["instancias"]) == 1

    async def test_detalle_slot_404(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/encuentros/slots/{uuid.uuid4()}")
        assert response.status_code == 404

    # ── CRUD instancias ──

    async def test_editar_instancia_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "C1", "hora": "18:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })
            inst_id = create_resp.json()["instancias"][0]["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(f"/api/encuentros/instancias/{inst_id}", json={
                "estado": "Realizado",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "Realizado"

    async def test_listar_instancias_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "C1", "hora": "18:00",
                "cant_semanas": 2, "dia_semana": "Lunes",
                "fecha_inicio": "2026-03-02",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-04-01",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/encuentros/instancias", params={
                "materia_id": seed["materia_id"],
            })
        assert response.status_code == 200
        data = response.json()
        assert len(data["instancias"]) == 2

    # ── Contenido aula ──

    async def test_contenido_aula_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "C1", "hora": "18:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/encuentros/contenido-aula", params={
                "materia_id": seed["materia_id"],
            })
        assert response.status_code == 200
        assert "<table>" in response.text

    # ── Vista admin ──

    async def test_vista_admin_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/encuentros/slots", json={
                "asignacion_id": seed["asignacion_id"],
                "materia_id": seed["materia_id"],
                "titulo": "Admin", "hora": "18:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/encuentros/vista-admin")
        assert response.status_code == 200
        data = response.json()
        assert len(data["encuentros"]) == 1

    # ── Multi-tenant ──

    async def test_multi_tenant_isolation(self, db_session, test_settings):
        tenant1 = await _create_tenant(db_session)
        tenant2 = await _create_tenant(db_session)
        user1 = await create_user(
            db_session, tenant_id=tenant1.id,
            email=f"t1-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        user2 = await create_user(
            db_session, tenant_id=tenant2.id,
            email=f"t2-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "encuentros:gestionar")
        materia1 = Materia(id=str(uuid.uuid4()), tenant_id=tenant1.id,
                           codigo="MT1", nombre="Materia T1")
        db_session.add(materia1)
        materia2 = Materia(id=str(uuid.uuid4()), tenant_id=tenant2.id,
                           codigo="MT2", nombre="Materia T2")
        db_session.add(materia2)
        await db_session.flush()

        asig1 = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant1.id,
            usuario_id=user1.id, rol="PROFESOR",
            materia_id=materia1.id, desde=date(2026, 1, 1),
        )
        db_session.add(asig1)
        asig2 = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant2.id,
            usuario_id=user2.id, rol="PROFESOR",
            materia_id=materia2.id, desde=date(2026, 1, 1),
        )
        db_session.add(asig2)
        await db_session.flush()

        # Create slot for tenant1
        app1 = _build_app(db_session, test_settings, user1)
        async with AsyncClient(transport=ASGITransport(app=app1), base_url="http://test") as client:
            await client.post("/api/encuentros/slots", json={
                "asignacion_id": asig1.id,
                "materia_id": materia1.id,
                "titulo": "T1", "hora": "18:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-15",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })

        app2 = _build_app(db_session, test_settings, user2)
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://test") as client:
            await client.post("/api/encuentros/slots", json={
                "asignacion_id": asig2.id,
                "materia_id": materia2.id,
                "titulo": "T2", "hora": "19:00",
                "cant_semanas": 0, "fecha_unica": "2026-03-16",
                "vig_desde": "2026-03-01", "vig_hasta": "2026-03-31",
            })

        async with AsyncClient(transport=ASGITransport(app=app1), base_url="http://test") as client:
            response = await client.get("/api/encuentros/slots", params={
                "materia_id": materia1.id,
            })
        assert response.status_code == 200
        data = response.json()
        assert len(data["slots"]) == 1
        assert data["slots"][0]["titulo"] == "T1"
