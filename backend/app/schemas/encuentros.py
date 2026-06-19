"""Pydantic schemas for Encuentros (SlotEncuentro, InstanciaEncuentro)."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class SlotEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: str
    materia_id: str
    titulo: str
    hora: str
    dia_semana: str | None = None
    fecha_inicio: date | None = None
    cant_semanas: int | None = None
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date


class SlotEncuentroRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    asignacion_id: str
    materia_id: str
    titulo: str
    hora: str
    dia_semana: str | None = None
    fecha_inicio: date | None = None
    cant_semanas: int | None = None
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date
    tenant_id: str


class InstanciaEncuentroUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None


class InstanciaEncuentroRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    slot_id: str | None = None
    materia_id: str
    fecha: date
    hora: str
    titulo: str
    estado: str
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    tenant_id: str
