"""Tests for TareaService."""

import uuid

import pytest

from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.tarea_repository import TareaRepository
from app.repositories.comentario_repository import ComentarioRepository
from app.services.tarea_service import TareaService


@pytest.fixture
async def seed_data(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"ts-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    admin = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc_admin", email_hash="h_adm", password_hash="h",
        nombre="Admin", apellidos="User", dni="e_adm", estado="Activo",
    )
    asignado = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc_asig", email_hash="h_asig", password_hash="h",
        nombre="Asignado", apellidos="User", dni="e_asig", estado="Activo",
    )
    otro = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc_otro", email_hash="h_otro", password_hash="h",
        nombre="Otro", apellidos="User", dni="e_otro", estado="Activo",
    )
    db_session.add_all([admin, asignado, otro])
    await db_session.flush()
    return {
        "tenant_id": tenant.id,
        "admin_id": admin.id,
        "asignado_id": asignado.id,
        "otro_id": otro.id,
    }


class TestTareaService:
    @pytest.fixture
    def _service(self, db_session, seed_data):
        tarea_repo = TareaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        comentario_repo = ComentarioRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        return TareaService(
            tarea_repo=tarea_repo,
            comentario_repo=comentario_repo,
            session=db_session,
        )

    async def test_crear_tarea(self, db_session, seed_data, _service):
        tarea = await _service.crear(
            data={"asignado_a": seed_data["asignado_id"], "descripcion": "Completar tarea"},
            user_id=seed_data["admin_id"],
            tenant_id=seed_data["tenant_id"],
        )
        assert tarea.id is not None
        assert tarea.estado == "Pendiente"
        assert tarea.asignado_a == seed_data["asignado_id"]
        assert tarea.asignado_por == seed_data["admin_id"]
        assert tarea.descripcion == "Completar tarea"

    async def test_mis_tareas_returns_only_own(self, db_session, seed_data, _service):
        await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Tarea 1"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        await _service.crear(
            {"asignado_a": seed_data["otro_id"], "descripcion": "Tarea 2"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        mis_tareas = await _service.mis_tareas(
            seed_data["asignado_id"], seed_data["tenant_id"],
        )
        assert len(mis_tareas) == 1
        assert mis_tareas[0]["descripcion"] == "Tarea 1"

    async def test_mis_tareas_filter_by_estado(self, db_session, seed_data, _service):
        t1 = await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Pendiente"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "En progreso"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        await _service.cambiar_estado(t1.id, "En progreso", seed_data["admin_id"], seed_data["tenant_id"])
        await _service.cambiar_estado(t1.id, "Resuelta", seed_data["admin_id"], seed_data["tenant_id"])

        filtro_resueltas = await _service.mis_tareas(
            seed_data["asignado_id"], seed_data["tenant_id"], estado="Resuelta",
        )
        assert len(filtro_resueltas) == 1
        assert filtro_resueltas[0]["estado"] == "Resuelta"

    async def test_listar_todas(self, db_session, seed_data, _service):
        await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Admin view 1"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        await _service.crear(
            {"asignado_a": seed_data["otro_id"], "descripcion": "Admin view 2"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        todas = await _service.listar_todas(seed_data["tenant_id"], {})
        assert len(todas) == 2

    async def test_cambiar_estado_valido(self, db_session, seed_data, _service):
        tarea = await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "State change"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        updated = await _service.cambiar_estado(
            tarea.id, "En progreso", seed_data["admin_id"], seed_data["tenant_id"],
        )
        assert updated.estado == "En progreso"

    async def test_cambiar_estado_full_chain(self, db_session, seed_data, _service):
        tarea = await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Full chain"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        t1 = await _service.cambiar_estado(tarea.id, "En progreso", seed_data["admin_id"], seed_data["tenant_id"])
        assert t1.estado == "En progreso"
        t2 = await _service.cambiar_estado(tarea.id, "Resuelta", seed_data["admin_id"], seed_data["tenant_id"])
        assert t2.estado == "Resuelta"

    async def test_cambiar_estado_invalido_raises(self, db_session, seed_data, _service):
        tarea = await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Invalid"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        with pytest.raises(ValueError, match="Transición inválida"):
            await _service.cambiar_estado(
                tarea.id, "Resuelta", seed_data["admin_id"], seed_data["tenant_id"],
            )

    async def test_agregar_comentario(self, db_session, seed_data, _service):
        tarea = await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Comentario test"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        comentario = await _service.agregar_comentario(
            tarea_id=tarea.id,
            texto="Mi primer comentario",
            autor_id=seed_data["asignado_id"],
            tenant_id=seed_data["tenant_id"],
        )
        assert comentario.id is not None
        assert comentario.texto == "Mi primer comentario"
        assert comentario.tarea_id == tarea.id

    async def test_detalle_incluye_comentarios(self, db_session, seed_data, _service):
        tarea = await _service.crear(
            {"asignado_a": seed_data["asignado_id"], "descripcion": "Detalle test"},
            seed_data["admin_id"], seed_data["tenant_id"],
        )
        await _service.agregar_comentario(tarea.id, "Comentario 1", seed_data["asignado_id"], seed_data["tenant_id"])
        await _service.agregar_comentario(tarea.id, "Comentario 2", seed_data["admin_id"], seed_data["tenant_id"])
        detalle = await _service.detalle(tarea.id, seed_data["tenant_id"])
        assert detalle["id"] == tarea.id
        assert len(detalle["comentarios"]) == 2
        assert detalle["comentarios"][0]["texto"] == "Comentario 1"

    async def test_multi_tenant_isolation(self, db_session, seed_data, _service):
        tenant2 = Tenant(
            id=str(uuid.uuid4()), slug=f"ts2-{uuid.uuid4().hex[:8]}",
            nombre="Tenant2", estado="Activo",
        )
        db_session.add(tenant2)
        await db_session.flush()
        user_t2 = User(
            id=str(uuid.uuid4()), tenant_id=tenant2.id,
            email="enc_t2", email_hash="h_t2", password_hash="h",
            nombre="T2", apellidos="U", dni="e_t2", estado="Activo",
        )
        db_session.add(user_t2)
        await db_session.flush()

        tarea_repo_t2 = TareaRepository(session=db_session, tenant_id=tenant2.id)
        comentario_repo_t2 = ComentarioRepository(session=db_session, tenant_id=tenant2.id)
        svc_t2 = TareaService(tarea_repo_t2, comentario_repo_t2, db_session)

        await svc_t2.crear(
            {"asignado_a": user_t2.id, "descripcion": "T2 task"},
            user_t2.id, tenant2.id,
        )
        t1_count = await _service.listar_todas(seed_data["tenant_id"], {})
        assert len(t1_count) == 0
