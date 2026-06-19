"""Tests for CalificacionesParser service."""

import uuid
from decimal import Decimal

import pytest

from app.services.calificaciones_parser import CalificacionesParser


class TestColumnDetection:
    def test_detect_numeric_column(self):
        result = CalificacionesParser._detect_column_type("Parcial 1 (Real)")
        assert result == "numerica"

    def test_detect_textual_column(self):
        result = CalificacionesParser._detect_column_type("TP Grupal")
        assert result == "textual"

    def test_detect_numeric_case_insensitive(self):
        result = CalificacionesParser._detect_column_type("EXAMEN (real)")
        assert result == "numerica"

    def test_detect_textual_without_real(self):
        result = CalificacionesParser._detect_column_type("Parcial 1")
        assert result == "textual"


class TestParseGradesFile:
    def test_parse_csv_with_numeric_column(self):
        content = "Alumno,Parcial 1 (Real),TP Grupal\nJuan Perez,75,Satisfactorio\nMaria Gomez,45,Regular\n"
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        assert len(result["columnas"]) == 2
        assert result["columnas"][0]["nombre"] == "Parcial 1 (Real)"
        assert result["columnas"][0]["tipo"] == "numerica"
        assert result["columnas"][1]["nombre"] == "TP Grupal"
        assert result["columnas"][1]["tipo"] == "textual"
        assert len(result["filas"]) == 2
        assert result["filas"][0]["alumno"] == "Juan Perez"
        assert result["filas"][0]["actividades"]["Parcial 1 (Real)"] == "75"
        assert result["filas"][1]["actividades"]["Parcial 1 (Real)"] == "45"

    def test_parse_csv_all_textual(self):
        content = "Alumno,TP1,TP2\nJuan Perez,Bien,Regular\n"
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        for col in result["columnas"]:
            assert col["tipo"] == "textual"

    def test_parse_csv_single_column(self):
        content = "Alumno\nJuan Perez\n"
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        assert len(result["columnas"]) == 0
        assert len(result["filas"]) == 1

    def test_parse_csv_empty(self):
        content = "Alumno\n"
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        assert len(result["filas"]) == 0

    def test_parse_invalid_extension(self):
        with pytest.raises(ValueError, match="no soportado"):
            CalificacionesParser.parse_grades_file(b"data", "grades.pdf")

    def test_parse_csv_empty_alumno_skipped(self):
        content = "Alumno,Nota\n,70\nJuan,80\n"
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        assert len(result["filas"]) == 1
        assert result["filas"][0]["alumno"] == "Juan"

    def test_parse_csv_all_empty_alumnos(self):
        content = "Alumno,Nota\n,\n,\n"
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        assert len(result["filas"]) == 0

    def test_parse_csv_empty_file(self):
        content = ""
        result = CalificacionesParser.parse_grades_file(content.encode("utf-8"), "grades.csv")
        assert len(result["columnas"]) == 0
        assert len(result["filas"]) == 0


class TestGenerarPreview:
    def test_generar_preview_basic(self):
        parsed = {
            "columnas": [
                {"nombre": "Parcial 1 (Real)", "tipo": "numerica"},
                {"nombre": "TP Grupal", "tipo": "textual"},
            ],
            "filas": [
                {"alumno": "Juan", "actividades": {"Parcial 1 (Real)": "75", "TP Grupal": "Satisfactorio"}},
                {"alumno": "Maria", "actividades": {"Parcial 1 (Real)": "45", "TP Grupal": "Regular"}},
            ],
            "errores": [],
        }
        preview = CalificacionesParser.generar_preview(parsed)
        assert preview["total_alumnos"] == 2
        assert len(preview["actividades"]) == 2
        assert preview["actividades"][0]["nombre"] == "Parcial 1 (Real)"
        assert preview["actividades"][0]["tipo"] == "numerica"
        assert preview["actividades"][0]["seleccionada"] is True
        assert len(preview["muestra"]) == 2

    def test_generar_preview_muestra_max_5(self):
        filas = [{"alumno": f"U{i}", "actividades": {}} for i in range(10)]
        parsed = {"columnas": [{"nombre": "TP1", "tipo": "textual"}], "filas": filas, "errores": []}
        preview = CalificacionesParser.generar_preview(parsed)
        assert len(preview["muestra"]) == 5

    def test_generar_preview_empty(self):
        parsed = {"columnas": [], "filas": [], "errores": []}
        preview = CalificacionesParser.generar_preview(parsed)
        assert preview["total_alumnos"] == 0
        assert len(preview["muestra"]) == 0
        assert len(preview["actividades"]) == 0


class TestDerivarAprobado:
    def test_numeric_above_threshold(self):
        assert CalificacionesParser.derivar_aprobado(Decimal("75"), None, 60, ["Satisfactorio"]) is True

    def test_numeric_at_threshold(self):
        assert CalificacionesParser.derivar_aprobado(Decimal("60"), None, 60, ["Satisfactorio"]) is True

    def test_numeric_below_threshold(self):
        assert CalificacionesParser.derivar_aprobado(Decimal("45"), None, 60, ["Satisfactorio"]) is False

    def test_textual_in_valores_aprobatorios(self):
        assert CalificacionesParser.derivar_aprobado(None, "Satisfactorio", 60, ["Satisfactorio", "Supera lo esperado"]) is True

    def test_textual_not_in_valores_aprobatorios(self):
        assert CalificacionesParser.derivar_aprobado(None, "Regular", 60, ["Satisfactorio", "Supera lo esperado"]) is False

    def test_both_none(self):
        assert CalificacionesParser.derivar_aprobado(None, None, 60, ["Satisfactorio"]) is False

    def test_numeric_takes_precedence(self):
        assert CalificacionesParser.derivar_aprobado(Decimal("30"), "Satisfactorio", 60, ["Satisfactorio"]) is False

    def test_custom_threshold(self):
        assert CalificacionesParser.derivar_aprobado(Decimal("80"), None, 80, ["Satisfactorio"]) is True
        assert CalificacionesParser.derivar_aprobado(Decimal("79"), None, 80, ["Satisfactorio"]) is False


class TestDetectCompletions:
    def test_detect_uncorrected(self):
        content = "Alumno,TP1,TP2,Estado\nJuan Perez,completado,,completado\n"
        calificaciones = []
        result = CalificacionesParser.detect_completions(content.encode("utf-8"), calificaciones)
        assert len(result) == 1
        assert result[0]["alumno"] == "Juan Perez"
        assert result[0]["actividad"] == "TP1"

    def test_no_uncorrected_all_empty(self):
        content = "Alumno,TP1,Estado\nJuan Perez,,pendiente\n"
        result = CalificacionesParser.detect_completions(content.encode("utf-8"), [])
        assert len(result) == 0

    def test_multiple_alumnos_uncorrected(self):
        content = "Alumno,TP1,Estado\nJuan Perez,completado,completado\nMaria Gomez,completado,completado\n"
        result = CalificacionesParser.detect_completions(content.encode("utf-8"), [])
        assert len(result) == 2

    def test_mixed_states(self):
        content = "Alumno,TP1,TP2,Estado\nJuan Perez,completado,,completado\nMaria Gomez,,completado,completado\n"
        result = CalificacionesParser.detect_completions(content.encode("utf-8"), [])
        assert len(result) == 2
