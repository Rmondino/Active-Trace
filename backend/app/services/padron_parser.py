"""PadronParser service — parse .xlsx and .csv roster files with preview."""

import csv
import io

from app.core.security import mask_email


class PadronParser:
    EXPECTED_COLUMNS = {"nombre", "apellidos", "email"}
    OPTIONAL_COLUMNS = {"comision", "regional"}

    @staticmethod
    def parse_xlsx(file_content: bytes) -> dict:
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("openpyxl is required to parse .xlsx files")

        wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)
        ws = wb.active
        if ws is None:
            return {"total_filas": 0, "columnas": [], "filas": [], "errores": []}

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return {"total_filas": 0, "columnas": [], "filas": [], "errores": []}

        headers = [str(h).strip().lower() if h else "" for h in rows[0]]
        PadronParser._validate_headers(headers)

        filas = []
        for row in rows[1:]:
            if all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            fila = {}
            for i, header in enumerate(headers):
                val = str(row[i]).strip() if i < len(row) and row[i] is not None else ""
                fila[header] = val if val else None
            filas.append(fila)

        return {
            "total_filas": len(filas),
            "columnas": headers,
            "filas": filas,
            "errores": [],
        }

    @staticmethod
    def parse_csv(file_content: bytes) -> dict:
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        if reader.fieldnames is None:
            return {"total_filas": 0, "columnas": [], "filas": [], "errores": []}

        headers = [h.strip().lower() for h in reader.fieldnames]
        PadronParser._validate_headers(headers)

        filas = []
        for row in reader:
            clean = {}
            for h in headers:
                val = row.get(h, "").strip() if row.get(h) else ""
                clean[h] = val if val else None
            if any(clean.get(h) for h in PadronParser.EXPECTED_COLUMNS):
                filas.append(clean)

        return {
            "total_filas": len(filas),
            "columnas": headers,
            "filas": filas,
            "errores": [],
        }

    @staticmethod
    def _validate_headers(headers: list[str]) -> None:
        header_set = set(headers)
        missing = PadronParser.EXPECTED_COLUMNS - header_set
        if missing:
            raise ValueError(f"Columnas requeridas faltantes: {', '.join(sorted(missing))}")

    @staticmethod
    def validate_filas(filas: list[dict]) -> list[dict]:
        validas = []
        for fila in filas:
            email = fila.get("email", "")
            if email and email.strip():
                validas.append(fila)
        return validas

    @staticmethod
    def generar_preview(filas: list[dict]) -> dict:
        muestra = []
        for fila in filas[:5]:
            item = dict(fila)
            if item.get("email"):
                item["email"] = mask_email(item["email"])
            muestra.append(item)

        columnas = list(PadronParser.EXPECTED_COLUMNS | PadronParser.OPTIONAL_COLUMNS)
        presentes = set()
        if filas:
            presentes = set(filas[0].keys())
        columnas = [c for c in columnas if c in presentes]

        return {
            "total_filas": len(filas),
            "columnas": columnas,
            "muestra": muestra,
            "errores": [],
        }
