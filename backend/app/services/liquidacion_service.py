"""LiquidacionService — generación de liquidaciones con salario base y plus."""

import logging
import uuid
from collections import defaultdict
from datetime import date, datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.liquidacion import Factura, Liquidacion
from app.models.user import User
from app.repositories.liquidacion_repository import FacturaRepository, LiquidacionRepository
from app.repositories.salario_repository import (
    MateriaGrupoPlusRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)

logger = logging.getLogger(__name__)


def _parse_periodo(periodo: str) -> date:
    parts = periodo.split("-")
    return date(int(parts[0]), int(parts[1]), 1)


class LiquidacionService:

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.salario_base_repo = SalarioBaseRepository(
            session=session, tenant_id=tenant_id
        )
        self.salario_plus_repo = SalarioPlusRepository(
            session=session, tenant_id=tenant_id
        )
        self.materia_grupo_repo = MateriaGrupoPlusRepository(
            session=session, tenant_id=tenant_id
        )
        self.liquidacion_repo = LiquidacionRepository(
            session=session, tenant_id=tenant_id
        )
        self.factura_repo = FacturaRepository(
            session=session, tenant_id=tenant_id
        )

    async def generar_liquidaciones(
        self,
        cohorte_id: str,
        periodo: str,
    ) -> list[Liquidacion]:
        ref = _parse_periodo(periodo)
        ref_end = date(ref.year, ref.month, 1)

        stmt = select(Asignacion).where(
            Asignacion.tenant_id == self.tenant_id,
            Asignacion.cohorte_id == cohorte_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= ref_end,
            (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ref_end),
        )
        result = await self.session.execute(stmt)
        asignaciones = list(result.scalars().all())

        docentes_map: dict[str, list[Asignacion]] = defaultdict(list)
        for a in asignaciones:
            docentes_map[a.usuario_id].append(a)

        liquidaciones: list[Liquidacion] = []
        roles_nexo = {"NEXO"}

        for usuario_id, asigns in docentes_map.items():
            rol = asigns[0].rol
            comisiones = list(
                set(
                    c
                    for a in asigns
                    if isinstance(a.comisiones, list)
                    for c in a.comisiones
                )
            )
            es_nexo = rol.upper() in roles_nexo

            result_user = await self.session.execute(
                select(User).where(User.id == usuario_id)
            )
            user = result_user.scalar_one_or_none()
            excluido_por_factura = bool(user and user.facturador)

            salario_base = await self.salario_base_repo.get_vigente_por_rol(
                self.tenant_id, rol, ref_end
            )
            monto_base = float(salario_base.monto) if salario_base else 0.0

            monto_plus = 0.0
            comisiones_contadas: dict[str, int] = defaultdict(int)

            for a in asigns:
                if not a.materia_id:
                    continue
                grupos = await self.materia_grupo_repo.get_vigentes_por_materia(
                    self.tenant_id, a.materia_id, ref_end
                )
                for gp in grupos:
                    plus_list = await self.salario_plus_repo.get_vigentes_por_grupo(
                        self.tenant_id, gp.grupo, ref_end
                    )
                    for plus in plus_list:
                        if plus.rol and plus.rol != rol:
                            continue
                        comisiones_contadas[gp.grupo] += 1
                        if (
                            plus.tope_acumulacion
                            and comisiones_contadas[gp.grupo] > plus.tope_acumulacion
                        ):
                            continue
                        monto_plus += float(plus.monto)

            liquidacion = Liquidacion(
                id=str(uuid.uuid4()),
                tenant_id=self.tenant_id,
                cohorte_id=cohorte_id,
                periodo=periodo,
                usuario_id=usuario_id,
                rol=rol,
                comisiones=comisiones,
                monto_base=round(monto_base, 2),
                monto_plus=round(monto_plus, 2),
                total=round(monto_base + monto_plus, 2),
                es_nexo=es_nexo,
                excluido_por_factura=excluido_por_factura,
                estado="Abierta",
            )
            self.session.add(liquidacion)
            liquidaciones.append(liquidacion)

        if liquidaciones:
            await self.session.flush()

        return liquidaciones

    async def cerrar_liquidacion(self, liquidacion_id: str) -> Liquidacion:
        liquidacion = await self.liquidacion_repo.get(liquidacion_id)
        if liquidacion is None:
            raise ValueError("Liquidacion no encontrada")
        if liquidacion.estado == "Cerrada":
            raise ValueError("La liquidacion ya se encuentra cerrada")
        liquidacion.estado = "Cerrada"
        await self.session.flush()
        return liquidacion

    async def obtener_kpis(
        self,
        cohorte_id: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        return await self.liquidacion_repo.get_kpis(
            self.tenant_id, cohorte_id, periodo
        )
