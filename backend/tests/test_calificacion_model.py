"""Tests for Calificacion and UmbralMateria models."""

import uuid
from decimal import Decimal

from sqlalchemy import select

from app.models.calificacion import Calificacion
from app.models.umbral_materia import UmbralMateria
from app.models.tenant import Tenant


async def _seed_tenant(db_session):
    tenant = Tenant(id=str(uuid.uuid4()), slug="test-cal", nombre="Test", estado="Activo")
    db_session.add(tenant)
    await db_session.flush()
    return tenant


class TestCalificacionModel:
    async def _seed_base(self, db_session):
        tenant = await _seed_tenant(db_session)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-CAL", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        return tenant, materia

    async def test_create_calificacion_numerica(self, db_session):
        tenant, materia = await self._seed_base(db_session)
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, actividad="Parcial 1",
            nota_numerica=Decimal("75.00"), origen="Importado",
            aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await db_session.execute(select(Calificacion).where(Calificacion.id == cal.id))
        fetched = result.scalar_one()
        assert fetched.id == cal.id
        assert fetched.materia_id == materia.id
        assert fetched.actividad == "Parcial 1"
        assert fetched.nota_numerica == Decimal("75.00")
        assert fetched.aprobado is True
        assert fetched.origen == "Importado"

    async def test_create_calificacion_textual(self, db_session):
        tenant, materia = await self._seed_base(db_session)
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, actividad="TP Grupal",
            nota_textual="Satisfactorio", origen="Importado",
            aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await db_session.execute(select(Calificacion).where(Calificacion.id == cal.id))
        fetched = result.scalar_one()
        assert fetched.nota_textual == "Satisfactorio"
        assert fetched.nota_numerica is None
        assert fetched.aprobado is True

    async def test_create_calificacion_sin_nota(self, db_session):
        tenant, materia = await self._seed_base(db_session)
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, actividad="TP No entregado",
            origen="Importado", aprobado=False,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await db_session.execute(select(Calificacion).where(Calificacion.id == cal.id))
        fetched = result.scalar_one()
        assert fetched.nota_numerica is None
        assert fetched.nota_textual is None
        assert fetched.aprobado is False

    async def test_calificacion_con_entrada_padron(self, db_session):
        tenant, materia = await self._seed_base(db_session)
        from app.models.version_padron import VersionPadron
        from app.models.entrada_padron import EntradaPadron
        from app.models.cohorte import Cohorte
        from app.models.carrera import Carrera
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        from app.models.user import User
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="e@t.com", email_hash="h", password_hash="p", nombre="U", apellidos="T", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=1,
        )
        db_session.add(vp)
        await db_session.flush()
        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            version_id=vp.id, nombre="Juan", apellidos="Perez",
            email="enc_email",
        )
        db_session.add(ep)
        await db_session.flush()

        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep.id, materia_id=materia.id,
            actividad="Parcial", nota_numerica=Decimal("80"),
            origen="Importado", aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await db_session.execute(select(Calificacion).where(Calificacion.id == cal.id))
        fetched = result.scalar_one()
        assert fetched.entrada_padron_id == ep.id

    async def test_calificacion_entrada_padron_nullable(self, db_session):
        tenant, materia = await self._seed_base(db_session)
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=None, materia_id=materia.id,
            actividad="Manual", nota_textual="Aprobado",
            origen="Manual", aprobado=True,
        )
        db_session.add(cal)
        await db_session.flush()

        result = await db_session.execute(select(Calificacion).where(Calificacion.id == cal.id))
        fetched = result.scalar_one()
        assert fetched.entrada_padron_id is None
        assert fetched.origen == "Manual"

    async def test_calificacion_soft_delete(self, db_session):
        from datetime import UTC, datetime
        tenant, materia = await self._seed_base(db_session)
        cal = Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, actividad="Test", origen="Importado",
            aprobado=False,
        )
        db_session.add(cal)
        await db_session.flush()

        cal.deleted_at = datetime.now(UTC)
        await db_session.flush()

        result = await db_session.execute(
            select(Calificacion).where(Calificacion.id == cal.id, Calificacion.deleted_at.is_(None))
        )
        assert result.scalar_one_or_none() is None

    async def test_calificacion_unique_constraint(self, db_session):
        tenant, materia = await self._seed_base(db_session)
        from app.models.entrada_padron import EntradaPadron
        from app.models.version_padron import VersionPadron
        from app.models.user import User
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR2", nombre="T2")
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id, nombre="2026", anio=2026, vig_desde="2026-01-01")
        db_session.add(cohorte)
        await db_session.flush()
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="e2@t.com", email_hash="h2", password_hash="p", nombre="U2", apellidos="T2", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()
        vp = VersionPadron(id=str(uuid.uuid4()), tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, cargado_por=user.id, origen="manual", total_filas=1)
        db_session.add(vp)
        await db_session.flush()
        ep = EntradaPadron(id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id, nombre="A", apellidos="B", email="e@t.com")
        db_session.add(ep)
        await db_session.flush()

        cal1 = Calificacion(id=str(uuid.uuid4()), tenant_id=tenant.id, entrada_padron_id=ep.id, materia_id=materia.id, actividad="TP1", nota_numerica=Decimal("70"), origen="Importado", aprobado=True)
        db_session.add(cal1)
        await db_session.flush()

        import pytest
        cal2 = Calificacion(id=str(uuid.uuid4()), tenant_id=tenant.id, entrada_padron_id=ep.id, materia_id=materia.id, actividad="TP1", nota_numerica=Decimal("80"), origen="Importado", aprobado=True)
        db_session.add(cal2)
        with pytest.raises(Exception):
            await db_session.flush()


class TestUmbralMateriaModel:
    async def _seed_base(self, db_session):
        tenant = await _seed_tenant(db_session)
        from app.models.materia import Materia
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-UMB", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        from app.models.user import User
        user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="u@t.com", email_hash="h", password_hash="p", nombre="U", apellidos="T", dni="e", estado="Activo")
        db_session.add(user)
        await db_session.flush()
        return tenant, materia, user

    async def _make_asig(self, db_session, tenant, user):
        from app.models.asignacion import Asignacion
        from datetime import date
        asig = Asignacion(id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id, rol="PROFESOR", desde=date(2020, 1, 1))
        db_session.add(asig)
        await db_session.flush()
        return asig

    async def test_create_umbral_materia(self, db_session):
        tenant, materia, user = await self._seed_base(db_session)
        asig = await self._make_asig(db_session, tenant, user)

        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asig.id, materia_id=materia.id,
            umbral_pct=75, valores_aprobatorios=["Aprobado", "Muy bueno"],
        )
        db_session.add(umbral)
        await db_session.flush()

        result = await db_session.execute(select(UmbralMateria).where(UmbralMateria.id == umbral.id))
        fetched = result.scalar_one()
        assert fetched.asignacion_id == asig.id
        assert fetched.materia_id == materia.id
        assert fetched.umbral_pct == 75
        assert fetched.valores_aprobatorios == ["Aprobado", "Muy bueno"]

    async def test_umbral_default_values(self, db_session):
        tenant, materia, user = await self._seed_base(db_session)
        asig = await self._make_asig(db_session, tenant, user)

        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asig.id, materia_id=materia.id,
        )
        db_session.add(umbral)
        await db_session.flush()

        assert umbral.umbral_pct == 60
        assert umbral.valores_aprobatorios == ["Satisfactorio", "Supera lo esperado"]

    async def test_umbral_soft_delete(self, db_session):
        from datetime import UTC, datetime
        tenant, materia, user = await self._seed_base(db_session)
        asig = await self._make_asig(db_session, tenant, user)

        umbral = UmbralMateria(id=str(uuid.uuid4()), tenant_id=tenant.id, asignacion_id=asig.id, materia_id=materia.id)
        db_session.add(umbral)
        await db_session.flush()

        umbral.deleted_at = datetime.now(UTC)
        await db_session.flush()

        result = await db_session.execute(
            select(UmbralMateria).where(UmbralMateria.id == umbral.id, UmbralMateria.deleted_at.is_(None))
        )
        assert result.scalar_one_or_none() is None

    async def test_umbral_unique_constraint(self, db_session):
        tenant, materia, user = await self._seed_base(db_session)
        import pytest
        asig = await self._make_asig(db_session, tenant, user)

        u1 = UmbralMateria(id=str(uuid.uuid4()), tenant_id=tenant.id, asignacion_id=asig.id, materia_id=materia.id, umbral_pct=60)
        db_session.add(u1)
        await db_session.flush()

        u2 = UmbralMateria(id=str(uuid.uuid4()), tenant_id=tenant.id, asignacion_id=asig.id, materia_id=materia.id, umbral_pct=70)
        db_session.add(u2)
        with pytest.raises(Exception):
            await db_session.flush()
