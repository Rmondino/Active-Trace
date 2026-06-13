# RBAC — Seed de Roles y Permisos

## ADDED Requirements

### Requirement: Seed de roles del dominio
La migración 003 SHALL insertar los 7 roles del dominio si no existen (idempotente):

| slug | nombre |
|------|--------|
| alumno | ALUMNO |
| tutor | TUTOR |
| profesor | PROFESOR |
| coordinador | COORDINADOR |
| nexo | NEXO |
| admin | ADMIN |
| finanzas | FINANZAS |

#### Scenario: Migración ejecutada por primera vez
- **WHEN** se ejecuta `alembic upgrade head` en una base vacía
- **THEN** los 7 roles del dominio existen en la tabla `rol`

#### Scenario: Migración ejecutada dos veces (idempotente)
- **WHEN** se ejecuta `alembic upgrade head` por segunda vez
- **THEN** no se crean roles duplicados (INSERT ... ON CONFLICT DO NOTHING)

### Requirement: Seed de permisos base
La migración 003 SHALL insertar los permisos base del sistema si no existen. Cada permiso tiene código `modulo:accion` y descripción.

Permisos base:

| Código | Descripción |
|--------|-------------|
| calificaciones:importar | Importar calificaciones de alumnos |
| atrasados:ver | Ver alumnos atrasados |
| entregas:ver_sin_corregir | Ver entregas sin corregir |
| comunicacion:enviar | Enviar comunicaciones a alumnos |
| comunicacion:aprobar | Aprobar comunicaciones masivas |
| encuentros:gestionar | Gestionar encuentros y guardias |
| guardias:registrar | Registrar guardias |
| tareas:gestionar | Gestionar tareas internas |
| avisos:publicar | Publicar avisos |
| equipos:asignar | Gestionar equipos docentes |
| estructura:gestionar | Gestionar estructura académica |
| usuarios:gestionar | Gestionar usuarios del tenant |
| auditoria:ver | Ver registros de auditoría |
| grilla:operar | Operar grilla salarial |
| liquidaciones:calcular | Calcular y cerrar liquidaciones |
| facturas:gestionar | Gestionar facturas |
| configuracion:gestionar | Configurar el tenant |
| impersonacion:usar | Usar impersonación |
| rbac:gestionar | Gestionar roles y permisos |
| perfil:ver | Ver estado académico propio (ALUMNO) |
| evaluaciones:reservar | Reservar instancias de evaluación |
| avisos:confirmar | Confirmar avisos (acknowledgment) |

#### Scenario: Permisos base existen post-migración
- **WHEN** se ejecuta `alembic upgrade head`
- **THEN** los 22 permisos base existen en la tabla `permiso`

### Requirement: Seed de la matriz Rol→Permiso (KB §3.3)
La migración 003 SHALL insertar la matriz de permisos según `knowledge-base/03_actores_y_roles.md` §3.3, con su alcance (`propio` | `global`).

Matriz completa:

| Permiso | ALUMNO | TUTOR | PROFESOR | COORDINADOR | ADMIN | FINANZAS |
|---------|:------:|:-----:|:--------:|:-----------:|:-----:|:--------:|
| perfil:ver | global | — | — | — | — | — |
| evaluaciones:reservar | global | — | — | — | — | — |
| avisos:confirmar | global | global | global | global | global | global |
| calificaciones:importar | — | — | propio | global | global | — |
| atrasados:ver | — | global | propio | global | global | — |
| entregas:ver_sin_corregir | — | global | propio | global | global | — |
| comunicacion:enviar | — | — | propio | global | global | — |
| comunicacion:aprobar | — | — | — | global | global | — |
| encuentros:gestionar | — | global | propio | global | global | — |
| guardias:registrar | — | propio | propio | global | global | — |
| tareas:gestionar | — | — | propio | global | global | — |
| avisos:publicar | — | — | — | global | global | — |
| equipos:asignar | — | — | — | global | global | — |
| estructura:gestionar | — | — | — | — | global | — |
| usuarios:gestionar | — | — | — | — | global | — |
| auditoria:ver | — | — | — | propio | global | global |
| grilla:operar | — | — | — | — | — | global |
| liquidaciones:calcular | — | — | — | — | — | global |
| facturas:gestionar | — | — | — | — | — | global |
| configuracion:gestionar | — | — | — | — | global | — |
| impersonacion:usar | — | — | — | — | global | — |
| rbac:gestionar | — | — | — | — | global | — |

#### Scenario: Matriz completa post-migración
- **WHEN** se ejecuta `alembic upgrade head`
- **THEN** los registros en `rol_permiso` reflejan exactamente la matriz de la KB §3.3

#### Scenario: ALUMNO tiene permisos limitados
- **WHEN** se consultan los permisos del rol ALUMNO
- **THEN** solo tiene `perfil:ver`, `evaluaciones:reservar` y `avisos:confirmar`

#### Scenario: ADMIN tiene todos los permisos excepto los financieros
- **WHEN** se consultan los permisos del rol ADMIN
- **THEN** tiene todos los permisos excepto `grilla:operar`, `liquidaciones:calcular`, `facturas:gestionar`
