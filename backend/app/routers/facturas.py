"""Facturas router — CRUD de facturas y marcado como abonada.

Endpoints:
    - GET  /api/facturas
    - POST /api/facturas
    - GET  /api/facturas/{id}
    - POST /api/facturas/{id}/abonar
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.liquidacion_repository import FacturaRepository
from app.schemas.liquidacion import FacturaCreate, FacturaResponse

router = APIRouter(prefix="/api/facturas", tags=["facturas"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _to_factura_response(f) -> dict:
    return {
        "id": f.id,
        "tenant_id": f.tenant_id,
        "usuario_id": f.usuario_id,
        "periodo": f.periodo,
        "detalle": f.detalle,
        "referencia_archivo": f.referencia_archivo,
        "tamano_kb": float(f.tamano_kb) if f.tamano_kb else None,
        "estado": f.estado,
        "cargada_at": f.cargada_at,
        "abonada_at": f.abonada_at,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
    }


@router.get("")
async def list_facturas(
    periodo: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FacturaRepository(session=db, tenant_id=tenant_id)
    facturas = await repo.list_by_filters(tenant_id=tenant_id, periodo=periodo)
    return [_to_factura_response(f) for f in facturas]


@router.post("", status_code=201)
async def create_factura(
    body: FacturaCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FacturaRepository(session=db, tenant_id=tenant_id)
    data = body.model_dump()
    data["cargada_at"] = datetime.now(UTC)
    factura = await repo.create(data)
    return _to_factura_response(factura)


@router.get("/{factura_id}")
async def get_factura(
    factura_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FacturaRepository(session=db, tenant_id=tenant_id)
    factura = await repo.get(factura_id)
    if factura is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return _to_factura_response(factura)


@router.post("/{factura_id}/abonar")
async def abonar_factura(
    factura_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("liquidaciones:abonar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FacturaRepository(session=db, tenant_id=tenant_id)
    factura = await repo.get(factura_id)
    if factura is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if factura.estado == "Abonada":
        raise HTTPException(status_code=400, detail="La factura ya se encuentra abonada")
    factura.estado = "Abonada"
    factura.abonada_at = datetime.now(UTC)
    await db.flush()
    return _to_factura_response(factura)
