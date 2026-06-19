"""TenantRepository — CRUD for Tenant model."""

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    model_class = Tenant

    async def get_by_slug(self, slug: str) -> Tenant | None:
        from sqlalchemy import select
        stmt = select(self.model_class).where(self.model_class.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
