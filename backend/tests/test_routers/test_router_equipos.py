"""Tests for equipos router endpoints."""

import uuid
from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
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
        __import__("sqlalchemy").select(Rol).where(Rol.slug == slug)
    )
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db_session.add(role)
        await db_session.flush()

    result = await db_session.execute(
        __import__("sqlalchemy").select(Permiso).where(Permiso.codigo == codigo)
    )
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db_session.add(permiso)
        await db_session.flush()

    result = await db_session.execute(
        __import__("sqlalchemy").select(RolPermiso).where(
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

    from app.routers.equipos import router as equipos_router
    app.include_router(equipos_router)
    return app


def _make_test_settings():
    from app.core.config import Settings
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestEquiposRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="MAT-EQ-R", nombre="Programación I")
        db_session.add(materia)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="TUPAD", nombre="Tecnicatura")
        db_session.add(carrera)
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          carrera_id=carrera.id, nombre="2025 AGO", anio=2025,
                          vig_desde="2025-08-01")
        db_session.add(cohorte)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"eq-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "equipos:asignar")
        await db_session.flush()

        asig = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia.id, carrera_id=carrera.id,
            cohorte_id=cohorte.id, comisiones=["A"], desde=date.today(),
        )
        db_session.add(asig)
        await db_session.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id,
                "carrera_id": carrera.id, "cohorte_id": cohorte.id,
                "user": user, "asignacion_id": asig.id}

    # ── Mis equipos ──

    async def test_mis_equipos_returns_200(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"me-{uuid.uuid4().hex[:8]}@test.com",
        )
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="MAT-ME", nombre="Mi Mat")
        db_session.add(materia)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="CARR", nombre="Carrera")
        db_session.add(carrera)
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          carrera_id=carrera.id, nombre="C1", anio=2025,
                          vig_desde="2025-01-01")
        db_session.add(cohorte)
        asig = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia.id, carrera_id=carrera.id,
            cohorte_id=cohorte.id, comisiones=[], desde=date.today(),
        )
        db_session.add(asig)
        await db_session.flush()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/mis-equipos")
        assert response.status_code == 200
        data = response.json()
        assert "asignaciones" in data
        assert len(data["asignaciones"]) == 1
        assert data["asignaciones"][0]["rol"] == "PROFESOR"

    async def test_mis_equipos_filters_vigente(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"me2-{uuid.uuid4().hex[:8]}@test.com",
        )
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="MAT-ME2", nombre="Mat")
        db_session.add(materia)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="CARR2", nombre="Car")
        db_session.add(carrera)
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          carrera_id=carrera.id, nombre="C2", anio=2025,
                          vig_desde="2025-01-01")
        db_session.add(cohorte)
        past = date.today() - timedelta(days=365)
        asig1 = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia.id, carrera_id=carrera.id,
            cohorte_id=cohorte.id, comisiones=[], desde=date.today(),
        )
        db_session.add(asig1)
        asig2 = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="TUTOR", materia_id=materia.id, carrera_id=carrera.id,
            cohorte_id=cohorte.id, comisiones=[], desde=past, hasta=past,
        )
        db_session.add(asig2)
        await db_session.flush()

        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/mis-equipos",
                                         params={"estado": "vigente"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["asignaciones"]) == 1
        assert data["asignaciones"][0]["vigente"] is True

    # ── Asignaciones (admin view) ──

    async def test_asignaciones_403_for_profesor(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"prof-{uuid.uuid4().hex[:8]}@test.com",
            roles=["profesor"],
        )
        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/asignaciones")
        assert response.status_code == 403

    async def test_asignaciones_200_for_coordinador(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/asignaciones")
        assert response.status_code == 200
        data = response.json()
        assert "asignaciones" in data
        assert len(data["asignaciones"]) >= 1

    async def test_asignaciones_filters_by_rol(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user2 = await create_user(
            db_session, tenant_id=seed["tenant_id"],
            email=f"tutor-{uuid.uuid4().hex[:8]}@test.com",
        )
        asig_tutor = Asignacion(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"], usuario_id=user2.id,
            rol="TUTOR", materia_id=seed["materia_id"],
            carrera_id=seed["carrera_id"], cohorte_id=seed["cohorte_id"],
            comisiones=[], desde=date.today(),
        )
        db_session.add(asig_tutor)
        await db_session.flush()

        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/asignaciones",
                                         params={"rol": "TUTOR"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["asignaciones"]) == 1
        assert data["asignaciones"][0]["rol"] == "TUTOR"

    # ── Asignación masiva ──

    async def test_masiva_creates_assignments(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user2 = await create_user(
            db_session, tenant_id=seed["tenant_id"],
            email=f"mas-{uuid.uuid4().hex[:8]}@test.com",
        )
        await db_session.flush()
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/equipos/asignaciones/masiva", json={
                "docente_ids": [seed["user"].id, user2.id],
                "rol": "PROFESOR",
                "materia_id": seed["materia_id"],
                "carrera_id": seed["carrera_id"],
                "cohorte_id": seed["cohorte_id"],
                "desde": str(date.today()),
            })
        assert response.status_code == 201
        data = response.json()
        assert data["total_creadas"] == 2

    async def test_masiva_403_without_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"noasig-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/equipos/asignaciones/masiva", json={
                "docente_ids": [], "rol": "PROFESOR",
                "materia_id": str(uuid.uuid4()), "carrera_id": str(uuid.uuid4()),
                "cohorte_id": str(uuid.uuid4()), "desde": "2025-01-01",
            })
        assert response.status_code == 403

    # ── Clonar ──

    async def test_clonar_returns_201(self, db_session, test_settings):
        seed = await self._seed(db_session)
        cohorte2 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            carrera_id=seed["carrera_id"], nombre="2026", anio=2026,
            vig_desde="2026-03-01",
        )
        db_session.add(cohorte2)
        await db_session.flush()

        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/equipos/clonar", json={
                "origen_materia_id": seed["materia_id"],
                "origen_carrera_id": seed["carrera_id"],
                "origen_cohorte_id": seed["cohorte_id"],
                "destino_materia_id": seed["materia_id"],
                "destino_carrera_id": seed["carrera_id"],
                "destino_cohorte_id": cohorte2.id,
                "nuevo_desde": "2026-03-01",
                "nuevo_hasta": "2026-12-31",
            })
        assert response.status_code == 201
        data = response.json()
        assert data["total_clonadas"] >= 1

    # ── Vigencia ──

    async def test_vigencia_updates_dates(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch("/api/equipos/vigencia", json={
                "materia_id": seed["materia_id"],
                "carrera_id": seed["carrera_id"],
                "cohorte_id": seed["cohorte_id"],
                "nuevo_desde": "2026-01-01",
                "nuevo_hasta": "2026-12-31",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["total_actualizadas"] >= 1

    # ── Export ──

    async def test_export_returns_xlsx(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/export", params={
                "materia_id": seed["materia_id"],
                "carrera_id": seed["carrera_id"],
                "cohorte_id": seed["cohorte_id"],
            })
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(response.content) > 0

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
        await _seed_role_permiso(db_session, "coordinador", "equipos:asignar")
        materia1 = Materia(id=str(uuid.uuid4()), tenant_id=tenant1.id,
                           codigo="M1", nombre="Materia 1")
        db_session.add(materia1)
        materia2 = Materia(id=str(uuid.uuid4()), tenant_id=tenant2.id,
                           codigo="M2", nombre="Materia 2")
        db_session.add(materia2)
        await db_session.flush()

        db_session.add(Asignacion(id=str(uuid.uuid4()), tenant_id=tenant1.id, usuario_id=user1.id,
                   rol="PROFESOR", materia_id=materia1.id,
                   comisiones=[], desde=date.today()))
        db_session.add(Asignacion(id=str(uuid.uuid4()), tenant_id=tenant2.id, usuario_id=user2.id,
                   rol="PROFESOR", materia_id=materia2.id,
                   comisiones=[], desde=date.today()))
        await db_session.flush()

        app = _build_app(db_session, test_settings, user1)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/equipos/asignaciones")
        assert response.status_code == 200
        data = response.json()
        for a in data["asignaciones"]:
            assert a["tenant_id"] == tenant1.id
