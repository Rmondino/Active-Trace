"""ComentarioRepository — queries for ComentarioTarea model."""

from sqlalchemy import select

from app.models.comentario_tarea import ComentarioTarea
from app.repositories.base import BaseRepository


class ComentarioRepository(BaseRepository[ComentarioTarea]):
    """Repository for ComentarioTarea entity."""

    model_class = ComentarioTarea

    async def get_by_tarea(self, tarea_id: str) -> list[ComentarioTarea]:
        stmt = (
            select(ComentarioTarea)
            .where(
                ComentarioTarea.tarea_id == tarea_id,
                ComentarioTarea.deleted_at.is_(None),
            )
            .order_by(ComentarioTarea.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
