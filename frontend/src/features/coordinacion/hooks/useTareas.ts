import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tareasService } from '../services/tareasService'
import type { TareaPayload, ComentarioPayload } from '../types/tareas'

export function useTareas(params?: { estado?: string; materia_id?: string; asignado_a_id?: string }) {
  return useQuery({
    queryKey: ['tareas', params],
    queryFn: () => tareasService.list(params),
  })
}

export function useMisTareas(params?: { estado?: string }) {
  return useQuery({
    queryKey: ['tareas', 'mias', params],
    queryFn: () => tareasService.misTareas(params),
  })
}

export function useTarea(id: string) {
  return useQuery({
    queryKey: ['tareas', id],
    queryFn: () => tareasService.get(id),
    enabled: !!id,
  })
}

export function useCreateTarea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: TareaPayload) => tareasService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tareas'] }),
  })
}

export function useUpdateEstadoTarea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: string }) => tareasService.updateEstado(id, estado),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tareas'] }),
  })
}

export function useAddComentario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ComentarioPayload }) =>
      tareasService.addComentario(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tareas'] }),
  })
}
