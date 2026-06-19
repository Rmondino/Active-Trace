import { useQuery } from '@tanstack/react-query'
import { auditoriaService, type AuditLogParams } from '../services/auditoriaService'

export function useAuditoria(params?: AuditLogParams) {
  return useQuery({
    queryKey: ['admin', 'auditoria', params],
    queryFn: () => auditoriaService.list(params),
  })
}

export function useAccionesPorDia(desde?: string, hasta?: string) {
  return useQuery({
    queryKey: ['admin', 'auditoria', 'acciones-por-dia', desde, hasta],
    queryFn: () => auditoriaService.accionesPorDia(desde, hasta),
  })
}

export function useUltimasAcciones(limit?: number) {
  return useQuery({
    queryKey: ['admin', 'auditoria', 'ultimas-acciones', limit],
    queryFn: () => auditoriaService.ultimasAcciones(limit),
  })
}
