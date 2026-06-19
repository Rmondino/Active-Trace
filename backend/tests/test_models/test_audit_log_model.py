"""Tests for AuditLog model — append-only semantics."""

import uuid
from datetime import UTC, datetime

from app.models.audit_log import AuditLog
from app.models.tenant import Tenant
from app.models.user import User


class TestAuditLogModel:
    async def _seed_tenant_user(self, db_session) -> tuple[Tenant, User]:
        tenant = Tenant(
            id=str(uuid.uuid4()),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            estado="Activo",
        )
        db_session.add(tenant)
        await db_session.flush()
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="enc",
            email_hash="h",
            password_hash="h",
            nombre="T",
            apellidos="U",
            dni="e",
            estado="Activo",
        )
        db_session.add(user)
        await db_session.flush()
        return tenant, user

    async def test_create_with_all_fields(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_ACCION",
            materia_id=str(uuid.uuid4()),
            detalle={"key": "value"},
            filas_afectadas=42,
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            impersonado_id=user.id,
        )
        db_session.add(log)
        await db_session.flush()

        assert log.id is not None
        assert log.accion == "TEST_ACCION"
        assert log.filas_afectadas == 42
        assert log.user_agent == "Mozilla/5.0"
        assert log.impersonado_id == user.id
        assert log.detalle == {"key": "value"}
        assert log.ip == "192.168.1.1"
        assert log.created_at is not None

    async def test_create_minimal_fields(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_MINIMAL",
        )
        db_session.add(log)
        await db_session.flush()

        assert log.accion == "TEST_MINIMAL"
        assert log.filas_afectadas is None
        assert log.user_agent is None
        assert log.impersonado_id is None
        assert log.materia_id is None
        assert log.detalle is None
        assert log.ip is None

    async def test_impersonado_id_nullable(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_IMPERSONADO",
            impersonado_id=None,
        )
        db_session.add(log)
        await db_session.flush()
        assert log.impersonado_id is None

    async def test_filas_afectadas_nullable(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_FILAS",
            filas_afectadas=None,
        )
        db_session.add(log)
        await db_session.flush()
        assert log.filas_afectadas is None

    async def test_user_agent_nullable(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_UA",
            user_agent=None,
        )
        db_session.add(log)
        await db_session.flush()
        assert log.user_agent is None

    async def test_created_at_defaults_to_now(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        before = datetime.now(UTC)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_TIME",
        )
        db_session.add(log)
        await db_session.flush()
        after = datetime.now(UTC)
        assert before <= log.created_at.replace(tzinfo=UTC) <= after

    async def test_model_has_no_deleted_at(self):
        assert not hasattr(AuditLog, "deleted_at")

    async def test_repr(self, db_session):
        tenant, user = await self._seed_tenant_user(db_session)
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user.id,
            tenant_id=tenant.id,
            accion="TEST_REPR",
        )
        assert "AuditLog" in repr(log)
        assert "TEST_REPR" in repr(log)
