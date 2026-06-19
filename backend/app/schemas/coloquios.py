"""Pydantic schemas for Coloquios (Evaluacion, ReservaEvaluacion, ResultadoEvaluacion)."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: str
    cohorte_id: str
    instancia: str
    tipo: str = "Coloquio"
    dias_disponibles: int = 5
    cupo_por_dia: int = 10


class EvaluacionRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    materia_id: str
    cohorte_id: str
    tipo: str
    instancia: str
    dias_disponibles: int
    cupo_por_dia: int
    activa: bool
    convocados: list
    materia_nombre: str | None = None
    cohorte_nombre: str | None = None


class EvaluacionDetalle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    materia_id: str
    cohorte_id: str
    tipo: str
    instancia: str
    dias_disponibles: int
    cupo_por_dia: int
    activa: bool
    convocados: list
    materia_nombre: str | None = None
    cohorte_nombre: str | None = None
    total_convocados: int = 0
    reservas_activas: int = 0
    cupos_libres: int = 0


class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    hora: str


class ReservaRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    evaluacion_id: str
    alumno_id: str
    fecha: date
    hora: str
    estado: str


class ResultadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: str
    nota_final: str


class ResultadoRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    evaluacion_id: str
    alumno_id: str
    nota_final: str


class AlumnosImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_ids: list[str]


class AdminGlobalItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    materia_id: str
    cohorte_id: str
    instancia: str
    tipo: str
    activa: bool
    total_convocados: int = 0
    reservas_activas: int = 0
    total_reservas: int = 0
    total_resultados: int = 0
