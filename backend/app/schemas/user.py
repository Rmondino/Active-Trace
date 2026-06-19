"""Pydantic schemas for User — CRUD, PII masking, and detail views.

Conventions:
    - extra='forbid' on all schemas (rejects undeclared fields)
    - UserRead: PII masked for list responses
    - UserDetail: full PII for ADMIN or own user
"""

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Schema for creating a new user (full profile with PII)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    email: str
    dni: str
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False


class UserUpdate(BaseModel):
    """Schema for updating an existing user (all fields optional)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    email: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None
    estado: str | None = None


class UserRead(BaseModel):
    """Schema for listing users — PII fields are masked."""

    model_config = ConfigDict(extra="forbid")

    id: str
    nombre: str
    apellidos: str
    email: str
    dni: str | None = None
    legajo: str | None = None
    regional: str | None = None
    estado: str
    facturador: bool


class UserDetail(BaseModel):
    """Schema for reading a single user — full PII (ADMIN or own user)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    nombre: str
    apellidos: str
    email: str
    dni: str
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool
    estado: str
