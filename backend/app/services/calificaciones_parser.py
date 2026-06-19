"""CalificacionesParser service — parse grade files with numeric/textual detection."""

import csv
import io
from decimal import Decimal


class CalificacionesParser:

    @staticmethod
    def parse_grades_file(file_content: bytes, filename: str) -> dict:
        ext = CalificacionesParser._get_extension(filename)
        if ext == ".csv":
            return CalificacionesParser._parse_csv_grades(file_content)
        elif ext == ".xlsx":
            return CalificacionesParser._parse_xlsx_grades(file_content)
        raise ValueError(f"Formato de archivo no soportado: {ext}")

    @staticmethod
    def _get_extension(filename: str) -> str:
        dot_idx = filename.rfind(".")
        if dot_idx == -1:
            return ""
        return filename[dot_idx:].lower()

    @staticmethod
    def _detect_column_type(col_name: str) -> str:
        if col_name.strip().lower().endswith("(real)"):
            return "numerica"
        return "textual"

    @staticmethod
    def _parse_csv_grades(file_content: bytes) -> dict:
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            return {"columnas": [], "filas": [], "errores": []}

        headers = [h.strip() for h in reader.fieldnames]
        if not headers:
            return {"columnas": [], "filas": [], "errores": []}

        alumno_col = headers[0]
        actividad_cols = headers[1:]

        columnas = []
        for col in actividad_cols:
            columnas.append({
                "nombre": col,
                "tipo": CalificacionesParser._detect_column_type(col),
            })

        filas = []
        errores = []
        for row_idx, row in enumerate(reader):
            alumno_val = row.get(alumno_col, "").strip()
            if not alumno_val:
                continue

            actividades = {}
            for col_info in columnas:
                raw_val = row.get(col_info["nombre"], "").strip()
                if raw_val:
                    actividades[col_info["nombre"]] = raw_val
                else:
                    actividades[col_info["nombre"]] = None

            filas.append({
                "alumno": alumno_val,
                "actividades": actividades,
            })

        return {
            "columnas": columnas,
            "filas": filas,
            "errores": errores,
        }

    @staticmethod
    def _parse_xlsx_grades(file_content: bytes) -> dict:
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("openpyxl is required to parse .xlsx files")

        wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)
        ws = wb.active
        if ws is None:
            return {"columnas": [], "filas": [], "errores": []}

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {"columnas": [], "filas": [], "errores": []}

        headers = [str(h).strip() if h else "" for h in rows[0]]
        if not headers or not headers[0]:
            return {"columnas": [], "filas": [], "errores": []}

        alumno_col = headers[0]
        actividad_cols = headers[1:]

        columnas = []
        for col in actividad_cols:
            columnas.append({
                "nombre": col,
                "tipo": CalificacionesParser._detect_column_type(col),
            })

        filas = []
        for row in rows[1:]:
            alumno_val = str(row[0]).strip() if row[0] is not None else ""
            if not alumno_val:
                continue

            actividades = {}
            for i, col_info in enumerate(columnas):
                col_idx = i + 1
                if col_idx < len(row) and row[col_idx] is not None:
                    raw_val = str(row[col_idx]).strip()
                    actividades[col_info["nombre"]] = raw_val if raw_val else None
                else:
                    actividades[col_info["nombre"]] = None

            filas.append({
                "alumno": alumno_val,
                "actividades": actividades,
            })

        return {
            "columnas": columnas,
            "filas": filas,
            "errores": [],
        }

    @staticmethod
    def generar_preview(parsed: dict) -> dict:
        columnas = parsed.get("columnas", [])
        filas = parsed.get("filas", [])

        actividades = []
        for col in columnas:
            actividades.append({
                "nombre": col["nombre"],
                "tipo": col["tipo"],
                "seleccionada": True,
            })

        muestra = filas[:5]

        return {
            "total_alumnos": len(filas),
            "actividades": actividades,
            "muestra": muestra,
        }

    @staticmethod
    def derivar_aprobado(
        nota_numerica: Decimal | None,
        nota_textual: str | None,
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> bool:
        if nota_numerica is not None:
            return nota_numerica >= Decimal(str(umbral_pct))
        if nota_textual is not None:
            return nota_textual in valores_aprobatorios
        return False

    @staticmethod
    def detect_completions(
        file_content: bytes,
        calificaciones_existentes: list,
    ) -> list:
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            return []

        headers = [h.strip() for h in reader.fieldnames]
        alumno_col = headers[0]
        estado_col = next((h for h in headers if h.lower() in ("estado", "state", "completado")), headers[-1])

        existing_set = set()
        for cal in calificaciones_existentes:
            if cal.nota_textual is not None or cal.nota_numerica is not None:
                existing_set.add((cal.entrada_padron_id or "", cal.actividad))

        entregas_sin_corregir = []
        for row in reader:
            alumno_val = row.get(alumno_col, "").strip()
            estado_val = row.get(estado_col, "").strip().lower()
            if not alumno_val:
                continue

            if estado_val not in ("completado", "finished", "completo"):
                continue

            for key, val in row.items():
                key_clean = key.strip()
                if key_clean == alumno_col or key_clean == estado_col:
                    continue
                if val and val.strip().lower() in ("completado", "finished", "completo", "si", "yes"):
                    if (alumno_val, key_clean) not in existing_set:
                        entregas_sin_corregir.append({
                            "alumno": alumno_val,
                            "actividad": key_clean,
                        })

        return entregas_sin_corregir
