"""Tests for admin auditoria router."""

import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.models.tenant import Tenant
from app.models.user import User
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

    from app.routers.admin.auditoria import router as auditoria_router
    app.include_router(auditoria_router)
    return app


class TestAuditoriaPermisos:
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
        user_no_perm = await create_user(db_session, tenant.id, email=f"noperm-{uuid.uuid4().hex[:8]}@test.com")
        app = _build_app(db_session, test_settings, user_no_perm)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria")
        assert resp.status_code == 403


class TestAuditoriaEndpoints:
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
            db, tenant.id, email=f"admin-{uuid.uuid4().hex[:8]}@test.com", roles=["admin"],
        )
        await _seed_role_permiso(db, "admin", "auditoria:ver")
        return {"tenant_id": tenant.id, "user": user, "tenant": tenant}

    async def test_listar_auditoria_returns_logs(self, db_session, test_settings):
        seed = await self._seed(db_session)
        actor = _make_user(seed["tenant_id"])
        db_session.add(actor)
        await db_session.flush()
        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="TEST_LIST")
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="TEST_LIST_2")

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_filter_by_accion(self, db_session, test_settings):
        seed = await self._seed(db_session)
        actor = _make_user(seed["tenant_id"])
        db_session.add(actor)
        await db_session.flush()
        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="FILTERED")
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="OTHER")
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="FILTERED")

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria", params={"accion": "FILTERED"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(d["accion"] == "FILTERED" for d in data)

    async def test_filter_by_materia_id(self, db_session, test_settings):
        seed = await self._seed(db_session)
        actor = _make_user(seed["tenant_id"])
        db_session.add(actor)
        await db_session.flush()
        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        m1 = str(uuid.uuid4())
        m2 = str(uuid.uuid4())
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="TEST", materia_id=m1)
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="TEST", materia_id=m2)

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria", params={"materia_id": m1})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    async def test_filter_by_actor_id(self, db_session, test_settings):
        seed = await self._seed(db_session)
        actor_a = _make_user(seed["tenant_id"])
        actor_b = _make_user(seed["tenant_id"])
        db_session.add_all([actor_a, actor_b])
        await db_session.flush()
        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        await svc.log(actor_id=actor_a.id, tenant_id=seed["tenant_id"], accion="TEST")
        await svc.log(actor_id=actor_b.id, tenant_id=seed["tenant_id"], accion="TEST")

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria", params={"actor_id": actor_a.id})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    async def test_filter_by_fecha_desde(self, db_session, test_settings):
        seed = await self._seed(db_session)
        actor = _make_user(seed["tenant_id"])
        db_session.add(actor)
        await db_session.flush()
        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        from datetime import UTC, datetime, timedelta
        old = __import__("app.models.audit_log", fromlist=["AuditLog"]).AuditLog(
            id=str(uuid.uuid4()), actor_id=actor.id,
            tenant_id=seed["tenant_id"], accion="OLD",
            created_at=datetime.now(UTC) - timedelta(days=2),
        )
        db_session.add(old)
        await db_session.flush()
        await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="NEW")

        desde = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria", params={"desde": desde})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["accion"] == "NEW"

    async def test_multi_tenant_isolation(self, db_session, test_settings):
        t1 = await _create_tenant(db_session)
        t2 = await _create_tenant(db_session)
        user1 = await create_user(db_session, t1.id, email=f"u1-{uuid.uuid4().hex[:8]}@test.com", roles=["admin"])
        user2 = await create_user(db_session, t2.id, email=f"u2-{uuid.uuid4().hex[:8]}@test.com", roles=["admin"])
        await _seed_role_permiso(db_session, "admin", "auditoria:ver")

        actor1 = _make_user(t1.id)
        actor2 = _make_user(t2.id)
        db_session.add_all([actor1, actor2])
        await db_session.flush()

        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        await svc.log(actor_id=actor1.id, tenant_id=t1.id, accion="T1_LOG")
        await svc.log(actor_id=actor2.id, tenant_id=t2.id, accion="T2_LOG")

        app1 = _build_app(db_session, test_settings, user1)
        transport = ASGITransport(app=app1)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.get("/api/admin/auditoria")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1) == 1
        assert data1[0]["accion"] == "T1_LOG"

        app2 = _build_app(db_session, test_settings, user2)
        transport2 = ASGITransport(app=app2)
        async with AsyncClient(transport=transport2, base_url="http://test") as client:
            resp2 = await client.get("/api/admin/auditoria")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2) == 1
        assert data2[0]["accion"] == "T2_LOG"

    async def test_limit_param(self, db_session, test_settings):
        seed = await self._seed(db_session)
        actor = _make_user(seed["tenant_id"])
        db_session.add(actor)
        await db_session.flush()
        svc = __import__("app.services.audit_log_service", fromlist=["AuditLogService"]).AuditLogService(db_session)
        for _ in range(10):
            await svc.log(actor_id=actor.id, tenant_id=seed["tenant_id"], accion="LIMIT_TEST")

        app = _build_app(db_session, test_settings, seed["user"])
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/admin/auditoria", params={"limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
