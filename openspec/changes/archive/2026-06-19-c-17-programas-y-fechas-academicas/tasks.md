## 1. Modelos

- [x] 1.1 Crear `app/models/programa_materia.py` con modelo `ProgramaMateria` (id, tenant_id, materia_id, carrera_id, cohorte_id, titulo, referencia_archivo, cargado_at) + mixins
- [x] 1.2 Crear `app/models/fecha_academica.py` con modelo `FechaAcademica` (id, tenant_id, materia_id, cohorte_id, tipo, numero, periodo, fecha, titulo) + unique constraint + mixins

## 2. Migración Alembic

- [x] 2.1 Crear migración `006_create_programa_materia_fecha_academica` con ambas tablas

## 3. Repositories

- [x] 3.1 Crear `app/repositories/programa_repository.py` con `ProgramaMateriaRepository`
- [x] 3.2 Crear `app/repositories/fecha_academica_repository.py` con `FechaAcademicaRepository`

## 4. Router: Programas

- [x] 4.1 Crear `app/routers/programas.py` con CRUD completo de programas + schema inline
- [x] 4.2 Crear `app/routers/fechas_academicas.py` con CRUD completo de fechas + schema inline
- [x] 4.3 Registrar ambos routers en `app/main.py`
- [x] 4.4 Implementar endpoints `/api/programas/contenido-lms` y `/api/fechas-academicas/contenido-lms`

## 5. Tests

- [x] 5.1 Tests de modelo `ProgramaMateria`: creación, unique constraint por tenant
- [x] 5.2 Tests de modelo `FechaAcademica`: creación, unique constraint, enum tipo
- [x] 5.3 Tests de repositorio programa: CRUD, tenant isolation
- [x] 5.4 Tests de repositorio fecha: CRUD, tenant isolation, filtros
- [x] 5.5 Tests de router programas: CRUD via HTTP + permiso + tenant isolation + contenido-lms
- [x] 5.6 Tests de router fechas: CRUD via HTTP + permiso + tenant isolation + contenido-lms
