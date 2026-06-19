"""ColoquioService — gestión de evaluaciones, reservas y resultados."""

import uuid

from datetime import date

from fastapi import HTTPException
from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.models.evaluacion import Evaluacion
from app.models.reserva_evaluacion import ReservaEvaluacion
from app.models.resultado_evaluacion import ResultadoEvaluacion


class ColoquioService:

    def __init__(self, session, evaluacion_repo, reserva_repo, resultado_repo, tenant_id: str):
        self.session = session
        self.evaluacion_repo = evaluacion_repo
        self.reserva_repo = reserva_repo
        self.resultado_repo = resultado_repo
        self.tenant_id = tenant_id

    async def crear(self, data: dict, user_id: str) -> Evaluacion:
        evaluacion = Evaluacion(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            materia_id=data["materia_id"],
            cohorte_id=data["cohorte_id"],
            tipo=data.get("tipo", "Coloquio"),
            instancia=data["instancia"],
            dias_disponibles=data.get("dias_disponibles", 5),
            cupo_por_dia=data.get("cupo_por_dia", 10),
            convocados=[],
        )
        self.session.add(evaluacion)
        await self.session.flush()
        return evaluacion

    async def listar(self, filtros: dict | None = None, usuario_id: str | None = None, roles: list[str] | None = None) -> list[dict]:
        if roles and "ALUMNO" in roles and usuario_id:
            cohorte_ids = await self._get_cohortes_for_alumno(usuario_id)
            if not cohorte_ids:
                return []
            evaluaciones = await self._list_by_cohortes(cohorte_ids, filtros)
        else:
            evaluaciones = await self._list_all(filtros)
        return [self._evaluacion_to_dict(e) for e in evaluaciones]

    async def detalle(self, id: str) -> dict:
        evaluacion = await self.evaluacion_repo.get(id)
        if not evaluacion:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        return await self._build_detalle(evaluacion)

    async def importar_alumnos(self, id: str, alumno_ids: list[str]) -> dict:
        evaluacion = await self.evaluacion_repo.get(id)
        if not evaluacion:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        existing = set(evaluacion.convocados or [])
        existing.update(alumno_ids)
        evaluacion.convocados = list(existing)
        await self.session.flush()
        return {"convocados": evaluacion.convocados}

    async def reservar(self, evaluacion_id: str, alumno_id: str, fecha: date, hora: str) -> ReservaEvaluacion:
        evaluacion = await self.evaluacion_repo.get(evaluacion_id)
        if not evaluacion:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        if not evaluacion.activa:
            raise HTTPException(status_code=400, detail="La evaluación no está activa")

        existing = await self.reserva_repo.get_by_alumno_evaluacion(alumno_id, evaluacion_id)
        if existing:
            raise HTTPException(status_code=400, detail="Ya tienes una reserva para esta evaluación")

        activas = await self.reserva_repo.count_activas_by_fecha(evaluacion_id, fecha)
        if activas >= evaluacion.cupo_por_dia:
            raise HTTPException(status_code=400, detail="Cupo completo para esta fecha")

        reserva = ReservaEvaluacion(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            fecha=fecha,
            hora=hora,
        )
        self.session.add(reserva)
        await self.session.flush()
        return reserva

    async def cancelar_reserva(self, reserva_id: str, alumno_id: str) -> None:
        reserva = await self.reserva_repo.get(reserva_id)
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        if reserva.alumno_id != alumno_id:
            raise HTTPException(status_code=403, detail="No puedes cancelar una reserva que no te pertenece")
        reserva.estado = "Cancelada"
        await self.session.flush()

    async def registrar_resultado(self, evaluacion_id: str, alumno_id: str, nota: str) -> ResultadoEvaluacion:
        evaluacion = await self.evaluacion_repo.get(evaluacion_id)
        if not evaluacion:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")

        existing = await self.resultado_repo.get_by_alumno_evaluacion(alumno_id, evaluacion_id)
        if existing:
            existing.nota_final = nota
            await self.session.flush()
            return existing

        resultado = ResultadoEvaluacion(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            nota_final=nota,
        )
        self.session.add(resultado)
        await self.session.flush()
        return resultado

    async def listar_reservas(self, evaluacion_id: str) -> list[ReservaEvaluacion]:
        evaluacion = await self.evaluacion_repo.get(evaluacion_id)
        if not evaluacion:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        return await self.reserva_repo.get_by_evaluacion(evaluacion_id)

    async def listar_resultados(self, evaluacion_id: str) -> list[ResultadoEvaluacion]:
        evaluacion = await self.evaluacion_repo.get(evaluacion_id)
        if not evaluacion:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        return await self.resultado_repo.get_by_evaluacion(evaluacion_id)

    async def admin_global(self) -> list[dict]:
        evaluaciones = await self.evaluacion_repo.list()
        result = []
        for e in evaluaciones:
            reservas = await self.reserva_repo.get_by_evaluacion(e.id)
            resultados = await self.resultado_repo.get_by_evaluacion(e.id)
            activas = sum(1 for r in reservas if r.estado == "Activa")
            result.append({
                "id": e.id,
                "materia_id": e.materia_id,
                "cohorte_id": e.cohorte_id,
                "instancia": e.instancia,
                "tipo": e.tipo,
                "activa": e.activa,
                "total_convocados": len(e.convocados or []),
                "reservas_activas": activas,
                "total_reservas": len(reservas),
                "total_resultados": len(resultados),
            })
        return result

    async def _get_cohortes_for_alumno(self, usuario_id: str) -> list[str]:
        stmt = select(Asignacion.cohorte_id).where(
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.rol == "ALUMNO",
            Asignacion.deleted_at.is_(None),
            Asignacion.cohorte_id.isnot(None),
        )
        result = await self.session.execute(stmt)
        return list(set(row[0] for row in result.all()))

    async def _list_by_cohortes(self, cohorte_ids: list[str], filtros: dict | None) -> list[Evaluacion]:
        stmt = select(Evaluacion).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.deleted_at.is_(None),
            Evaluacion.cohorte_id.in_(cohorte_ids),
        )
        if filtros:
            if filtros.get("activa") is not None:
                stmt = stmt.where(Evaluacion.activa == filtros["activa"])
            if filtros.get("materia_id"):
                stmt = stmt.where(Evaluacion.materia_id == filtros["materia_id"])
        stmt = stmt.order_by(Evaluacion.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _list_all(self, filtros: dict | None) -> list[Evaluacion]:
        stmt = select(Evaluacion).where(
            Evaluacion.tenant_id == self.tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        if filtros:
            if filtros.get("materia_id"):
                stmt = stmt.where(Evaluacion.materia_id == filtros["materia_id"])
            if filtros.get("cohorte_id"):
                stmt = stmt.where(Evaluacion.cohorte_id == filtros["cohorte_id"])
            if filtros.get("activa") is not None:
                stmt = stmt.where(Evaluacion.activa == filtros["activa"])
        stmt = stmt.order_by(Evaluacion.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _build_detalle(self, evaluacion: Evaluacion) -> dict:
        reservas = await self.reserva_repo.get_by_evaluacion(evaluacion.id)
        activas = sum(1 for r in reservas if r.estado == "Activa")
        convocados_count = len(evaluacion.convocados or [])
        cupos_libres = evaluacion.cupo_por_dia - activas
        materia_nombre = evaluacion.materia.nombre if evaluacion.materia else None
        cohorte_nombre = evaluacion.cohorte.nombre if evaluacion.cohorte else None
        return {
            "id": evaluacion.id,
            "materia_id": evaluacion.materia_id,
            "cohorte_id": evaluacion.cohorte_id,
            "tipo": evaluacion.tipo,
            "instancia": evaluacion.instancia,
            "dias_disponibles": evaluacion.dias_disponibles,
            "cupo_por_dia": evaluacion.cupo_por_dia,
            "activa": evaluacion.activa,
            "convocados": evaluacion.convocados or [],
            "materia_nombre": materia_nombre,
            "cohorte_nombre": cohorte_nombre,
            "total_convocados": convocados_count,
            "reservas_activas": activas,
            "cupos_libres": max(0, cupos_libres),
        }

    @staticmethod
    def _evaluacion_to_dict(e: Evaluacion) -> dict:
        materia_nombre = e.materia.nombre if e.materia else None
        cohorte_nombre = e.cohorte.nombre if e.cohorte else None
        return {
            "id": e.id,
            "materia_id": e.materia_id,
            "cohorte_id": e.cohorte_id,
            "tipo": e.tipo,
            "instancia": e.instancia,
            "dias_disponibles": e.dias_disponibles,
            "cupo_por_dia": e.cupo_por_dia,
            "activa": e.activa,
            "convocados": e.convocados or [],
            "materia_nombre": materia_nombre,
            "cohorte_nombre": cohorte_nombre,
        }
