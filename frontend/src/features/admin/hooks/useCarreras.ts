import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { estructuraService } from '../services/estructuraService'
import type { CarreraPayload } from '../types/estructura'

export function useCarreras() {
  return useQuery({
    queryKey: ['admin', 'carreras'],
    queryFn: () => estructuraService.carreras.list(),
  })
}

export function useCreateCarrera() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CarreraPayload) => estructuraService.carreras.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'carreras'] }),
  })
}

export function useUpdateCarrera() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CarreraPayload }) =>
      estructuraService.carreras.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'carreras'] }),
  })
}

export function useDeleteCarrera() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.carreras.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'carreras'] }),
  })
}
