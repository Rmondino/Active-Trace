import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { umbralService } from '../services/umbralService'

export function useUmbral(materiaId: string) {
  return useQuery({
    queryKey: ['umbral', materiaId],
    queryFn: () => umbralService.get(materiaId),
  })
}

export function useUpdateUmbral() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ materiaId, data }: { materiaId: string; data: { umbral_pct: number; valores_aprobatorios: string[] } }) =>
      umbralService.update(materiaId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['umbral', variables.materiaId] })
    },
  })
}
