# Fechas Académicas

> **Capability**: `fechas-academicas` (C-17)
> **Estado**: Propuesto
> **Dependencias**: `C-06 estructura-academica`

## Descripción

Calendarización de instancias evaluativas (parciales, trabajos prácticos, coloquios, recuperatorios) dentro de un período académico. Cada fecha se asocia a una materia y cohorte, con tipo, número de instancia y título descriptivo.

## Entidad: FechaAcademica

```
FechaAcademica {
  id          : UUID       — PK
  tenant_id   : UUID       — FK → Tenant
  materia_id  : UUID       — FK → Materia
  cohorte_id  : UUID       — FK → Cohorte
  tipo        : enum       — Parcial | TP | Coloquio | Recuperatorio
  numero      : integer    — número de instancia (1er parcial, 2do parcial, etc.)
  periodo     : string     — cuatrimestre/año (ej: "2026-1")
  fecha       : date       — fecha de la evaluación
  titulo      : string     — título descriptivo (ej: "1er Parcial - Unidades 1 a 4")
}
```

**Unique constraint**: `(tenant_id, materia_id, cohorte_id, tipo, numero, periodo)` — no duplicados de instancia × tipo × periodo.

## API

### `GET /api/fechas-academicas`

Lista todas las fechas académicas del tenant activo.

**Query params**: `materia_id`, `cohorte_id`, `tipo`, `periodo` (filtros opcionales)

**Response**: `200` con array de `FechaAcademicaResponse`

### `GET /api/fechas-academicas/{id}`

Obtiene una fecha por ID.

**Response**: `200` con `FechaAcademicaResponse` | `404`

### `POST /api/fechas-academicas`

Crea una nueva fecha académica.

**Body**: `FechaAcademicaCreate` (materia_id, cohorte_id, tipo, numero, periodo, fecha, titulo)

**Response**: `201` con `FechaAcademicaResponse`

**Errors**: `409` si ya existe esa combinación (materia, cohorte, tipo, numero, periodo)

### `PUT /api/fechas-academicas/{id}`

Actualiza una fecha existente.

**Response**: `200` con `FechaAcademicaResponse` | `404`

### `DELETE /api/fechas-academicas/{id}`

Soft-delete de una fecha académica.

**Response**: `204` | `404`

### `POST /api/fechas-academicas/contenido-lms`

Genera un fragmento HTML con el calendario evaluativo, listo para publicar en el aula virtual del LMS.

**Body**: opcional con filtros (materia_id, cohorte_id)

**Response**: `200` con `{ "html": "..." }`

## Permisos

Todos los endpoints requieren `estructura:gestionar` (ADMIN, COORDINADOR).
