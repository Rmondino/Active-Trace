"""Liquidaciones router — generación, consulta y cierre de liquidaciones.

Endpoints:
    - POST /api/liquidaciones/generar
    - GET  /api/liquidaciones
    - GET  /api/liquidaciones/{id}
    - POST /api/liquidaciones/{id}/cerrar
    - GET  /api/liquidaciones/kpis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.schemas.liquidacion import (
    LiquidacionKPIResponse,
    LiquidacionResponse,
)
from app.services.liquidacion_service import LiquidacionService

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _build_svc(db: AsyncSession, tenant_id: str) -> LiquidacionService:
    return LiquidacionService(session=db, tenant_id=tenant_id)


def _to_liquidacion_response(l) -> dict:
    return {
        "id": l.id,
        "tenant_id": l.tenant_id,
        "cohorte_id": l.cohorte_id,
        "periodo": l.periodo,
        "usuario_id": l.usuario_id,
        "rol": l.rol,
        "comisiones": l.comisiones,
        "monto_base": float(l.monto_base),
        "monto_plus": float(l.monto_plus),
        "total": float(l.total),
        "es_nexo": l.es_nexo,
        "excluido_por_factura": l.excluido_por_factura,
        "estado": l.estado,
        "created_at": l.created_at,
        "updated_at": l.updated_at,
    }


@router.post("/generar", status_code=201)
async def generar_liquidaciones(
    cohorte_id: str = Query(...),
    periodo: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:configurar-salarios")),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    liquidaciones = await svc.generar_liquidaciones(
        cohorte_id=cohorte_id, periodo=periodo
    )
    return [_to_liquidacion_response(l) for l in liquidaciones]


@router.get("")
async def list_liquidaciones(
    cohorte_id: str | None = Query(default=None),
    periodo: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = LiquidacionRepository(session=db, tenant_id=tenant_id)
    liquidaciones = await repo.list_by_filters(
        tenant_id=tenant_id, cohorte_id=cohorte_id, periodo=periodo
    )
    return [_to_liquidacion_response(l) for l in liquidaciones]


@router.get("/kpis", response_model=LiquidacionKPIResponse)
async def get_kpis(
    cohorte_id: str | None = Query(default=None),
    periodo: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    kpis = await svc.obtener_kpis(cohorte_id=cohorte_id, periodo=periodo)
    return LiquidacionKPIResponse(**kpis)


@router.get("/{liquidacion_id}")
async def get_liquidacion(
    liquidacion_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = LiquidacionRepository(session=db, tenant_id=tenant_id)
    liquidacion = await repo.get(liquidacion_id)
    if liquidacion is None:
        raise HTTPException(status_code=404, detail="Liquidacion no encontrada")
    return _to_liquidacion_response(liquidacion)


@router.post("/{liquidacion_id}/cerrar")
async def cerrar_liquidacion(
    liquidacion_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:cerrar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    try:
        liquidacion = await svc.cerrar_liquidacion(liquidacion_id)
    except ValueError as e:
        if "ya se encuentra cerrada" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    return _to_liquidacion_response(liquidacion)
