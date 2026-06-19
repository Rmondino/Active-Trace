import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { inboxService, type EnviarMensajePayload, type ResponderMensajePayload } from '@/features/inbox/services/inboxService'

const INBOX_QUERY_KEY = ['inbox']
const NO_LEIDOS_KEY = ['inbox', 'no-leidos']
const ENVIADOS_KEY = ['inbox', 'enviados']

export function useMensajesRecibidos() {
  return useQuery({
    queryKey: INBOX_QUERY_KEY,
    queryFn: inboxService.getRecibidos,
  })
}

export function useMensajesEnviados() {
  return useQuery({
    queryKey: ENVIADOS_KEY,
    queryFn: inboxService.getEnviados,
  })
}

export function useMensajeDetalle(id: string) {
  return useQuery({
    queryKey: ['inbox', id],
    queryFn: () => inboxService.getDetalle(id),
    enabled: !!id,
  })
}

export function useNoLeidos() {
  return useQuery({
    queryKey: NO_LEIDOS_KEY,
    queryFn: inboxService.getNoLeidos,
    refetchInterval: 30_000,
  })
}

export function useEnviarMensaje() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EnviarMensajePayload) => inboxService.enviar(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ENVIADOS_KEY })
    },
  })
}

export function useResponderMensaje() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ResponderMensajePayload }) =>
      inboxService.responder(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INBOX_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: ENVIADOS_KEY })
    },
  })
}
