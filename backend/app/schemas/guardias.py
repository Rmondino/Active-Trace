"""Pydantic schemas for Guardia."""

from pydantic import BaseModel, ConfigDict


class GuardiaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: str
    materia_id: str
    carrera_id: str | None = None
    cohorte_id: str | None = None
    dia: str
    horario: str
    comentarios: str | None = None


class GuardiaRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    asignacion_id: str
    materia_id: str
    carrera_id: str | None = None
    cohorte_id: str | None = None
    dia: str
    horario: str
    estado: str
    comentarios: str | None = None
    tenant_id: str
