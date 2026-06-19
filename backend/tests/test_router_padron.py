"""Tests for padron router endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.models.carrera import Carrera
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


async def _create_carrera(db_session, tenant_id) -> Carrera:
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

    from app.routers.padron import router as padron_router
    app.include_router(padron_router)
    return app


class TestPadronImport:
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
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT200", nombre="Test")
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
            csv_content = "nombre,apellidos,email,comision\nJuan,Perez,juan@test.com,A\nMaria,Gomez,maria@test.com,B\n"
            response = await client.post(
                "/api/padron/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("test.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 200
            data = response.json()
            assert "preview_id" in data
            assert data["total_filas"] == 2
            assert len(data["muestra"]) == 2

    async def test_import_csv_confirm(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            csv_content = "nombre,apellidos,email\nJuan,Perez,juan@test.com\n"
            response = await client.post(
                "/api/padron/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "true",
                },
                files={"file": ("test.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 201
            data = response.json()
            assert "version_id" in data
            assert data["filas_importadas"] == 1

    async def test_import_invalid_file_type(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/padron/import",
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
            csv_content = "nombre,apellidos,email\nJuan,juan@test.com\n"
            response = await client.post(
                "/api/padron/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("test.csv", csv_content, "text/csv")},
            )
            assert response.status_code == 403


class TestPadronPreviewConfirm:
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
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT201", nombre="Test")
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
            csv_content = "nombre,apellidos,email\nJuan,Perez,juan@test.com\nMaria,Gomez,maria@test.com\n"
            preview_resp = await client.post(
                "/api/padron/import",
                data={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "confirm": "false",
                },
                files={"file": ("test.csv", csv_content, "text/csv")},
            )
            assert preview_resp.status_code == 200
            preview_id = preview_resp.json()["preview_id"]

            confirm_resp = await client.post(
                f"/api/padron/preview/{preview_id}/confirm",
                params={"materia_id": seed["materia_id"], "cohorte_id": seed["cohorte_id"]},
            )
            assert confirm_resp.status_code == 201
            data = confirm_resp.json()
            assert data["filas_importadas"] == 2
            assert "version_id" in data

    async def test_confirm_nonexistent_preview(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/padron/preview/{uuid.uuid4()}/confirm",
                params={"materia_id": seed["materia_id"], "cohorte_id": seed["cohorte_id"]},
            )
            assert response.status_code == 404


class TestPadronVersiones:
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
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT202", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")

        from app.models.version_padron import VersionPadron
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=3,
        )
        db_session.add(vp)
        await db_session.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_list_versiones(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/padron/versiones",
                params={"materia_id": seed["materia_id"], "cohorte_id": seed["cohorte_id"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["origen"] == "manual"
            assert data[0]["total_filas"] == 3


class TestPadronVaciar:
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
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT203", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")

        from app.models.version_padron import VersionPadron
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=3,
        )
        db_session.add(vp)
        await db_session.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_vaciar_materia(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/padron/materia/{seed['materia_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["versiones_afectadas"] == 1


class TestPadronMoodleSync:
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
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT204", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.cohorte import Cohorte
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": cohorte.id, "user": user}

    async def test_moodle_sync_no_config(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/padron/moodle/sync",
                params={
                    "materia_id": seed["materia_id"],
                    "cohorte_id": seed["cohorte_id"],
                    "course_id": 1,
                },
            )
            assert response.status_code == 502
