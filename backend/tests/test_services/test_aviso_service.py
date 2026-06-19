"""Tests for AvisoService."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models.asignacion import Asignacion
from app.models.aviso import Aviso
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.aviso_repository import AvisoRepository
from app.repositories.ack_repository import AckRepository
from app.services.aviso_service import AvisoService


@pytest.fixture
async def seed_data(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()), slug=f"svc-av-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
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
        codigo=f"MAT-{uuid.uuid4().hex[:4]}", nombre="Test Materia",
    )
    db_session.add(materia)
    await db_session.flush()
    return {"tenant_id": tenant.id, "user_id": user.id, "materia_id": materia.id}


def _ahora():
    return datetime.now(UTC)


class TestAvisoService:
    async def _service(self, db_session, tenant_id):
        aviso_repo = AvisoRepository(session=db_session, tenant_id=tenant_id)
        ack_repo = AckRepository(session=db_session, tenant_id=tenant_id)
        return AvisoService(aviso_repo=aviso_repo, ack_repo=ack_repo, session=db_session)

    async def test_crear_aviso(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        data = {
            "alcance": "Global",
            "severidad": "Info",
            "titulo": "Nuevo Aviso",
            "cuerpo": "Contenido del aviso",
            "inicio_en": ahora,
            "fin_en": ahora + timedelta(hours=2),
            "orden": 5,
            "requiere_ack": False,
        }
        aviso = await svc.crear(data, seed_data["tenant_id"])
        assert aviso.id is not None
        assert aviso.titulo == "Nuevo Aviso"
        assert aviso.orden == 5

    async def test_listar_visibles_global(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        data = {
            "alcance": "Global",
            "titulo": "Global Aviso",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
            "orden": 1,
        }
        await svc.crear(data, seed_data["tenant_id"])

        result = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"], roles=[], asignaciones=[],
        )
        assert len(result) == 1
        assert result[0]["titulo"] == "Global Aviso"

    async def test_listar_visibles_por_materia(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        data = {
            "alcance": "PorMateria",
            "materia_id": seed_data["materia_id"],
            "titulo": "Materia Aviso",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
            "orden": 1,
        }
        await svc.crear(data, seed_data["tenant_id"])

        # Without asignacion → not visible
        result1 = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"], roles=[], asignaciones=[],
        )
        assert len(result1) == 0

        # With matching asignacion → visible
        from datetime import date
        asig = Asignacion(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            usuario_id=seed_data["user_id"], rol="PROFESOR",
            materia_id=seed_data["materia_id"],
            desde=date(2020, 1, 1),
        )
        db_session.add(asig)
        await db_session.flush()

        result2 = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"],
            roles=["profesor"], asignaciones=[asig],
        )
        assert len(result2) == 1
        assert result2[0]["titulo"] == "Materia Aviso"

    async def test_listar_visibles_por_rol(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        data = {
            "alcance": "PorRol",
            "rol_destino": "coordinador",
            "titulo": "Rol Aviso",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
            "orden": 1,
        }
        await svc.crear(data, seed_data["tenant_id"])

        # Without role → not visible
        result1 = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"],
            roles=["profesor"], asignaciones=[],
        )
        assert len(result1) == 0

        # With matching role → visible
        result2 = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"],
            roles=["profesor", "coordinador"], asignaciones=[],
        )
        assert len(result2) == 1
        assert result2[0]["titulo"] == "Rol Aviso"

    async def test_listar_visibles_fuera_vigencia(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        # Aviso that expired 1 hour ago
        data = {
            "alcance": "Global",
            "titulo": "Expired Aviso",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=3),
            "fin_en": ahora - timedelta(hours=1),
            "orden": 1,
        }
        await svc.crear(data, seed_data["tenant_id"])

        result = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"], roles=[], asignaciones=[],
        )
        assert len(result) == 0

    async def test_listar_visibles_orden_desc(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        for orden in [10, 30, 20]:
            await svc.crear({
                "alcance": "Global",
                "titulo": f"Aviso-{orden}",
                "cuerpo": "Cuerpo",
                "inicio_en": ahora - timedelta(hours=1),
                "fin_en": ahora + timedelta(hours=1),
                "orden": orden,
            }, seed_data["tenant_id"])

        result = await svc.listar_visibles(
            seed_data["user_id"], seed_data["tenant_id"], roles=[], asignaciones=[],
        )
        assert len(result) == 3
        ordenes = [r["orden"] for r in result]
        assert ordenes == [30, 20, 10]

    async def test_ack_creates_record(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        aviso = await svc.crear({
            "alcance": "Global",
            "titulo": "Ack Test",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
        }, seed_data["tenant_id"])

        ack = await svc.ack(aviso.id, seed_data["user_id"], seed_data["tenant_id"])
        assert ack is not None
        assert ack.aviso_id == aviso.id
        assert ack.usuario_id == seed_data["user_id"]

    async def test_ack_duplicate_raises(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        aviso = await svc.crear({
            "alcance": "Global",
            "titulo": "Dup Ack",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
        }, seed_data["tenant_id"])

        await svc.ack(aviso.id, seed_data["user_id"], seed_data["tenant_id"])
        with pytest.raises(ValueError, match="Ya has acusado"):
            await svc.ack(aviso.id, seed_data["user_id"], seed_data["tenant_id"])

    async def test_stats(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        aviso = await svc.crear({
            "alcance": "Global",
            "titulo": "Stats Test",
            "cuerpo": "Cuerpo",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
        }, seed_data["tenant_id"])

        # Two users ack
        user2 = User(
            id=str(uuid.uuid4()), tenant_id=seed_data["tenant_id"],
            email="enc2", email_hash="h2", password_hash="h",
            nombre="T2", apellidos="U2", dni="e2", estado="Activo",
        )
        db_session.add(user2)
        await db_session.flush()

        await svc.ack(aviso.id, seed_data["user_id"], seed_data["tenant_id"])
        await svc.ack(aviso.id, user2.id, seed_data["tenant_id"])

        stats = await svc.stats(aviso.id, seed_data["tenant_id"])
        assert stats["total_acks"] == 2

    async def test_actualizar_aviso(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        aviso = await svc.crear({
            "alcance": "Global",
            "titulo": "Original",
            "cuerpo": "Original body",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
        }, seed_data["tenant_id"])

        updated = await svc.actualizar(aviso.id, {"titulo": "Updated"}, seed_data["tenant_id"])
        assert updated is not None
        assert updated.titulo == "Updated"

    async def test_eliminar_aviso(self, db_session, seed_data):
        svc = await self._service(db_session, seed_data["tenant_id"])
        ahora = _ahora()
        aviso = await svc.crear({
            "alcance": "Global",
            "titulo": "To Delete",
            "cuerpo": "Body",
            "inicio_en": ahora - timedelta(hours=1),
            "fin_en": ahora + timedelta(hours=1),
        }, seed_data["tenant_id"])

        await svc.eliminar(aviso.id, seed_data["tenant_id"])

        repo = AvisoRepository(session=db_session, tenant_id=seed_data["tenant_id"])
        fetched = await repo.get(aviso.id)
        assert fetched is None
