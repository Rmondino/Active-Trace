"""GuardiaService — registro, listado y exportación de guardias."""

import logging
import uuid

from io import BytesIO

from openpyxl import Workbook

from app.models.guardia import Guardia

logger = logging.getLogger(__name__)


class GuardiaService:

    def __init__(self, session, guardia_repo, tenant_id: str) -> None:
        self.session = session
        self.guardia_repo = guardia_repo
        self.tenant_id = tenant_id

    async def registrar(self, data: dict, user_id: str) -> Guardia:
        guardia = Guardia(
            id=str(uuid.uuid4()),
            asignacion_id=data["asignacion_id"],
            materia_id=data["materia_id"],
            carrera_id=data.get("carrera_id"),
            cohorte_id=data.get("cohorte_id"),
            dia=data["dia"],
            horario=data["horario"],
            estado="Pendiente",
            comentarios=data.get("comentarios"),
            tenant_id=self.tenant_id,
        )
        self.session.add(guardia)
        await self.session.flush()
        return guardia

    async def listar(self, materia_id: str | None = None) -> list[Guardia]:
        if materia_id:
            return await self.guardia_repo.get_by_materia(materia_id)
        return await self.guardia_repo.list()

    async def exportar(self, materia_id: str | None = None) -> bytes:
        guardias = await self.listar(materia_id)
        wb = Workbook()
        ws = wb.active
        ws.append(["Día", "Horario", "Estado", "Materia", "Comentarios"])
        for g in guardias:
            ws.append([
                g.dia,
                g.horario,
                g.estado,
                g.materia.nombre if g.materia else "",
                g.comentarios or "",
            ])
        output = BytesIO()
        wb.save(output)
        return output.getvalue()
