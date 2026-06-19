"""Tests for Aviso and AcknowledgmentAviso models."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.models.aviso import Aviso
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.user import User


async def _seed_tenant(db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=f"aviso-{uuid.uuid4().hex[:8]}",
        nombre="Test", estado="Activo",
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


async def _seed_materia(db_session, tenant_id):
    materia = Materia(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:4]}", nombre="Test Materia",
    )
    db_session.add(materia)
    await db_session.flush()
    return materia


async def _seed_user(db_session, tenant_id):
    user = User(
        id=str(uuid.uuid4()), tenant_id=tenant_id,
        email="enc", email_hash="h", password_hash="h",
        nombre="T", apellidos="U", dni="e", estado="Activo",
    )
    db_session.add(user)
    await db_session.flush()
    return user


class TestAvisoModel:
    async def test_create_aviso(self, db_session):
        tenant = await _seed_tenant(db_session)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="Global",
            severidad="Info",
            titulo="Test Aviso",
            cuerpo="Cuerpo del aviso",
            inicio_en=ahora - timedelta(hours=1),
            fin_en=ahora + timedelta(hours=1),
            orden=10,
            activo=True,
            requiere_ack=False,
        )
        db_session.add(aviso)
        await db_session.flush()

        assert aviso.id is not None
        assert aviso.titulo == "Test Aviso"
        assert aviso.alcance == "Global"
        assert aviso.severidad == "Info"
        assert aviso.orden == 10
        assert aviso.activo is True
        assert aviso.requiere_ack is False

    async def test_aviso_defaults(self, db_session):
        tenant = await _seed_tenant(db_session)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="Global",
            titulo="Defaults",
            cuerpo="Cuerpo",
            inicio_en=ahora,
            fin_en=ahora + timedelta(hours=1),
        )
        db_session.add(aviso)
        await db_session.flush()

        assert aviso.severidad == "Info"
        assert aviso.orden == 0
        assert aviso.activo is True
        assert aviso.requiere_ack is False

    async def test_aviso_timestamps(self, db_session):
        tenant = await _seed_tenant(db_session)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="Global",
            titulo="Timestamps",
            cuerpo="Cuerpo",
            inicio_en=ahora,
            fin_en=ahora + timedelta(hours=1),
        )
        db_session.add(aviso)
        await db_session.flush()

        assert aviso.created_at is not None
        assert aviso.updated_at is not None

    async def test_aviso_soft_delete(self, db_session):
        tenant = await _seed_tenant(db_session)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="Global",
            titulo="Soft Delete",
            cuerpo="Cuerpo",
            inicio_en=ahora,
            fin_en=ahora + timedelta(hours=1),
        )
        db_session.add(aviso)
        await db_session.flush()

        aviso.deleted_at = datetime.now(UTC)
        await db_session.flush()

        result = await db_session.execute(
            select(Aviso).where(Aviso.id == aviso.id)
        )
        fetched = result.scalar_one()
        assert fetched.deleted_at is not None

    async def test_aviso_materia_relationship(self, db_session):
        tenant = await _seed_tenant(db_session)
        materia = await _seed_materia(db_session, tenant.id)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="PorMateria",
            titulo="Materia Aviso",
            cuerpo="Cuerpo",
            materia_id=materia.id,
            inicio_en=ahora,
            fin_en=ahora + timedelta(hours=1),
        )
        db_session.add(aviso)
        await db_session.flush()

        assert aviso.materia_id == materia.id
        assert aviso.materia is not None
        assert aviso.materia.codigo == materia.codigo

    async def test_create_acknowledgment(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = await _seed_user(db_session, tenant.id)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="Global",
            titulo="Ack Test",
            cuerpo="Cuerpo",
            inicio_en=ahora,
            fin_en=ahora + timedelta(hours=1),
            requiere_ack=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        ack = AcknowledgmentAviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
        )
        db_session.add(ack)
        await db_session.flush()

        assert ack.id is not None
        assert ack.aviso_id == aviso.id
        assert ack.usuario_id == user.id
        assert ack.confirmado_at is not None

    async def test_ack_unique_constraint(self, db_session):
        tenant = await _seed_tenant(db_session)
        user = await _seed_user(db_session, tenant.id)
        ahora = datetime.now(UTC)
        aviso = Aviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            alcance="Global",
            titulo="Unique Ack",
            cuerpo="Cuerpo",
            inicio_en=ahora,
            fin_en=ahora + timedelta(hours=1),
        )
        db_session.add(aviso)
        await db_session.flush()

        ack1 = AcknowledgmentAviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
        )
        db_session.add(ack1)
        await db_session.flush()

        ack2 = AcknowledgmentAviso(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
        )
        db_session.add(ack2)
        with pytest.raises(Exception):
            await db_session.flush()

    async def test_multi_tenant_isolation(self, db_session):
        t1 = await _seed_tenant(db_session)
        t2 = await _seed_tenant(db_session)
        ahora = datetime.now(UTC)
        a1 = Aviso(id=str(uuid.uuid4()), tenant_id=t1.id, alcance="Global", titulo="A1", cuerpo="C", inicio_en=ahora, fin_en=ahora + timedelta(hours=1))
        a2 = Aviso(id=str(uuid.uuid4()), tenant_id=t2.id, alcance="Global", titulo="A2", cuerpo="C", inicio_en=ahora, fin_en=ahora + timedelta(hours=1))
        db_session.add_all([a1, a2])
        await db_session.flush()

        result = await db_session.execute(
            select(Aviso).where(Aviso.tenant_id == t1.id)
        )
        items = list(result.scalars().all())
        assert len(items) == 1
        assert items[0].id == a1.id
