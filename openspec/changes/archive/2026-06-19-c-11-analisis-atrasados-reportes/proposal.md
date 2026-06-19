## Why

Con C-10 tenemos calificaciones importadas y umbrales configurados. El siguiente paso lógico es **analizar esos datos**: detectar alumnos atrasados, ranking de actividades, notas finales, y monitores de seguimiento. Sin esto, los datos importados son solo números — el análisis es el valor real del sistema.

Este change no crea modelos nuevos; toda la lógica es de **cómputo sobre datos existentes** (Calificacion + UmbralMateria + VersionPadron).

## What Changes

### Servicios de análisis (sin nuevos modelos)

| Funcionalidad | Descripción | Reglas |
|--------------|-------------|--------|
| **F2.2** Alumnos atrasados | Alumnos con actividades faltantes o nota < umbral | RN-06 |
| **F2.3** Ranking aprobadas | Alumnos ordenados por cantidad de actividades aprobadas | RN-09 |
| **F2.4** Reportes rápidos | Métricas clave de la materia (total alumnos, % aprobación, actividades) | — |
| **F2.5** Notas finales | Promedio/agrupación de notas por alumno | — |
| **F2.6** Export TPs sin corregir | Exportable con entregas textuales sin calificación | RN-07/08 |
| **F2.7** Monitor general | Vista transversal de todos los alumnos del tenant | — |
| **F2.8** Monitor seguimiento | Vista filtrable por tutor/profesor (alumno, comisión, actividad) | — |
| **F2.9** Monitor extendido | F2.8 + rango de fechas para coordinación/admin | — |

### API endpoints

```
GET /api/analisis/atrasados?materia_id=X&cohorte_id=Y
GET /api/analisis/ranking?materia_id=X
GET /api/analisis/reporte-rapido?materia_id=X
GET /api/analisis/notas-finales?materia_id=X&cohorte_id=Y
GET /api/analisis/exportar-sin-corregir?materia_id=X
GET /api/analisis/monitor?scope=general|propio&materia_id=&regional=&comision=&alumno=&actividad=&desde=&hasta=
```

### Cómputos clave

**Alumno atrasado** (RN-06):
```python
# Para cada alumno del padrón activo de la materia:
tiene_faltantes = alguna actividad sin registro de calificación
tiene_baja_nota = alguna calificación con nota_numerica < umbral OR nota_textual ∉ aprobatorios
es_atrasado = tiene_faltantes OR tiene_baja_nota
```

**Ranking** (RN-09):
```python
# Solo alumnos con ≥1 actividad aprobada
ranking = sorted(aprobadas_count por alumno, desc)
excluye_alumnos_sin_aprobadas
```

**Notas finales**:
```python
# Promedio simple de notas numéricas por alumno
# Agrupado por actividad
```

**Monitor general** (F2.7):
- Vista transversal: todos los alumnos del tenant con su estado
- Filtros: materia, regional, comisión, búsqueda libre, estado de actividad
- Exportable

### Permisos
- `atrasados:ver` — nuevo permiso para todos los endpoints de análisis
- Scope `(propio)`: TUTOR/PROFESOR ven solo sus alumnos
- Scope global: COORDINADOR/ADMIN ven todo el tenant

### Dependencias
- Ninguna nueva — todo es consulta sobre datos existentes
- Reusa openpyxl para export (xlsx)

## Capabilities

- `analisis-atrasados`: Cómputo de alumnos atrasados por materia.
- `analisis-ranking`: Ranking de aprobación.
- `analisis-reportes`: Reportes rápidos y notas finales.
- `analisis-monitor`: Monitores general y de seguimiento.
- `analisis-export`: Exportación de trabajos sin corregir.

## Impact

- **Nuevo permiso**: `atrasados:ver` en seed de C-04 (simulado en tests).
- **Servicios**: `backend/app/services/analisis_service.py` (cómputos).
- **Router**: `backend/app/routers/analisis.py` (6 endpoints).
- **Sin migración**: no se crean tablas nuevas.
- **Tests**: cómputos contra datos seedeados en DB de test.
