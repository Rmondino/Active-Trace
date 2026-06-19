"""Tests for auditoria metrics router — /api/auditoria/* endpoints."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.models.tenant import Tenant
from app.models.user import User
from app.services.audit_log_service import AuditLogService
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


def _make_user(tenant_id: str) -> User:
    return User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email="enc",
        email_hash="h",
        password_hash="h",
        nombre="U",
        apellidos="U",
        dni="e",
        estado="Activo",
    )


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

    from app.routers.auditoria import router as auditoria_router
    app.include_router(auditoria_router)
    return app


class TestPermisos:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def test_403_sin_permiso(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(
            db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/acciones-por-dia")
        assert resp.status_code == 403

    async def test_403_sin_permiso_ultimas(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        user_no_perm = await create_user(
            db_session, tenant.id, email=f"noperm2-{uuid.uuid4().hex[:8]}@test.com",
        )
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/ultimas-acciones")
        assert resp.status_code == 403


class TestEndpoints:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def _seed_base(self, db):
        tenant = await _create_tenant(db)
        user = await create_user(
            db, tenant.id, email=f"admin-{uuid.uuid4().hex[:8]}@test.com", roles=["admin"],
        )
        await _seed_role_permiso(db, "admin", "auditoria:ver")
        actor = _make_user(tenant.id)
        db.add(actor)
        await db.flush()
        audit = AuditLogService(db)
        for i in range(3):
            await audit.log(
                actor_id=actor.id, tenant_id=tenant.id,
                accion=f"ACCION_{i}", materia_id=str(uuid.uuid4()),
            )
        return {"tenant": tenant, "user": user, "actor": actor}

    async def test_acciones_por_dia_ok(self, db_session, test_settings):
        seed = await self._seed_base(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/acciones-por-dia")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "dia" in data[0]
        assert "total" in data[0]
        assert data[0]["total"] >= 3

    async def test_acciones_por_dia_filtro_actor(self, db_session, test_settings):
        seed = await self._seed_base(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/auditoria/acciones-por-dia",
                params={"actor_id": seed["actor"].id},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    async def test_ultimas_acciones_default_limit(self, db_session, test_settings):
        seed = await self._seed_base(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/ultimas-acciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    async def test_ultimas_acciones_custom_limit(self, db_session, test_settings):
        seed = await self._seed_base(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/auditoria/ultimas-acciones", params={"limit": 2},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_log_completo_ok(self, db_session, test_settings):
        seed = await self._seed_base(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/log")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    async def test_comunicaciones_por_docente_ok(self, db_session, test_settings):
        from app.models.materia import Materia

        tenant = await _create_tenant(db_session)
        user = await create_user(
            db_session, tenant.id, email=f"coord-{uuid.uuid4().hex[:8]}@test.com",
            roles=["admin"],
        )
        await _seed_role_permiso(db_session, "admin", "auditoria:ver")

        actor = _make_user(tenant.id)
        materia = Materia(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            codigo="MAT-TEST", nombre="Test",
        )
        db_session.add_all([actor, materia])
        await db_session.flush()

        from app.models.comunicacion import Comunicacion
        c = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            enviado_por=actor.id, materia_id=materia.id,
            destinatario="d@t.com", asunto="S", cuerpo="B",
            estado="Enviado", lote_id=str(uuid.uuid4()),
        )
        db_session.add(c)
        await db_session.flush()

        app = _build_app(db_session, test_settings, user)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/comunicaciones-por-docente")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    async def test_interacciones_por_docente_materia_ok(self, db_session, test_settings):
        seed = await self._seed_base(db_session)
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/interacciones-por-docente-materia")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_multi_tenant_isolation(self, db_session, test_settings):
        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        user1 = await create_user(
            db_session, t1.id, email=f"u1-{uuid.uuid4().hex[:8]}@test.com",
            roles=["admin"],
        )
        user2 = await create_user(
            db_session, t2.id, email=f"u2-{uuid.uuid4().hex[:8]}@test.com",
            roles=["admin"],
        )
        await _seed_role_permiso(db_session, "admin", "auditoria:ver")

        actor1 = _make_user(t1.id)
        actor2 = _make_user(t2.id)
        db_session.add_all([actor1, actor2])
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=actor1.id, tenant_id=t1.id, accion="T1_LOG")
        await audit.log(actor_id=actor2.id, tenant_id=t2.id, accion="T2_LOG")

        app1 = _build_app(db_session, test_settings, user1)
        transport = ASGITransport(app=app1)
        async with AsyncClient(transport=transport, base_url="http://test") as client1:
            resp1 = await client1.get("/api/auditoria/ultimas-acciones")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1) == 1
        assert data1[0]["accion"] == "T1_LOG"

        app2 = _build_app(db_session, test_settings, user2)
        transport2 = ASGITransport(app=app2)
        async with AsyncClient(transport=transport2, base_url="http://test") as client2:
            resp2 = await client2.get("/api/auditoria/ultimas-acciones")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2) == 1
        assert data2[0]["accion"] == "T2_LOG"


class TestScopePropio:
    @pytest.fixture
    def test_settings(self):
        from app.core.config import Settings
        return Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="b" * 32,
        )

    async def test_coordinador_ve_solo_sus_acciones(self, db_session, test_settings):
        tenant = await _create_tenant(db_session)
        coord = await create_user(
            db_session, tenant.id, email=f"coord-{uuid.uuid4().hex[:8]}@test.com",
            roles=["coordinador"],
        )
        await _seed_role_permiso(db_session, "coordinador", "auditoria:ver", alcance="propio")

        otro = _make_user(tenant.id)
        db_session.add(otro)
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=coord.id, tenant_id=tenant.id, accion="COORD_ACTION")
        await audit.log(actor_id=otro.id, tenant_id=tenant.id, accion="OTRO_ACTION")

        app = _build_app(db_session, test_settings, coord)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auditoria/ultimas-acciones")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["accion"] == "COORD_ACTION"
