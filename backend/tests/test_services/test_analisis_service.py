"""Tests for AnalisisService — pure Python computation over seeded data."""

import uuid
from decimal import Decimal

import pytest

from app.models.calificacion import Calificacion
from app.models.tenant import Tenant
from app.models.materia import Materia
from app.models.cohorte import Cohorte
from app.models.carrera import Carrera
from app.models.version_padron import VersionPadron
from app.models.entrada_padron import EntradaPadron
from app.models.umbral_materia import UmbralMateria
from app.models.asignacion import Asignacion
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository
from app.repositories.version_padron_repository import VersionPadronRepository
from app.repositories.entrada_padron_repository import EntradaPadronRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.services.analisis_service import AnalisisService
from tests.conftest import create_user


async def _seed_role_permiso(db, slug, codigo, alcance="global"):
    result = await db.execute(
        __import__("sqlalchemy").select(Rol).where(Rol.slug == slug)
    )
    role = result.scalar_one_or_none()
    if not role:
        role = Rol(id=str(uuid.uuid4()), slug=slug, nombre=slug.upper())
        db.add(role)
        await db.flush()

    result = await db.execute(
        __import__("sqlalchemy").select(Permiso).where(Permiso.codigo == codigo)
    )
    permiso = result.scalar_one_or_none()
    if not permiso:
        permiso = Permiso(id=str(uuid.uuid4()), codigo=codigo, descripcion=f"Permiso {codigo}")
        db.add(permiso)
        await db.flush()

    result = await db.execute(
        __import__("sqlalchemy").select(RolPermiso).where(
            RolPermiso.rol_id == role.id, RolPermiso.permiso_id == permiso.id
        )
    )
    if result.scalar_one_or_none():
        return
    rp = RolPermiso(id=str(uuid.uuid4()), rol_id=role.id, permiso_id=permiso.id, alcance=alcance)
    db.add(rp)
    await db.flush()


def _make_service(db, tenant_id):
    return AnalisisService(
        calificacion_repo=CalificacionRepository(session=db, tenant_id=tenant_id),
        umbral_repo=UmbralMateriaRepository(session=db, tenant_id=tenant_id),
        version_padron_repo=VersionPadronRepository(session=db, tenant_id=tenant_id),
        entrada_padron_repo=EntradaPadronRepository(session=db, tenant_id=tenant_id),
        asignacion_repo=AsignacionRepository(session=db, tenant_id=tenant_id),
    )


async def _create_tenant_min(db):
    t = Tenant(id=str(uuid.uuid4()), slug=f"min-{uuid.uuid4().hex[:8]}", nombre="Test", estado="Activo")
    db.add(t)
    await db.flush()
    return t


class TestAlumnosAtrasados:
    async def _seed(self, db):
        tenant = Tenant(id=str(uuid.uuid4()), slug="atr-test", nombre="Test", estado="Activo")
        db.add(tenant)
        await db.flush()

        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db.add(carrera)
        await db.flush()

        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-ATR", nombre="Test")
        db.add(materia)
        await db.flush()

        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db.add(cohorte)
        await db.flush()

        user = await create_user(
            db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"],
        )
        from datetime import date
        asig = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia.id,
            desde=date(2020, 1, 1), comisiones=[],
        )
        db.add(asig)
        await db.flush()

        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=3, activa=True,
        )
        db.add(vp)
        await db.flush()

        ep_a = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Juan", apellidos="Perez", email="juan@test.com", comision="A",
        )
        ep_b = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Maria", apellidos="Gomez", email="maria@test.com", comision="A",
        )
        db.add(ep_a)
        db.add(ep_b)
        await db.flush()

        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asig.id, materia_id=materia.id,
            umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
        )
        db.add(umbral)
        await db.flush()

        for act in ["TP1", "TP2", "TP3"]:
            db.add(Calificacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                entrada_padron_id=ep_a.id, materia_id=materia.id,
                actividad=act, nota_numerica=Decimal("80"),
                origen="Importado", aprobado=True,
            ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep_b.id, materia_id=materia.id,
            actividad="TP1", nota_numerica=Decimal("45"),
            origen="Importado", aprobado=False,
        ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep_b.id, materia_id=materia.id,
            actividad="TP2", nota_numerica=Decimal("75"),
            origen="Importado", aprobado=True,
        ))
        await db.flush()

        return {
            "tenant_id": tenant.id,
            "materia_id": materia.id,
            "cohorte_id": cohorte.id,
            "ep_a_id": ep_a.id,
            "ep_b_id": ep_b.id,
            "user": user,
        }

    async def test_student_with_missing_activity_is_atrasado(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.alumnos_atrasados(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        atrasados = [r for r in result if r["es_atrasado"]]
        assert any(r["entrada_padron_id"] == seed["ep_b_id"] for r in atrasados)
        b = next(r for r in result if r["entrada_padron_id"] == seed["ep_b_id"])
        assert "TP3" in b["causas"]["faltantes"]

    async def test_student_with_low_grade_is_atrasado(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.alumnos_atrasados(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        b = next(r for r in result if r["entrada_padron_id"] == seed["ep_b_id"])
        assert len(b["causas"]["baja_nota"]) >= 1

    async def test_student_all_passing_not_atrasado(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.alumnos_atrasados(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        a = next(r for r in result if r["entrada_padron_id"] == seed["ep_a_id"])
        assert not a["es_atrasado"]

    async def test_atrasados_detail_includes_causes(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.alumnos_atrasados(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        b = next(r for r in result if r["entrada_padron_id"] == seed["ep_b_id"])
        assert "faltantes" in b["causas"]
        assert "baja_nota" in b["causas"]
        assert b["total_actividades"] == 3
        assert b["aprobadas"] == 1
        assert b["desaprobadas"] == 1
        assert b["sin_nota"] == 1

    async def test_atrasados_includes_student_info(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.alumnos_atrasados(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        a = next(r for r in result if r["entrada_padron_id"] == seed["ep_a_id"])
        assert a["alumno"] == "Juan Perez"
        assert a["comision"] == "A"
        assert a["email_masked"] == "jua...@test.com"


class TestRankingAprobadas:
    async def _seed(self, db):
        tenant = await _create_tenant_min(db)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db.add(carrera)
        await db.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-RNK", nombre="Test")
        db.add(materia)
        await db.flush()
        user = await create_user(db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db.add(cohorte)
        await db.flush()

        rnk_cohorte = cohorte.id
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=rnk_cohorte,
            cargado_por=user.id, origen="manual", total_filas=3, activa=True,
        )
        db.add(vp)
        await db.flush()

        eps = {}
        for name, apellido in [("Ana", "Lopez"), ("Luis", "Martinez"), ("Pedro", "Ramirez")]:
            ep = EntradaPadron(
                id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
                nombre=name, apellidos=apellido, email=f"{name.lower()}@test.com",
            )
            db.add(ep)
            await db.flush()
            eps[f"{name} {apellido}"] = ep

        for act in ["A1", "A2", "A3", "A4", "A5"]:
            db.add(Calificacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                entrada_padron_id=eps["Ana Lopez"].id, materia_id=materia.id,
                actividad=act, nota_numerica=Decimal("80"), origen="Importado", aprobado=True,
            ))
        for act in ["A1", "A2"]:
            db.add(Calificacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                entrada_padron_id=eps["Luis Martinez"].id, materia_id=materia.id,
                actividad=act, nota_numerica=Decimal("75"), origen="Importado", aprobado=True,
            ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=eps["Luis Martinez"].id, materia_id=materia.id,
            actividad="A3", nota_numerica=Decimal("30"), origen="Importado", aprobado=False,
        ))
        for act in ["A1", "A2", "A3"]:
            db.add(Calificacion(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                entrada_padron_id=eps["Pedro Ramirez"].id, materia_id=materia.id,
                actividad=act, nota_numerica=Decimal("50"), origen="Importado", aprobado=False,
            ))
        await db.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id, "eps": eps}

    async def test_ranking_sorted_descending(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.ranking_aprobadas(seed["materia_id"], seed["tenant_id"])
        assert len(result) >= 2
        assert result[0]["aprobadas"] >= result[1]["aprobadas"]

    async def test_ranking_excludes_zero_approved(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.ranking_aprobadas(seed["materia_id"], seed["tenant_id"])
        slugs = [r["alumno"] for r in result]
        assert "Pedro Ramirez" not in slugs

    async def test_ranking_includes_detail(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.ranking_aprobadas(seed["materia_id"], seed["tenant_id"])
        ana = next(r for r in result if r["alumno"] == "Ana Lopez")
        assert ana["aprobadas"] == 5
        assert ana["total"] == 5
        assert ana["porcentaje"] == 100.0

    async def test_ranking_with_textual_grade_counts_as_approved(self, db_session):
        tenant = await _create_tenant_min(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-RNK2", nombre="Test")
        db_session.add(materia)
        await db_session.flush()
        user = await create_user(db_session, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com")
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db_session.add(carrera)
        await db_session.flush()
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db_session.add(cohorte)
        await db_session.flush()
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=1, activa=True,
        )
        db_session.add(vp)
        await db_session.flush()
        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Test", apellidos="Student", email="t@test.com",
        )
        db_session.add(ep)
        await db_session.flush()
        db_session.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep.id, materia_id=materia.id,
            actividad="TP", nota_textual="Satisfactorio",
            origen="Importado", aprobado=True,
        ))
        await db_session.flush()

        service = _make_service(db_session, tenant.id)
        result = await service.ranking_aprobadas(materia.id, tenant.id)
        assert len(result) == 1
        assert result[0]["aprobadas"] == 1


class TestReporteRapido:
    async def _seed(self, db):
        tenant = await _create_tenant_min(db)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db.add(carrera)
        await db.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-RPT", nombre="Test")
        db.add(materia)
        await db.flush()
        user = await create_user(db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com")
        from datetime import date
        asig = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia.id,
            desde=date(2020, 1, 1), comisiones=[],
        )
        db.add(asig)
        await db.flush()
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db.add(cohorte)
        await db.flush()
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=2, activa=True,
        )
        db.add(vp)
        await db.flush()

        eps = []
        for name in ["A", "B"]:
            ep = EntradaPadron(
                id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
                nombre=name, apellidos="Student", email=f"{name}@test.com",
            )
            db.add(ep)
            await db.flush()
            eps.append(ep)

        umbral = UmbralMateria(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            asignacion_id=asig.id, materia_id=materia.id,
            umbral_pct=60,
        )
        db.add(umbral)
        await db.flush()

        for ep in eps:
            for act in ["A1", "A2"]:
                db.add(Calificacion(
                    id=str(uuid.uuid4()), tenant_id=tenant.id,
                    entrada_padron_id=ep.id, materia_id=materia.id,
                    actividad=act, nota_numerica=Decimal("75"),
                    origen="Importado", aprobado=True,
                ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=eps[0].id, materia_id=materia.id,
            actividad="A3", nota_numerica=Decimal("40"),
            origen="Importado", aprobado=False,
        ))
        await db.flush()

        return {"tenant_id": tenant.id, "materia_id": materia.id}

    async def test_reporte_rapido_includes_all_metrics(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.reporte_rapido(seed["materia_id"], seed["tenant_id"])
        assert result["total_alumnos"] == 2
        assert result["total_actividades"] == 3
        assert result["alumnos_atrasados"] >= 0
        assert isinstance(result["tasa_aprobacion_gral"], float)
        assert len(result["actividades"]) == 3

    async def test_reporte_rapido_empty_materia(self, db_session):
        tenant = await _create_tenant_min(db_session)
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-RPT-E", nombre="Empty")
        db_session.add(materia)
        await db_session.flush()
        service = _make_service(db_session, tenant.id)
        result = await service.reporte_rapido(materia.id, tenant.id)
        assert result["total_alumnos"] == 0
        assert result["total_actividades"] == 0


class TestNotasFinales:
    async def _seed(self, db):
        tenant = await _create_tenant_min(db)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db.add(carrera)
        await db.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-NF", nombre="Test")
        db.add(materia)
        await db.flush()
        user = await create_user(db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com")
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db.add(cohorte)
        await db.flush()
        nf_coh = cohorte.id
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=nf_coh,
            cargado_por=user.id, origen="manual", total_filas=1, activa=True,
        )
        db.add(vp)
        await db.flush()
        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Test", apellidos="Student", email="t@test.com",
        )
        db.add(ep)
        await db.flush()
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep.id, materia_id=materia.id,
            actividad="Parcial 1", nota_numerica=Decimal("75"),
            origen="Importado", aprobado=True,
        ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep.id, materia_id=materia.id,
            actividad="TP Grupal", nota_textual="Satisfactorio",
            origen="Importado", aprobado=True,
        ))
        await db.flush()
        return {"tenant_id": tenant.id, "materia_id": materia.id, "cohorte_id": nf_coh, "ep_id": ep.id}

    async def test_notas_finales_include_numeric_and_textual(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.notas_finales(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        assert len(result) == 1
        student = result[0]
        assert "Parcial 1" in student["actividades"]
        assert "TP Grupal" in student["actividades"]
        assert student["promedio_numerico"] == 75.0
        assert student["aprobadas"] == 2
        assert student["total_actividades"] == 2

    async def test_notas_finales_student_info(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.notas_finales(seed["materia_id"], seed["cohorte_id"], seed["tenant_id"])
        assert result[0]["alumno"] == "Test Student"
        assert result[0]["entrada_padron_id"] == seed["ep_id"]


class TestExportarSinCorregir:
    async def _seed(self, db):
        tenant = await _create_tenant_min(db)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db.add(carrera)
        await db.flush()
        materia = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-EXP", nombre="Test")
        db.add(materia)
        await db.flush()
        user = await create_user(db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com")
        cohorte = Cohorte(
            id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="2026", anio=2026, vig_desde="2026-01-01",
        )
        db.add(cohorte)
        await db.flush()
        vp = VersionPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            materia_id=materia.id, cohorte_id=cohorte.id,
            cargado_por=user.id, origen="manual", total_filas=1, activa=True,
        )
        db.add(vp)
        await db.flush()
        ep = EntradaPadron(
            id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
            nombre="Test", apellidos="Student", email="t@test.com",
        )
        db.add(ep)
        await db.flush()

        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep.id, materia_id=materia.id,
            actividad="TP Grupal", nota_numerica=None,
            nota_textual=None, origen="Importado", aprobado=False,
        ))
        db.add(Calificacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id,
            entrada_padron_id=ep.id, materia_id=materia.id,
            actividad="Parcial 1 (Real)", nota_numerica=Decimal("75"),
            nota_textual=None, origen="Importado", aprobado=True,
        ))
        await db.flush()
        return {"tenant_id": tenant.id, "materia_id": materia.id}

    async def test_export_includes_textual_without_grade(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.exportar_sin_corregir(seed["materia_id"], seed["tenant_id"])
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_export_returns_valid_xlsx(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.exportar_sin_corregir(seed["materia_id"], seed["tenant_id"])
        assert result.startswith(b"PK")

    async def test_export_excludes_numeric_activities(self, db_session):
        seed = await self._seed(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.exportar_sin_corregir(seed["materia_id"], seed["tenant_id"])
        import openpyxl
        from io import BytesIO
        wb = openpyxl.load_workbook(BytesIO(result))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert len(rows) == 2
        header, data = rows
        assert "Actividad" in header


class TestMonitor:
    async def _seed_with_two_materias(self, db):
        tenant = await _create_tenant_min(db)
        carrera = Carrera(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="CARR", nombre="T")
        db.add(carrera)
        await db.flush()
        materia_a = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-MON-A", nombre="A")
        materia_b = Materia(id=str(uuid.uuid4()), tenant_id=tenant.id, codigo="MAT-MON-B", nombre="B")
        db.add(materia_a)
        db.add(materia_b)
        await db.flush()
        user = await create_user(db, tenant.id, email=f"prof-{uuid.uuid4().hex[:8]}@test.com", roles=["profesor"])
        from datetime import date
        asig_a = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia_a.id,
            desde=date(2020, 1, 1), comisiones=[],
        )
        db.add(asig_a)
        asig_b = Asignacion(
            id=str(uuid.uuid4()), tenant_id=tenant.id, usuario_id=user.id,
            rol="PROFESOR", materia_id=materia_b.id,
            desde=date(2020, 1, 1), comisiones=[],
        )
        db.add(asig_b)
        await db.flush()

        for idx, (m_id, total) in enumerate([(materia_a.id, 2), (materia_b.id, 1)]):
            cohorte = Cohorte(
                id=str(uuid.uuid4()), tenant_id=tenant.id, carrera_id=carrera.id,
                nombre=f"2026-{idx}", anio=2026, vig_desde="2026-01-01",
            )
            db.add(cohorte)
            await db.flush()
            vp = VersionPadron(
                id=str(uuid.uuid4()), tenant_id=tenant.id,
                materia_id=m_id, cohorte_id=cohorte.id,
                cargado_por=user.id, origen="manual",
                total_filas=total, activa=True,
            )
            db.add(vp)
            await db.flush()
            for i in range(total):
                ep = EntradaPadron(
                    id=str(uuid.uuid4()), tenant_id=tenant.id, version_id=vp.id,
                    nombre=f"Student{i}", apellidos=f"Last{i}",
                    email=f"s{i}@test.com", comision="A",
                )
                db.add(ep)
                await db.flush()
                for act in ["TP1", "TP2"]:
                    db.add(Calificacion(
                        id=str(uuid.uuid4()), tenant_id=tenant.id,
                        entrada_padron_id=ep.id, materia_id=m_id,
                        actividad=act, nota_numerica=Decimal("75"),
                        origen="Importado", aprobado=True,
                    ))
                await db.flush()

        await db.flush()
        return {
            "tenant_id": tenant.id,
            "materia_a_id": materia_a.id,
            "materia_b_id": materia_b.id,
            "user_id": user.id,
        }

    async def test_monitor_propio_filters_by_user_materias(self, db_session):
        seed = await self._seed_with_two_materias(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.monitor(
            scope="propio", filtros={}, user_id=seed["user_id"], tenant_id=seed["tenant_id"],
        )
        assert len(result) == 3

    async def test_monitor_general_returns_all(self, db_session):
        seed = await self._seed_with_two_materias(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.monitor(
            scope="general", filtros={}, user_id=seed["user_id"], tenant_id=seed["tenant_id"],
        )
        assert len(result) == 3

    async def test_monitor_filter_by_comision(self, db_session):
        seed = await self._seed_with_two_materias(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.monitor(
            scope="general", filtros={"comision": "A"}, user_id=seed["user_id"], tenant_id=seed["tenant_id"],
        )
        assert len(result) == 3
        assert all(r["comision"] == "A" for r in result)

    async def test_monitor_filter_by_materia(self, db_session):
        seed = await self._seed_with_two_materias(db_session)
        service = _make_service(db_session, seed["tenant_id"])
        result = await service.monitor(
            scope="general", filtros={"materia_id": seed["materia_a_id"]},
            user_id=seed["user_id"], tenant_id=seed["tenant_id"],
        )
        assert len(result) == 2
