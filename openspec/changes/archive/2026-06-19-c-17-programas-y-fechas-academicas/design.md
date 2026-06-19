## Context

Activia Trace necesita gestionar dos conceptos académicos fundamentales: los **programas de materia** (documentos oficiales por materia × carrera × cohorte) y las **fechas académicas** (calendarización de parciales, TPs y coloquios). Ambos son datos de consulta frecuente para docentes y coordinación, y alimentan la generación de contenido para el aula virtual del LMS.

El sistema ya cuenta con los modelos base `Materia`, `Carrera` y `Cohorte` del change C-06, que son los ejes de asociación de estas nuevas entidades.

## Goals / Non-Goals

### Goals
- Modelar `ProgramaMateria` y `FechaAcademica` con tenant isolation, soft delete y timestamps.
- CRUD completo para programas (upload de referencia de archivo).
- CRUD completo para fechas académicas (listado tabular).
- Endpoint de generación de fragmento HTML listo para publicar en el aula virtual.
- Aislamiento multi-tenant completo (tenant_id en todas las tablas, filtro automático en repos).
- Tests de modelo, repositorio, router y multi-tenant.

### Non-Goals
- No se implementa almacenamiento real de archivos (solo referencia opaca).
- No se implementa generación de PDF ni formatos de exportación adicionales.
- No se implementa lógica de coloquios ni evaluaciones (eso es C-14).

## Decisions

1. **ProgramaMateria con referencia_archivo opaca en lugar de S3/Blob**
   - La KB especifica `referencia_archivo` como puntero opaco al servicio de almacenamiento. No se implementa un cliente de almacenamiento real — el campo guarda un identificador que otro sistema resolverá.
   - Alternativa descartada: implementar subida de archivos real al backend (scope extra, no necesario ahora).

2. **Router separado para programas y fechas (no meterlo en admin/estructura)**
   - Aunque ambos usan `estructura:gestionar`, son conceptos distintos con endpoints propios. Ubicarlos en `routers/programas.py` y `routers/fechas_academicas.py` sigue el patrón del proyecto (cada entidad tiene su router).
   - Alternativa descartada: meter todo en `admin/estructura.py` (ya está muy cargado con carreras, cohortes, materias).

3. **Repositories separados por entidad**
   - Sigue el patrón actual: un repository por modelo. `ProgramaMateriaRepository` y `FechaAcademicaRepository` heredan de `BaseRepository`.

4. **Uniqueness de FechaAcademica: `(tenant_id, materia_id, cohorte_id, tipo, numero, periodo)`**
   - No puede haber dos "1er Parcial" para la misma materia×cohorte×periodo. La unique constraint lo asegura.

5. **Uniqueness de ProgramaMateria: `(tenant_id, materia_id, carrera_id, cohorte_id)`**
   - Una materia solo tiene un programa por combinación carrera×cohorte.

## Risks / Trade-offs

- **[Riesgo] referencia_archivo como string libre** → no hay validación de que el archivo exista. Mitigación: es intencional — el campo es opaco y se resuelve en otro servicio.
- **[Riesgo] Fechas sin validación de superposición** → un coordinador podría cargar dos evaluaciones el mismo día. Mitigación: no se valida porque puede ser intencional (ej: dos turnos del mismo parcial). El diseño lo permite.

## Migration Plan

1. Crear modelos `ProgramaMateria` y `FechaAcademica`.
2. Generar migración Alembic `006_create_programa_materia_fecha_academica`.
3. Crear repositories.
4. Crear routers con schemas inline.
5. Agregar tests.
6. Rollback: `alembic downgrade -1`.

## Open Questions

Ninguna. El diseño está cubierto por la KB y los patrones existentes.
