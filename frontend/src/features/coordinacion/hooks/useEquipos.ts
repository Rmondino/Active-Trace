import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { equiposService } from '../services/equiposService'
import type { AsignacionMasivaPayload, ClonarPayload, VigenciaPayload } from '../types/equipos'

const QUERY_KEY = ['equipos']

export function useAsignaciones(params?: { materia_id?: string; carrera_id?: string; cohorte_id?: string; rol?: string }) {
  return useQuery({
    queryKey: [...QUERY_KEY, 'asignaciones', params],
    queryFn: () => equiposService.list(params),
  })
}

export function useAsignacionMasiva() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AsignacionMasivaPayload) => equiposService.masiva(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useClonarEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ClonarPayload) => equiposService.clonar(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useVigenciaEquipo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: VigenciaPayload) => equiposService.vigencia(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
