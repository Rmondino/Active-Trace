import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { perfilService, type ActualizarPerfilPayload } from '@/features/perfil/services/perfilService'

const PERFIL_QUERY_KEY = ['perfil']

export function usePerfil() {
  return useQuery({
    queryKey: PERFIL_QUERY_KEY,
    queryFn: perfilService.getPerfil,
  })
}

export function useActualizarPerfil() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ActualizarPerfilPayload) =>
      perfilService.actualizarPerfil(data),
    onSuccess: (updated) => {
      queryClient.setQueryData(PERFIL_QUERY_KEY, updated)
    },
  })
}
