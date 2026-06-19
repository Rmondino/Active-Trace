import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { estructuraService } from '../services/estructuraService'
import type { MateriaPayload } from '../types/estructura'

export function useMaterias() {
  return useQuery({
    queryKey: ['admin', 'materias'],
    queryFn: () => estructuraService.materias.list(),
  })
}

export function useCreateMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: MateriaPayload) => estructuraService.materias.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'materias'] }),
  })
}

export function useUpdateMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MateriaPayload }) =>
      estructuraService.materias.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'materias'] }),
  })
}

export function useDeleteMateria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.materias.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'materias'] }),
  })
}
