"""Tests for SlotEncuentro, InstanciaEncuentro, Guardia models."""

import uuid
from datetime import UTC, date, datetime

import pytest

from app.models.asignacion import Asignacion
from app.models.guardia import Guardia
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.materia import Materia
from app.models.slot_encuentro import SlotEncuentro
from app.models.tenant import Tenant
from app.models.user import User


class TestSlotEncuentroModel:
    async def _seed(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        user = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email="e", email_hash="h", password_hash="h",
            nombre="T", apellidos="U", dni="e", estado="Activo",
        )
        db_session.add(user)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-SLOT", nombre="Slot Test")
        db_session.add(materia)
        await db_session.flush()
        asignacion = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            usuario_id=user.id, rol="PROFESOR",
            materia_id=materia.id, desde=date(2026, 1, 1),
        )
        db_session.add(asignacion)
        await db_session.flush()
        return tenant, materia, asignacion

    async def test_create_slot(self, db_session):
        tenant, materia, asignacion = await self._seed(db_session)
        slot = SlotEncuentro(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            asignacion_id=asignacion.id,
            materia_id=materia.id,
            titulo="Clase 1",
            hora="18:00",
            dia_semana="Lunes",
            fecha_inicio=date(2026, 1, 5),
            cant_semanas=4,
            meet_url="https://meet.example.com",
            vig_desde=date(2026, 1, 1),
            vig_hasta=date(2026, 3, 1),
        )
        db_session.add(slot)
        await db_session.flush()

        assert slot.id is not None
        assert slot.titulo == "Clase 1"
        assert slot.cant_semanas == 4
        assert slot.dia_semana == "Lunes"

    async def test_slot_soft_delete(self, db_session):
        tenant, materia, asignacion = await self._seed(db_session)
        slot = SlotEncuentro(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asignacion.id, materia_id=materia.id,
            titulo="T", hora="18:00",
            vig_desde=date(2026, 1, 1), vig_hasta=date(2026, 3, 1),
        )
        db_session.add(slot)
        await db_session.flush()

        slot.deleted_at = datetime.now(UTC)
        await db_session.flush()

        from sqlalchemy import select
        result = await db_session.execute(
            select(SlotEncuentro).where(SlotEncuentro.id == slot.id)
        )
        fetched = result.scalar_one()
        assert fetched.deleted_at is not None


class TestInstanciaEncuentroModel:
    async def test_create_instancia(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-INST", nombre="Inst Test")
        db_session.add(materia)
        await db_session.flush()

        inst = InstanciaEncuentro(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            materia_id=materia.id,
            fecha=date(2026, 1, 5),
            hora="18:00",
            titulo="Clase 1",
        )
        db_session.add(inst)
        await db_session.flush()

        assert inst.id is not None
        assert inst.estado == "Programado"
        assert inst.fecha == date(2026, 1, 5)

    async def test_instancia_default_estado(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-INST2", nombre="Inst2")
        db_session.add(materia)
        await db_session.flush()

        inst = InstanciaEncuentro(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, fecha=date(2026, 1, 5),
            hora="18:00", titulo="C",
        )
        db_session.add(inst)
        await db_session.flush()
        assert inst.estado == "Programado"


class TestGuardiaModel:
    async def _seed(self, db_session):
        tenant = Tenant(id=str(uuid.uuid4()), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T", estado="Activo")
        db_session.add(tenant)
        await db_session.flush()
        user = User(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            email="e", email_hash="h", password_hash="h",
            nombre="T", apellidos="U", dni="e", estado="Activo",
        )
        db_session.add(user)
        await db_session.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-GUA", nombre="Guardia Test")
        db_session.add(materia)
        await db_session.flush()
        asignacion = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            usuario_id=user.id, rol="PROFESOR",
            materia_id=materia.id, desde=date(2026, 1, 1),
        )
        db_session.add(asignacion)
        await db_session.flush()
        return tenant, materia, asignacion

    async def test_create_guardia(self, db_session):
        tenant, materia, asignacion = await self._seed(db_session)
        guardia = Guardia(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            asignacion_id=asignacion.id,
            materia_id=materia.id,
            dia="Lunes",
            horario="14:00-14:45",
        )
        db_session.add(guardia)
        await db_session.flush()

        assert guardia.id is not None
        assert guardia.estado == "Pendiente"
        assert guardia.dia == "Lunes"

    async def test_guardia_default_estado(self, db_session):
        tenant, materia, asignacion = await self._seed(db_session)
        g = Guardia(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asignacion.id, materia_id=materia.id,
            dia="Martes", horario="15:00-15:45",
        )
        db_session.add(g)
        await db_session.flush()
        assert g.estado == "Pendiente"
