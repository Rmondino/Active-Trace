## Servicio de Análisis

### `AnalisisService` en `services/analisis_service.py`

Servicio sin estado que recibe datos de repositorios y computa los análisis. No accede a DB directamente.

```python
class AnalisisService:
    def __init__(self, calificacion_repo, umbral_repo, version_padron_repo, entrada_padron_repo):
        ...

    async def alumnos_atrasados(self, materia_id: str, cohorte_id: str, tenant_id: str) -> list[dict]:
        """Retorna lista de alumnos atrasados con detalle de causas (RN-06)."""
        ...

    async def ranking_aprobadas(self, materia_id: str, tenant_id: str) -> list[dict]:
        """Ranking descendente de alumnos con >=1 actividad aprobada (RN-09)."""
        ...

    async def reporte_rapido(self, materia_id: str, tenant_id: str) -> dict:
        """Métricas agregadas de la materia."""
        ...

    async def notas_finales(self, materia_id: str, cohorte_id: str, tenant_id: str) -> list[dict]:
        """Promedio simple por alumno."""
        ...

    async def exportar_sin_corregir(self, materia_id: str, tenant_id: str) -> bytes:
        """Genera archivo xlsx con entregas textuales sin calificar (RN-07/08)."""
        ...

    async def monitor(self, scope: str, filtros: dict, user_id: str, tenant_id: str) -> list[dict]:
        """Monitor transversal o propio con filtros."""
        ...
```

### Cómputo de atrasados (RN-06)

```
Por cada entrada_padron_id en el padrón activo de (materia, cohorte):
  1. Obtener todas las calificaciones de ese alumno para la materia
  2. Detectar actividades FALTANTES: actividades del import sin calificación
  3. Detectar NOTA BAJA: calificaciones con aprobado=False
  4. Si cumple al menos una condición → es atrasado

Output:
[
  {
    "alumno": "Juan Pérez",
    "entrada_padron_id": "uuid",
    "email": "j***@example.com",
    "comision": "A",
    "es_atrasado": true,
    "causas": {
      "faltantes": ["TP2", "TP3"],
      "baja_nota": ["Parcial 1 (Real)"]
    },
    "total_actividades": 5,
    "aprobadas": 2,
    "desaprobadas": 1,
    "sin_nota": 2
  }
]
```

### Cómputo de ranking (RN-09)

```
1. Obtener todas las calificaciones de la materia
2. Agrupar por entrada_padron_id
3. Contar aprobadas por alumno
4. Filtrar alumnos con count >= 1 (RN-09)
5. Ordenar descendente

Output:
[
  { "alumno": "María García", "aprobadas": 4, "total": 5 },
  { "alumno": "Juan Pérez",   "aprobadas": 2, "total": 5 },
  ...
]
```

### Reporte rápido (F2.4)

```
{
  "materia": "Programación I",
  "total_alumnos": 30,
  "total_actividades": 5,
  "alumnos_atrasados": 8,
  "tasa_aprobacion_gral": 0.73,
  "actividades": [
    { "nombre": "Parcial 1 (Real)", "tasa_aprobacion": 0.80, "promedio": 72.5 },
    { "nombre": "TP Grupal", "tasa_aprobacion": 0.65, "promedio": null }
  ]
}
```

### Notas finales (F2.5)

```
[
  {
    "alumno": "Juan Pérez",
    "entrada_padron_id": "uuid",
    "actividades": {
      "Parcial 1 (Real)": 75,
      "TP Grupal": "Satisfactorio"
    },
    "promedio_numerico": 75.0,
    "aprobadas": 2,
    "total_actividades": 2
  }
]
```

### Export sin corregir (F2.6)

Genera un `.xlsx` descargable con:
- Columnas: Alumno, Actividad, Estado
- Solo actividades textuales sin calificación (RN-08)
- Filas: cada (alumno, actividad) que está completada pero sin nota

### Monitor (F2.7 / F2.8 / F2.9)

Un solo endpoint con distintos filtros según scope:

```
GET /api/analisis/monitor?scope=general|propio
```

**Filtros comunes**: materia_id, regional, comision, busqueda (texto libre), actividad, estado (atrasado/no_atrasado)

**Filtros adicionales (scope=general)**: desde, hasta (rango de fechas)

**Scope `propio`** (F2.8): filtra por las asignaciones del usuario logueado como TUTOR o PROFESOR.

**Scope `general`** (F2.7/F2.9): todos los alumnos del tenant. COORDINADOR/ADMIN.

Output paginado con filtros aplicados server-side.

## Endpoints Resumen

| Método | Ruta | Permiso | Scope | Descripción |
|--------|------|---------|-------|-------------|
| `GET` | `/api/analisis/atrasados` | `atrasados:ver` | (propio) | Alumnos atrasados por materia |
| `GET` | `/api/analisis/ranking` | `atrasados:ver` | (propio) | Ranking de aprobadas |
| `GET` | `/api/analisis/reporte-rapido` | `atrasados:ver` | (propio) | Métricas agregadas |
| `GET` | `/api/analisis/notas-finales` | `atrasados:ver` | (propio) | Notas finales agrupadas |
| `GET` | `/api/analisis/exportar-sin-corregir` | `atrasados:ver` | (propio) | Export xlsx |
| `GET` | `/api/analisis/monitor` | `atrasados:ver` | general/propio | Monitor con filtros |

## Permisos

Agregar al seed:
- `atrasados:ver` — visualizar análisis y reportes (TUTOR, PROFESOR, COORDINADOR, ADMIN)

## Tests (TDD estricto — governance MEDIO)

### Safety Net
- Ejecutar tests existentes (311 tests), capturar baseline.

### AnalisisService
- atrasados: alumno con faltantes → es atrasado; alumno con nota < umbral → es atrasado; alumno con todo ok → no atrasado.
- ranking: orden descendente; excluye alumnos sin aprobadas.
- reporte_rapido: métricas correctas.
- notas_finales: promedio agrupado.
- exportar_sin_corregir: solo textuales; xlsx generado.
- monitor: filtros por materia, comisión, estado; scope propio filtra por usuario.

### Router
- 403 sin permiso `atrasados:ver`.
- 404 materia no existe.
- Multi-tenant isolation.
- Scope (propio) vs scope global.

### Export
- Archivo xlsx válido (bytes con cabecera correcta).
- Content-Type correcto.
