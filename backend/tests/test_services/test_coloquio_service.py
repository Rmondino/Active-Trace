"""Tests for ColoquioService."""

import uuid
from datetime import date

import pytest

from app.models.asignacion import Asignacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.evaluacion import Evaluacion
from app.models.materia import Materia
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.resultado_repository import ResultadoRepository
from app.services.coloquio_service import ColoquioService


async def _seed_base(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"col-{uuid.uuid4().hex[:8]}",
        nombre="Test Coloquio", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()

    materia = Materia(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo="MAT-COL", nombre="Coloquio Test",
    )
    db_session.add(materia)
    await db_session.flush()

    carrera = Carrera(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo=f"CAR-{uuid.uuid4().hex[:4]}", nombre="Test Carrera",
    )
    db_session.add(carrera)
    await db_session.flush()

    cohorte = Cohorte(
        id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
        nombre="COL-2026", anio=2026, vig_desde="2026-01-01", estado="Activa",
    )
    db_session.add(cohorte)
    await db_session.flush()

    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="col", email_hash="colh", password_hash="h",
        nombre="Col", apellidos="Oquio", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()

    alumno = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="alum", email_hash="alumh", password_hash="h",
        nombre="Alu", apellidos="Mno", dni="e", estado="Activo",
    )
    db_session.add(alumno)
    await db_session.flush()

    asignacion_alumno = Asignacion(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        usuario_id=alumno.id, rol="ALUMNO",
        cohorte_id=cohorte.id, desde=date(2026, 1, 1),
    )
    db_session.add(asignacion_alumno)
    await db_session.flush()

    return {
        "tenant_id": tenant.id,
        "materia_id": materia.id,
        "cohorte_id": cohorte.id,
        "user_id": user.id,
        "alumno_id": alumno.id,
    }


class TestCrear:
    async def test_crear_convocatoria_ok(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Primer Llamado",
            "tipo": "Coloquio",
            "cupo_por_dia": 15,
        }, user_id=seed["user_id"])

        assert evaluacion.id is not None
        assert evaluacion.instancia == "Primer Llamado"
        assert evaluacion.cupo_por_dia == 15
        assert evaluacion.activa is True

    async def test_crear_con_defaults(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Segundo Llamado",
        }, user_id=seed["user_id"])

        assert evaluacion.tipo == "Coloquio"
        assert evaluacion.dias_disponibles == 5
        assert evaluacion.cupo_por_dia == 10


class TestListar:
    async def test_listar_admin_ve_todas(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Admin List",
        }, user_id=seed["user_id"])

        result = await svc.listar()
        assert len(result) == 1
        assert result[0]["instancia"] == "Admin List"

    async def test_listar_alumno_filtra_por_cohorte(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Alumno List",
        }, user_id=seed["user_id"])

        result = await svc.listar(
            usuario_id=seed["alumno_id"],
            roles=["ALUMNO"],
        )
        assert len(result) == 1
        assert result[0]["instancia"] == "Alumno List"

    async def test_listar_alumno_sin_cohorte_vacia(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        otro_alumno = User(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            email="otro", email_hash="otroh", password_hash="h",
            nombre="Otro", apellidos="User", dni="e", estado="Activo",
        )
        db_session.add(otro_alumno)
        await db_session.flush()

        result = await svc.listar(
            usuario_id=otro_alumno.id,
            roles=["ALUMNO"],
        )
        assert result == []

    async def test_listar_sin_roles_devuelve_todas(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "No Role",
        }, user_id=seed["user_id"])

        result = await svc.listar()
        assert len(result) == 1


class TestDetalle:
    async def test_detalle_con_metricas(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Metricas",
            "cupo_por_dia": 10,
        }, user_id=seed["user_id"])

        detalle = await svc.detalle(evaluacion.id)
        assert detalle["total_convocados"] == 0
        assert detalle["reservas_activas"] == 0
        assert detalle["cupos_libres"] == 10

    async def test_detalle_404(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        with pytest.raises(Exception):
            await svc.detalle(str(uuid.uuid4()))


class TestImportarAlumnos:
    async def test_importar_alumnos_ok(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Import Test",
        }, user_id=seed["user_id"])

        result = await svc.importar_alumnos(evaluacion.id, [seed["alumno_id"]])
        assert seed["alumno_id"] in result["convocados"]

    async def test_importar_alumnos_idempotente(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Idempotent",
        }, user_id=seed["user_id"])

        await svc.importar_alumnos(evaluacion.id, [seed["alumno_id"]])
        result = await svc.importar_alumnos(evaluacion.id, [seed["alumno_id"]])
        assert len(result["convocados"]) == 1


class TestReservar:
    async def test_reservar_ok(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Reservar OK",
            "cupo_por_dia": 5,
        }, user_id=seed["user_id"])

        reserva = await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")
        assert reserva.evaluacion_id == evaluacion.id
        assert reserva.alumno_id == seed["alumno_id"]
        assert reserva.fecha == date(2026, 7, 1)
        assert reserva.estado == "Activa"

    async def test_reservar_sin_cupo_error(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Sin Cupo",
            "cupo_por_dia": 1,
        }, user_id=seed["user_id"])

        # Fill the only slot
        await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")

        otro = User(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            email="otro2", email_hash="otro2h", password_hash="h",
            nombre="Otro2", apellidos="Dos", dni="e", estado="Activo",
        )
        db_session.add(otro)
        await db_session.flush()

        with pytest.raises(Exception) as exc:
            await svc.reservar(evaluacion.id, otro.id, date(2026, 7, 1), "11:00")
        assert "Cupo completo" in str(exc.value)

    async def test_reservar_duplicado_error(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Duplicado",
            "cupo_por_dia": 10,
        }, user_id=seed["user_id"])

        await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")

        with pytest.raises(Exception) as exc:
            await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 2), "11:00")
        assert "Ya tienes una reserva" in str(exc.value)

    async def test_reservar_evaluacion_inactiva_error(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Inactiva",
            "cupo_por_dia": 10,
        }, user_id=seed["user_id"])

        evaluacion.activa = False
        await db_session.flush()

        with pytest.raises(Exception) as exc:
            await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")
        assert "no está activa" in str(exc.value)


class TestCancelarReserva:
    async def test_cancelar_propia_ok(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Cancelar",
            "cupo_por_dia": 5,
        }, user_id=seed["user_id"])

        reserva = await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")
        await svc.cancelar_reserva(reserva.id, seed["alumno_id"])
        assert reserva.estado == "Cancelada"

    async def test_cancelar_ajena_error(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Ajena",
            "cupo_por_dia": 5,
        }, user_id=seed["user_id"])

        reserva = await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")
        otro = User(
            id=str(uuid.uuid4()), tenant_id=seed["tenant_id"],
            email="otro3", email_hash="otro3h", password_hash="h",
            nombre="Otro3", apellidos="Tres", dni="e", estado="Activo",
        )
        db_session.add(otro)
        await db_session.flush()

        with pytest.raises(Exception) as exc:
            await svc.cancelar_reserva(reserva.id, otro.id)
        assert "No puedes cancelar" in str(exc.value)


class TestResultados:
    async def test_registrar_resultado_ok(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Resultado",
        }, user_id=seed["user_id"])

        resultado = await svc.registrar_resultado(evaluacion.id, seed["alumno_id"], "Aprobado")
        assert resultado.nota_final == "Aprobado"
        assert resultado.evaluacion_id == evaluacion.id

    async def test_registrar_resultado_actualiza_existente(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Resultado Update",
        }, user_id=seed["user_id"])

        await svc.registrar_resultado(evaluacion.id, seed["alumno_id"], "Aprobado")
        resultado = await svc.registrar_resultado(evaluacion.id, seed["alumno_id"], "10")
        assert resultado.nota_final == "10"

    async def test_listar_resultados(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "List Resultados",
        }, user_id=seed["user_id"])

        await svc.registrar_resultado(evaluacion.id, seed["alumno_id"], "Aprobado")
        resultados = await svc.listar_resultados(evaluacion.id)
        assert len(resultados) == 1
        assert resultados[0].nota_final == "Aprobado"


class TestAdminGlobal:
    async def test_admin_global_retorna_lista(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Admin Global",
        }, user_id=seed["user_id"])

        items = await svc.admin_global()
        assert len(items) == 1
        assert items[0]["instancia"] == "Admin Global"
        assert items[0]["total_convocados"] == 0
        assert items[0]["reservas_activas"] == 0
        assert items[0]["total_reservas"] == 0
        assert items[0]["total_resultados"] == 0

    async def test_admin_global_con_reservas_y_resultados(self, db_session):
        seed = await _seed_base(db_session)
        ev_repo = EvaluacionRepository(session=db_session, tenant_id=seed["tenant_id"])
        res_repo = ReservaRepository(session=db_session, tenant_id=seed["tenant_id"])
        rt_repo = ResultadoRepository(session=db_session, tenant_id=seed["tenant_id"])
        svc = ColoquioService(db_session, ev_repo, res_repo, rt_repo, seed["tenant_id"])

        evaluacion = await svc.crear({
            "materia_id": seed["materia_id"],
            "cohorte_id": seed["cohorte_id"],
            "instancia": "Admin Con Datos",
        }, user_id=seed["user_id"])

        await svc.reservar(evaluacion.id, seed["alumno_id"], date(2026, 7, 1), "10:00")
        await svc.registrar_resultado(evaluacion.id, seed["alumno_id"], "9")

        items = await svc.admin_global()
        assert len(items) == 1
        assert items[0]["reservas_activas"] == 1
        assert items[0]["total_reservas"] == 1
        assert items[0]["total_resultados"] == 1
