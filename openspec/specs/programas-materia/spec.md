# Programas de Materia

> **Capability**: `programas-materia` (C-17)
> **Estado**: Propuesto
> **Dependencias**: `C-06 estructura-academica`

## Descripción

Gestión de programas/documentos oficiales de cada materia, asociados a una carrera y cohorte específicas. Cada combinación (materia × carrera × cohorte) puede tener un programa asociado.

## Entidad: ProgramaMateria

```
ProgramaMateria {
  id                  : UUID       — PK
  tenant_id           : UUID       — FK → Tenant
  materia_id          : UUID       — FK → Materia
  carrera_id          : UUID       — FK → Carrera
  cohorte_id          : UUID       — FK → Cohorte
  titulo              : string     — título descriptivo del programa
  referencia_archivo  : string     — referencia opaca al archivo (no un path de disco)
  cargado_at          : datetime   — timestamp de carga
}
```

**Unique constraint**: `(tenant_id, materia_id, carrera_id, cohorte_id)` — una materia solo tiene un programa por carrera×cohorte.

## API

### `GET /api/programas`

Lista todos los programas del tenant activo.

**Query params**: `materia_id`, `carrera_id`, `cohorte_id` (filtros opcionales)

**Response**: `200` con array de `ProgramaMateriaResponse`

### `GET /api/programas/{id}`

Obtiene un programa por ID.

**Response**: `200` con `ProgramaMateriaResponse` | `404`

### `POST /api/programas`

Crea un nuevo programa.

**Body**: `ProgramaMateriaCreate` (materia_id, carrera_id, cohorte_id, titulo, referencia_archivo)

**Response**: `201` con `ProgramaMateriaResponse`

**Errors**: `409` si ya existe programa para esa materia×carrera×cohorte

### `PUT /api/programas/{id}`

Actualiza un programa existente (título y/o referencia_archivo).

**Response**: `200` con `ProgramaMateriaResponse` | `404`

### `DELETE /api/programas/{id}`

Soft-delete de un programa.

**Response**: `204` | `404`

### `POST /api/programas/contenido-lms`

Genera un fragmento HTML con los programas activos, listo para publicar en el aula virtual del LMS.

**Body**: opcional con filtros (materia_id, cohorte_id)

**Response**: `200` con `{ "html": "..." }`

## Permisos

Todos los endpoints requieren `estructura:gestionar` (ADMIN, COORDINADOR).
