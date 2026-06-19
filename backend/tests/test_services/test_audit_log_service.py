"""Tests for AuditLogService."""

import uuid

from app.models.tenant import Tenant
from app.models.user import User
from app.services.audit_log_service import AuditLogService


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


class TestAuditLogService:
    async def _seed_tenant(self, db_session) -> Tenant:
        tenant = Tenant(
            id=str(uuid.uuid4()),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            estado="Activo",
        )
        db_session.add(tenant)
        await db_session.flush()
        return tenant

    async def test_log_basic_fields(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        svc = AuditLogService(db_session)
        entry = await svc.log(
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_LOG",
            materia_id=str(uuid.uuid4()),
            detalle={"msg": "test"},
            ip="10.0.0.1",
        )
        assert entry.id is not None
        assert entry.accion == "TEST_LOG"
        assert entry.materia_id is not None
        assert entry.detalle == {"msg": "test"}
        assert entry.ip == "10.0.0.1"
        assert entry.filas_afectadas is None
        assert entry.user_agent is None
        assert entry.impersonado_id is None

    async def test_log_with_filas_afectadas(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        svc = AuditLogService(db_session)
        entry = await svc.log(
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_FILAS",
            filas_afectadas=99,
        )
        assert entry.filas_afectadas == 99

    async def test_log_with_impersonado_id(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        impersonado = _make_user(tenant.id)
        db_session.add_all([user, impersonado])
        await db_session.flush()
        svc = AuditLogService(db_session)
        entry = await svc.log(
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_IMPERSONALOG",
            impersonado_id=impersonado.id,
        )
        assert entry.impersonado_id == impersonado.id

    async def test_log_with_user_agent(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        svc = AuditLogService(db_session)
        entry = await svc.log(
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_UA",
            user_agent="curl/7.68.0",
        )
        assert entry.user_agent == "curl/7.68.0"

    async def test_log_with_all_fields(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        impersonado = _make_user(tenant.id)
        db_session.add_all([user, impersonado])
        await db_session.flush()
        svc = AuditLogService(db_session)
        entry = await svc.log(
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_ALL",
            materia_id=str(uuid.uuid4()),
            detalle={"data": "value"},
            filas_afectadas=10,
            ip="1.2.3.4",
            user_agent="Mozilla/5.0",
            impersonado_id=impersonado.id,
        )
        assert entry.accion == "TEST_ALL"
        assert entry.filas_afectadas == 10
        assert entry.user_agent == "Mozilla/5.0"
        assert entry.impersonado_id == impersonado.id
        assert entry.ip == "1.2.3.4"

    async def test_get_all_no_filters(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        svc = AuditLogService(db_session)
        for i in range(5):
            await svc.log(actor_id=user.id, tenant_id=tenant.id, accion=f"ACT_{i}")
        results = await svc.get_all(tenant.id)
        assert len(results) == 5

    async def test_get_all_with_accion_filter(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        svc = AuditLogService(db_session)
        await svc.log(actor_id=user.id, tenant_id=tenant.id, accion="FILTER_ME")
        await svc.log(actor_id=user.id, tenant_id=tenant.id, accion="OTHER")
        await svc.log(actor_id=user.id, tenant_id=tenant.id, accion="FILTER_ME")
        results = await svc.get_all(tenant.id, filtros={"accion": "FILTER_ME"})
        assert len(results) == 2

    async def test_get_all_multi_tenant(self, db_session):
        t1 = Tenant(id=str(uuid.uuid4()), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1", estado="Activo")
        t2 = Tenant(id=str(uuid.uuid4()), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2", estado="Activo")
        db_session.add_all([t1, t2])
        await db_session.flush()
        u1 = _make_user(t1.id)
        u2 = _make_user(t2.id)
        db_session.add_all([u1, u2])
        await db_session.flush()
        svc = AuditLogService(db_session)
        await svc.log(actor_id=u1.id, tenant_id=t1.id, accion="T1_ONLY")
        await svc.log(actor_id=u2.id, tenant_id=t2.id, accion="T2_ONLY")

        r1 = await svc.get_all(t1.id)
        assert len(r1) == 1
        assert r1[0].accion == "T1_ONLY"

        r2 = await svc.get_all(t2.id)
        assert len(r2) == 1
        assert r2[0].accion == "T2_ONLY"

    async def test_get_all_with_limit(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        svc = AuditLogService(db_session)
        for _ in range(10):
            await svc.log(actor_id=user.id, tenant_id=tenant.id, accion="LIMIT_TEST")
        results = await svc.get_all(tenant.id, limit=3)
        assert len(results) == 3
