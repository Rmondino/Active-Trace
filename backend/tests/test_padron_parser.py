"""Tests for PadronParser service."""

import io
import csv
import uuid

import pytest

from app.services.padron_parser import PadronParser


class TestPadronParser:
    def test_parse_csv_valid(self):
        content = "nombre,apellidos,email,comision,regional\nJuan,Perez,juan@test.com,A,CABA\nMaria,Gomez,maria@test.com,B,BSAS\n"
        result = PadronParser.parse_csv(content.encode("utf-8"))
        assert result["total_filas"] == 2
        assert len(result["filas"]) == 2
        assert result["filas"][0]["nombre"] == "Juan"
        assert result["filas"][0]["email"] == "juan@test.com"
        assert result["filas"][1]["apellidos"] == "Gomez"

    def test_parse_csv_minimal_columns(self):
        content = "nombre,apellidos,email\nAna,Lopez,ana@test.com\n"
        result = PadronParser.parse_csv(content.encode("utf-8"))
        assert result["total_filas"] == 1
        assert result["filas"][0]["nombre"] == "Ana"
        assert "comision" not in result["filas"][0] or result["filas"][0]["comision"] is None
        assert "regional" not in result["filas"][0] or result["filas"][0]["regional"] is None

    def test_parse_csv_empty(self):
        content = "nombre,apellidos,email\n"
        result = PadronParser.parse_csv(content.encode("utf-8"))
        assert result["total_filas"] == 0
        assert len(result["filas"]) == 0

    def test_parse_csv_missing_required_columns(self):
        content = "nombre,apellidos\nJuan,Perez\n"
        with pytest.raises(ValueError, match="email"):
            PadronParser.parse_csv(content.encode("utf-8"))

    def test_validate_filas_removes_empty_email(self):
        filas = [
            {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com"},
            {"nombre": "", "apellidos": "SinEmail", "email": ""},
        ]
        result = PadronParser.validate_filas(filas)
        assert len(result) == 1
        assert result[0]["nombre"] == "Juan"

    def test_validate_filas_all_valid(self):
        filas = [
            {"nombre": "A", "apellidos": "B", "email": "a@b.com"},
            {"nombre": "C", "apellidos": "D", "email": "c@d.com"},
        ]
        result = PadronParser.validate_filas(filas)
        assert len(result) == 2

    def test_generar_preview_masks_email(self):
        filas = [
            {"nombre": "Juan", "apellidos": "Perez", "email": "juan@test.com", "comision": "A"},
        ]
        preview = PadronParser.generar_preview(filas)
        assert preview["total_filas"] == 1
        assert "columnas" in preview
        assert len(preview["muestra"]) == 1
        assert "***" in preview["muestra"][0]["email"]

    def test_generar_preview_muestra_max_5(self):
        filas = [{"nombre": f"U{i}", "apellidos": "A", "email": f"u{i}@t.com"} for i in range(10)]
        preview = PadronParser.generar_preview(filas)
        assert len(preview["muestra"]) == 5

    def test_generar_preview_empty(self):
        preview = PadronParser.generar_preview([])
        assert preview["total_filas"] == 0
        assert len(preview["muestra"]) == 0
