"""Tests for AuditLogRepository — append-only semantics."""

import uuid
from datetime import UTC, datetime, timedelta

from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository


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


class TestAuditLogRepository:
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

    async def test_create(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_CREATE",
        )
        result = await repo.create(log)
        assert result.id == log.id
        assert result.accion == "TEST_CREATE"

    async def test_get_found(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_GET",
        )
        db_session.add(log)
        await db_session.flush()
        result = await repo.get(log.id)
        assert result is not None
        assert result.id == log.id

    async def test_get_not_found(self, db_session):
        repo = AuditLogRepository(db_session)
        result = await repo.get(str(uuid.uuid4()))
        assert result is None

    async def test_get_all_scoped_by_tenant(self, db_session):
        t1 = Tenant(id=str(uuid.uuid4()), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1", estado="Activo")
        t2 = Tenant(id=str(uuid.uuid4()), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2", estado="Activo")
        db_session.add_all([t1, t2])
        await db_session.flush()
        u1 = _make_user(t1.id)
        u2 = _make_user(t2.id)
        db_session.add_all([u1, u2])
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        for t, u in [(t1, u1), (t2, u2)]:
            for _ in range(3):
                db_session.add(AuditLog(
                    id=str(uuid.uuid4()), actor_id=u.id,
                    tenant_id=t.id, accion="TEST_MT",
                ))
        await db_session.flush()
        results_t1 = await repo.get_all(t1.id)
        assert len(results_t1) == 3
        results_t2 = await repo.get_all(t2.id)
        assert len(results_t2) == 3

    async def test_get_all_with_accion_filter(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="ACCION_A",
        ))
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="ACCION_B",
        ))
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="ACCION_A",
        ))
        await db_session.flush()
        results = await repo.get_all(tenant.id, filtros={"accion": "ACCION_A"})
        assert len(results) == 2

    async def test_get_all_with_materia_id_filter(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        m1 = str(uuid.uuid4())
        m2 = str(uuid.uuid4())
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="TEST", materia_id=m1,
        ))
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="TEST", materia_id=m2,
        ))
        await db_session.flush()
        results = await repo.get_all(tenant.id, filtros={"materia_id": m1})
        assert len(results) == 1

    async def test_get_all_with_limit(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        for _ in range(10):
            db_session.add(AuditLog(
                id=str(uuid.uuid4()), actor_id=user.id,
                tenant_id=tenant.id, accion="TEST_LIMIT",
            ))
        await db_session.flush()
        results = await repo.get_all(tenant.id, limit=3)
        assert len(results) == 3

    async def test_get_all_ordered_by_created_at_desc(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        old = AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="TEST_ORDER",
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        new = AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="TEST_ORDER",
            created_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add_all([old, new])
        await db_session.flush()
        results = await repo.get_all(tenant.id)
        assert results[0].id == new.id
        assert results[1].id == old.id

    async def test_get_all_with_actor_id_filter(self, db_session):
        tenant = await self._seed_tenant(db_session)
        user_a = _make_user(tenant.id)
        user_b = _make_user(tenant.id)
        db_session.add_all([user_a, user_b])
        await db_session.flush()
        repo = AuditLogRepository(db_session)
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user_a.id,
            tenant_id=tenant.id, accion="TEST",
        ))
        db_session.add(AuditLog(
            id=str(uuid.uuid4()), actor_id=user_b.id,
            tenant_id=tenant.id, accion="TEST",
        ))
        await db_session.flush()
        results = await repo.get_all(tenant.id, filtros={"actor_id": user_a.id})
        assert len(results) == 1

    async def test_no_update_method(self, db_session):
        repo = AuditLogRepository(db_session)
        assert not hasattr(repo, "update")

    async def test_no_delete_method(self, db_session):
        repo = AuditLogRepository(db_session)
        assert not hasattr(repo, "delete")

    async def test_no_soft_delete_method(self, db_session):
        repo = AuditLogRepository(db_session)
        assert not hasattr(repo, "soft_delete")
