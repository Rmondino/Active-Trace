"""Pydantic schemas for Aviso — CRUD and detail views."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AvisoCreate(BaseModel):
    """Schema for creating a new notice."""

    model_config = ConfigDict(extra="forbid")

    alcance: str = "Global"
    materia_id: str | None = None
    cohorte_id: str | None = None
    rol_destino: str | None = None
    severidad: str = "Info"
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdate(BaseModel):
    """Schema for updating an existing notice (all fields optional)."""

    model_config = ConfigDict(extra="forbid")

    alcance: str | None = None
    materia_id: str | None = None
    cohorte_id: str | None = None
    rol_destino: str | None = None
    severidad: str | None = None
    titulo: str | None = None
    cuerpo: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None


class AvisoRead(BaseModel):
    """Schema for reading a notice (returned to users)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    alcance: str
    materia_id: str | None = None
    cohorte_id: str | None = None
    rol_destino: str | None = None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    ackeado: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AcknowledgmentRead(BaseModel):
    """Schema for reading an acknowledgment record."""

    model_config = ConfigDict(extra="forbid")

    id: str
    aviso_id: str
    usuario_id: str
    confirmado_at: datetime


class AvisoStats(BaseModel):
    """Schema for notice statistics."""

    model_config = ConfigDict(extra="forbid")

    total_acks: int
