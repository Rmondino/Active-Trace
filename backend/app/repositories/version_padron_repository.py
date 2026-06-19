"""VersionPadronRepository — CRUD for VersionPadron with tenant scope."""

from datetime import UTC, datetime

from sqlalchemy import select, update

from app.models.version_padron import VersionPadron
from app.repositories.base import BaseRepository


class VersionPadronRepository(BaseRepository[VersionPadron]):
    model_class = VersionPadron

    async def get_activa(self, materia_id: str, cohorte_id: str) -> VersionPadron | None:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(
            self.model_class.materia_id == materia_id,
            self.model_class.cohorte_id == cohorte_id,
            self.model_class.activa == True,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def desactivar_anteriores(
        self, materia_id: str, cohorte_id: str, except_id: str | None = None
    ) -> None:
        stmt = (
            update(self.model_class)
            .where(
                self.model_class.materia_id == materia_id,
                self.model_class.cohorte_id == cohorte_id,
                self.model_class.activa == True,
            )
            .values(activa=False)
        )
        stmt = self._apply_tenant_scope(stmt)
        if except_id is not None:
            stmt = stmt.where(self.model_class.id != except_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def list_by_materia(self, materia_id: str) -> list[VersionPadron]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.materia_id == materia_id)
        stmt = stmt.order_by(self.model_class.cargado_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def vaciar_materia(self, materia_id: str) -> None:
        stmt = (
            update(self.model_class)
            .where(self.model_class.materia_id == materia_id)
            .values(deleted_at=datetime.now(UTC))
        )
        stmt = self._apply_tenant_scope(stmt)
        await self.session.execute(stmt)
        await self.session.flush()
