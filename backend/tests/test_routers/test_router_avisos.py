"""Tests for avisos router endpoints."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.models.asignacion import Asignacion
from app.models.aviso import Aviso
from app.models.acknowledgment_aviso import AcknowledgmentAviso
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
        nombre="Test", estado="Activo",
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

    from app.routers.avisos import router as avisos_router
    app.include_router(avisos_router)
    return app


def _make_test_settings():
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


class TestAvisosRouter:
    @pytest.fixture
    def test_settings(self):
        return _make_test_settings()

    async def _seed(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-AVISOS", nombre="Test Avisos")
        db_session.add(materia)
        await db_session.flush()
        user = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"avisos-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "avisos:publicar")
        return {"tenant_id": tenant.id, "materia_id": materia.id, "user": user}

    async def _seed_aviso(self, db_session, tenant_id, **overrides):
        ahora = datetime.now(UTC)
        defaults = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "alcance": "Global",
            "titulo": "Test Aviso",
            "cuerpo": "Cuerpo del aviso",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
            "orden": 0,
        }
        defaults.update(overrides)
        aviso = Aviso(**defaults)
        db_session.add(aviso)
        await db_session.flush()
        return aviso

    # ── Management endpoints (require avisos:publicar) ──

    async def test_403_without_permission(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(
            db_session, tenant_id=tenant.id,
            email=f"noperm-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/avisos",
                json={"alcance": "Global", "titulo": "T", "cuerpo": "C", "inicio_en": "2026-01-01T00:00:00Z", "fin_en": "2026-12-31T00:00:00Z"},
            )
            assert response.status_code == 403

    async def test_create_aviso(self, db_session, test_settings):
        seed = await self._seed(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        ahora = datetime.now(UTC)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/avisos",
                json={
                    "alcance": "Global",
                    "titulo": "Nuevo Aviso",
                    "cuerpo": "Contenido",
                    "inicio_en": ahora.isoformat(),
                    "fin_en": (ahora + timedelta(hours=2)).isoformat(),
                    "orden": 5,
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["titulo"] == "Nuevo Aviso"
            assert data["orden"] == 5

    async def test_get_aviso_detail(self, db_session, test_settings):
        seed = await self._seed(db_session)
        aviso = await self._seed_aviso(db_session, seed["tenant_id"])
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/avisos/{aviso.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == aviso.id
            assert data["titulo"] == aviso.titulo

    async def test_update_aviso(self, db_session, test_settings):
        seed = await self._seed(db_session)
        aviso = await self._seed_aviso(db_session, seed["tenant_id"])
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/avisos/{aviso.id}",
                json={"titulo": "Updated Title"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["titulo"] == "Updated Title"

    async def test_delete_aviso(self, db_session, test_settings):
        seed = await self._seed(db_session)
        aviso = await self._seed_aviso(db_session, seed["tenant_id"])
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/avisos/{aviso.id}")
            assert response.status_code == 204

            # Verify soft-deleted
            response2 = await client.get(f"/api/avisos/{aviso.id}")
            assert response2.status_code == 404

    # ── List / Visible for user ──

    async def test_list_avisos_returns_visible(self, db_session, test_settings):
        seed = await self._seed(db_session)
        await self._seed_aviso(db_session, seed["tenant_id"], titulo="Visible Aviso")
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/avisos")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert any(a["titulo"] == "Visible Aviso" for a in data)

    # ── Ack ──

    async def test_ack_aviso(self, db_session, test_settings):
        seed = await self._seed(db_session)
        aviso = await self._seed_aviso(db_session, seed["tenant_id"], requiere_ack=True)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/avisos/{aviso.id}/ack")
            assert response.status_code == 201
            data = response.json()
            assert data["aviso_id"] == aviso.id
            assert data["usuario_id"] == seed["user"].id

    async def test_ack_duplicate_returns_409(self, db_session, test_settings):
        seed = await self._seed(db_session)
        aviso = await self._seed_aviso(db_session, seed["tenant_id"], requiere_ack=True)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(f"/api/avisos/{aviso.id}/ack")
            response2 = await client.post(f"/api/avisos/{aviso.id}/ack")
            assert response2.status_code == 409

    # ── Stats ──

    async def test_aviso_stats(self, db_session, test_settings):
        seed = await self._seed(db_session)
        aviso = await self._seed_aviso(db_session, seed["tenant_id"], requiere_ack=True)

        # Create a second user in same tenant and ack
        user2 = await create_user(
            db_session, tenant_id=seed["tenant_id"],
            email=f"user2-{uuid.uuid4().hex[:8]}@test.com",
        )
        ack = AcknowledgmentAviso(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            aviso_id=aviso.id, usuario_id=user2.id,
        )
        db_session.add(ack)
        await db_session.flush()

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/avisos/{aviso.id}/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["total_acks"] == 1

    # ── Multi-tenant isolation ──

    async def test_multi_tenant_isolation(self, db_session, test_settings):
        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        ahora = datetime.now(UTC)
        a1 = Aviso(id=str(uuid.uuid4()), tenant_id=t1.id, alcance="Global", titulo="T1 Aviso", cuerpo="C", inicio_en=ahora - timedelta(hours=1), fin_en=ahora + timedelta(hours=1))
        a2 = Aviso(id=str(uuid.uuid4()), tenant_id=t2.id, alcance="Global", titulo="T2 Aviso", cuerpo="C", inicio_en=ahora - timedelta(hours=1), fin_en=ahora + timedelta(hours=1))
        db_session.add_all([a1, a2])
        await db_session.flush()

        user1 = await create_user(
            db_session, tenant_id=t1.id,
            email=f"u1-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user1)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/avisos")
            assert response.status_code == 200
            data = response.json()
            assert all(a["tenant_id"] == t1.id for a in data)
            assert any(a["titulo"] == "T1 Aviso" for a in data)
            assert not any(a["titulo"] == "T2 Aviso" for a in data)
