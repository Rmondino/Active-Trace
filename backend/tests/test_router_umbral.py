"""Tests for umbral router endpoints."""

import uuid
from datetime import date

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

    from app.routers.umbral import router as umbral_router
    app.include_router(umbral_router)
    return app


class TestUmbralGet:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed(self, db_session, with_asignacion=True):
        tenant = await _create_tenant(db_session)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT600", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=[])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:ver")

        if with_asignacion:
            from app.models.asignacion import Asignacion
            asig = Asignacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                usuario_id=user.id, rol="PROFESOR",
                materia_id=materia.id, desde=date(2020, 1, 1),
            )
            db_session.add(asig)
            await db_session.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id, "user": user}

    async def test_get_umbral_default_when_not_configured(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["umbral_pct"] == 60
            assert "Satisfactorio" in data["valores_aprobatorios"]

    async def test_get_umbral_with_existing(self, db_session, test_settings):
        seed = await self._seed(db_session)
        from app.models.asignacion import Asignacion
        from sqlalchemy import select
        result = await db_session.execute(
            select(Asignacion).where(Asignacion.usuario_id == seed["user"].id)
        )
        asig = result.scalar_one()

        from app.models.umbral_materia import UmbralMateria
        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            asignacion_id=asig.id, materia_id=seed["materia_id"],
            umbral_pct=75, valores_aprobatorios=["Aprobado", "Muy bueno"],
        )
        db_session.add(umbral)
        await db_session.flush()

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["umbral_pct"] == 75
            assert data["valores_aprobatorios"] == ["Aprobado", "Muy bueno"]

    async def test_get_umbral_sin_permiso_403(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user_no_perm = await create_user(db_session, tenant_id=seed["tenant_id"], email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
            )
            assert response.status_code == 403


class TestUmbralUpdate:
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
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT601", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        user = await create_user(db_session, tenant_id=tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=[])
        await _seed_role_permiso(db_session, "profesor", "calificaciones:importar")
        await _seed_role_permiso(db_session, "profesor", "calificaciones:ver")

        from app.models.asignacion import Asignacion
        asig = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            usuario_id=user.id, rol="PROFESOR",
            materia_id=materia.id, desde=date(2020, 1, 1),
        )
        db_session.add(asig)
        await db_session.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id, "user": user}

    async def test_update_umbral_pct(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
                json={"umbral_pct": 75},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["umbral_pct"] == 75

    async def test_update_valores_aprobatorios(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
                json={"valores_aprobatorios": ["Excelente", "Sobresaliente"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["valores_aprobatorios"] == ["Excelente", "Sobresaliente"]

    async def test_update_persists(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.put(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
                json={"umbral_pct": 80},
            )

            get_resp = await client.get(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
            )
            assert get_resp.status_code == 200
            assert get_resp.json()["umbral_pct"] == 80

    async def test_update_sin_permiso_403(self, db_session, test_settings):
        seed = await self._seed(db_session)
        user_no_perm = await create_user(db_session, tenant_id=seed["tenant_id"], email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/umbral",
                params={"materia_id": seed["materia_id"]},
                json={"umbral_pct": 75},
            )
            assert response.status_code == 403

    async def test_update_sin_asignacion_403(self, db_session, test_settings):
        seed = await self._seed(db_session)

        other_materia_id = str(uuid.uuid4())

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/umbral",
                params={"materia_id": other_materia_id},
                json={"umbral_pct": 75},
            )
            assert response.status_code == 403


class TestUmbralDefault:
    async def test_get_default(self, db_session, test_settings):
        from fastapi import FastAPI
        from app.core.config import get_settings
        from app.core.current_user import get_current_user
        from app.core.database import get_db_session

        app = FastAPI()
        app.dependency_overrides[get_settings] = lambda: test_settings

        async def _db_override():
            yield db_session
        app.dependency_overrides[get_db_session] = _db_override

        from app.routers.umbral import router as umbral_router
        app.include_router(umbral_router)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/umbral/default")
            assert response.status_code == 200
            data = response.json()
            assert data["umbral_pct"] == 60
            assert data["valores_aprobatorios"] == ["Satisfactorio", "Supera lo esperado"]
