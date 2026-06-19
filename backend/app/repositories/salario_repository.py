"""SalarioRepository — CRUD for SalarioBase, SalarioPlus, MateriaGrupoPlus."""

from datetime import date

from sqlalchemy import select

from app.models.liquidacion import MateriaGrupoPlus, SalarioBase, SalarioPlus
from app.repositories.base import BaseRepository


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    model_class = SalarioBase

    async def get_vigente_por_rol(
        self, tenant_id: str, rol: str, fecha: date | None = None
    ) -> SalarioBase | None:
        ref = fecha or date.today()
        stmt = (
            select(SalarioBase)
            .where(
                SalarioBase.tenant_id == tenant_id,
                SalarioBase.rol == rol,
                SalarioBase.deleted_at.is_(None),
                SalarioBase.desde <= ref,
                (SalarioBase.hasta.is_(None)) | (SalarioBase.hasta >= ref),
            )
            .order_by(SalarioBase.desde.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    model_class = SalarioPlus

    async def get_vigentes_por_grupo(
        self, tenant_id: str, grupo: str, fecha: date | None = None
    ) -> list[SalarioPlus]:
        ref = fecha or date.today()
        stmt = select(SalarioPlus).where(
            SalarioPlus.tenant_id == tenant_id,
            SalarioPlus.grupo == grupo,
            SalarioPlus.deleted_at.is_(None),
            SalarioPlus.desde <= ref,
            (SalarioPlus.hasta.is_(None)) | (SalarioPlus.hasta >= ref),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class MateriaGrupoPlusRepository(BaseRepository[MateriaGrupoPlus]):
    model_class = MateriaGrupoPlus

    async def get_vigentes_por_materia(
        self, tenant_id: str, materia_id: str, fecha: date | None = None
    ) -> list[MateriaGrupoPlus]:
        ref = fecha or date.today()
        stmt = select(MateriaGrupoPlus).where(
            MateriaGrupoPlus.tenant_id == tenant_id,
            MateriaGrupoPlus.materia_id == materia_id,
            MateriaGrupoPlus.deleted_at.is_(None),
            MateriaGrupoPlus.desde <= ref,
            (MateriaGrupoPlus.hasta.is_(None)) | (MateriaGrupoPlus.hasta >= ref),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
