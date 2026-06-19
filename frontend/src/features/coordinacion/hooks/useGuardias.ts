import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { guardiasService } from '../services/guardiasService'
import type { GuardiaPayload } from '../types/guardias'

export function useGuardias(materiaId?: string) {
  return useQuery({
    queryKey: ['guardias', materiaId],
    queryFn: () => guardiasService.list(materiaId),
  })
}

export function useCreateGuardia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: GuardiaPayload) => guardiasService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['guardias'] }),
  })
}
