## 1. Modelos SQLAlchemy

- [x] 1.1 Crear `backend/app/models/carrera.py` con UUID PK, codigo, nombre, estado, soft delete y tenant scope
- [x] 1.2 Crear `backend/app/models/cohorte.py` con UUID PK, carrera_id FK, nombre, anio, vig_desde, vig_hasta, estado, soft delete y tenant scope
- [x] 1.3 Crear `backend/app/models/materia.py` con UUID PK, codigo, nombre, estado, soft delete y tenant scope
- [x] 1.4 Registrar los tres modelos en `backend/app/models/__init__.py`

## 2. Repositorios

- [x] 2.1 Crear `CarreraRepository` en `backend/app/repositories/carrera_repository.py` con método `exists_by_codigo` para validar unicidad
- [x] 2.2 Crear `CohorteRepository` en `backend/app/repositories/cohorte_repository.py` con validación de carrera activa para cohortes abiertas y `exists_by_nombre_y_carrera`
- [x] 2.3 Crear `MateriaRepository` en `backend/app/repositories/materia_repository.py` con método `exists_by_codigo`
- [x] 2.4 Registrar repositorios en `backend/app/repositories/__init__.py`

## 3. Schemas Pydantic y Router

- [x] 3.1 Crear schemas request/response para Carrera (CarreraCreate, CarreraUpdate, CarreraResponse, CarreraListResponse)
- [x] 3.2 Crear schemas para Cohorte (CohorteCreate, CohorteUpdate, CohorteResponse, CohorteListResponse)
- [x] 3.3 Crear schemas para Materia (MateriaCreate, MateriaUpdate, MateriaResponse, MateriaListResponse)
- [x] 3.4 Crear `backend/app/routers/admin/__init__.py` con el router de admin
- [x] 3.5 Crear `backend/app/routers/admin/estructura.py` con endpoints GET/POST/PUT/DELETE para carreras, cohortes y materias, protegidos con `require_permission("estructura:gestionar")`
- [x] 3.6 Registrar `admin/estructura.py` en `backend/app/main.py`

## 4. Migración Alembic 004

- [x] 4.1 Generar migración 004 con tablas `carrera`, `cohorte`, `materia` usando `alembic revision --autogenerate`
- [x] 4.2 Verificar que la migración incluye UniqueConstraint para `(tenant_id, codigo)` en carrera y materia, y `(tenant_id, carrera_id, nombre)` en cohorte
- [x] 4.3 Ejecutar `alembic upgrade head` y verificar que las tablas se crean correctamente

## 5. Tests

- [x] 5.1 Escribir tests de modelo: instanciación, tenant_id automático, relaciones
- [x] 5.2 Escribir tests de repositorio: create, get, list, update, soft_delete, restore, exists_by_codigo, unicidad
- [x] 5.3 Escribir tests de router: CRUD exitoso, validación de unicidad (409), regla carrera-inactiva (400), soft delete (204), 403 sin permiso
- [x] 5.4 Escribir tests de aislamiento multi-tenant: crear en tenant A, verificar no visible en tenant B
- [x] 5.5 Verificar cobertura ≥80% líneas y ≥90% reglas de negocio
