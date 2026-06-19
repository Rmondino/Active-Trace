"""EquipoService — equipos docentes: mis equipos, gestión, clonar, exportar."""

import logging
from datetime import date
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger(__name__)


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    parts = value.split("-")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


class EquipoService:

    def __init__(
        self,
        asignacion_repo,
        audit: AuditLogService,
        session,
    ) -> None:
        self.asignacion_repo = asignacion_repo
        self.audit = audit
        self.session = session

    async def mis_equipos(
        self,
        usuario_id: str,
        tenant_id: str,
        filtros: dict | None = None,
    ) -> list[dict]:
        asignaciones = await self.asignacion_repo.get_by_usuario(
            tenant_id, usuario_id, solo_vigentes=False
        )
        result = []
        for a in asignaciones:
            item = {
                "id": a.id,
                "usuario_id": a.usuario_id,
                "rol": a.rol,
                "materia": (
                    {"id": a.materia_id, "nombre": a.materia.nombre if a.materia else None}
                    if a.materia_id else None
                ),
                "carrera": (
                    {"id": a.carrera_id, "nombre": a.carrera.nombre if a.carrera else None}
                    if a.carrera_id else None
                ),
                "cohorte": (
                    {"id": a.cohorte_id, "nombre": a.cohorte.nombre if a.cohorte else None}
                    if a.cohorte_id else None
                ),
                "comisiones": a.comisiones,
                "responsable": {"id": a.responsable_id} if a.responsable_id else None,
                "desde": a.desde.isoformat(),
                "hasta": a.hasta.isoformat() if a.hasta else None,
                "vigente": (
                    a.desde <= date.today()
                    and (a.hasta is None or a.hasta >= date.today())
                ),
            }
            result.append(item)
        if filtros:
            estado = filtros.get("estado")
            if estado == "vigente":
                result = [r for r in result if r["vigente"]]
            elif estado == "no_vigente":
                result = [r for r in result if not r["vigente"]]
            if filtros.get("materia_id"):
                mid = filtros["materia_id"]
                result = [r for r in result if r["materia"] and r["materia"]["id"] == mid]
        return result

    async def listar_asignaciones(
        self,
        tenant_id: str,
        filtros: dict | None = None,
    ) -> dict:
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.deleted_at.is_(None),
        )
        if filtros:
            if filtros.get("materia_id"):
                stmt = stmt.where(Asignacion.materia_id == filtros["materia_id"])
            if filtros.get("rol"):
                stmt = stmt.where(Asignacion.rol == filtros["rol"])
            if filtros.get("carrera_id"):
                stmt = stmt.where(Asignacion.carrera_id == filtros["carrera_id"])
            if filtros.get("cohorte_id"):
                stmt = stmt.where(Asignacion.cohorte_id == filtros["cohorte_id"])
            if filtros.get("usuario_id"):
                stmt = stmt.where(Asignacion.usuario_id == filtros["usuario_id"])
        stmt = stmt.order_by(Asignacion.created_at.desc())
        result = await self.session.execute(stmt)
        asignaciones = list(result.scalars().all())
        return {
            "asignaciones": [self._to_dict(a) for a in asignaciones],
        }

    async def asignacion_masiva(
        self,
        data: dict,
        user_id: str,
        tenant_id: str,
    ) -> dict:
        nuevas = []
        for did in data["docente_ids"]:
            a = Asignacion(
                usuario_id=did,
                rol=data["rol"],
                materia_id=data.get("materia_id"),
                carrera_id=data.get("carrera_id"),
                cohorte_id=data.get("cohorte_id"),
                comisiones=data.get("comisiones", []),
                responsable_id=data.get("responsable_id"),
                desde=_parse_date(data["desde"]),
                hasta=_parse_date(data["hasta"]) if data.get("hasta") else None,
                tenant_id=tenant_id,
            )
            self.session.add(a)
            nuevas.append(a)
        await self.session.flush()
        await self.audit.log(
            actor_id=user_id,
            tenant_id=tenant_id,
            accion="ASIGNACION_MODIFICAR",
            materia_id=data.get("materia_id"),
            detalle={"tipo": "masiva", "total": len(nuevas), "rol": data["rol"]},
        )
        return {
            "total_creadas": len(nuevas),
            "asignaciones": [{"id": a.id, "usuario_id": a.usuario_id} for a in nuevas],
        }

    async def clonar_equipo(
        self,
        data: dict,
        user_id: str,
        tenant_id: str,
    ) -> dict:
        today = date.today()
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.materia_id == data["origen_materia_id"],
            Asignacion.carrera_id == data["origen_carrera_id"],
            Asignacion.cohorte_id == data["origen_cohorte_id"],
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= today,
            (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= today),
        )
        result = await self.session.execute(stmt)
        origen = list(result.scalars().all())

        nuevas = []
        for a in origen:
            nueva = Asignacion(
                usuario_id=a.usuario_id,
                rol=a.rol,
                comisiones=a.comisiones,
                responsable_id=a.responsable_id,
                materia_id=data["destino_materia_id"],
                carrera_id=data["destino_carrera_id"],
                cohorte_id=data["destino_cohorte_id"],
                desde=_parse_date(data["nuevo_desde"]),
                hasta=_parse_date(data["nuevo_hasta"]) if data.get("nuevo_hasta") else None,
                tenant_id=tenant_id,
            )
            self.session.add(nueva)
            nuevas.append(nueva)
        await self.session.flush()

        await self.audit.log(
            actor_id=user_id,
            tenant_id=tenant_id,
            accion="ASIGNACION_MODIFICAR",
            materia_id=data["destino_materia_id"],
            detalle={
                "tipo": "clonar",
                "total": len(nuevas),
                "origen_cohorte": data["origen_cohorte_id"],
            },
        )
        return {
            "total_clonadas": len(nuevas),
            "asignaciones": [{"id": a.id, "usuario_id": a.usuario_id} for a in nuevas],
        }

    async def actualizar_vigencia(
        self,
        data: dict,
        user_id: str,
        tenant_id: str,
    ) -> dict:
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.materia_id == data["materia_id"],
            Asignacion.carrera_id == data["carrera_id"],
            Asignacion.cohorte_id == data["cohorte_id"],
            Asignacion.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        asignaciones = list(result.scalars().all())
        for a in asignaciones:
            if "nuevo_desde" in data:
                a.desde = _parse_date(data["nuevo_desde"])
            if "nuevo_hasta" in data:
                a.hasta = _parse_date(data["nuevo_hasta"])
        await self.session.flush()
        await self.audit.log(
            actor_id=user_id,
            tenant_id=tenant_id,
            accion="ASIGNACION_MODIFICAR",
            materia_id=data["materia_id"],
            detalle={"tipo": "vigencia", "total": len(asignaciones)},
        )
        return {"total_actualizadas": len(asignaciones)}

    async def exportar_equipo(
        self,
        materia_id: str,
        carrera_id: str,
        cohorte_id: str,
        tenant_id: str,
    ) -> bytes:
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.materia_id == materia_id,
            Asignacion.carrera_id == carrera_id,
            Asignacion.cohorte_id == cohorte_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        asignaciones = list(result.scalars().all())

        wb = Workbook()
        ws = wb.active
        ws.append([
            "Docente", "Email", "Rol", "Comisiones", "Materia",
            "Carrera", "Cohorte", "Desde", "Hasta", "Vigente", "Responsable",
        ])
        today = date.today()
        for a in asignaciones:
            vigente = (
                a.desde <= today
                and (a.hasta is None or a.hasta >= today)
            )
            ws.append([
                f"{a.usuario.nombre} {a.usuario.apellidos}" if a.usuario else "",
                "",
                a.rol,
                ", ".join(a.comisiones) if a.comisiones else "",
                a.materia.nombre if a.materia else "",
                a.carrera.nombre if a.carrera else "",
                a.cohorte.nombre if a.cohorte else "",
                a.desde.isoformat(),
                a.hasta.isoformat() if a.hasta else "",
                "Sí" if vigente else "No",
                f"{a.responsable.nombre} {a.responsable.apellidos}" if a.responsable else "",
            ])
        output = BytesIO()
        wb.save(output)
        return output.getvalue()

    def _to_dict(self, a: Asignacion) -> dict:
        return {
            "id": a.id,
            "usuario_id": a.usuario_id,
            "rol": a.rol,
            "tenant_id": a.tenant_id,
            "materia": (
                {"id": a.materia_id, "nombre": a.materia.nombre if a.materia else None}
                if a.materia_id else None
            ),
            "carrera": (
                {"id": a.carrera_id, "nombre": a.carrera.nombre if a.carrera else None}
                if a.carrera_id else None
            ),
            "cohorte": (
                {"id": a.cohorte_id, "nombre": a.cohorte.nombre if a.cohorte else None}
                if a.cohorte_id else None
            ),
            "comisiones": a.comisiones,
            "responsable_id": a.responsable_id,
            "desde": a.desde.isoformat(),
            "hasta": a.hasta.isoformat() if a.hasta else None,
            "vigente": (
                a.desde <= date.today()
                and (a.hasta is None or a.hasta >= date.today())
            ),
        }
