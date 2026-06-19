"""Pydantic schemas for Asignacion — CRUD with derived estado_vigencia.

Conventions:
    - extra='forbid' on all schemas
    - estado_vigencia is derived (not stored): "Vigente" or "Vencida"
"""

from datetime import date

from pydantic import BaseModel, ConfigDict


class AsignacionCreate(BaseModel):
    """Schema for creating an asignacion."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: str
    rol: str
    materia_id: str | None = None
    carrera_id: str | None = None
    cohorte_id: str | None = None
    comisiones: list[str] = []
    responsable_id: str | None = None
    desde: date
    hasta: date | None = None


class AsignacionUpdate(BaseModel):
    """Schema for updating an asignacion (all fields optional)."""

    model_config = ConfigDict(extra="forbid")

    rol: str | None = None
    materia_id: str | None = None
    carrera_id: str | None = None
    cohorte_id: str | None = None
    comisiones: list[str] | None = None
    responsable_id: str | None = None
    desde: date | None = None
    hasta: date | None = None


class AsignacionRead(BaseModel):
    """Schema for reading an asignacion with derived estado_vigencia."""

    model_config = ConfigDict(extra="forbid")

    id: str
    usuario_id: str
    rol: str
    materia_id: str | None = None
    carrera_id: str | None = None
    cohorte_id: str | None = None
    comisiones: list[str] = []
    responsable_id: str | None = None
    desde: date
    hasta: date | None = None
    estado_vigencia: str
