## Why

El sistema necesita un tablón de avisos institucionales: anuncios de coordinación visibles para los usuarios según su rol, materia y cohorte, con ventana de vigencia y opción de acuse de recibo. Sin esto, toda comunicación institucional queda fuera del sistema.

## What Changes

### Modelos (2 nuevos)
- **Aviso**: alcance (Global/PorMateria/PorCohorte/PorRol), severidad, vigencia, orden, requiere_ack
- **AcknowledgmentAviso**: acuse de lectura por usuario

### Endpoints
| Método | Ruta | Descripción | Permiso |
|--------|------|-------------|---------|
| `POST` | `/api/avisos` | Crear aviso | `avisos:publicar` |
| `GET` | `/api/avisos` | Listar avisos visibles para el usuario | autenticado (filtrado por scope RN-20) |
| `GET` | `/api/avisos/{id}` | Detalle | autenticado (si visible) |
| `PUT` | `/api/avisos/{id}` | Editar | `avisos:publicar` |
| `DELETE` | `/api/avisos/{id}` | Eliminar (soft) | `avisos:publicar` |
| `POST` | `/api/avisos/{id}/ack` | Acuse de recibo | autenticado (propio) |
| `GET` | `/api/avisos/{id}/stats` | Contadores (total, ack) | `avisos:publicar` |

### Filtrado de visibilidad (RN-20)
- Global → todos los usuarios del tenant
- PorMateria → usuarios con asignación a esa materia
- PorCohorte → usuarios con asignación a esa cohorte
- PorRol → usuarios con ese rol
- Además: `rol_destino` filtra por rol específico (nullable = todos)
- Vigencia: solo visible si `ahora BETWEEN inicio_en AND fin_en` (RN-18)
- Orden: descendente por `orden` (mayor orden = más prioritario)

### Migración 011
- `aviso`, `acknowledgment_aviso`
