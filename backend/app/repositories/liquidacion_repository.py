"""LiquidacionRepository — CRUD for Liquidacion and Factura."""

from sqlalchemy import func, select

from app.models.liquidacion import Factura, Liquidacion
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    model_class = Liquidacion

    async def list_by_filters(
        self,
        tenant_id: str,
        cohorte_id: str | None = None,
        periodo: str | None = None,
    ) -> list[Liquidacion]:
        stmt = select(Liquidacion).where(
            Liquidacion.tenant_id == tenant_id,
            Liquidacion.deleted_at.is_(None),
        )
        if cohorte_id:
            stmt = stmt.where(Liquidacion.cohorte_id == cohorte_id)
        if periodo:
            stmt = stmt.where(Liquidacion.periodo == periodo)
        stmt = stmt.order_by(Liquidacion.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_kpis(
        self,
        tenant_id: str,
        cohorte_id: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        stmt = select(Liquidacion).where(
            Liquidacion.tenant_id == tenant_id,
            Liquidacion.deleted_at.is_(None),
        )
        if cohorte_id:
            stmt = stmt.where(Liquidacion.cohorte_id == cohorte_id)
        if periodo:
            stmt = stmt.where(Liquidacion.periodo == periodo)

        result = await self.session.execute(stmt)
        liquidaciones = list(result.scalars().all())

        total_general = sum(float(l.total) for l in liquidaciones)
        total_facturantes = sum(
            float(l.total) for l in liquidaciones if l.excluido_por_factura
        )
        total_no_facturantes = sum(
            float(l.total) for l in liquidaciones if not l.excluido_por_factura
        )
        total_nexo = sum(float(l.total) for l in liquidaciones if l.es_nexo)
        cant_docs = len(set(l.usuario_id for l in liquidaciones))

        return {
            "total_general": round(total_general, 2),
            "total_facturantes": round(total_facturantes, 2),
            "total_no_facturantes": round(total_no_facturantes, 2),
            "total_nexo": round(total_nexo, 2),
            "cant_docs": cant_docs,
        }


class FacturaRepository(BaseRepository[Factura]):
    model_class = Factura

    async def list_by_filters(
        self,
        tenant_id: str,
        periodo: str | None = None,
    ) -> list[Factura]:
        stmt = select(Factura).where(
            Factura.tenant_id == tenant_id,
            Factura.deleted_at.is_(None),
        )
        if periodo:
            stmt = stmt.where(Factura.periodo == periodo)
        stmt = stmt.order_by(Factura.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
