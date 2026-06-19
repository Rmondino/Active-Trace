"""Tests for AuditoriaMetricsService — aggregation queries over AuditLog/Comunicacion."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion
from app.models.tenant import Tenant
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.auditoria_metrics_service import AuditoriaMetricsService


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


async def _seed_tenant(db) -> Tenant:
    tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test",
        estado="Activo",
    )
    db.add(tenant)
    await db.flush()
    return tenant


class TestAccionesPorDia:
    async def _seed(self, db, tenant_id: str):
        user = _make_user(tenant_id)
        db.add(user)
        await db.flush()
        audit = AuditLogService(db)
        for i in range(3):
            await audit.log(actor_id=user.id, tenant_id=tenant_id, accion=f"ACT_{i}")
        return user

    async def test_agrupa_por_dia(self, db_session):
        tenant = await _seed_tenant(db_session)
        await self._seed(db_session, tenant.id)
        svc = AuditoriaMetricsService(db_session)
        result = await svc.acciones_por_dia(tenant_id=tenant.id)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "dia" in result[0]
        assert "total" in result[0]
        assert result[0]["total"] >= 3

    async def test_filtro_desde(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        old = AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="OLD",
            created_at=datetime.now(UTC) - timedelta(days=10),
        )
        db_session.add(old)
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=user.id, tenant_id=tenant.id, accion="NEW")

        svc = AuditoriaMetricsService(db_session)
        desde = datetime.now(UTC) - timedelta(days=5)
        result = await svc.acciones_por_dia(tenant_id=tenant.id, desde=desde)
        total = sum(r["total"] for r in result)
        assert total == 1, f"Expected 1 action after date, got {total}"

    async def test_filtro_actor_id(self, db_session):
        tenant = await _seed_tenant(db_session)
        user_a = _make_user(tenant.id)
        user_b = _make_user(tenant.id)
        db_session.add_all([user_a, user_b])
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=user_a.id, tenant_id=tenant.id, accion="A_ONLY")
        await audit.log(actor_id=user_b.id, tenant_id=tenant.id, accion="B_ONLY")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.acciones_por_dia(tenant_id=tenant.id, actor_id=user_a.id)
        total = sum(r["total"] for r in result)
        assert total == 1, f"Expected 1 action for actor_a, got {total}"

    async def test_filtro_hasta(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        future = AuditLog(
            id=str(uuid.uuid4()), actor_id=user.id,
            tenant_id=tenant.id, accion="FUTURE",
            created_at=datetime.now(UTC) + timedelta(days=10),
        )
        db_session.add(future)
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=user.id, tenant_id=tenant.id, accion="NOW")

        hasta = datetime.now(UTC) + timedelta(hours=1)
        svc = AuditoriaMetricsService(db_session)
        result = await svc.acciones_por_dia(tenant_id=tenant.id, hasta=hasta)
        total_future = sum(r["total"] for r in result)
        assert total_future == 1, f"Expected 1 (NOW) filtered by hasta, got {total_future}"


class TestComunicacionesPorDocente:
    async def _seed_materia(self, db, tenant_id: str):
        from app.models.materia import Materia
        m = Materia(
            id=str(uuid.uuid4()), tenant_id=tenant_id,
            codigo="TEST-MAT", nombre="Test Materia",
        )
        db.add(m)
        await db.flush()
        return m.id

    async def test_agrupa_por_docente_y_estado(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()
        materia_id = await self._seed_materia(db_session, tenant.id)

        for estado in ["Pendiente", "Enviado", "Enviado", "Error"]:
            c = Comunicacion(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                enviado_por=user.id,
                materia_id=materia_id,
                destinatario="dest@test.com",
                asunto="Test",
                cuerpo="Test body",
                estado=estado,
                lote_id=str(uuid.uuid4()),
            )
            db_session.add(c)
        await db_session.flush()

        svc = AuditoriaMetricsService(db_session)
        result = await svc.comunicaciones_por_docente(tenant_id=tenant.id)
        assert len(result) > 0
        user_entries = [r for r in result if r["usuario_id"] == user.id]
        estados = {r["estado"]: r["total"] for r in user_entries}
        assert estados.get("Pendiente") == 1
        assert estados.get("Enviado") == 2
        assert estados.get("Error") == 1

    async def test_multi_tenant_aislamiento(self, db_session):
        t1 = await _seed_tenant(db_session)
        t2 = await _seed_tenant(db_session)
        u1 = _make_user(t1.id)
        u2 = _make_user(t2.id)
        db_session.add_all([u1, u2])
        await db_session.flush()
        m1 = await self._seed_materia(db_session, t1.id)
        m2 = await self._seed_materia(db_session, t2.id)

        for t, u, m in [(t1, u1, m1), (t2, u2, m2)]:
            c = Comunicacion(
                id=str(uuid.uuid4()), tenant_id=t.id,
                enviado_por=u.id, materia_id=m,
                destinatario="d@t.com", asunto="S", cuerpo="B",
                estado="Pendiente", lote_id=str(uuid.uuid4()),
            )
            db_session.add(c)
        await db_session.flush()

        svc = AuditoriaMetricsService(db_session)
        r1 = await svc.comunicaciones_por_docente(tenant_id=t1.id)
        r2 = await svc.comunicaciones_por_docente(tenant_id=t2.id)
        assert len(r1) == 1
        assert len(r2) == 1
        assert r1[0]["usuario_id"] != r2[0]["usuario_id"]


class TestInteraccionesPorDocenteMateria:
    async def test_agrupa_por_actor_materia_accion(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        m1 = str(uuid.uuid4())
        m2 = str(uuid.uuid4())
        audit = AuditLogService(db_session)
        for m in [m1, m1, m2]:
            await audit.log(
                actor_id=user.id, tenant_id=tenant.id,
                accion="VER", materia_id=m,
            )

        svc = AuditoriaMetricsService(db_session)
        result = await svc.interacciones_por_docente_materia(tenant_id=tenant.id)
        assert len(result) >= 2
        total = sum(r["total"] for r in result)
        assert total == 3

    async def test_filtro_actor_id(self, db_session):
        tenant = await _seed_tenant(db_session)
        u1 = _make_user(tenant.id)
        u2 = _make_user(tenant.id)
        db_session.add_all([u1, u2])
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=u1.id, tenant_id=tenant.id, accion="EDIT")
        await audit.log(actor_id=u2.id, tenant_id=tenant.id, accion="EDIT")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.interacciones_por_docente_materia(
            tenant_id=tenant.id, actor_id=u1.id,
        )
        assert len(result) == 1
        assert result[0]["actor_id"] == u1.id


class TestUltimasAcciones:
    async def test_retorna_limitadas(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        audit = AuditLogService(db_session)
        for i in range(5):
            await audit.log(actor_id=user.id, tenant_id=tenant.id, accion=f"X_{i}")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.ultimas_acciones(tenant_id=tenant.id, limit=3)
        assert len(result) == 3

    async def test_limite_default(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        audit = AuditLogService(db_session)
        for i in range(10):
            await audit.log(actor_id=user.id, tenant_id=tenant.id, accion=f"Y_{i}")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.ultimas_acciones(tenant_id=tenant.id)
        assert len(result) == 10
        assert "created_at" in result[0]

    async def test_filtro_actor_id(self, db_session):
        tenant = await _seed_tenant(db_session)
        u1 = _make_user(tenant.id)
        u2 = _make_user(tenant.id)
        db_session.add_all([u1, u2])
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=u1.id, tenant_id=tenant.id, accion="U1_ONLY")
        await audit.log(actor_id=u2.id, tenant_id=tenant.id, accion="U2_ONLY")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.ultimas_acciones(tenant_id=tenant.id, actor_id=u1.id)
        assert len(result) == 1
        assert result[0]["actor_id"] == u1.id

    async def test_reverse_chronological(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        audit = AuditLogService(db_session)
        for i in range(3):
            await audit.log(actor_id=user.id, tenant_id=tenant.id, accion=f"Z_{i}")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.ultimas_acciones(tenant_id=tenant.id, limit=10)
        fechas = [r["created_at"] for r in result]
        assert fechas == sorted(fechas, reverse=True), (
            "Expected reverse chronological order"
        )


class TestLogCompleto:
    async def test_sin_filtros_retorna_todos(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        audit = AuditLogService(db_session)
        for i in range(4):
            await audit.log(actor_id=user.id, tenant_id=tenant.id, accion=f"LOG_{i}")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.log_completo(tenant_id=tenant.id, limit=10)
        assert len(result) == 4

    async def test_con_filtro_accion(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = _make_user(tenant.id)
        db_session.add(user)
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=user.id, tenant_id=tenant.id, accion="FILTRO_1")
        await audit.log(actor_id=user.id, tenant_id=tenant.id, accion="FILTRO_2")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.log_completo(
            tenant_id=tenant.id, filtros={"accion": "FILTRO_1"},
        )
        assert len(result) == 1
        assert result[0]["accion"] == "FILTRO_1"

    async def test_multi_tenant(self, db_session):
        t1 = await _seed_tenant(db_session)
        t2 = await _seed_tenant(db_session)
        u1 = _make_user(t1.id)
        u2 = _make_user(t2.id)
        db_session.add_all([u1, u2])
        await db_session.flush()

        audit = AuditLogService(db_session)
        await audit.log(actor_id=u1.id, tenant_id=t1.id, accion="T1_ONLY")
        await audit.log(actor_id=u2.id, tenant_id=t2.id, accion="T2_ONLY")

        svc = AuditoriaMetricsService(db_session)
        result = await svc.log_completo(tenant_id=t1.id)
        assert len(result) == 1
        assert result[0]["accion"] == "T1_ONLY"
