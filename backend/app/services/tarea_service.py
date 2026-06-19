"""TareaService — internal task management with state machine."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import Tarea, validar_transicion_tarea
from app.models.comentario_tarea import ComentarioTarea
from app.repositories.tarea_repository import TareaRepository
from app.repositories.comentario_repository import ComentarioRepository

logger = logging.getLogger(__name__)


class TareaService:

    def __init__(
        self,
        tarea_repo: TareaRepository,
        comentario_repo: ComentarioRepository,
        session: AsyncSession,
    ) -> None:
        self.tarea_repo = tarea_repo
        self.comentario_repo = comentario_repo
        self.session = session

    async def crear(self, data: dict, user_id: str, tenant_id: str) -> Tarea:
        data["asignado_por"] = user_id
        return await self.tarea_repo.create(data)

    async def mis_tareas(
        self,
        usuario_id: str,
        tenant_id: str,
        estado: str | None = None,
    ) -> list[dict]:
        filtros = {}
        if estado:
            filtros["estado"] = estado
        tareas = await self.tarea_repo.get_by_asignado(tenant_id, usuario_id, filtros)
        return [self._to_dict(t) for t in tareas]

    async def listar_todas(self, tenant_id: str, filtros: dict) -> list[dict]:
        tareas = await self.tarea_repo.get_all_filtered(tenant_id, filtros)
        return [self._to_dict(t) for t in tareas]

    async def detalle(self, id: str, tenant_id: str) -> dict:
        tarea = await self.tarea_repo.get(id)
        if tarea is None:
            raise ValueError("Tarea no encontrada")
        comentarios = await self.comentario_repo.get_by_tarea(id)
        result = self._to_dict(tarea)
        result["comentarios"] = [
            {
                "id": c.id,
                "tarea_id": c.tarea_id,
                "autor_id": c.autor_id,
                "texto": c.texto,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in comentarios
        ]
        return result

    async def cambiar_estado(
        self,
        id: str,
        nuevo_estado: str,
        usuario_id: str,
        tenant_id: str,
    ) -> Tarea:
        tarea = await self.tarea_repo.get(id)
        if tarea is None:
            raise ValueError("Tarea no encontrada")
        validar_transicion_tarea(tarea.estado, nuevo_estado)
        tarea.estado = nuevo_estado
        await self.session.flush()
        return tarea

    async def agregar_comentario(
        self,
        tarea_id: str,
        texto: str,
        autor_id: str,
        tenant_id: str,
    ) -> ComentarioTarea:
        tarea = await self.tarea_repo.get(tarea_id)
        if tarea is None:
            raise ValueError("Tarea no encontrada")
        comentario = ComentarioTarea(
            tenant_id=tenant_id,
            tarea_id=tarea_id,
            autor_id=autor_id,
            texto=texto,
        )
        self.session.add(comentario)
        await self.session.flush()
        return comentario

    def _to_dict(self, t: Tarea) -> dict:
        return {
            "id": t.id,
            "tenant_id": t.tenant_id,
            "materia_id": t.materia_id,
            "asignado_a": t.asignado_a,
            "asignado_por": t.asignado_por,
            "estado": t.estado,
            "descripcion": t.descripcion,
            "contexto_id": t.contexto_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
