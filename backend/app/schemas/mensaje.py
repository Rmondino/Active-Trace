"""Pydantic schemas for mensajería interna."""

from pydantic import BaseModel, ConfigDict


class MensajeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destinatario_id: str
    asunto: str
    cuerpo: str


class MensajeResponder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cuerpo: str
