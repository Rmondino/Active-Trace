"""Tests for Tarea and ComentarioTarea models."""

import uuid

import pytest

from app.models.tarea import Tarea, validar_transicion_tarea, VALID_TRANSITIONS_TAREA
from app.models.comentario_tarea import ComentarioTarea
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture
async def seed_data(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"tm-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    user1 = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc1", email_hash="h1", password_hash="h",
        nombre="A", apellidos="Uno", dni="e1", estado="Activo",
    )
    user2 = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc2", email_hash="h2", password_hash="h",
        nombre="B", apellidos="Dos", dni="e2", estado="Activo",
    )
    db_session.add_all([user1, user2])
    await db_session.flush()
    return {"tenant_id": tenant.id, "asignado_id": user1.id, "asignador_id": user2.id}


class TestTareaModel:
    async def test_crear_tarea(self, db_session, seed_data):
        tarea = Tarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            asignado_a=seed_data["asignado_id"],
            asignado_por=seed_data["asignador_id"],
            descripcion="Completar informe mensual",
        )
        db_session.add(tarea)
        await db_session.flush()
        assert tarea.id is not None
        assert tarea.estado == "Pendiente"
        assert tarea.descripcion == "Completar informe mensual"

    async def test_tarea_default_estado(self, db_session, seed_data):
        tarea = Tarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            asignado_a=seed_data["asignado_id"],
            asignado_por=seed_data["asignador_id"],
            descripcion="Revisar planilla",
        )
        db_session.add(tarea)
        await db_session.flush()
        assert tarea.estado == "Pendiente"

    async def test_tarea_soft_delete(self, db_session, seed_data):
        tarea = Tarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            asignado_a=seed_data["asignado_id"],
            asignado_por=seed_data["asignador_id"],
            descripcion="Tarea a eliminar",
        )
        db_session.add(tarea)
        await db_session.flush()
        assert tarea.deleted_at is None
        tarea.deleted_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
        await db_session.flush()
        assert tarea.deleted_at is not None

    async def test_tarea_relationships(self, db_session, seed_data):
        tarea = Tarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            asignado_a=seed_data["asignado_id"],
            asignado_por=seed_data["asignador_id"],
            descripcion="Tarea con relaciones",
        )
        db_session.add(tarea)
        await db_session.flush()
        db_session.expunge_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(Tarea).where(Tarea.id == tarea.id)
        )
        loaded = result.scalar_one()
        assert loaded.asignado.id == seed_data["asignado_id"]
        assert loaded.asignador.id == seed_data["asignador_id"]

    async def test_crear_comentario(self, db_session, seed_data):
        tarea = Tarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            asignado_a=seed_data["asignado_id"],
            asignado_por=seed_data["asignador_id"],
            descripcion="Tarea con comentario",
        )
        db_session.add(tarea)
        await db_session.flush()
        comentario = ComentarioTarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            tarea_id=tarea.id,
            autor_id=seed_data["asignado_id"],
            texto="Este es un comentario de prueba",
        )
        db_session.add(comentario)
        await db_session.flush()
        assert comentario.id is not None
        assert comentario.texto == "Este es un comentario de prueba"
        assert comentario.tarea_id == tarea.id

    async def test_comentario_tarea_relationship(self, db_session, seed_data):
        tarea = Tarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            asignado_a=seed_data["asignado_id"],
            asignado_por=seed_data["asignador_id"],
            descripcion="Tarea con relacion comentario",
        )
        db_session.add(tarea)
        await db_session.flush()
        c = ComentarioTarea(
            id=str(uuid.uuid4()),
            tenant_id=seed_data["tenant_id"],
            tarea_id=tarea.id,
            autor_id=seed_data["asignado_id"],
            texto="Comentario",
        )
        db_session.add(c)
        await db_session.flush()
        db_session.expunge_all()
        from sqlalchemy import select
        result = await db_session.execute(
            select(ComentarioTarea).where(ComentarioTarea.id == c.id)
        )
        loaded = result.scalar_one()
        assert loaded.tarea.id == tarea.id
        assert loaded.autor.id == seed_data["asignado_id"]


class TestStateMachine:
    def test_valid_transitions(self):
        assert VALID_TRANSITIONS_TAREA == {
            "Pendiente": {"En progreso", "Cancelada"},
            "En progreso": {"Resuelta", "Cancelada"},
        }

    def test_transition_pendiente_to_en_progreso(self):
        validar_transicion_tarea("Pendiente", "En progreso")

    def test_transition_pendiente_to_cancelada(self):
        validar_transicion_tarea("Pendiente", "Cancelada")

    def test_transition_en_progreso_to_resuelta(self):
        validar_transicion_tarea("En progreso", "Resuelta")

    def test_transition_terminal_resuelta_raises(self):
        with pytest.raises(ValueError, match="terminal"):
            validar_transicion_tarea("Resuelta", "Pendiente")

    def test_transition_terminal_cancelada_raises(self):
        with pytest.raises(ValueError, match="terminal"):
            validar_transicion_tarea("Cancelada", "Pendiente")

    def test_transition_invalid_skip(self):
        with pytest.raises(ValueError, match="Transición inválida"):
            validar_transicion_tarea("Pendiente", "Resuelta")

    def test_unknown_state_raises(self):
        with pytest.raises(ValueError, match="terminal"):
            validar_transicion_tarea("Inexistente", "Pendiente")
