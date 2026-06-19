"""Pydantic schemas for liquidaciones, salarios, and facturas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# ── SalarioBase ──

class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rol: str
    monto: float
    desde: date
    hasta: date | None = None


class SalarioBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rol: str | None = None
    monto: float | None = None
    desde: date | None = None
    hasta: date | None = None


class SalarioBaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    rol: str
    monto: float
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime


# ── SalarioPlus ──

class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grupo: str
    rol: str | None = None
    descripcion: str
    monto: float
    desde: date
    hasta: date | None = None
    tope_acumulacion: int | None = None


class SalarioPlusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grupo: str | None = None
    rol: str | None = None
    descripcion: str | None = None
    monto: float | None = None
    desde: date | None = None
    hasta: date | None = None
    tope_acumulacion: int | None = None


class SalarioPlusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    grupo: str
    rol: str | None
    descripcion: str
    monto: float
    desde: date
    hasta: date | None
    tope_acumulacion: int | None
    created_at: datetime
    updated_at: datetime


# ── MateriaGrupoPlus ──

class MateriaGrupoPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: str
    grupo: str
    desde: date
    hasta: date | None = None


class MateriaGrupoPlusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    materia_id: str | None = None
    grupo: str | None = None
    desde: date | None = None
    hasta: date | None = None


class MateriaGrupoPlusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    materia_id: str
    grupo: str
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime


# ── Liquidacion ──

class LiquidacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    cohorte_id: str
    periodo: str
    usuario_id: str
    rol: str
    comisiones: list
    monto_base: float
    monto_plus: float
    total: float
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    created_at: datetime
    updated_at: datetime


class LiquidacionKPIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_general: float
    total_facturantes: float
    total_no_facturantes: float
    total_nexo: float
    cant_docs: int


# ── Factura ──

class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: str
    periodo: str
    detalle: str
    referencia_archivo: str | None = None
    tamano_kb: float | None = None


class FacturaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    usuario_id: str
    periodo: str
    detalle: str
    referencia_archivo: str | None
    tamano_kb: float | None
    estado: str
    cargada_at: datetime
    abonada_at: datetime | None
    created_at: datetime
    updated_at: datetime
