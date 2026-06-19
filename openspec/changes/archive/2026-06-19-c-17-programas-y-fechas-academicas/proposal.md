## Why

Cada materia necesita un programa oficial (documento) asociado por carrera y cohorte, y un calendario de fechas evaluativas (parciales, TPs, coloquios) visibles para docentes y coordinación. Hoy no existe un lugar centralizado para gestionar estos datos — los programas están dispersos y las fechas se comunican informalmente.

## What Changes

- Nuevo modelo `ProgramaMateria` para asociar el programa/documento oficial de una materia × carrera × cohorte.
- Nuevo modelo `FechaAcademica` para calendarizar instancias evaluativas por materia × cohorte × número.
- API CRUD para programas (`/api/programas`) con permiso `estructura:gestionar`.
- API CRUD para fechas académicas (`/api/fechas-academicas`) con permiso `estructura:gestionar`.
- Endpoint de generación de contenido LMS (fragmento HTML ready para el aula virtual).
- Migración Alembic `006_create_programa_materia_fecha_academica`.

## Capabilities

### New Capabilities
- `programas-materia`: gestionar programas/documentos oficiales de materias por carrera y cohorte
- `fechas-academicas`: gestionar y consultar el calendario evaluativo (parciales, TPs, coloquios)

### Modified Capabilities
<!-- No existing specs are modified -->

## Impact

- Nuevos modelos SQLAlchemy: `ProgramaMateria`, `FechaAcademica`
- Nuevos repositories: `ProgramaMateriaRepository`, `FechaAcademicaRepository`
- Nuevas rutas: `/api/programas/*`, `/api/fechas-academicas/*`
- Nueva migración Alembic (006)
- Dependencias: `C-06 estructura-academica` (Materia, Carrera, Cohorte)
