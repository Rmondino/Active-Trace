"""EntradaPadronRepository — CRUD for EntradaPadron with tenant scope."""

from datetime import UTC, datetime

from sqlalchemy import select, func, update

from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron
from app.repositories.base import BaseRepository


class EntradaPadronRepository(BaseRepository[EntradaPadron]):
    model_class = EntradaPadron

    async def bulk_create(self, entradas: list[EntradaPadron]) -> None:
        for entrada in entradas:
            self.session.add(entrada)
        await self.session.flush()

    async def get_by_version(self, version_id: str) -> list[EntradaPadron]:
        stmt = select(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.version_id == version_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_version(self, version_id: str) -> int:
        stmt = select(func.count()).select_from(self.model_class)
        stmt = self._apply_tenant_scope(stmt)
        stmt = self._exclude_deleted(stmt)
        stmt = stmt.where(self.model_class.version_id == version_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def vaciar_by_version(self, version_id: str) -> None:
        stmt = (
            update(self.model_class)
            .where(self.model_class.version_id == version_id)
            .values(deleted_at=datetime.now(UTC))
        )
        stmt = self._apply_tenant_scope(stmt)
        await self.session.execute(stmt)
        await self.session.flush()
