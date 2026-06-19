"""Tests for C-18 liquidaciones y honorarios.

Cubre:
    - CRUD salario base
    - CRUD salario plus
    - CRUD materia grupo plus
    - Generar liquidacion (base + plus)
    - Plus con tope (PA-23)
    - Cerrar liquidacion (éxito + error si ya cerrada)
    - Facturas CRUD + abonar
"""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import (
    Factura,
    Liquidacion,
    MateriaGrupoPlus,
    SalarioBase,
    SalarioPlus,
)
from app.models.tenant import Tenant
from app.repositories.liquidacion_repository import (
    FacturaRepository,
    LiquidacionRepository,
)
from app.repositories.salario_repository import (
    MateriaGrupoPlusRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.services.liquidacion_service import LiquidacionService


# ── Helpers ──

async def _create_tenant(db: AsyncSession) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
        estado="Activo",
    )
    db.add(t)
    await db.flush()
    return t


async def _create_user(db, tenant_id, facturador=False, **extra):
    from tests.conftest import create_user
    return await create_user(
        db, tenant_id,
        email=f"user-{uuid.uuid4().hex[:8]}@test.com",
        facturador=facturador,
        **extra,
    )


async def _create_materia(db, tenant_id):
    from app.models.materia import Materia
    m = Materia(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6]}",
        nombre="Materia Test",
        estado="Activa",
    )
    db.add(m)
    await db.flush()
    return m


async def _create_cohorte(db, tenant_id, carrera_id=None):
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    if carrera_id is None:
        c = Carrera(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            codigo=f"CARR-{uuid.uuid4().hex[:6]}",
            nombre="Carrera Test",
            estado="Activa",
        )
        db.add(c)
        await db.flush()
        carrera_id = c.id
    coh = Cohorte(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre=f"COH-{uuid.uuid4().hex[:6]}",
        anio=2026,
        vig_desde="2026-01-01",
        estado="Activa",
    )
    db.add(coh)
    await db.flush()
    return coh


async def _create_asignacion(db, tenant_id, usuario_id, cohorte_id, materia_id=None, rol="PROFESOR", comisiones=None):
    from app.models.asignacion import Asignacion
    a = Asignacion(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol=rol,
        cohorte_id=cohorte_id,
        materia_id=materia_id,
        comisiones=comisiones or [],
        desde=date(2026, 1, 1),
    )
    db.add(a)
    await db.flush()
    return a


# ── Tests ──

class TestSalarioBaseCRUD:

    async def test_create_and_get(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        base = await repo.create({
            "rol": "PROFESOR",
            "monto": 50000.00,
            "desde": date(2026, 1, 1),
        })
        assert base.rol == "PROFESOR"
        assert float(base.monto) == 50000.00

        fetched = await repo.get(base.id)
        assert fetched is not None
        assert fetched.id == base.id

    async def test_list(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({"rol": "PROFESOR", "monto": 50000, "desde": date(2026, 1, 1)})
        await repo.create({"rol": "TUTOR", "monto": 30000, "desde": date(2026, 1, 1)})
        items = await repo.list()
        assert len(items) == 2

    async def test_update(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        base = await repo.create({"rol": "PROFESOR", "monto": 50000, "desde": date(2026, 1, 1)})
        updated = await repo.update(base.id, {"monto": 55000.00})
        assert updated is not None
        assert float(updated.monto) == 55000.00

    async def test_soft_delete(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        base = await repo.create({"rol": "PROFESOR", "monto": 50000, "desde": date(2026, 1, 1)})
        deleted = await repo.soft_delete(base.id)
        assert deleted is True
        assert await repo.get(base.id) is None

    async def test_vigente_por_rol(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "rol": "PROFESOR", "monto": 40000,
            "desde": date(2025, 1, 1), "hasta": date(2025, 12, 31),
        })
        vigente = await repo.create({
            "rol": "PROFESOR", "monto": 50000,
            "desde": date(2026, 1, 1), "hasta": None,
        })
        result = await repo.get_vigente_por_rol(tenant.id, "PROFESOR", date(2026, 6, 1))
        assert result is not None
        assert result.id == vigente.id
        assert float(result.monto) == 50000.00


class TestSalarioPlusCRUD:

    async def test_create_and_get(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioPlusRepository(session=db_session, tenant_id=tenant.id)
        plus = await repo.create({
            "grupo": "A",
            "descripcion": "Plus grupo A",
            "monto": 5000.00,
            "desde": date(2026, 1, 1),
            "tope_acumulacion": 3,
        })
        assert plus.grupo == "A"
        assert float(plus.monto) == 5000.00
        assert plus.tope_acumulacion == 3

        fetched = await repo.get(plus.id)
        assert fetched is not None

    async def test_vigentes_por_grupo(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioPlusRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "grupo": "A", "descripcion": "Plus A", "monto": 5000,
            "desde": date(2025, 1, 1), "hasta": date(2025, 12, 31),
        })
        vigente = await repo.create({
            "grupo": "A", "descripcion": "Plus A vigente", "monto": 6000,
            "desde": date(2026, 1, 1),
        })
        result = await repo.get_vigentes_por_grupo(tenant.id, "A", date(2026, 6, 1))
        assert len(result) == 1
        assert result[0].id == vigente.id

    async def test_update(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioPlusRepository(session=db_session, tenant_id=tenant.id)
        plus = await repo.create({
            "grupo": "B", "descripcion": "Plus B", "monto": 3000,
            "desde": date(2026, 1, 1),
        })
        updated = await repo.update(plus.id, {"monto": 3500.00})
        assert updated is not None
        assert float(updated.monto) == 3500.00

    async def test_soft_delete(self, db_session):
        tenant = await _create_tenant(db_session)
        repo = SalarioPlusRepository(session=db_session, tenant_id=tenant.id)
        plus = await repo.create({
            "grupo": "C", "descripcion": "Plus C", "monto": 2000,
            "desde": date(2026, 1, 1),
        })
        assert await repo.soft_delete(plus.id) is True
        assert await repo.get(plus.id) is None


class TestMateriaGrupoPlusCRUD:

    async def test_create_and_get(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = await _create_materia(db_session, tenant.id)
        repo = MateriaGrupoPlusRepository(session=db_session, tenant_id=tenant.id)
        gp = await repo.create({
            "materia_id": materia.id,
            "grupo": "A",
            "desde": date(2026, 1, 1),
        })
        assert gp.grupo == "A"
        assert gp.materia_id == materia.id

    async def test_vigentes_por_materia(self, db_session):
        tenant = await _create_tenant(db_session)
        materia = await _create_materia(db_session, tenant.id)
        repo = MateriaGrupoPlusRepository(session=db_session, tenant_id=tenant.id)
        await repo.create({
            "materia_id": materia.id, "grupo": "A",
            "desde": date(2025, 1, 1), "hasta": date(2025, 12, 31),
        })
        vigente = await repo.create({
            "materia_id": materia.id, "grupo": "B",
            "desde": date(2026, 1, 1),
        })
        result = await repo.get_vigentes_por_materia(tenant.id, materia.id, date(2026, 6, 1))
        assert len(result) == 1
        assert result[0].id == vigente.id


class TestGenerarLiquidacion:

    async def test_generar_liquidacion_con_base(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        await _create_asignacion(
            db_session, tenant.id, usuario.id, cohorte.id,
            materia_id=materia.id, comisiones=["COM-01"],
        )

        # Crear salario base
        sb_repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await sb_repo.create({
            "rol": "PROFESOR", "monto": 50000,
            "desde": date(2026, 1, 1),
        })

        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        liquidaciones = await svc.generar_liquidaciones(
            cohorte_id=cohorte.id, periodo="2026-06"
        )

        assert len(liquidaciones) == 1
        liq = liquidaciones[0]
        assert liq.usuario_id == usuario.id
        assert float(liq.monto_base) == 50000.00
        assert float(liq.monto_plus) == 0
        assert float(liq.total) == 50000.00
        assert liq.estado == "Abierta"
        assert liq.es_nexo is False
        assert liq.excluido_por_factura is False

    async def test_generar_liquidacion_con_base_y_plus(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        await _create_asignacion(
            db_session, tenant.id, usuario.id, cohorte.id,
            materia_id=materia.id, comisiones=["COM-01"],
        )

        sb_repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await sb_repo.create({
            "rol": "PROFESOR", "monto": 50000,
            "desde": date(2026, 1, 1),
        })

        # Crear grupo plus y asociarlo a la materia
        gp_repo = MateriaGrupoPlusRepository(session=db_session, tenant_id=tenant.id)
        await gp_repo.create({
            "materia_id": materia.id, "grupo": "A",
            "desde": date(2026, 1, 1),
        })

        sp_repo = SalarioPlusRepository(session=db_session, tenant_id=tenant.id)
        await sp_repo.create({
            "grupo": "A", "descripcion": "Plus grupo A",
            "monto": 5000, "desde": date(2026, 1, 1),
        })

        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        liquidaciones = await svc.generar_liquidaciones(
            cohorte_id=cohorte.id, periodo="2026-06"
        )

        assert len(liquidaciones) == 1
        liq = liquidaciones[0]
        assert float(liq.monto_base) == 50000.00
        assert float(liq.monto_plus) == 5000.00
        assert float(liq.total) == 55000.00

    async def test_plus_con_tope_pa23(self, db_session):
        """PA-23: Plus con tope de acumulacion."""
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        # Dos materias, ambas del grupo A
        materia_a = await _create_materia(db_session, tenant.id)
        materia_b = await _create_materia(db_session, tenant.id)
        await _create_asignacion(
            db_session, tenant.id, usuario.id, cohorte.id,
            materia_id=materia_a.id, comisiones=["COM-01"],
        )
        await _create_asignacion(
            db_session, tenant.id, usuario.id, cohorte.id,
            materia_id=materia_b.id, comisiones=["COM-02"],
        )

        sb_repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await sb_repo.create({
            "rol": "PROFESOR", "monto": 50000,
            "desde": date(2026, 1, 1),
        })

        gp_repo = MateriaGrupoPlusRepository(session=db_session, tenant_id=tenant.id)
        await gp_repo.create({
            "materia_id": materia_a.id, "grupo": "A",
            "desde": date(2026, 1, 1),
        })
        await gp_repo.create({
            "materia_id": materia_b.id, "grupo": "A",
            "desde": date(2026, 1, 1),
        })

        sp_repo = SalarioPlusRepository(session=db_session, tenant_id=tenant.id)
        await sp_repo.create({
            "grupo": "A", "descripcion": "Plus grupo A",
            "monto": 5000, "desde": date(2026, 1, 1),
            "tope_acumulacion": 1,  # solo 1 comision
        })

        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        liquidaciones = await svc.generar_liquidaciones(
            cohorte_id=cohorte.id, periodo="2026-06"
        )

        assert len(liquidaciones) == 1
        liq = liquidaciones[0]
        # 2 materias del grupo A, pero tope=1 → solo 1 plus de 5000
        assert float(liq.monto_plus) == 5000.00
        assert float(liq.total) == 55000.00

    async def test_excluido_por_factura(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id, facturador=True)
        cohorte = await _create_cohorte(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        await _create_asignacion(
            db_session, tenant.id, usuario.id, cohorte.id,
            materia_id=materia.id,
        )

        sb_repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await sb_repo.create({
            "rol": "PROFESOR", "monto": 50000,
            "desde": date(2026, 1, 1),
        })

        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        liquidaciones = await svc.generar_liquidaciones(
            cohorte_id=cohorte.id, periodo="2026-06"
        )

        assert len(liquidaciones) == 1
        assert liquidaciones[0].excluido_por_factura is True

    async def test_nexo_role(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)
        materia = await _create_materia(db_session, tenant.id)
        await _create_asignacion(
            db_session, tenant.id, usuario.id, cohorte.id,
            materia_id=materia.id, rol="NEXO",
        )

        sb_repo = SalarioBaseRepository(session=db_session, tenant_id=tenant.id)
        await sb_repo.create({
            "rol": "NEXO", "monto": 40000,
            "desde": date(2026, 1, 1),
        })

        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        liquidaciones = await svc.generar_liquidaciones(
            cohorte_id=cohorte.id, periodo="2026-06"
        )

        assert len(liquidaciones) == 1
        assert liquidaciones[0].es_nexo is True


class TestCerrarLiquidacion:

    async def test_cerrar_con_exito(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        liq_repo = LiquidacionRepository(session=db_session, tenant_id=tenant.id)
        liquidacion = await liq_repo.create({
            "cohorte_id": cohorte.id,
            "periodo": "2026-06",
            "usuario_id": usuario.id,
            "rol": "PROFESOR",
            "comisiones": [],
            "monto_base": 50000,
            "monto_plus": 0,
            "total": 50000,
            "es_nexo": False,
            "excluido_por_factura": False,
            "estado": "Abierta",
        })
        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        result = await svc.cerrar_liquidacion(liquidacion.id)
        assert result.estado == "Cerrada"

    async def test_cerrar_ya_cerrada_error(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        liq_repo = LiquidacionRepository(session=db_session, tenant_id=tenant.id)
        liquidacion = await liq_repo.create({
            "cohorte_id": cohorte.id,
            "periodo": "2026-06",
            "usuario_id": usuario.id,
            "rol": "PROFESOR",
            "comisiones": [],
            "monto_base": 50000,
            "monto_plus": 0,
            "total": 50000,
            "es_nexo": False,
            "excluido_por_factura": False,
            "estado": "Cerrada",
        })
        await db_session.commit()

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        with pytest.raises(ValueError, match="ya se encuentra cerrada"):
            await svc.cerrar_liquidacion(liquidacion.id)

    async def test_cerrar_no_encontrada(self, db_session):
        tenant = await _create_tenant(db_session)
        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        with pytest.raises(ValueError, match="no encontrada"):
            await svc.cerrar_liquidacion(str(uuid.uuid4()))


class TestFacturas:

    async def test_create_and_get(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        repo = FacturaRepository(session=db_session, tenant_id=tenant.id)

        factura = await repo.create({
            "usuario_id": usuario.id,
            "periodo": "2026-06",
            "detalle": "Honorarios junio 2026",
            "cargada_at": datetime.now(UTC),
        })
        assert factura.periodo == "2026-06"
        assert factura.estado == "Pendiente"
        assert factura.abonada_at is None

        fetched = await repo.get(factura.id)
        assert fetched is not None

    async def test_list(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        repo = FacturaRepository(session=db_session, tenant_id=tenant.id)

        await repo.create({
            "usuario_id": usuario.id,
            "periodo": "2026-06",
            "detalle": "Factura 1",
            "cargada_at": datetime.now(UTC),
        })
        await repo.create({
            "usuario_id": usuario.id,
            "periodo": "2026-06",
            "detalle": "Factura 2",
            "cargada_at": datetime.now(UTC),
        })

        items = await repo.list()
        assert len(items) == 2

    async def test_abonar(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        repo = FacturaRepository(session=db_session, tenant_id=tenant.id)

        factura = await repo.create({
            "usuario_id": usuario.id,
            "periodo": "2026-06",
            "detalle": "Honorarios",
            "cargada_at": datetime.now(UTC),
        })
        await db_session.commit()

        fetched = await repo.get(factura.id)
        fetched.estado = "Abonada"
        fetched.abonada_at = datetime.now(UTC)
        await db_session.flush()

        updated = await repo.get(factura.id)
        assert updated.estado == "Abonada"
        assert updated.abonada_at is not None


class TestKPI:

    async def test_kpis(self, db_session):
        tenant = await _create_tenant(db_session)
        usuario = await _create_user(db_session, tenant.id)
        cohorte = await _create_cohorte(db_session, tenant.id)

        liq_repo = LiquidacionRepository(session=db_session, tenant_id=tenant.id)

        # Facturante
        await liq_repo.create({
            "cohorte_id": cohorte.id, "periodo": "2026-06",
            "usuario_id": usuario.id, "rol": "PROFESOR",
            "comisiones": [], "monto_base": 50000, "monto_plus": 0, "total": 50000,
            "es_nexo": False, "excluido_por_factura": True, "estado": "Abierta",
        })
        # No facturante
        await liq_repo.create({
            "cohorte_id": cohorte.id, "periodo": "2026-06",
            "usuario_id": usuario.id, "rol": "PROFESOR",
            "comisiones": [], "monto_base": 40000, "monto_plus": 0, "total": 40000,
            "es_nexo": False, "excluido_por_factura": False, "estado": "Abierta",
        })
        # Nexo
        await liq_repo.create({
            "cohorte_id": cohorte.id, "periodo": "2026-06",
            "usuario_id": usuario.id, "rol": "NEXO",
            "comisiones": [], "monto_base": 30000, "monto_plus": 0, "total": 30000,
            "es_nexo": True, "excluido_por_factura": False, "estado": "Abierta",
        })

        svc = LiquidacionService(session=db_session, tenant_id=tenant.id)
        kpis = await svc.obtener_kpis(cohorte_id=cohorte.id, periodo="2026-06")
        assert kpis["total_general"] == 120000.0
        assert kpis["total_facturantes"] == 50000.0
        assert kpis["total_no_facturantes"] == 70000.0
        assert kpis["total_nexo"] == 30000.0
        assert kpis["cant_docs"] == 1
