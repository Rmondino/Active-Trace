"""Pydantic schemas for Tarea — CRUD and detail views."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TareaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignado_a: str
    materia_id: str | None = None
    descripcion: str
    contexto_id: str | None = None


class TareaUpdateEstado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str


class ComentarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str


class ComentarioRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tarea_id: str
    autor_id: str
    texto: str
    created_at: datetime | None = None


class TareaRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    materia_id: str | None = None
    asignado_a: str
    asignado_por: str
    estado: str
    descripcion: str
    contexto_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    comentarios: list[ComentarioRead] = []
