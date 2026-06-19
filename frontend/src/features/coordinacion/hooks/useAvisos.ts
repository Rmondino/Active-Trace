import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { avisosService } from '../services/avisosService'
import type { AvisoPayload } from '../types/avisos'

export function useAvisos() {
  return useQuery({
    queryKey: ['avisos'],
    queryFn: () => avisosService.list(),
  })
}

export function useAviso(id: string) {
  return useQuery({
    queryKey: ['avisos', id],
    queryFn: () => avisosService.get(id),
    enabled: !!id,
  })
}

export function useCreateAviso() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AvisoPayload) => avisosService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['avisos'] }),
  })
}

export function useUpdateAviso() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: AvisoPayload }) => avisosService.update(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['avisos'] }),
  })
}

export function useDeleteAviso() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => avisosService.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['avisos'] }),
  })
}

export function useAckAviso() {
  return useMutation({
    mutationFn: (id: string) => avisosService.ack(id),
  })
}
