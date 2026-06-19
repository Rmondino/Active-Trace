"""Fechas academicas router — ABM de fechas del calendario evaluativo.

All endpoints require `estructura:gestionar` permission.
Multi-tenant isolation via BaseRepository tenant filtering.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permission
from app.core.current_user import get_current_user
from app.models.user import User
from app.repositories.fecha_academica_repository import FechaAcademicaRepository

router = APIRouter(prefix="/api/fechas-academicas", tags=["fechas-academicas"])


class FechaAcademicaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: str
    cohorte_id: str
    tipo: str
    numero: int
    periodo: str
    fecha: date
    titulo: str


class FechaAcademicaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipo: str | None = None
    numero: int | None = None
    periodo: str | None = None
    fecha: date | None = None
    titulo: str | None = None


class FechaAcademicaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    materia_id: str
    cohorte_id: str
    tipo: str
    numero: int
    periodo: str
    fecha: date
    titulo: str
    tenant_id: str


def _get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.tenant_id


@router.get("", response_model=list[FechaAcademicaResponse])
async def list_fechas(
    materia_id: str | None = Query(default=None),
    cohorte_id: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
    periodo: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FechaAcademicaRepository(session=db, tenant_id=tenant_id)
    fechas = await repo.list_by_filters(
        materia_id=materia_id, cohorte_id=cohorte_id,
        tipo=tipo, periodo=periodo,
    )
    return [
        FechaAcademicaResponse(
            id=f.id, materia_id=f.materia_id, cohorte_id=f.cohorte_id,
            tipo=f.tipo, numero=f.numero, periodo=f.periodo,
            fecha=f.fecha, titulo=f.titulo, tenant_id=f.tenant_id,
        )
        for f in fechas
    ]


@router.get("/{fecha_id}", response_model=FechaAcademicaResponse)
async def get_fecha(
    fecha_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FechaAcademicaRepository(session=db, tenant_id=tenant_id)
    fecha = await repo.get(fecha_id)
    if fecha is None:
        raise HTTPException(status_code=404, detail="Fecha academica no encontrada")
    return FechaAcademicaResponse(
        id=fecha.id, materia_id=fecha.materia_id, cohorte_id=fecha.cohorte_id,
        tipo=fecha.tipo, numero=fecha.numero, periodo=fecha.periodo,
        fecha=fecha.fecha, titulo=fecha.titulo, tenant_id=fecha.tenant_id,
    )


@router.post("", response_model=FechaAcademicaResponse, status_code=201)
async def create_fecha(
    body: FechaAcademicaCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FechaAcademicaRepository(session=db, tenant_id=tenant_id)
    if await repo.exists_by_unique(
        body.materia_id, body.cohorte_id, body.tipo, body.numero, body.periodo,
    ):
        raise HTTPException(
            status_code=409,
            detail="Ya existe una fecha academica con esa combinacion de materia, cohorte, tipo, numero y periodo",
        )
    fecha = await repo.create(body.model_dump())
    return FechaAcademicaResponse(
        id=fecha.id, materia_id=fecha.materia_id, cohorte_id=fecha.cohorte_id,
        tipo=fecha.tipo, numero=fecha.numero, periodo=fecha.periodo,
        fecha=fecha.fecha, titulo=fecha.titulo, tenant_id=fecha.tenant_id,
    )


@router.put("/{fecha_id}", response_model=FechaAcademicaResponse)
async def update_fecha(
    fecha_id: str,
    body: FechaAcademicaUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FechaAcademicaRepository(session=db, tenant_id=tenant_id)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    fecha = await repo.update(fecha_id, data)
    if fecha is None:
        raise HTTPException(status_code=404, detail="Fecha academica no encontrada")
    return FechaAcademicaResponse(
        id=fecha.id, materia_id=fecha.materia_id, cohorte_id=fecha.cohorte_id,
        tipo=fecha.tipo, numero=fecha.numero, periodo=fecha.periodo,
        fecha=fecha.fecha, titulo=fecha.titulo, tenant_id=fecha.tenant_id,
    )


@router.delete("/{fecha_id}", status_code=204)
async def delete_fecha(
    fecha_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FechaAcademicaRepository(session=db, tenant_id=tenant_id)
    deleted = await repo.soft_delete(fecha_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fecha academica no encontrada")
    return None


@router.post("/contenido-lms")
async def contenido_lms_fechas(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission("estructura:gestionar")),
    tenant_id: str = Depends(_get_tenant_id),
):
    repo = FechaAcademicaRepository(session=db, tenant_id=tenant_id)
    fechas = await repo.list()
    rows_html = "".join(
        f"<tr><td>{f.fecha.isoformat()}</td><td>{f.tipo}</td>"
        f"<td>{f.numero}</td><td>{f.titulo}</td><td>{f.periodo}</td></tr>"
        for f in fechas
    )
    if fechas:
        html = (
            "<h3>Calendario Evaluativo</h3>"
            "<table border='1'><tr><th>Fecha</th><th>Tipo</th>"
            "<th>Numero</th><th>Titulo</th><th>Periodo</th></tr>"
            f"{rows_html}</table>"
        )
    else:
        html = "<h3>Calendario Evaluativo</h3><p>Sin fechas academicas cargadas</p>"
    return {"html": html}
