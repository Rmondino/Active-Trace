## Endpoints

### 1. Mis equipos (F4.2)
```
GET /api/equipos/mis-equipos?filtro_estado=&filtro_materia=&filtro_rol=&filtro_carrera=&filtro_cohorte=
```
Retorna las asignaciones del usuario autenticado, con datos expandidos:
```json
{
  "asignaciones": [
    {
      "id": "uuid",
      "rol": "PROFESOR",
      "materia": { "id": "uuid", "nombre": "Programación I", "codigo": "PROG_I" },
      "carrera": { "id": "uuid", "nombre": "TUPAD" },
      "cohorte": { "id": "uuid", "nombre": "2025 AGO" },
      "comisiones": ["A", "B"],
      "responsable": { "id": "uuid", "nombre": "Carlos López" },
      "desde": "2025-03-01",
      "hasta": "2025-12-31",
      "vigente": true
    }
  ]
}
```
Filtros opcionales: estado (vigente/no_vigente/todos), materia_id, rol, carrera_id, cohorte_id.

### 2. Gestión de asignaciones (F4.3)
```
GET /api/equipos/asignaciones?materia_id=&carrera_id=&cohorte_id=&usuario_id=&rol=&busqueda=
```
Vista para COORDINADOR/ADMIN de todas las asignaciones del tenant con filtros. Paginado.

### 3. Asignación masiva (F4.4)
```
POST /api/equipos/asignaciones/masiva
Body: {
  "docente_ids": ["uuid1", "uuid2"],
  "materia_id": "uuid",
  "carrera_id": "uuid",
  "cohorte_id": "uuid",
  "rol": "PROFESOR",
  "comisiones": ["A", "B"],
  "desde": "2025-03-01",
  "hasta": "2025-12-31",
  "responsable_id": "uuid | null"
}
→ Response 201: { "total_creadas": 2, "asignaciones": [{"id": "uuid", "usuario_id": "uuid"}, ...] }
```
Crea una `Asignacion` por cada `docente_id` en el array. Mismo contexto, rol, comisiones y vigencia para todos.

### 4. Clonar equipo (F4.5, RN-12)
```
POST /api/equipos/clonar
Body: {
  "origen_materia_id": "uuid",
  "origen_carrera_id": "uuid",
  "origen_cohorte_id": "uuid",
  "destino_materia_id": "uuid",
  "destino_carrera_id": "uuid",
  "destino_cohorte_id": "uuid",
  "nuevo_desde": "2026-03-01",
  "nuevo_hasta": "2026-12-31"
}
→ Response 201: { "total_clonadas": 5, "asignaciones": [...] }
```
1. Busca todas las asignaciones vigentes del equipo origen
2. Las duplica con los nuevos IDs, nuevas fechas, nuevo contexto (materia/carrera/cohorte destino)
3. Preserva: usuario_id, rol, comisiones, responsable_id
4. Audit: `ASIGNACION_MODIFICAR`

### 5. Vigencia general (F4.6)
```
PATCH /api/equipos/vigencia
Body: {
  "materia_id": "uuid",
  "carrera_id": "uuid",
  "cohorte_id": "uuid",
  "nuevo_desde": "2026-03-01",
  "nuevo_hasta": "2026-12-31"
}
→ Response 200: { "total_actualizadas": 5 }
```
Actualiza `desde` y/o `hasta` de todas las asignaciones que coincidan con el filtro `(materia, carrera, cohorte)`.

### 6. Exportar equipo (F4.7)
```
GET /api/equipos/export?materia_id=X&carrera_id=Y&cohorte_id=Z
→ Response: xlsx file
```
Genera un `.xlsx` con columnas:
- Docente (nombre + apellido), Email, Rol, Comisiones, Materia, Carrera, Cohorte, Desde, Hasta, Vigente, Responsable

## Servicio

### EquipoService

```python
class EquipoService:
    def __init__(self, asignacion_repo, user_repo, materia_repo, carrera_repo, cohorte_repo, audit_log_service):
        ...

    async def mis_equipos(self, usuario_id: str, tenant_id: str, filtros: dict) -> list[dict]:
        """Retorna asignaciones del usuario con datos expandidos."""
        asignaciones = await self.asignacion_repo.get_by_usuario(tenant_id, usuario_id, solo_vigentes=False)
        # Aplicar filtros en Python
        # Expandir con datos de materia, carrera, cohorte
        # Calcular vigente
        return result

    async def listar_asignaciones(self, tenant_id: str, filtros: dict) -> list[dict]:
        """Vista de COORDINADOR/ADMIN con filtros."""
        ...

    async def asignacion_masiva(self, data: dict, user_id: str, tenant_id: str) -> dict:
        """Crea N asignaciones, una por docente_id."""
        asignaciones = [
            Asignacion(usuario_id=did, materia_id=data["materia_id"], ...)
            for did in data["docente_ids"]
        ]
        await self.asignacion_repo.bulk_create(asignaciones)
        await self.audit_log_service.log(accion="ASIGNACION_MODIFICAR", ...)
        return {"total_creadas": len(asignaciones), "asignaciones": [...]}

    async def clonar_equipo(self, data: dict, user_id: str, tenant_id: str) -> dict:
        """Clona asignaciones vigentes de origen a destino (RN-12)."""
        origen = await self.asignacion_repo.get_by_materia(tenant_id, data["origen_materia_id"])
        # Filtrar por carrera + cohorte + vigentes
        nuevas = [
            Asignacion(
                usuario_id=a.usuario_id, rol=a.rol, comisiones=a.comisiones,
                responsable_id=a.responsable_id,
                materia_id=data["destino_materia_id"],
                carrera_id=data["destino_carrera_id"],
                cohorte_id=data["destino_cohorte_id"],
                desde=data["nuevo_desde"], hasta=data["nuevo_hasta"],
                tenant_id=tenant_id,
            )
            for a in origen if a.carrera_id == data["origen_carrera_id"]
            and a.cohorte_id == data["origen_cohorte_id"]
            and a.desde <= date.today() and (a.hasta is None or a.hasta >= date.today())
        ]
        await self.asignacion_repo.bulk_create(nuevas)
        await self.audit_log_service.log(accion="ASIGNACION_MODIFICAR", ...)
        return {"total_clonadas": len(nuevas), "asignaciones": [...]}

    async def actualizar_vigencia(self, data: dict, user_id: str, tenant_id: str) -> dict:
        """Actualiza desde/hasta de asignaciones que matcheen (materia, carrera, cohorte)."""
        asignaciones = await self.asignacion_repo.get_by_materia(tenant_id, data["materia_id"])
        # Filtrar por carrera + cohorte
        actualizadas = 0
        for a in asignaciones:
            if a.carrera_id == data["carrera_id"] and a.cohorte_id == data["cohorte_id"]:
                if "nuevo_desde" in data:
                    a.desde = data["nuevo_desde"]
                if "nuevo_hasta" in data:
                    a.hasta = data["nuevo_hasta"]
                actualizadas += 1
        await self.session.flush()
        await self.audit_log_service.log(accion="ASIGNACION_MODIFICAR", ...)
        return {"total_actualizadas": actualizadas}

    async def exportar_equipo(self, materia_id: str, carrera_id: str, cohorte_id: str, tenant_id: str) -> bytes:
        """Genera xlsx con openpyxl."""
        asignaciones = await self.asignacion_repo.get_by_materia(tenant_id, materia_id)
        # Filtrar por carrera + cohorte
        # Generar xlsx
        wb = Workbook()
        ws = wb.active
        ws.append(["Docente", "Email", "Rol", "Comisiones", "Materia", "Carrera", "Cohorte", "Desde", "Hasta", "Vigente", "Responsable"])
        for a in filtrar:
            ws.append([...])
        output = BytesIO()
        wb.save(output)
        return output.getvalue()
```

## Router

```python
router = APIRouter(prefix="/api/equipos", tags=["equipos"])

@router.get("/mis-equipos")  # cualquier rol autenticado
@router.get("/asignaciones")  # equipos:asignar
@router.post("/asignaciones/masiva")  # equipos:asignar, audit
@router.post("/clonar")  # equipos:asignar, audit
@router.patch("/vigencia")  # equipos:asignar, audit
@router.get("/export")  # equipos:asignar
```

## Permisos
- `equipos:asignar` — nuevo permiso para COORDINADOR y ADMIN
- Mis equipos (`GET /mis-equipos`) — cualquier rol autenticado (se filtra por usuario_id del token)

## Tests

- **Mis equipos**: devuelve solo las del usuario, filtros funcionan
- **Asignaciones**: COORDINADOR ve todas, filtros, paginado
- **Masiva**: crea N asignaciones correctas, 403 sin permiso
- **Clonar**: duplica vigentes, preserva campos, no duplica no-vigentes, audit ASIGNACION_MODIFICAR
- **Vigencia**: actualiza en bloque, solo las que matchean filtro
- **Export**: genera xlsx válido con columnas correctas
- **Multi-tenant**: aislado
