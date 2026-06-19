import { useQuery } from '@tanstack/react-query'
import { analisisService } from '../services/analisisService'

export function useAtrasados(materiaId: string, cohorteId: string) {
  return useQuery({
    queryKey: ['analisis', 'atrasados', materiaId, cohorteId],
    queryFn: () => analisisService.getAtrasados(materiaId, cohorteId),
  })
}

export function useRanking(materiaId: string, cohorteId: string) {
  return useQuery({
    queryKey: ['analisis', 'ranking', materiaId, cohorteId],
    queryFn: () => analisisService.getRanking(materiaId, cohorteId),
  })
}

export function useReporte(materiaId: string, cohorteId: string) {
  return useQuery({
    queryKey: ['analisis', 'reporte', materiaId, cohorteId],
    queryFn: () => analisisService.getReporte(materiaId, cohorteId),
  })
}

export function useNotasFinales(materiaId: string, cohorteId: string) {
  return useQuery({
    queryKey: ['analisis', 'notas-finales', materiaId, cohorteId],
    queryFn: () => analisisService.getNotasFinales(materiaId, cohorteId),
  })
}
