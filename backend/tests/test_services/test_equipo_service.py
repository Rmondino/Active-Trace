"""Tests for EquipoService."""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.asignacion_repository import AsignacionRepository
from app.services.audit_log_service import AuditLogService
from app.services.equipo_service import EquipoService


@pytest.fixture
def today():
    return date.today()


@pytest.fixture
def past_date():
    return date.today() - timedelta(days=365)


@pytest.fixture
def future_date():
    return date.today() + timedelta(days=365)


async def _seed_base(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"eq-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo", config={},
    )
    db_session.add(tenant)
    await db_session.flush()

    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc", email_hash="h", password_hash="h",
        nombre="Carlos", apellidos="López", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()

    materia = Materia(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo="MAT-EQ", nombre="Programación I",
    )
    db_session.add(materia)
    await db_session.flush()

    carrera = Carrera(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo="TUPAD", nombre="Tecnicatura",
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        carrera_id=carrera.id, nombre="2025 AGO", anio=2025,
        vig_desde="2025-08-01",
    )
    db_session.add(cohorte)
    await db_session.flush()

    return {"tenant_id": tenant.id, "user_id": user.id, "materia_id": materia.id,
            "carrera_id": carrera.id, "cohorte_id": cohorte.id}


async def _seed_asignacion(db_session, tenant_id, usuario_id, materia_id, carrera_id,
                           cohorte_id, desde, hasta=None, rol="PROFESOR",
                           comisiones=None):
    a = Asignacion(
        id=str(uuid.uuid4()), tenant_id=tenant_id, usuario_id=usuario_id, rol=rol,
        materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id,
        comisiones=comisiones or [], desde=desde, hasta=hasta,
    )
    db_session.add(a)
    await db_session.flush()
    return a


class TestMisEquipos:
    async def test_returns_user_assignments(self, db_session, today):
        seed = await _seed_base(db_session)
        a1 = await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                      seed["materia_id"], seed["carrera_id"],
                                      seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.mis_equipos(seed["user_id"], seed["tenant_id"])
        assert len(result) == 1
        assert result[0]["id"] == a1.id
        assert result[0]["rol"] == "PROFESOR"
        assert result[0]["materia"]["nombre"] == "Programación I"
        assert result[0]["carrera"]["nombre"] == "Tecnicatura"
        assert result[0]["cohorte"]["nombre"] == "2025 AGO"
        assert result[0]["vigente"] is True

    async def test_filters_by_estado_vigente(self, db_session, today, past_date):
        seed = await _seed_base(db_session)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], past_date, past_date)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.mis_equipos(seed["user_id"], seed["tenant_id"],
                                        filtros={"estado": "vigente"})
        assert len(result) == 1
        assert result[0]["vigente"] is True

    async def test_filters_by_materia_id(self, db_session, today):
        seed = await _seed_base(db_session)
        materia2 = Materia(id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
                           codigo="MAT2", nombre="Programación II")
        db_session.add(materia2)
        await db_session.flush()

        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                materia2.id, seed["carrera_id"],
                                seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.mis_equipos(seed["user_id"], seed["tenant_id"],
                                        filtros={"materia_id": seed["materia_id"]})
        assert len(result) == 1
        assert result[0]["materia"]["id"] == seed["materia_id"]


class TestListarAsignaciones:
    async def test_returns_all_in_tenant(self, db_session, today):
        seed = await _seed_base(db_session)
        user2 = User(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            email="enc2", email_hash="h2", password_hash="h",
            nombre="Ana", apellidos="García", dni="e", estado="Activo",
        )
        db_session.add(user2)
        await db_session.flush()

        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)
        await _seed_asignacion(db_session, seed["tenant_id"], user2.id,
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.listar_asignaciones(seed["tenant_id"])
        assert len(result["asignaciones"]) == 2

    async def test_filters_by_rol(self, db_session, today):
        seed = await _seed_base(db_session)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today, rol="PROFESOR")
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today, rol="TUTOR")

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.listar_asignaciones(seed["tenant_id"],
                                                filtros={"rol": "PROFESOR"})
        assert len(result["asignaciones"]) == 1
        assert result["asignaciones"][0]["rol"] == "PROFESOR"

    async def test_filters_by_usuario_id(self, db_session, today):
        seed = await _seed_base(db_session)
        user2 = User(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            email="enc3", email_hash="h3", password_hash="h",
            nombre="Otro", apellidos="User", dni="e", estado="Activo",
        )
        db_session.add(user2)
        await db_session.flush()

        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)
        await _seed_asignacion(db_session, seed["tenant_id"], user2.id,
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.listar_asignaciones(seed["tenant_id"],
                                                filtros={"usuario_id": user2.id})
        assert len(result["asignaciones"]) == 1
        assert result["asignaciones"][0]["usuario_id"] == user2.id


class TestAsignacionMasiva:
    async def test_creates_multiple_assignments(self, db_session, today):
        seed = await _seed_base(db_session)
        user2 = User(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            email="enc4", email_hash="h4", password_hash="h",
            nombre="Docente2", apellidos="Test", dni="e", estado="Activo",
        )
        db_session.add(user2)
        await db_session.flush()

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.asignacion_masiva({
            "docente_ids": [seed["user_id"], user2.id],
            "rol": "PROFESOR",
            "materia_id": seed["materia_id"],
            "carrera_id": seed["carrera_id"],
            "cohorte_id": seed["cohorte_id"],
            "comisiones": ["A", "B"],
            "desde": today.isoformat(),
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        assert result["total_creadas"] == 2
        assert len(result["asignaciones"]) == 2

        stmt = select(Asignacion).where(Asignacion.tenant_id == seed["tenant_id"])
        rows = (await db_session.execute(stmt)).scalars().all()
        assert len(rows) == 2

    async def test_creates_audit_log(self, db_session, today):
        seed = await _seed_base(db_session)
        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        await svc.asignacion_masiva({
            "docente_ids": [seed["user_id"]],
            "rol": "PROFESOR",
            "materia_id": seed["materia_id"],
            "carrera_id": seed["carrera_id"],
            "cohorte_id": seed["cohorte_id"],
            "desde": today.isoformat(),
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        stmt = select(AuditLog).where(AuditLog.accion == "ASIGNACION_MODIFICAR")
        log = (await db_session.execute(stmt)).scalar_one_or_none()
        assert log is not None
        assert log.actor_id == seed["user_id"]


class TestClonarEquipo:
    async def test_clones_vigentes_only(self, db_session, today, past_date):
        seed = await _seed_base(db_session)
        cohorte2 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            carrera_id=seed["carrera_id"], nombre="2026 MAR", anio=2026,
            vig_desde="2026-03-01",
        )
        db_session.add(cohorte2)
        await db_session.flush()

        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today, rol="PROFESOR",
                                comisiones=["A"])
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], past_date, past_date,
                                rol="TUTOR")

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.clonar_equipo({
            "origen_materia_id": seed["materia_id"],
            "origen_carrera_id": seed["carrera_id"],
            "origen_cohorte_id": seed["cohorte_id"],
            "destino_materia_id": seed["materia_id"],
            "destino_carrera_id": seed["carrera_id"],
            "destino_cohorte_id": cohorte2.id,
            "nuevo_desde": "2026-03-01",
            "nuevo_hasta": "2026-12-31",
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        assert result["total_clonadas"] == 1

    async def test_preserves_rol_and_comisiones(self, db_session, today):
        seed = await _seed_base(db_session)
        cohorte2 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            carrera_id=seed["carrera_id"], nombre="2026 MAR", anio=2026,
            vig_desde="2026-03-01",
        )
        db_session.add(cohorte2)
        await db_session.flush()

        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today, rol="TUTOR",
                                comisiones=["C"])

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.clonar_equipo({
            "origen_materia_id": seed["materia_id"],
            "origen_carrera_id": seed["carrera_id"],
            "origen_cohorte_id": seed["cohorte_id"],
            "destino_materia_id": seed["materia_id"],
            "destino_carrera_id": seed["carrera_id"],
            "destino_cohorte_id": cohorte2.id,
            "nuevo_desde": "2026-03-01",
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        assert result["total_clonadas"] == 1
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == seed["tenant_id"],
            Asignacion.cohorte_id == cohorte2.id,
        )
        cloned = (await db_session.execute(stmt)).scalar_one()
        assert cloned.rol == "TUTOR"
        assert cloned.comisiones == ["C"]

    async def test_creates_audit_log(self, db_session, today):
        seed = await _seed_base(db_session)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        await svc.clonar_equipo({
            "origen_materia_id": seed["materia_id"],
            "origen_carrera_id": seed["carrera_id"],
            "origen_cohorte_id": seed["cohorte_id"],
            "destino_materia_id": seed["materia_id"],
            "destino_carrera_id": seed["carrera_id"],
            "destino_cohorte_id": seed["cohorte_id"],
            "nuevo_desde": "2026-03-01",
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        stmt = select(AuditLog).where(AuditLog.accion == "ASIGNACION_MODIFICAR")
        logs = (await db_session.execute(stmt)).scalars().all()
        assert len(logs) >= 1


class TestActualizarVigencia:
    async def test_updates_dates_for_matching_assignments(self, db_session, today, future_date):
        seed = await _seed_base(db_session)
        a1 = await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                     seed["materia_id"], seed["carrera_id"],
                                     seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.actualizar_vigencia({
            "materia_id": seed["materia_id"],
            "carrera_id": seed["carrera_id"],
            "cohorte_id": seed["cohorte_id"],
            "nuevo_desde": future_date.isoformat(),
            "nuevo_hasta": future_date.isoformat(),
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        assert result["total_actualizadas"] == 1
        stmt = select(Asignacion).where(Asignacion.id == a1.id)
        updated = (await db_session.execute(stmt)).scalar_one()
        assert updated.desde == future_date
        assert updated.hasta == future_date

    async def test_only_updates_matching_assignments(self, db_session, today):
        seed = await _seed_base(db_session)
        cohorte2 = Cohorte(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            carrera_id=seed["carrera_id"], nombre="2026 MAR", anio=2026,
            vig_desde="2026-03-01",
        )
        db_session.add(cohorte2)
        await db_session.flush()

        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                cohorte2.id, today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.actualizar_vigencia({
            "materia_id": seed["materia_id"],
            "carrera_id": seed["carrera_id"],
            "cohorte_id": seed["cohorte_id"],
            "nuevo_desde": "2026-01-01",
        }, user_id=seed["user_id"], tenant_id=seed["tenant_id"])

        assert result["total_actualizadas"] == 1


class TestExportarEquipo:
    async def test_returns_xlsx_bytes(self, db_session, today):
        seed = await _seed_base(db_session)
        await _seed_asignacion(db_session, seed["tenant_id"], seed["user_id"],
                                seed["materia_id"], seed["carrera_id"],
                                seed["cohorte_id"], today)

        repo = AsignacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        audit = AuditLogService(db_session)
        svc = EquipoService(repo, audit, db_session)

        result = await svc.exportar_equipo(
            seed["materia_id"], seed["carrera_id"], seed["cohorte_id"],
            seed["tenant_id"],
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:2] == b"PK"  # xlsx is a zip file
