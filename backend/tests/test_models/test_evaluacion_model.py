"""Tests for Evaluacion, ReservaEvaluacion, ResultadoEvaluacion models."""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion
from app.models.tenant import Tenant


async def _create_carrera(db_session, tenant_id):
    carrera = Carrera(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        codigo=f"CAR-{uuid.uuid4().hex[:4]}", nombre="Test Carrera",
    )
    db_session.add(carrera)
    await db_session.flush()
    return carrera


async def _seed_base(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-EVAL", nombre="Evaluacion Test")
    db_session.add(materia)
    await db_session.flush()
    carrera = await _create_carrera(db_session, tenant.id)
    cohorte = Cohorte(
        id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
        nombre="MAR-2026", anio=2026, vig_desde="2026-01-01", estado="Activa",
    )
    db_session.add(cohorte)
    await db_session.flush()
    return tenant, materia, cohorte


class TestEvaluacionModel:
    async def test_create_evaluacion(self, db_session):
        tenant, materia, cohorte = await _seed_base(db_session)
        ev = Evaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            instancia="Primer llamado",
        )
        db_session.add(ev)
        await db_session.flush()

        assert ev.id is not None
        assert ev.instancia == "Primer llamado"
        assert ev.tipo == "Coloquio"
        assert ev.dias_disponibles == 5
        assert ev.cupo_por_dia == 10
        assert ev.activa is True
        assert ev.convocados == []

    async def test_evaluacion_defaults(self, db_session):
        tenant, materia, cohorte = await _seed_base(db_session)
        ev = Evaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            instancia="Único",
        )
        db_session.add(ev)
        await db_session.flush()
        assert ev.tipo == "Coloquio"
        assert ev.dias_disponibles == 5
        assert ev.cupo_por_dia == 10
        assert ev.activa is True

    async def test_evaluacion_soft_delete(self, db_session):
        tenant, materia, cohorte = await _seed_base(db_session)
        ev = Evaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            instancia="Borrar",
        )
        db_session.add(ev)
        await db_session.flush()

        ev.deleted_at = datetime.now(UTC)
        await db_session.flush()

        result = await db_session.execute(
            select(Evaluacion).where(Evaluacion.id == ev.id)
        )
        fetched = result.scalar_one()
        assert fetched.deleted_at is not None


class TestReservaEvaluacionModel:
    async def _seed(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-RES", nombre="Reserva Test")
        db_session.add(materia)
        await db_session.flush()
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="ABR-2026", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte)
        await db_session.flush()
        evaluacion = Evaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            instancia="Reserva Test",
        )
        db_session.add(evaluacion)
        await db_session.flush()
        return tenant, evaluacion

    async def test_create_reserva(self, db_session):
        tenant, evaluacion = await self._seed(db_session)
        from app.models.user import User
        alumno = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email="r@t.com", email_hash="rh", password_hash="h",
            nombre="A", apellidos="B", dni="e", estado="Activo",
        )
        db_session.add(alumno)
        await db_session.flush()

        reserva = ReservaEvaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            evaluacion_id=evaluacion.id, alumno_id=alumno.id,
            fecha=date(2026, 7, 1), hora="10:00",
        )
        db_session.add(reserva)
        await db_session.flush()

        assert reserva.id is not None
        assert reserva.fecha == date(2026, 7, 1)
        assert reserva.hora == "10:00"
        assert reserva.estado == "Activa"

    async def test_reserva_unique_constraint(self, db_session):
        tenant, evaluacion = await self._seed(db_session)
        from app.models.user import User
        alumno = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email="u@t.com", email_hash="uh", password_hash="h",
            nombre="U", apellidos="V", dni="e", estado="Activo",
        )
        db_session.add(alumno)
        await db_session.flush()

        r1 = ReservaEvaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            evaluacion_id=evaluacion.id, alumno_id=alumno.id,
            fecha=date(2026, 7, 1), hora="10:00",
        )
        db_session.add(r1)
        await db_session.flush()

        r2 = ReservaEvaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            evaluacion_id=evaluacion.id, alumno_id=alumno.id,
            fecha=date(2026, 7, 2), hora="11:00",
        )
        db_session.add(r2)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_reserva_default_estado(self, db_session):
        tenant, evaluacion = await self._seed(db_session)
        from app.models.user import User
        alumno = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email="de@t.com", email_hash="deh", password_hash="h",
            nombre="D", apellidos="E", dni="e", estado="Activo",
        )
        db_session.add(alumno)
        await db_session.flush()

        r = ReservaEvaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            evaluacion_id=evaluacion.id, alumno_id=alumno.id,
            fecha=date(2026, 7, 1), hora="10:00",
        )
        db_session.add(r)
        await db_session.flush()
        assert r.estado == "Activa"


class TestResultadoEvaluacionModel:
    async def _seed_resultado(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-RES2", nombre="Resultado Test")
        db_session.add(materia)
        await db_session.flush()
        carrera = await _create_carrera(db_session, tenant.id)
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="MAY-2026", anio=2026, vig_desde="2026-01-01", estado="Activa",
        )
        db_session.add(cohorte)
        await db_session.flush()
        evaluacion = Evaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            instancia="Resultado Test",
        )
        db_session.add(evaluacion)
        await db_session.flush()
        from app.models.user import User
        alumno = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email="res@t.com", email_hash="resh", password_hash="h",
            nombre="R", apellidos="S", dni="e", estado="Activo",
        )
        db_session.add(alumno)
        await db_session.flush()
        return tenant, evaluacion, alumno

    async def test_create_resultado(self, db_session):
        tenant, evaluacion, alumno = await self._seed_resultado(db_session)

        resultado = ResultadoEvaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            evaluacion_id=evaluacion.id, alumno_id=alumno.id,
            nota_final="Aprobado",
        )
        db_session.add(resultado)
        await db_session.flush()

        assert resultado.id is not None
        assert resultado.nota_final == "Aprobado"

    async def test_resultado_soft_delete(self, db_session):
        tenant, evaluacion, alumno = await self._seed_resultado(db_session)

        resultado = ResultadoEvaluacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            evaluacion_id=evaluacion.id, alumno_id=alumno.id,
            nota_final="8",
        )
        db_session.add(resultado)
        await db_session.flush()

        resultado.deleted_at = datetime.now(UTC)
        await db_session.flush()

        result = await db_session.execute(
            select(ResultadoEvaluacion).where(ResultadoEvaluacion.id == resultado.id)
        )
        fetched = result.scalar_one()
        assert fetched.deleted_at is not None
