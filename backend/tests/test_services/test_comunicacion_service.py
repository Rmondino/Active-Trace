"""Tests for ComunicacionService."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import Settings
from app.core.crypto import CipherService
from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.audit_log_service import AuditLogService
from app.services.comunicacion_service import (
    ComunicacionService,
    _get_and_validate_preview,
    _preview_store,
    _store_preview,
    validar_transicion,
)


@pytest.fixture
def cipher():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://app_user:dev_password@localhost:5432/activia_trace_test",
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )
    return CipherService(settings)


@pytest.fixture
async def seed_data(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"svc-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo", config={},
    )
    db_session.add(tenant)
    await db_session.flush()
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        email="enc", email_hash="h", password_hash="h",
        nombre="T", apellidos="U", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()
    materia = Materia(
        id=str(uuid.uuid4()), tenant_id=tenant.id,
        codigo="MAT-SVC", nombre="Test Materia",
    )
    db_session.add(materia)
    await db_session.flush()
    return {"tenant_id": tenant.id, "user_id": user.id, "materia_id": materia.id}


class TestValidarTransicion:
    def test_valid_transitions(self):
        validar_transicion("Pendiente", "Enviando")
        validar_transicion("Pendiente", "Cancelado")
        validar_transicion("Enviando", "Enviado")
        validar_transicion("Enviando", "Error")

    def test_invalid_transitions(self):
        with pytest.raises(ValueError):
            validar_transicion("Enviado", "Cancelado")
        with pytest.raises(ValueError):
            validar_transicion("Enviado", "Enviando")
        with pytest.raises(ValueError):
            validar_transicion("Cancelado", "Enviando")
        with pytest.raises(ValueError):
            validar_transicion("Error", "Enviando")


class TestPreviewStore:
    def setup_method(self):
        _preview_store.clear()

    def test_store_and_get(self):
        token = _store_preview({"data": "test"})
        entry = _get_and_validate_preview(token)
        assert entry["data"] == "test"

    def test_single_use(self):
        token = _store_preview({"data": "test"})
        _get_and_validate_preview(token)
        entry = _preview_store[token]
        entry["used"] = True
        with pytest.raises(ValueError, match="ya utilizado"):
            _get_and_validate_preview(token)

    def test_expired(self):
        token = _store_preview({"data": "test"})
        _preview_store[token]["created_at"] = datetime.now(UTC) - timedelta(minutes=31)
        with pytest.raises(ValueError, match="expirado"):
            _get_and_validate_preview(token)

    def test_not_found(self):
        with pytest.raises(ValueError, match="no encontrado"):
            _get_and_validate_preview("nonexistent")


class TestComunicacionService:
    async def test_generar_preview(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        alumnos = [
            {"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"},
            {"id": "a2", "nombre": "María", "apellidos": "Gómez", "comision": "B"},
        ]
        result = await svc.generar_preview(
            materia_id=seed_data["materia_id"],
            asunto_template="Hola {alumno_nombre}",
            cuerpo_template="Querido {alumno_nombre} {alumno_apellidos} de la comisión {comision}",
            alumnos=alumnos,
            tenant_id=seed_data["tenant_id"],
        )

        assert "previews" in result
        assert "preview_token" in result
        assert len(result["previews"]) == 2
        assert result["previews"][0]["asunto"] == "Hola Juan"
        assert result["previews"][0]["cuerpo"] == "Querido Juan Pérez de la comisión A"
        assert result["previews"][1]["asunto"] == "Hola María"
        assert result["previews"][1]["cuerpo"] == "Querido María Gómez de la comisión B"

    async def test_encolar_creates_records(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        alumnos = [{"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"}]
        preview = await svc.generar_preview(
            materia_id=seed_data["materia_id"],
            asunto_template="Hola {alumno_nombre}",
            cuerpo_template="Cuerpo {alumno_nombre}",
            alumnos=alumnos,
            tenant_id=seed_data["tenant_id"],
        )

        destinatarios = [
            {"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"},
            {"email": "maria@test.com", "nombre": "María", "apellidos": "Gómez"},
        ]
        result = await svc.encolar(
            materia_id=seed_data["materia_id"],
            asunto="Hola Juan",
            cuerpo="Cuerpo Juan",
            destinatarios=destinatarios,
            user_id=seed_data["user_id"],
            tenant_id=seed_data["tenant_id"],
            preview_token=preview["preview_token"],
        )

        assert result["total"] == 2
        assert result["lote_id"] is not None
        assert result["requiere_aprobacion"] is False

        mensajes = await repo.get_by_lote(result["lote_id"])
        assert len(mensajes) == 2
        for msg in mensajes:
            assert msg.estado == "Pendiente"
            assert msg.materia_id == seed_data["materia_id"]
            assert msg.asunto == "Hola Juan"

    async def test_encolar_without_preview_raises(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        with pytest.raises(ValueError, match="Preview requerido"):
            await svc.encolar(
                materia_id=seed_data["materia_id"],
                asunto="Test",
                cuerpo="Test",
                destinatarios=[{"email": "a@b.com", "nombre": "A", "apellidos": "B"}],
                user_id=seed_data["user_id"],
                tenant_id=seed_data["tenant_id"],
                preview_token=None,
            )

    async def test_encolar_encrypts_email(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        alumnos = [{"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"}]
        preview = await svc.generar_preview(
            materia_id=seed_data["materia_id"],
            asunto_template="Hola",
            cuerpo_template="Cuerpo",
            alumnos=alumnos,
            tenant_id=seed_data["tenant_id"],
        )

        await svc.encolar(
            materia_id=seed_data["materia_id"],
            asunto="Hola",
            cuerpo="Cuerpo",
            destinatarios=[{"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"}],
            user_id=seed_data["user_id"],
            tenant_id=seed_data["tenant_id"],
            preview_token=preview["preview_token"],
        )

        from sqlalchemy import select
        result = await db_session.execute(select(Comunicacion))
        com = result.scalar_one()
        decrypted = cipher.decrypt(com.destinatario)
        assert decrypted == "juan@test.com"
        assert com.destinatario != "juan@test.com"

    async def test_encolar_creates_audit_log(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        alumnos = [{"id": "a1", "nombre": "Juan", "apellidos": "Pérez", "comision": "A"}]
        preview = await svc.generar_preview(
            materia_id=seed_data["materia_id"],
            asunto_template="Hola",
            cuerpo_template="Cuerpo",
            alumnos=alumnos,
            tenant_id=seed_data["tenant_id"],
        )

        await svc.encolar(
            materia_id=seed_data["materia_id"],
            asunto="Hola",
            cuerpo="Cuerpo",
            destinatarios=[{"email": "juan@test.com", "nombre": "Juan", "apellidos": "Pérez"}],
            user_id=seed_data["user_id"],
            tenant_id=seed_data["tenant_id"],
            preview_token=preview["preview_token"],
        )

        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.accion == "COMUNICACION_ENVIAR")
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.actor_id == seed_data["user_id"]

    async def test_aprobar_lote(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        lote = str(uuid.uuid4())
        coms = [
            Comunicacion(
                id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
                enviado_por=seed_data["user_id"], materia_id=seed_data["materia_id"],
                destinatario="enc", asunto="A", cuerpo="C", lote_id=lote,
            )
            for _ in range(3)
        ]
        db_session.add_all(coms)
        await db_session.flush()

        result = await svc.aprobar_lote(lote, seed_data["user_id"], seed_data["tenant_id"])
        assert result["aprobados"] == 3

        mensajes = await repo.get_by_lote(lote)
        for msg in mensajes:
            assert msg.aprobado_por == seed_data["user_id"]
            assert msg.aprobado_at is not None

    async def test_aprobar_individual(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            enviado_por=seed_data["user_id"], materia_id=seed_data["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C", lote_id=str(uuid.uuid4()),
        )
        db_session.add(com)
        await db_session.flush()

        result = await svc.aprobar(com.id, seed_data["user_id"], seed_data["tenant_id"])
        assert result["estado"] == "Pendiente"

        msg = await repo.get(com.id)
        assert msg is not None
        assert msg.aprobado_por == seed_data["user_id"]

    async def test_rechazar(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            enviado_por=seed_data["user_id"], materia_id=seed_data["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C", lote_id=str(uuid.uuid4()),
        )
        db_session.add(com)
        await db_session.flush()

        result = await svc.rechazar(com.id, seed_data["tenant_id"], user_id=seed_data["user_id"])
        assert result["estado"] == "Cancelado"

        msg = await repo.get(com.id)
        assert msg is not None
        assert msg.estado == "Cancelado"

    async def test_cannot_reject_enviado(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        com = Comunicacion(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            enviado_por=seed_data["user_id"], materia_id=seed_data["materia_id"],
            destinatario="enc", asunto="A", cuerpo="C",
            lote_id=str(uuid.uuid4()), estado="Enviado",
        )
        db_session.add(com)
        await db_session.flush()

        with pytest.raises(ValueError, match="Estado terminal"):
            await svc.rechazar(com.id, seed_data["tenant_id"])

    async def test_tracking(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        coms = [
            Comunicacion(
                id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
                enviado_por=seed_data["user_id"], materia_id=seed_data["materia_id"],
                destinatario="enc", asunto=f"A{i}", cuerpo="C",
                lote_id=str(uuid.uuid4()),
            )
            for i in range(3)
        ]
        db_session.add_all(coms)
        await db_session.flush()

        track = await svc.tracking(seed_data["materia_id"], seed_data["tenant_id"])
        assert len(track) == 3
        for t in track:
            assert "estado" in t
            assert "asunto" in t
            assert "lote_id" in t

    async def test_pendientes_aprobacion(self, db_session, seed_data, cipher):
        repo = ComunicacionRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        materia_repo = MateriaRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        tenant_repo = TenantRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        audit = AuditLogService(db_session)
        svc = ComunicacionService(repo, materia_repo, tenant_repo, cipher, audit)

        lote = str(uuid.uuid4())
        coms = [
            Comunicacion(
                id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
                enviado_por=seed_data["user_id"], materia_id=seed_data["materia_id"],
                destinatario="enc", asunto="A", cuerpo="C",
                lote_id=lote, estado="Pendiente",
            )
            for _ in range(2)
        ]
        db_session.add_all(coms)
        await db_session.flush()

        pendientes = await svc.get_pendientes_aprobacion(seed_data["tenant_id"])
        assert len(pendientes) >= 1
