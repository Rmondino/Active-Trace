"""Calificaciones router — import, preview, confirm, list grades."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.current_user import get_current_user
from app.core.dependencies import get_db, require_permission
from app.models.user import User
from app.models.entrada_padron import EntradaPadron
from app.models.calificacion import Calificacion
from app.services.audit_log_service import AuditLogService
from app.services.calificaciones_parser import CalificacionesParser

router = APIRouter(prefix="/api/calificaciones", tags=["calificaciones"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

_previews: dict[str, dict[str, Any]] = {}


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


def _get_extension(filename: str) -> str:
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


@router.post("/import")
async def import_calificaciones(
    request: Request,
    file: UploadFile = File(...),
    materia_id: str = Form(...),
    cohorte_id: str = Form(...),
    confirm: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    extension = _get_extension(file.filename or "")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no soportado. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    try:
        parsed = CalificacionesParser.parse_grades_file(content, file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not parsed["columnas"]:
        raise HTTPException(status_code=400, detail="No se detectaron columnas de actividades")

    if confirm:
        result = await _persist_calificaciones(
            parsed=parsed,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tenant_id=tenant_id,
            current_user=current_user,
            db=db,
            actividades_seleccionadas=None,
        )
        audit = AuditLogService(db)
        await audit.log(
            actor_id=current_user.id,
            tenant_id=tenant_id,
            accion="CALIFICACIONES_IMPORTAR",
            materia_id=materia_id,
            detalle={
                "tipo": "import_directo",
                "total": result["total_calificaciones"],
                "aprobados": result["total_aprobados"],
            },
            ip=request.client.host if request.client else None,
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=201, content=result)

    preview_id = str(uuid.uuid4())
    _previews[preview_id] = {
        "parsed": parsed,
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
    }

    preview = CalificacionesParser.generar_preview(parsed)
    preview["preview_id"] = preview_id
    return preview


@router.post("/preview/{preview_id}/confirm", status_code=201)
async def confirm_preview_calificaciones(
    request: Request,
    preview_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    preview_data = _previews.pop(preview_id, None)
    if preview_data is None:
        raise HTTPException(status_code=404, detail="Preview no encontrada o expirada")

    actividades_seleccionadas = body.get("actividades_seleccionadas")

    result = await _persist_calificaciones(
        parsed=preview_data["parsed"],
        materia_id=preview_data["materia_id"],
        cohorte_id=preview_data["cohorte_id"],
        tenant_id=tenant_id,
        current_user=current_user,
        db=db,
        actividades_seleccionadas=actividades_seleccionadas,
    )

    audit = AuditLogService(db)
    await audit.log(
        actor_id=current_user.id,
        tenant_id=tenant_id,
        accion="CALIFICACIONES_IMPORTAR",
        materia_id=preview_data["materia_id"],
        detalle={
            "tipo": "preview_confirm",
            "total": result["total_calificaciones"],
            "aprobados": result["total_aprobados"],
        },
        ip=request.client.host if request.client else None,
    )

    return result


@router.post("/import/completions")
async def import_completions(
    request: Request,
    file: UploadFile = File(...),
    materia_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(_get_tenant_id),
):
    extension = _get_extension(file.filename or "")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no soportado. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    from app.repositories.calificacion_repository import CalificacionRepository

    repo = CalificacionRepository(session=db, tenant_id=tenant_id)
    calificaciones_existentes = await repo.get_by_materia(materia_id)

    entregas = CalificacionesParser.detect_completions(content, calificaciones_existentes)

    return {
        "entregas_sin_corregir": entregas,
        "total": len(entregas),
    }


@router.get("")
async def list_calificaciones(
    materia_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("calificaciones:ver")),
    tenant_id: str = Depends(_get_tenant_id),
):
    from app.repositories.calificacion_repository import CalificacionRepository

    repo = CalificacionRepository(session=db, tenant_id=tenant_id)
    calificaciones = await repo.get_by_materia(materia_id)

    result = []
    for cal in calificaciones:
        result.append({
            "id": cal.id,
            "entrada_padron_id": cal.entrada_padron_id,
            "materia_id": cal.materia_id,
            "actividad": cal.actividad,
            "nota_numerica": float(cal.nota_numerica) if cal.nota_numerica is not None else None,
            "nota_textual": cal.nota_textual,
            "aprobado": cal.aprobado,
            "origen": cal.origen,
            "importado_at": cal.importado_at.isoformat() if cal.importado_at else None,
        })
    return result


async def _get_or_create_umbral(
    db: AsyncSession,
    tenant_id: str,
    materia_id: str,
    current_user: User,
) -> tuple[int, list[str]]:
    from app.repositories.umbral_materia_repository import UmbralMateriaRepository
    from app.models.asignacion import Asignacion
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

    umbral_pct = 60
    valores_aprobatorios = ["Satisfactorio", "Supera lo esperado"]

    if asignacion:
        repo = UmbralMateriaRepository(session=db, tenant_id=tenant_id)
        umbral = await repo.get_by_asignacion_materia(asignacion.id, materia_id)
        if umbral:
            umbral_pct = umbral.umbral_pct
            valores_aprobatorios = umbral.valores_aprobatorios

    return umbral_pct, valores_aprobatorios


async def _persist_calificaciones(
    parsed: dict,
    materia_id: str,
    cohorte_id: str,
    tenant_id: str,
    current_user: User,
    db: AsyncSession,
    actividades_seleccionadas: list[str] | None,
) -> dict:
    from app.repositories.version_padron_repository import VersionPadronRepository
    from app.repositories.entrada_padron_repository import EntradaPadronRepository
    from app.repositories.calificacion_repository import CalificacionRepository

    ver_repo = VersionPadronRepository(session=db, tenant_id=tenant_id)
    version_activa = await ver_repo.get_activa(materia_id, cohorte_id)

    entrada_map: dict[str, dict] = {}
    if version_activa:
        ent_repo = EntradaPadronRepository(session=db, tenant_id=tenant_id)
        entradas = await ent_repo.get_by_version(version_activa.id)
        for ep in entradas:
            key = f"{ep.nombre} {ep.apellidos}".strip().lower()
            entrada_map[key] = {"id": ep.id, "nombre": ep.nombre, "apellidos": ep.apellidos}

    columnas = parsed.get("columnas", [])
    filas = parsed.get("filas", [])

    umbral_pct, valores_aprobatorios = await _get_or_create_umbral(
        db, tenant_id, materia_id, current_user
    )

    if actividades_seleccionadas is not None:
        selected_set = set(actividades_seleccionadas)
        columnas = [c for c in columnas if c["nombre"] in selected_set]

    calificaciones = []
    for fila in filas:
        alumno_key = fila["alumno"].strip().lower()
        entrada_id = None
        if alumno_key in entrada_map:
            entrada_id = entrada_map[alumno_key]["id"]

        for col_info in columnas:
            col_name = col_info["nombre"]
            raw_val = fila["actividades"].get(col_name)

            nota_numerica = None
            nota_textual = None

            if raw_val is not None and raw_val != "":
                if col_info["tipo"] == "numerica":
                    try:
                        nota_numerica = Decimal(str(raw_val))
                    except Exception:
                        nota_textual = raw_val
                else:
                    nota_textual = raw_val

            aprobado = CalificacionesParser.derivar_aprobado(
                nota_numerica, nota_textual, umbral_pct, valores_aprobatorios
            )

            cal = Calificacion(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                entrada_padron_id=entrada_id,
                materia_id=materia_id,
                actividad=col_name,
                nota_numerica=nota_numerica,
                nota_textual=nota_textual,
                aprobado=aprobado,
                origen="Importado",
                importado_at=datetime.now(UTC),
            )
            calificaciones.append(cal)

    repo = CalificacionRepository(session=db, tenant_id=tenant_id)
    await repo.bulk_create(calificaciones)

    total_aprobados = sum(1 for c in calificaciones if c.aprobado)
    return {
        "total_calificaciones": len(calificaciones),
        "total_aprobados": total_aprobados,
    }
