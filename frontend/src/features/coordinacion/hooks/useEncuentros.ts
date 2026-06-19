import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { encuentrosService } from '../services/encuentrosService'
import type { SlotPayload, InstanciaEditPayload } from '../types/encuentros'

export function useSlots(materiaId: string) {
  return useQuery({
    queryKey: ['encuentros', 'slots', materiaId],
    queryFn: () => encuentrosService.listSlots(materiaId),
    enabled: !!materiaId,
  })
}

export function useCreateSlot() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SlotPayload) => encuentrosService.createSlot(payload),
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['encuentros', 'slots', vars.materia_id] }),
  })
}

export function useInstancias(slotId: string) {
  return useQuery({
    queryKey: ['encuentros', 'instancias', slotId],
    queryFn: () => encuentrosService.getInstancias(slotId),
    enabled: !!slotId,
  })
}

export function useUpdateInstancia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: InstanciaEditPayload }) =>
      encuentrosService.updateInstancia(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['encuentros'] }),
  })
}

export function useAulaHtml(materiaId: string) {
  return useQuery({
    queryKey: ['encuentros', 'aula-html', materiaId],
    queryFn: () => encuentrosService.getAulaHtml(materiaId),
    enabled: !!materiaId,
  })
}
