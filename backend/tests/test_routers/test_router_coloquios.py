"""Tests for coloquios router endpoints."""

import uuid
from datetime import date

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

    from app.routers.coloquios import router as coloquios_router
    app.include_router(coloquios_router)
    return app


def _make_test_settings():
    from app.core.config import Settings
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestColoquiosRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session, extra_alumno=False):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id,
                          codigo="MAT-COL-R", nombre="Coloquio Test Router")
        db_session.add(materia)
        carrera = Carrera(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            codigo=f"CAR-{uuid.uuid4().hex[:4]}", nombre="Test Carrera",
        )
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="RTR-2026", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"col-rtr-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "coloquios:gestionar")
        asignacion = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            usuario_id=user.id, rol="COORDINADOR",
            materia_id=materia.id, desde=date(2026, 1, 1),
        )
        db_session.add(asignacion)
        if extra_alumno:
            alumno = await create_user(
                db_session, tenant_id=tenant.id,
                email=f"alu-rtr-{uuid.uuid4().hex[:8]}@test.com",
                roles=["alumno"],
            )
            asig_alumno = Asignacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                usuario_id=alumno.id, rol="ALUMNO",
                cohorte_id=cohorte.id, desde=date(2026, 1, 1),
            )
            db_session.add(asig_alumno)
        else:
            alumno = None
        await db_session.flush()
        return {
            "tenant_id": tenant.id, "materia_id": materia.id,
            "cohorte_id": cohorte.id, "user": user, "alumno": alumno,
        }

    # ── 403 ──

    async def test_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"no-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/coloquios", json={
                "materia_id": str(uuid.uuid4()),
                "cohorte_id": str(uuid.uuid4()),
                "instancia": "Test",
            })
        assert response.status_code == 403

    # ── CRUD evaluaciones ──

    async def test_crear_201(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Primer Llamado",
                "cupo_por_dia": 15,
            })
        assert response.status_code == 201
        data = response.json()
        assert data["instancia"] == "Primer Llamado"
        assert data["cupo_por_dia"] == 15
        assert data["activa"] is True

    async def test_listar_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "C1",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/coloquios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["instancia"] == "C1"

    async def test_detalle_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Detalle Test",
            })
            ev_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/coloquios/{ev_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["instancia"] == "Detalle Test"
        assert data["total_convocados"] == 0
        assert data["reservas_activas"] == 0

    async def test_detalle_404(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/coloquios/{uuid.uuid4()}")
        assert response.status_code == 404

    # ── Importar alumnos ──

    async def test_importar_alumnos_200(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Import",
            })
            ev_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/coloquios/{ev_id}/alumnos", json={
                "alumno_ids": [seed["alumno"].id],
            })
        assert response.status_code == 200
        data = response.json()
        assert seed["alumno"].id in data["convocados"]

    # ── Reservar ──

    async def test_reservar_201(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app_coord = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app_coord), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Reservar Test",
                "cupo_por_dia": 10,
            })
            ev_id = create_resp.json()["id"]
        app_alumno = _build_app(db_session, test_settings, seed["alumno"])
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            response = await client.post(f"/api/coloquios/{ev_id}/reservar", json={
                "fecha": "2026-07-01",
                "hora": "10:00",
            })
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "Activa"
        assert data["fecha"] == "2026-07-01"

    async def test_reservar_sin_cupo_400(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app_coord = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app_coord), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Sin Cupo Router",
                "cupo_por_dia": 1,
            })
            ev_id = create_resp.json()["id"]
        app_alumno = _build_app(db_session, test_settings, seed["alumno"])
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            await client.post(f"/api/coloquios/{ev_id}/reservar", json={
                "fecha": "2026-07-01", "hora": "10:00",
            })
        # Try with same alumno again → duplicate (400)
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            response = await client.post(f"/api/coloquios/{ev_id}/reservar", json={
                "fecha": "2026-07-02", "hora": "11:00",
            })
        assert response.status_code == 400

    # ── Cancelar reserva ──

    async def test_cancelar_reserva_200(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app_coord = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app_coord), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Cancel Router",
                "cupo_por_dia": 10,
            })
            ev_id = create_resp.json()["id"]
        app_alumno = _build_app(db_session, test_settings, seed["alumno"])
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            reserva_resp = await client.post(f"/api/coloquios/{ev_id}/reservar", json={
                "fecha": "2026-07-01", "hora": "10:00",
            })
            reserva_id = reserva_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            response = await client.patch(f"/api/coloquios/reservas/{reserva_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["detail"] == "Reserva cancelada"

    # ── Resultados ──

    async def test_registrar_resultado_201(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Resultado Router",
            })
            ev_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/api/coloquios/{ev_id}/resultados", json={
                "alumno_id": seed["alumno"].id,
                "nota_final": "Aprobado",
            })
        assert response.status_code == 201
        data = response.json()
        assert data["nota_final"] == "Aprobado"

    async def test_ver_resultados_200(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Ver Resultados",
            })
            ev_id = create_resp.json()["id"]
            await client.post(f"/api/coloquios/{ev_id}/resultados", json={
                "alumno_id": seed["alumno"].id,
                "nota_final": "8",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/coloquios/{ev_id}/resultados")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nota_final"] == "8"

    # ── Admin global ──

    async def test_admin_global_200(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "Admin Global Router",
            })
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/coloquios/admin")
        assert response.status_code == 200
        data = response.json()
        assert len(data["evaluaciones"]) == 1

    # ── Listar reservas ──

    async def test_listar_reservas_200(self, db_session, test_settings):
        seed = await self._seed(db_session, extra_alumno=True)
        app_coord = _build_app(db_session, test_settings, seed["user"])
        async with AsyncClient(transport=ASGITransport(app=app_coord), base_url="http://test") as client:
            create_resp = await client.post("/api/coloquios", json={
                "materia_id": seed["materia_id"],
                "cohorte_id": seed["cohorte_id"],
                "instancia": "List Reservas",
                "cupo_por_dia": 10,
            })
            ev_id = create_resp.json()["id"]
        app_alumno = _build_app(db_session, test_settings, seed["alumno"])
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            await client.post(f"/api/coloquios/{ev_id}/reservar", json={
                "fecha": "2026-07-01", "hora": "10:00",
            })
        async with AsyncClient(transport=ASGITransport(app=app_coord), base_url="http://test") as client:
            response = await client.get(f"/api/coloquios/{ev_id}/reservas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["estado"] == "Activa"

    # ── Multi-tenant isolation ──

    async def test_multi_tenant_isolation(self, db_session, test_settings):
        tenant1 = await _create_tenant(db_session)
        tenant2 = await _create_tenant(db_session)
        user1 = await create_user(
            db_session, tenant_id=tenant1.id,
            email=f"ct1-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        user2 = await create_user(
            db_session, tenant_id=tenant2.id,
            email=f"ct2-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "coloquios:gestionar")
        materia1 = Materia(id=str(uuid.uuid4()), tenant_id=tenant1.id, codigo="CT1", nombre="CT1")
        db_session.add(materia1)
        materia2 = Materia(id=str(uuid.uuid4()), tenant_id=tenant2.id, codigo="CT2", nombre="CT2")
        db_session.add(materia2)
        carrera1 = Carrera(id=str(uuid.uuid4()), tenant_id=tenant1.id, codigo="CAR1", nombre="C1")
        db_session.add(carrera1)
        carrera2 = Carrera(id=str(uuid.uuid4()), tenant_id=tenant2.id, codigo="CAR2", nombre="C2")
        db_session.add(carrera2)
        await db_session.flush()
        cohorte1 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant1.id, carrera_id=carrera1.id,
            nombre="CT1", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte1)
        cohorte2 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant2.id, carrera_id=carrera2.id,
            nombre="CT2", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte2)
        await db_session.flush()

        app1 = _build_app(db_session, test_settings, user1)
        async with AsyncClient(transport=ASGITransport(app=app1), base_url="http://test") as client:
            await client.post("/api/coloquios", json={
                "materia_id": materia1.id, "cohorte_id": cohorte1.id,
                "instancia": "T1 Only",
            })

        app2 = _build_app(db_session, test_settings, user2)
        async with AsyncClient(transport=ASGITransport(app=app2), base_url="http://test") as client:
            await client.post("/api/coloquios", json={
                "materia_id": materia2.id, "cohorte_id": cohorte2.id,
                "instancia": "T2 Only",
            })

        async with AsyncClient(transport=ASGITransport(app=app1), base_url="http://test") as client:
            response = await client.get("/api/coloquios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["instancia"] == "T1 Only"

    # ── Alumno ve solo su cohorte ──

    async def test_alumno_ve_solo_su_cohorte(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-FILTRO", nombre="Filtro")
        db_session.add(materia)
        carrera_test = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CAR-F", nombre="F")
        db_session.add(carrera_test)
        await db_session.flush()
        cohorte1 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera_test.id,
            nombre="C1", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte1)
        cohorte2 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera_test.id,
            nombre="C2", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte2)
        coordinador = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"coord-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "coloquios:gestionar")
        await db_session.flush()

        app_coord = _build_app(db_session, test_settings, coordinador)
        async with AsyncClient(transport=ASGITransport(app=app_coord), base_url="http://test") as client:
            await client.post("/api/coloquios", json={
                "materia_id": materia.id, "cohorte_id": cohorte1.id,
                "instancia": "Cohorte1",
            })
            await client.post("/api/coloquios", json={
                "materia_id": materia.id, "cohorte_id": cohorte2.id,
                "instancia": "Cohorte2",
            })

        alumno = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"alum-{uuid.uuid4().hex[:8]}@test.com",
            roles=["alumno"],
        )
        asig_alumno = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            usuario_id=alumno.id, rol="ALUMNO",
            cohorte_id=cohorte1.id, desde=date(2026, 1, 1),
        )
        db_session.add(asig_alumno)
        await db_session.flush()

        app_alumno = _build_app(db_session, test_settings, alumno)
        async with AsyncClient(transport=ASGITransport(app=app_alumno), base_url="http://test") as client:
            response = await client.get("/api/coloquios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["instancia"] == "Cohorte1"
