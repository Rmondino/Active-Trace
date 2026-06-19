"""Tests for calificaciones router endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.models.tenant import Tenant
from tests.conftest import create_user


async def _create_tenant(db_session) -> Tenant:
    tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test",
        estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _create_carrera(db_session, tenant_id):
    from app.models.carrera import Carrera
    carrera = Carrera(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        codigo=f"CARR-{uuid.uuid4().hex[:6]}",
        nombre="Test Carrera",
    )
    db_session.add(carrera)
    await db_session.flush()
    return carrera


async def _seed_role_permiso(db_session, slug, codigo, alcance="global"):
    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso
    from sqlalchemy import select

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

    from app.routers.calificaciones import router as calificaciones_router
    from app.routers.umbral import router as umbral_router
    app.include_router(calificaciones_router)
    app.include_router(umbral_router)
    return app


class TestCalificacionesImport:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT500", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_import_csv_preview(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1 (Real),TP Grupal\nJuan Perez,75,Satisfactorio\nMaria Gomez,45,Regular\n"
            response = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 200
            data = response.json()
            assert "preview_id" in data
            assert data["total_alumnos"] == 2
            assert len(data["actividades"]) == 2
            assert data["actividades"][0]["tipo"] == "numerica"
            assert data["actividades"][1]["tipo"] == "textual"

    async def test_import_csv_confirm(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1 (Real)\nJuan Perez,75\nMaria Gomez,45\n"
            response = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "true",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["total_calificaciones"] == 2
            assert data["total_aprobados"] == 1

    async def test_import_invalid_file_type(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("test.txt", b"some text", "text/plain")},
            )
            assert response.status_code == 400
            assert "formato" in response.json()["detail"].lower()

    async def test_import_sin_permiso_403(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user_no_perm = await create_user(db_session, tenant_id=seed["tenant_id"], email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Nota\nJuan,70\n"
            response = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 403

    async def test_import_no_columns(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno\nJuan\n"
            response = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 400
            assert "actividades" in response.json()["detail"].lower()


class TestCalificacionesPreviewConfirm:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT501", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_confirm_preview(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1 (Real)\nJuan Perez,75\nMaria Gomez,45\n"
            preview_resp = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert preview_resp.status_code == 200
            preview_id = preview_resp.json()["preview_id"]

            confirm_resp = await client.post(
                f"/api/calificaciones/preview/{preview_id}/confirm",
                json={"actividades_seleccionadas": ["Parcial 1 (Real)"]},
            )
            assert confirm_resp.status_code == 201
            data = confirm_resp.json()
            assert data["total_calificaciones"] == 2
            assert data["total_aprobados"] == 1

    async def test_confirm_preview_filtered(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1 (Real),TP Grupal\nJuan Perez,75,Satisfactorio\nMaria Gomez,45,Regular\n"
            preview_resp = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert preview_resp.status_code == 200
            preview_id = preview_resp.json()["preview_id"]

            confirm_resp = await client.post(
                f"/api/calificaciones/preview/{preview_id}/confirm",
                json={"actividades_seleccionadas": ["Parcial 1 (Real)"]},
            )
            assert confirm_resp.status_code == 201
            data = confirm_resp.json()
            assert data["total_calificaciones"] == 2

    async def test_confirm_nonexistent_preview(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/calificaciones/preview/{uuid.uuid4()}/confirm",
                json={"actividades_seleccionadas": []},
            )
            assert response.status_code == 404

    async def test_confirm_sin_permiso_403(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user_no_perm = await create_user(db_session, tenant_id=seed["tenant_id"], email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/calificaciones/preview/{uuid.uuid4()}/confirm",
                json={"actividades_seleccionadas": []},
            )
            assert response.status_code == 403


class TestCalificacionesList:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT502", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:ver")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_list_calificaciones_empty(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/calificaciones",
                params={"materia_id": seed["materia_id"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert data == []

    async def test_list_calificaciones_sin_permiso_403(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user_no_perm = await create_user(db_session, tenant_id=seed["tenant_id"], email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/calificaciones",
                params={"materia_id": seed["materia_id"]},
            )
            assert response.status_code == 403

    async def test_list_calificaciones_after_import(self, db_session, test_settings):
        seed = await self._seed(db_session)
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1 (Real)\nJuan Perez,75\nMaria Gomez,45\n"
            import_resp = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "true",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert import_resp.status_code == 201

            list_resp = await client.get(
                "/api/calificaciones",
                params={"materia_id": seed["materia_id"]},
            )
            assert list_resp.status_code == 200
            data = list_resp.json()
            assert len(data) == 2
            assert data[0]["actividad"] == "Parcial 1 (Real)"


class TestCalificacionesCompletions:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT503", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "user": user}

    async def test_completions_returns_uncorrected(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,TP1,Estado\nJuan Perez,completado,completado\nMaria Gomez,completado,completado\n"
            response = await client.post(
                "/api/calificaciones/import/completions",
                data={"materia_id": seed["materia_id"]},
                files={"file": ("completions.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["entregas_sin_corregir"]) == 2

    async def test_completions_invalid_file(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/calificaciones/import/completions",
                data={"materia_id": seed["materia_id"]},
                files={"file": ("test.txt", b"data", "text/plain")},
            )
            assert response.status_code == 400

    async def test_completions_sin_permiso_403(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user_no_perm = await create_user(db_session, tenant_id=seed["tenant_id"], email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,TP1,Estado\nJuan,completado,completado\n"
            response = await client.post(
                "/api/calificaciones/import/completions",
                data={"materia_id": seed["materia_id"]},
                files={"file": ("completions.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 403


class TestAuditCalificaciones:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        carrera = await _create_carrera(db_session, tenant.id)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT505", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_audit_on_import_confirm(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1\nJuan,75\nMaria,45\n"
            response = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "true",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 201

            from app.models.audit_log import AuditLog
            from sqlalchemy import select
            result = await db_session.execute(
                select(AuditLog).where(AuditLog.accion == "CALIFICACIONES_IMPORTAR")
            )
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].materia_id == seed["materia_id"]
            assert logs[0].detalle["total"] == 2

    async def test_audit_on_preview_confirm(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "Alumno,Parcial 1\nJuan,75\nMaria,45\n"
            preview_resp = await client.post(
                "/api/calificaciones/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("grades.csv", csv_content, "text/csv")},
            )
            assert preview_resp.status_code == 200
            preview_id = preview_resp.json()["preview_id"]

            confirm_resp = await client.post(
                f"/api/calificaciones/preview/{preview_id}/confirm",
                json={"actividades_seleccionadas": ["Parcial 1"]},
            )
            assert confirm_resp.status_code == 201

            from app.models.audit_log import AuditLog
            from sqlalchemy import select
            result = await db_session.execute(
                select(AuditLog).where(AuditLog.accion == "CALIFICACIONES_IMPORTAR")
            )
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].detalle["tipo"] == "preview_confirm"
