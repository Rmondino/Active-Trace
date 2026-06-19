"""Pydantic schemas for API request/response validation."""

from app.schemas.asignacion import AsignacionCreate, AsignacionRead, AsignacionUpdate
from app.schemas.user import UserCreate, UserDetail, UserRead, UserUpdate
from app.schemas.coloquios import (
    AdminGlobalItem,
    AlumnosImport,
    EvaluacionCreate,
    EvaluacionDetalle,
    EvaluacionRead,
    ReservaCreate,
    ReservaRead,
    ResultadoCreate,
    ResultadoRead,
)

__all__ = [
    "AsignacionCreate",
    "AsignacionRead",
    "AsignacionUpdate",
    "UserCreate",
    "UserDetail",
    "UserRead",
    "UserUpdate",
    "AdminGlobalItem",
    "AlumnosImport",
    "EvaluacionCreate",
    "EvaluacionDetalle",
    "EvaluacionRead",
    "ReservaCreate",
    "ReservaRead",
    "ResultadoCreate",
    "ResultadoRead",
]
