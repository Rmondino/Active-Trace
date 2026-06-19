"""Tests for Pydantic schemas — User and Asignacion (C-07)."""

import uuid
from datetime import date, timedelta

import pytest
from pydantic import ValidationError


class TestUserSchemas:
    """UserCreate, UserUpdate, UserRead, UserDetail validation."""

    def test_user_create_valid(self):
        from datetime import date
        from app.schemas.user import UserCreate

        data = UserCreate(
            nombre="Juan",
            apellidos="Pérez",
            email="juan@example.com",
            dni="12345678",
            cuil="20-12345678-9",
            legajo="LEG-001",
        )
        assert data.nombre == "Juan"
        assert data.apellidos == "Pérez"
        assert data.email == "juan@example.com"
        assert data.dni == "12345678"
        assert data.cuil == "20-12345678-9"
        assert data.legajo == "LEG-001"
        assert data.facturador is False

    def test_user_create_rejects_extra_fields(self):
        from app.schemas.user import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(
                nombre="Juan",
                apellidos="Pérez",
                email="j@e.com",
                dni="123",
                extra_field="not allowed",
            )

    def test_user_create_rejects_missing_required(self):
        from app.schemas.user import UserCreate

        with pytest.raises(ValidationError) as exc:
            UserCreate(
                nombre="Juan",
                apellidos="Pérez",
                email="j@e.com",
                # missing dni
            )
        errors = {e["loc"][0]: e["type"] for e in exc.value.errors()}
        assert "dni" in errors

    def test_user_read_masks_pii(self):
        from app.schemas.user import UserRead

        data = UserRead(
            id=str(uuid.uuid4()),
            nombre="Juan",
            apellidos="Pérez",
            email="j***@example.com",
            dni="*********123",
            legajo="LEG-001",
            regional="CABA",
            estado="Activo",
            facturador=False,
        )
        assert data.email == "j***@example.com"
        assert data.dni == "*********123"

    def test_user_detail_shows_full_pii(self):
        from app.schemas.user import UserDetail

        data = UserDetail(
            id=str(uuid.uuid4()),
            nombre="Juan",
            apellidos="Pérez",
            email="juan@example.com",
            dni="12345678",
            cuil="20-12345678-9",
            cbu="0000003100012345678901",
            alias_cbu="JUAN.PEREZ",
            banco="Banco Test",
            regional="CABA",
            legajo="LEG-001",
            legajo_profesional="LP-001",
            facturador=True,
            estado="Activo",
        )
        assert data.dni == "12345678"
        assert data.cuil == "20-12345678-9"

    def test_user_update_partial(self):
        from app.schemas.user import UserUpdate

        data = UserUpdate(nombre="Updated")
        assert data.nombre == "Updated"
        assert data.apellidos is None

    def test_user_update_rejects_extra(self):
        from app.schemas.user import UserUpdate

        with pytest.raises(ValidationError):
            UserUpdate(nombre="Test", banned_field="x")

    def test_user_read_rejects_extra(self):
        from app.schemas.user import UserRead

        with pytest.raises(ValidationError):
            UserRead(
                id=str(uuid.uuid4()),
                nombre="Test", apellidos="User",
                email="t@t.com", dni="123",
                legajo=None, regional=None,
                estado="Activo", facturador=False,
                extra="bad",
            )


class TestAsignacionSchemas:
    """AsignacionCreate, AsignacionUpdate, AsignacionRead validation."""

    def test_asignacion_create_valid(self):
        from app.schemas.asignacion import AsignacionCreate

        data = AsignacionCreate(
            usuario_id=str(uuid.uuid4()),
            rol="PROFESOR",
            desde=date(2024, 1, 1),
            comisiones=["COM-A"],
        )
        assert data.rol == "PROFESOR"
        assert data.desde == date(2024, 1, 1)
        assert data.comisiones == ["COM-A"]

    def test_asignacion_create_rejects_extra(self):
        from app.schemas.asignacion import AsignacionCreate

        with pytest.raises(ValidationError):
            AsignacionCreate(
                usuario_id=str(uuid.uuid4()),
                rol="PROFESOR",
                desde=date(2024, 1, 1),
                invalid=True,
            )

    def test_asignacion_read_has_estado_vigencia_vigente(self):
        from app.schemas.asignacion import AsignacionRead

        data = AsignacionRead(
            id=str(uuid.uuid4()),
            usuario_id=str(uuid.uuid4()),
            rol="PROFESOR",
            comisiones=[],
            desde=date(2020, 1, 1),
            hasta=None,
            estado_vigencia="Vigente",
        )
        assert data.estado_vigencia == "Vigente"

    def test_asignacion_read_has_estado_vigencia_vencida(self):
        from app.schemas.asignacion import AsignacionRead

        data = AsignacionRead(
            id=str(uuid.uuid4()),
            usuario_id=str(uuid.uuid4()),
            rol="TUTOR",
            comisiones=[],
            desde=date(2020, 1, 1),
            hasta=date(2020, 12, 31),
            estado_vigencia="Vencida",
        )
        assert data.estado_vigencia == "Vencida"

    def test_asignacion_update_partial(self):
        from app.schemas.asignacion import AsignacionUpdate

        data = AsignacionUpdate(rol="COORDINADOR")
        assert data.rol == "COORDINADOR"
        assert data.desde is None

    def test_asignacion_update_rejects_extra(self):
        from app.schemas.asignacion import AsignacionUpdate

        with pytest.raises(ValidationError):
            AsignacionUpdate(rol="ADMIN", invalid=True)

    def test_asignacion_read_rejects_extra(self):
        from app.schemas.asignacion import AsignacionRead

        with pytest.raises(ValidationError):
            AsignacionRead(
                id=str(uuid.uuid4()),
                usuario_id=str(uuid.uuid4()),
                rol="PROFESOR", comisiones=[],
                desde=date(2024, 1, 1),
                estado_vigencia="Vigente",
                invalid=True,
            )
