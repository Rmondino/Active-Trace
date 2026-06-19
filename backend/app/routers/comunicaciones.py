"""Comunicaciones router — preview, enqueue, approve, reject, track."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.current_user import get_current_user
from app.core.crypto import CipherService
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.audit_log_service import AuditLogService
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(prefix="/api/comunicaciones", tags=["comunicaciones"])


def _build_svc(
    db: AsyncSession, settings: Settings, tenant_id: str
) -> ComunicacionService:
    repo = ComunicacionRepository(session=db, tenant_id=tenant_id)
    materia_repo = MateriaRepository(session=db, tenant_id=tenant_id)
    tenant_repo = TenantRepository(session=db, tenant_id=tenant_id)
    cipher = CipherService(settings)
    audit = AuditLogService(db)
    return ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.post("/preview")
async def crear_preview(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:enviar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    try:
        result = await svc.generar_preview(
            materia_id=body["materia_id"],
            asunto_template=body["asunto_template"],
            cuerpo_template=body["cuerpo_template"],
            alumnos=body.get("alumnos", []),
            tenant_id=tenant_id,
        )
        return result
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo requerido: {e}")


@router.post("/enviar")
async def enviar(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:enviar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    try:
        result = await svc.encolar(
            materia_id=body["materia_id"],
            asunto=body["asunto"],
            cuerpo=body["cuerpo"],
            destinatarios=body.get("destinatarios", []),
            user_id=current_user.id,
            tenant_id=tenant_id,
            preview_token=body.get("preview_token"),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Campo requerido: {e}")


@router.get("")
async def tracking(
    materia_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:enviar")),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    return await svc.tracking(materia_id, tenant_id)


@router.get("/pendientes-aprobacion")
async def pendientes_aprobacion(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    return await svc.get_pendientes_aprobacion(tenant_id)


@router.post("/aprobar/lote/{lote_id}")
async def aprobar_lote(
    lote_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    try:
        result = await svc.aprobar_lote(lote_id, current_user.id, tenant_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aprobar/{id}")
async def aprobar_individual(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    try:
        result = await svc.aprobar(id, current_user.id, tenant_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rechazar/{id}")
async def rechazar(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("comunicacion:aprobar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    svc = _build_svc(db, settings, tenant_id)
    try:
        result = await svc.rechazar(id, tenant_id, user_id=current_user.id)
        return result
    except ValueError as e:
        status = 400
        if "no encontrada" in str(e).lower():
            status = 404
        raise HTTPException(status_code=status, detail=str(e))
