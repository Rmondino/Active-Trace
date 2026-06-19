"""Tests for Comunicacion model and state machine transitions."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.comunicacion import Comunicacion
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User

VALOROUS_TRANSITIONS: dict[str, set[str]] = {
    "Pendiente": {"Enviando", "Cancelado"},
    "Enviando": {"Enviado", "Error"},
}


def validar_transicion(actual: str, nuevo: str) -> None:
    if actual not in VALOROUS_TRANSITIONS:
        raise ValueError(f"Estado terminal '{actual}': no permite transiciones")
    if nuevo not in VALOROUS_TRANSITIONS[actual]:
        raise ValueError(f"Transición inválida: {actual} → {nuevo}")


async def _seed_tenant_user_materia(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug=f"test-{uuid.uuid4().hex[:8]}", nombre="Test", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc", email_hash="h", password_hash="h",
        nombre="T", apellidos="U", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()
    materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-COM", nombre="Test")
    db_session.add(materia)
    await db_session.flush()
    return tenant, user, materia


class TestComunicacionModel:
    async def test_create_comunicacion(self, db_session):
        tenant, user, materia = await _seed_tenant_user_materia(db_session)
        com = Comunicacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            enviado_por=user.id,
            materia_id=materia.id,
            destinatario="encrypted@email",
            asunto="Test asunto",
            cuerpo="Test cuerpo",
            lote_id=str(uuid.uuid4()),
        )
        db_session.add(com)
        await db_session.flush()

        assert com.id is not None
        assert com.estado == "Pendiente"
        assert com.destinatario == "encrypted@email"
        assert com.asunto == "Test asunto"
        assert com.cuerpo == "Test cuerpo"
        assert com.error_msg is None
        assert com.aprobado_por is None
        assert com.enviado_at is None

    async def test_default_estado(self, db_session):
        tenant, user, materia = await _seed_tenant_user_materia(db_session)
        com = Comunicacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            enviado_por=user.id,
            materia_id=materia.id,
            destinatario="e@e.com",
            asunto="A",
            cuerpo="C",
            lote_id=str(uuid.uuid4()),
        )
        db_session.add(com)
        await db_session.flush()
        assert com.estado == "Pendiente"

    async def test_soft_delete(self, db_session):
        tenant, user, materia = await _seed_tenant_user_materia(db_session)
        com = Comunicacion(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            enviado_por=user.id,
            materia_id=materia.id,
            destinatario="e@e.com",
            asunto="A",
            cuerpo="C",
            lote_id=str(uuid.uuid4()),
        )
        db_session.add(com)
        await db_session.flush()
        com.deleted_at = datetime.now(UTC)
        await db_session.flush()

        from sqlalchemy import select
        result = await db_session.execute(
            select(Comunicacion).where(Comunicacion.id == com.id)
        )
        fetched = result.scalar_one()
        assert fetched.deleted_at is not None

    async def test_multi_tenant_isolation(self, db_session):
        t1 = Tenant(id=str(uuid.uuid4()), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1", estado="Activo")
        t2 = Tenant(id=str(uuid.uuid4()), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2", estado="Activo")
        db_session.add_all([t1, t2])
        await db_session.flush()
        u1 = User(id=str(uuid.uuid4()), tenant_id=t1.id, email="e1", email_hash="h1", password_hash="h", nombre="U", apellidos="1", dni="e1", estado="Activo")
        u2 = User(id=str(uuid.uuid4()), tenant_id=t2.id, email="e2", email_hash="h2", password_hash="h", nombre="U", apellidos="2", dni="e2", estado="Activo")
        db_session.add_all([u1, u2])
        await db_session.flush()
        m1 = Materia(id=str(uuid.uuid4()), tenant_id=t1.id, codigo="M1", nombre="M1")
        m2 = Materia(id=str(uuid.uuid4()), tenant_id=t2.id, codigo="M2", nombre="M2")
        db_session.add_all([m1, m2])
        await db_session.flush()

        lote = str(uuid.uuid4())
        c1 = Comunicacion(id=str(uuid.uuid4()), tenant_id=t1.id, enviado_por=u1.id, materia_id=m1.id, destinatario="e1@e.com", asunto="A", cuerpo="C", lote_id=lote)
        c2 = Comunicacion(id=str(uuid.uuid4()), tenant_id=t2.id, enviado_por=u2.id, materia_id=m2.id, destinatario="e2@e.com", asunto="A", cuerpo="C", lote_id=lote)
        db_session.add_all([c1, c2])
        await db_session.flush()

        from sqlalchemy import select
        result = await db_session.execute(
            select(Comunicacion).where(
                Comunicacion.tenant_id == t1.id,
                Comunicacion.lote_id == lote,
            )
        )
        items = list(result.scalars().all())
        assert len(items) == 1
        assert items[0].tenant_id == t1.id

    async def test_timestamps_set_automatically(self, db_session):
        tenant, user, materia = await _seed_tenant_user_materia(db_session)
        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            enviado_por=user.id, materia_id=materia.id,
            destinatario="e@e.com", asunto="A", cuerpo="C",
            lote_id=str(uuid.uuid4()),
        )
        db_session.add(com)
        await db_session.flush()
        assert com.created_at is not None
        assert com.updated_at is not None


class TestStateMachine:
    def test_valid_pendiente_to_enviando(self):
        validar_transicion("Pendiente", "Enviando")

    def test_valid_pendiente_to_cancelado(self):
        validar_transicion("Pendiente", "Cancelado")

    def test_valid_enviando_to_enviado(self):
        validar_transicion("Enviando", "Enviado")

    def test_valid_enviando_to_error(self):
        validar_transicion("Enviando", "Error")

    def test_invalid_enviado_to_cancelado(self):
        with pytest.raises(ValueError, match="Estado terminal"):
            validar_transicion("Enviado", "Cancelado")

    def test_invalid_enviado_to_enviando(self):
        with pytest.raises(ValueError, match="Estado terminal"):
            validar_transicion("Enviado", "Enviando")

    def test_invalid_cancelado_to_enviando(self):
        with pytest.raises(ValueError, match="Estado terminal"):
            validar_transicion("Cancelado", "Enviando")

    def test_invalid_error_to_enviando(self):
        with pytest.raises(ValueError, match="Estado terminal"):
            validar_transicion("Error", "Enviando")

    def test_invalid_pendiente_to_enviado(self):
        with pytest.raises(ValueError, match="Transición inválida"):
            validar_transicion("Pendiente", "Enviado")

    def test_invalid_pendiente_to_error(self):
        with pytest.raises(ValueError, match="Transición inválida"):
            validar_transicion("Pendiente", "Error")

    def test_invalid_transition_message_format(self):
        with pytest.raises(ValueError) as exc:
            validar_transicion("Enviado", "Cancelado")
        assert "Enviado" in str(exc.value)

    def test_all_terminal_states_reject(self):
        for terminal in ("Enviado", "Error", "Cancelado"):
            for target in ("Pendiente", "Enviando", "Enviado", "Error", "Cancelado"):
                if terminal == target:
                    continue
                with pytest.raises(ValueError):
                    validar_transicion(terminal, target)
