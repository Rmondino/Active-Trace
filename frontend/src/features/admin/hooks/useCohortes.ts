import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { estructuraService } from '../services/estructuraService'
import type { CohortePayload } from '../types/estructura'

export function useCohortes(carrera_id?: string) {
  return useQuery({
    queryKey: ['admin', 'cohortes', carrera_id],
    queryFn: () => estructuraService.cohortes.list(carrera_id),
  })
}

export function useCreateCohorte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CohortePayload) => estructuraService.cohortes.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'cohortes'] }),
  })
}

export function useUpdateCohorte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CohortePayload }) =>
      estructuraService.cohortes.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'cohortes'] }),
  })
}

export function useDeleteCohorte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.cohortes.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'cohortes'] }),
  })
}
