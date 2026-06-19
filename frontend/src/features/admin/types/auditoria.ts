export interface AuditLog {
  id: string
  accion: string
  materia_id: string | null
  materia_nombre?: string
  actor_id: string
  actor_nombre?: string
  detalle: Record<string, unknown> | null
  tenant_id: string
  created_at: string
}

export interface AccionesPorDia {
  fecha: string
  total: number
}

export interface UltimasAcciones {
  id: string
  accion: string
  actor_nombre: string
  created_at: string
}
