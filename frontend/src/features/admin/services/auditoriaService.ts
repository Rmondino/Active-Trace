import api from '@/shared/services/api'
import type { AuditLog, AccionesPorDia, UltimasAcciones } from '../types/auditoria'

export interface AuditLogParams {
  accion?: string
  materia_id?: string
  actor_id?: string
  desde?: string
  hasta?: string
  limit?: number
}

export const auditoriaService = {
  list: (params?: AuditLogParams) =>
    api.get<AuditLog[]>('/api/admin/auditoria', { params }).then(r => r.data),
  accionesPorDia: (desde?: string, hasta?: string) =>
    api.get<AccionesPorDia[]>('/api/auditoria/acciones-por-dia', { params: { desde, hasta } }).then(r => r.data),
  ultimasAcciones: (limit?: number) =>
    api.get<UltimasAcciones[]>('/api/auditoria/ultimas-acciones', { params: { limit } }).then(r => r.data),
}
