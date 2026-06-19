"""Tests for analisis router endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.models.tenant import Tenant
from tests.conftest import create_user


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


async def _create_tenant(db) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test",
        estado="Activo",
    )
    db.add(t)
    await db.flush()
    return t


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

    from app.routers.analisis import router as analisis_router
    app.include_router(analisis_router)
    return app


class TestAnalisisPermisos:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db):
        tenant = await _create_tenant(db)
        user = await create_user(
            db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"],
        )
        await _seed_role_permiso(db, "profesor", "atrasados:ver")
        return {"tenant_id": tenant.id, "user": user}

    async def test_atrasados_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/atrasados", params={"materia_id": "x", "cohorte_id": "y"})
        assert resp.status_code == 403

    async def test_ranking_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/ranking", params={"materia_id": "x"})
        assert resp.status_code == 403

    async def test_reporte_rapido_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/reporte-rapido", params={"materia_id": "x"})
        assert resp.status_code == 403

    async def test_notas_finales_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/notas-finales", params={"materia_id": "x", "cohorte_id": "y"})
        assert resp.status_code == 403

    async def test_export_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/exportar-sin-corregir", params={"materia_id": "x"})
        assert resp.status_code == 403

    async def test_monitor_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/monitor")
        assert resp.status_code == 403


class TestAnalisisEndpoints:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed_full(self, db):
        tenant = await _create_tenant(db)
        carrera = __import__("app.models.carrera", fromlist=["Carrera"]).Carrera(
            id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T",
        )
        db.add(carrera)
        await db.flush()
        materia = __import__("app.models.materia", fromlist=["Materia"]).Materia(
            id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-ROUT", nombre="Test",
        )
        db.add(materia)
        await db.flush()
        cohorte = __import__("app.models.cohorte", fromlist=["Cohorte"]).Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db.add(cohorte)
        await db.flush()
        user = await create_user(
            db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"],
        )
        await _seed_role_permiso(db, "profesor", "atrasados:ver")

        from datetime import date
        asig = __import__("app.models.asignacion", fromlist=["Asignacion"]).Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia.id, desde=date(2020, 1, 1), comisiones=[],
        )
        db.add(asig)
        await db.flush()

        vp = __import__("app.models.version_padron", fromlist=["VersionPadron"]).VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=2, activa=True,
        )
        db.add(vp)
        await db.flush()

        ep_a = __import__("app.models.entrada_padron", fromlist=["EntradaPadron"]).EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Juan", apellidos="Perez", email="juan@test.com", comision="A",
        )
        ep_b = __import__("app.models.entrada_padron", fromlist=["EntradaPadron"]).EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Maria", apellidos="Gomez", email="maria@test.com", comision="A",
        )
        db.add(ep_a)
        db.add(ep_b)
        await db.flush()

        umbral = __import__("app.models.umbral_materia", fromlist=["UmbralMateria"]).UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asig.id, materia_id=materia.id,
            umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
        )
        db.add(umbral)
        await db.flush()

        Calificacion = __import__("app.models.calificacion", fromlist=["Calificacion"]).Calificacion
        for act in ["TP1", "TP2", "TP3"]:
            db.add(Calificacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                entrada_padron_id=ep_a.id, materia_id=materia.id,
                actividad=act, nota_numerica=__import__("decimal").Decimal("80"),
                origen="Importado", aprobado=True,
            ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep_b.id, materia_id=materia.id,
            actividad="TP1", nota_numerica=__import__("decimal").Decimal("80"),
            origen="Importado", aprobado=True,
        ))
        await db.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_atrasados_with_permiso(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/analisis/atrasados",
                params={"materia_id": seed["materia_id"], "cohorte_id": seed["cohorte_id"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_ranking_with_permiso(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/analisis/ranking",
                params={"materia_id": seed["materia_id"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_reporte_rapido_with_permiso(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/analisis/reporte-rapido",
                params={"materia_id": seed["materia_id"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alumnos" in data

    async def test_notas_finales_with_permiso(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/analisis/notas-finales",
                params={"materia_id": seed["materia_id"], "cohorte_id": seed["cohorte_id"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_export_sin_corregir_with_permiso(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/analisis/exportar-sin-corregir",
                params={"materia_id": seed["materia_id"]},
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    async def test_monitor_with_permiso(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/monitor")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_profesor_cannot_access_scope_general(self, db_session, test_settings):
        seed = await self._seed_full(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analisis/monitor?scope=general")
        assert resp.status_code == 403
