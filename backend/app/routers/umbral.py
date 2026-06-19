"""Umbral router — configure per-materia pass threshold."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.models.asignacion import Asignacion
from app.models.umbral_materia import UmbralMateria
from app.repositories.umbral_materia_repository import UmbralMateriaRepository

router = APIRouter(prefix="/api/umbral", tags=["umbral"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.get("")
async def get_umbral(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:ver")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    from sqlalchemy import select

    result = await db.execute(
        select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.usuario_id == current_user.id,
            Asignacion.materia_id == materia_id,
            Asignacion.deleted_at.is_(None),
        )
    )
    asignacion = result.scalar_one_or_none()
    if not asignacion:
        return {
            "umbral_pct": 60,
            "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"],
        }

    repo = UmbralMateriaRepository(session=db, tenant_id=tenant_id)
    umbral = await repo.get_by_asignacion_materia(asignacion.id, materia_id)
    if not umbral:
        return {
            "umbral_pct": 60,
            "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"],
        }

    return {
        "umbral_pct": umbral.umbral_pct,
        "valores_aprobatorios": umbral.valores_aprobatorios,
    }


@router.put("")
async def update_umbral(
    materia_id: str = Query(...),
    body: dict = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    from sqlalchemy import select
    import uuid

    if body is None:
        body = {}

    result = await db.execute(
        select(Asignacion).where(
            Asignacion.tenant_id == tenant_id,
            Asignacion.usuario_id == current_user.id,
            Asignacion.materia_id == materia_id,
            Asignacion.deleted_at.is_(None),
        )
    )
    asignacion = result.scalar_one_or_none()
    if not asignacion:
        raise HTTPException(status_code=403, detail="No tienes asignación a esta materia")

    repo = UmbralMateriaRepository(session=db, tenant_id=tenant_id)
    existing = await repo.get_by_asignacion_materia(asignacion.id, materia_id)

    umbral_pct = body.get("umbral_pct", existing.umbral_pct if existing else 60)
    valores_aprobatorios = body.get(
        "valores_aprobatorios",
        existing.valores_aprobatorios if existing else ["Satisfactorio", "Supera lo esperado"],
    )

    if existing:
        existing.umbral_pct = umbral_pct
        existing.valores_aprobatorios = valores_aprobatorios
        await db.flush()
        umbral = existing
    else:
        umbral = UmbralMateria(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            asignacion_id=asignacion.id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
        db.add(umbral)
        await db.flush()

    return {
        "umbral_pct": umbral.umbral_pct,
        "valores_aprobatorios": umbral.valores_aprobatorios,
    }


@router.get("/default")
async def get_umbral_default():
    return {
        "umbral_pct": 60,
        "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"],
    }
