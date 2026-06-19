"""Padron router — import, preview, confirm, list, vaciar, moodle sync.

All endpoints require `calificaciones:importar` permission.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.core.security import encrypt, get_encryption_key
from app.models.user import User
from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron
from app.services.audit_log_service import AuditLogService
from app.services.padron_parser import PadronParser

router = APIRouter(prefix="/api/padron", tags=["padron"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

# In-memory preview storage
_previews: dict[str, dict[str, Any]] = {}


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _get_extension(filename: str) -> str:
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _parse_file(file_content: bytes, extension: str) -> dict:
    if extension == ".csv":
        return PadronParser.parse_csv(file_content)
    elif extension == ".xlsx":
        return PadronParser.parse_xlsx(file_content)
    raise ValueError(f"Formato de archivo no soportado: {extension}")


async def _match_usuarios(
    filas: list[dict], enc_key: bytes, db: AsyncSession, tenant_id: str
) -> list[dict]:
    """Try to match each fila's email to an existing User.
    If no match, usuario_id stays None (don't fail).
    """
    from app.core.security import decrypt
    from sqlalchemy import select
    from app.models.user import User

    for fila in filas:
        email_plain = fila.get("email", "")
        if not email_plain:
            continue
        result = await db.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
            )
        )
        matched = False
        for user in result.scalars().all():
            try:
                decrypted = decrypt(user.email, enc_key)
            except Exception:
                continue
            if decrypted.lower() == email_plain.lower():
                fila["usuario_id"] = user.id
                matched = True
                break
        if not matched:
            fila["usuario_id"] = None
    return filas


async def _persist_version(
    filas: list[dict],
    materia_id: str,
    cohorte_id: str,
    current_user: User,
    db: AsyncSession,
    tenant_id: str,
    origen: str = "manual",
    enc_key: bytes | None = None,
) -> dict:
    from app.repositories.entrada_padron_repository import EntradaPadronRepository
    from app.repositories.version_padron_repository import VersionPadronRepository

    if enc_key is not None:
        filas = await _match_usuarios(filas, enc_key, db, tenant_id)

    repo_ver = VersionPadronRepository(session=db, tenant_id=tenant_id)

    version = await repo_ver.create({
        "id": str(uuid.uuid4()),
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "cargado_por": current_user.id,
        "origen": origen,
        "total_filas": len(filas),
        "activa": False,
    })

    repo_ent = EntradaPadronRepository(session=db, tenant_id=tenant_id)
    entradas = []
    for fila in filas:
        email_encrypted = encrypt(fila.get("email", ""), enc_key) if enc_key else fila.get("email", "")
        entradas.append(EntradaPadron(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            version_id=version.id,
            usuario_id=fila.get("usuario_id"),
            nombre=fila.get("nombre", ""),
            apellidos=fila.get("apellidos", ""),
            email=email_encrypted,
            comision=fila.get("comision"),
            regional=fila.get("regional"),
        ))
    await repo_ent.bulk_create(entradas)

    await repo_ver.desactivar_anteriores(materia_id, cohorte_id, except_id=version.id)
    await repo_ver.update(version.id, {"activa": True})

    return {
        "version_id": version.id,
        "filas_importadas": len(filas),
    }


@router.post("/import")
async def import_padron(
    request: Request,
    file: UploadFile = File(...),
    materia_id: str = Form(...),
    cohorte_id: str = Form(...),
    confirm: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    extension = _get_extension(file.filename or "")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no soportado. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    try:
        parsed = _parse_file(content, extension)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filas = PadronParser.validate_filas(parsed["filas"])

    if confirm:
        enc_key = get_encryption_key(settings)
        result = await _persist_version(
            filas=filas,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            current_user=current_user,
            db=db,
            tenant_id=tenant_id,
            origen="manual",
            enc_key=enc_key,
        )

        audit = AuditLogService(db)
        await audit.log(
            actor_id=current_user.id,
            tenant_id=tenant_id,
            accion="PADRON_CARGAR",
            materia_id=materia_id,
            detalle={
                "tipo": "import",
                "filas": len(filas),
                "version_id": result["version_id"],
            },
            ip=request.client.host if request.client else None,
        )

        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=201, content=result)

    preview_id = str(uuid.uuid4())
    _previews[preview_id] = {
        "filas": filas,
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
    }

    preview = PadronParser.generar_preview(filas)
    preview["preview_id"] = preview_id
    return preview


@router.post("/preview/{preview_id}/confirm", status_code=201)
async def confirm_preview(
    request: Request,
    preview_id: str,
    materia_id: str = Query(...),
    cohorte_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    preview_data = _previews.pop(preview_id, None)
    if preview_data is None:
        raise HTTPException(status_code=404, detail="Preview no encontrada o expirada")

    enc_key = get_encryption_key(settings)
    result = await _persist_version(
        filas=preview_data["filas"],
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        current_user=current_user,
        db=db,
        tenant_id=tenant_id,
        origen="manual",
        enc_key=enc_key,
    )

    audit = AuditLogService(db)
    await audit.log(
        actor_id=current_user.id,
        tenant_id=tenant_id,
        accion="PADRON_CARGAR",
        materia_id=materia_id,
        detalle={
            "tipo": "import",
            "filas": result["filas_importadas"],
            "version_id": result["version_id"],
        },
        ip=request.client.host if request.client else None,
    )

    return result


@router.get("/versiones", response_model=list[dict])
async def list_versiones(
    materia_id: str = Query(...),
    cohorte_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.version_padron_repository import VersionPadronRepository

    repo = VersionPadronRepository(session=db, tenant_id=tenant_id)
    versiones = await repo.list_by_materia(materia_id)

    result = []
    for v in versiones:
        if v.cohorte_id != cohorte_id:
            continue
        result.append({
            "id": v.id,
            "materia_id": v.materia_id,
            "cohorte_id": v.cohorte_id,
            "activa": v.activa,
            "origen": v.origen,
            "total_filas": v.total_filas,
            "cargado_at": v.cargado_at.isoformat() if v.cargado_at else None,
            "cargado_por": v.cargado_por,
        })
    return result


@router.delete("/materia/{materia_id}")
async def vaciar_materia(
    request: Request,
    materia_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.version_padron_repository import VersionPadronRepository

    repo = VersionPadronRepository(session=db, tenant_id=tenant_id)
    versiones = await repo.list_by_materia(materia_id)
    await repo.vaciar_materia(materia_id)

    audit = AuditLogService(db)
    await audit.log(
        actor_id=current_user.id,
        tenant_id=tenant_id,
        accion="PADRON_CARGAR",
        materia_id=materia_id,
        detalle={
            "tipo": "vaciar",
            "versiones_afectadas": len(versiones),
        },
        ip=request.client.host if request.client else None,
    )

    return {"versiones_afectadas": len(versiones), "materia_id": materia_id}


@router.get("/moodle/sync")
async def moodle_sync(
    request: Request,
    materia_id: str = Query(...),
    cohorte_id: str = Query(...),
    course_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
    settings: Settings = Depends(get_settings),
):
    from app.integrations.moodle_ws import (
        MoodleWSClient,
        MoodleWSAuthError,
        MoodleWSUnavailableError,
    )
    from app.repositories.materia_repository import MateriaRepository

    base_url = settings.MOODLE_BASE_URL if hasattr(settings, "MOODLE_BASE_URL") else None
    token = settings.MOODLE_TOKEN if hasattr(settings, "MOODLE_TOKEN") else None

    if not base_url or not token:
        raise HTTPException(
            status_code=502,
            detail="Moodle no configurado. Falta MOODLE_BASE_URL o MOODLE_TOKEN",
        )

    client = MoodleWSClient(base_url=base_url, token=token)

    try:
        participants = await client.get_course_participants(course_id)
    except MoodleWSAuthError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except MoodleWSUnavailableError as e:
        raise HTTPException(status_code=502, detail=str(e))

    filas = []
    for p in participants:
        filas.append({
            "nombre": p.get("firstname", ""),
            "apellidos": p.get("lastname", ""),
            "email": p.get("email", ""),
            "comision": None,
            "regional": None,
        })

    filas = PadronParser.validate_filas(filas)
    enc_key = get_encryption_key(settings)

    result = await _persist_version(
        filas=filas,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        current_user=current_user,
        db=db,
        tenant_id=tenant_id,
        origen="moodle",
        enc_key=enc_key,
    )

    audit = AuditLogService(db)
    await audit.log(
        actor_id=current_user.id,
        tenant_id=tenant_id,
        accion="PADRON_CARGAR",
        materia_id=materia_id,
        detalle={
            "tipo": "moodle",
            "filas": len(filas),
            "version_id": result["version_id"],
            "course_id": course_id,
        },
        ip=request.client.host if request.client else None,
    )

    return {
        **result,
        "curso": str(course_id),
        "materia": materia_id,
    }
