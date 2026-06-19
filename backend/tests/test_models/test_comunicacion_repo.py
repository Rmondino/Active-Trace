"""Tests for ComunicacionRepository."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.comunicacion import Comunicacion
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.comunicacion_repository import ComunicacionRepository


@pytest.fixture
async def seed_data(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug=f"repo-{uuid.uuid4().hex[:8]}", nombre="Test", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc", email_hash="h", password_hash="h",
        nombre="T", apellidos="U", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()
    materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-REPO", nombre="Test")
    db_session.add(materia)
    await db_session.flush()
    return {"tenant_id": tenant.id, "user_id": user.id, "materia_id": materia.id}


def _make_com(tenant_id, user_id, materia_id, lote_id=None, **kw):
    return Comunicacion(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        enviado_por=user_id,
        materia_id=materia_id,
        destinatario="enc@test.com",
        asunto="Asunto",
        cuerpo="Cuerpo",
        lote_id=lote_id or str(uuid.uuid4()),
        **kw,
    )


class TestComunicacionRepository:
    async def test_create_and_get(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        com = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
        db_session.add(com)
        await db_session.flush()

        fetched = await repo.get(com.id)
        assert fetched is not None
        assert fetched.estado == "Pendiente"
        assert fetched.asunto == "Asunto"

    async def test_get_returns_none_for_wrong_tenant(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        com = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
        db_session.add(com)
        await db_session.flush()

        other_repo = ComunicacionRepository(session=db_session, tenant_id=str(uuid.uuid4()))
        fetched = await other_repo.get(com.id)
        assert fetched is None

    async def test_bulk_create(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        lote = str(uuid.uuid4())
        coms = [
            _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"], lote_id=lote)
            for _ in range(3)
        ]
        await repo.bulk_create(coms)

        got = await repo.get_by_lote(lote)
        assert len(got) == 3

    async def test_get_by_lote(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        lote = str(uuid.uuid4())
        c1 = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"], lote_id=lote)
        c2 = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"], lote_id=lote)
        db_session.add_all([c1, c2])
        await db_session.flush()

        got = await repo.get_by_lote(lote)
        assert len(got) == 2

    async def test_get_by_materia(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        coms = [
            _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
            for _ in range(2)
        ]
        db_session.add_all(coms)
        await db_session.flush()

        got = await repo.get_by_materia(seed_data["materia_id"])
        assert len(got) == 2

    async def test_get_pendientes_aprobacion(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        lote = str(uuid.uuid4())
        pendiente = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                              lote_id=lote, estado="Pendiente")
        aprobado = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                             lote_id=lote, estado="Pendiente", aprobado_por=seed_data["user_id"],
                             aprobado_at=datetime.now(UTC))
        enviado = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                            lote_id=lote, estado="Enviado")
        db_session.add_all([pendiente, aprobado, enviado])
        await db_session.flush()

        got = await repo.get_pendientes_aprobacion()
        assert len(got) == 1
        assert got[0].id == pendiente.id

    async def test_get_pendientes_envio_returns_approved(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        lote = str(uuid.uuid4())
        approved = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                             lote_id=lote, estado="Pendiente", aprobado_por=seed_data["user_id"],
                             aprobado_at=datetime.now(UTC))
        db_session.add(approved)
        await db_session.flush()

        got = await repo.get_pendientes_envio(limit=20)
        assert len(got) >= 1

    async def test_actualizar_estado(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        com = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
        db_session.add(com)
        await db_session.flush()

        updated = await repo.actualizar_estado(com.id, "Enviando")
        assert updated is not None
        assert updated.estado == "Enviando"

    async def test_actualizar_estado_with_kwargs(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        com = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
        db_session.add(com)
        await db_session.flush()

        updated = await repo.actualizar_estado(com.id, "Error", error_msg="SMTP fail")
        assert updated is not None
        assert updated.estado == "Error"
        assert updated.error_msg == "SMTP fail"

    async def test_actualizar_estado_not_found(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        result = await repo.actualizar_estado(str(uuid.uuid4()), "Enviando")
        assert result is None

    async def test_count_by_lote(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        lote = str(uuid.uuid4())
        c1 = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                       lote_id=lote, estado="Pendiente")
        c2 = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                       lote_id=lote, estado="Pendiente")
        c3 = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"],
                       lote_id=lote, estado="Enviado")
        db_session.add_all([c1, c2, c3])
        await db_session.flush()

        counts = await repo.count_by_lote(lote)
        assert counts.get("Pendiente") == 2
        assert counts.get("Enviado") == 1

    async def test_soft_delete_repo(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        com = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
        db_session.add(com)
        await db_session.flush()

        deleted = await repo.soft_delete(com.id)
        assert deleted is True
        fetched = await repo.get(com.id)
        assert fetched is None

    async def test_multi_tenant_isolation(self, db_session, seed_data):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        com = _make_com(seed_data["tenant_id"], seed_data["user_id"], seed_data["materia_id"])
        db_session.add(com)
        await db_session.flush()

        other_repo = ComunicacionRepository(session=db_session, tenant_id=str(uuid.uuid4()))
        got = await other_repo.get(com.id)
        assert got is None
