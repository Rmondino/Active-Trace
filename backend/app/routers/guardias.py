"""Guardias router — registrar, listar, exportar."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.guardia_repository import GuardiaRepository
from app.services.guardia_service import GuardiaService

router = APIRouter(prefix="/api/guardias", tags=["guardias"])


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _build_svc(
    db: AsyncSession, tenant_id: str
) -> GuardiaService:
    guardia_repo = GuardiaRepository(session=db, tenant_id=tenant_id)
    return GuardiaService(db, guardia_repo, tenant_id)


@router.post("", status_code=201)
async def registrar_guardia(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    guardia = await svc.registrar(body, current_user.id)
    return {
        "id": guardia.id,
        "dia": guardia.dia,
        "horario": guardia.horario,
        "estado": guardia.estado,
        "materia_id": guardia.materia_id,
    }


@router.get("")
async def listar_guardias(
    materia_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    guardias = await svc.listar(materia_id)
    return {"guardias": [
        {
            "id": g.id,
            "dia": g.dia,
            "horario": g.horario,
            "estado": g.estado,
            "materia_id": g.materia_id,
            "comentarios": g.comentarios,
        }
        for g in guardias
    ]}


@router.get("/export")
async def exportar_guardias(
    materia_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("encuentros:gestionar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    svc = _build_svc(db, tenant_id)
    content = await svc.exportar(materia_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=guardias.xlsx"},
    )
