import api from '@/shared/services/api'

export interface Mensaje {
  id: string
  remitente_nombre: string
  remitente_id: string
  asunto: string
  cuerpo: string
  fecha: string
  leido: boolean
}

export interface NoLeidosResponse {
  count: number
}

export interface EnviarMensajePayload {
  destinatario_id: string
  asunto: string
  cuerpo: string
}

export interface ResponderMensajePayload {
  cuerpo: string
}

export const inboxService = {
  getRecibidos: () =>
    api.get<Mensaje[]>('/api/inbox').then((r) => r.data),

  getEnviados: () =>
    api.get<Mensaje[]>('/api/inbox/enviados').then((r) => r.data),

  getDetalle: (id: string) =>
    api.get<Mensaje>(`/api/inbox/${id}`).then((r) => r.data),

  enviar: (data: EnviarMensajePayload) =>
    api.post<Mensaje>('/api/inbox', data).then((r) => r.data),

  responder: (id: string, data: ResponderMensajePayload) =>
    api.post<Mensaje>(`/api/inbox/${id}/responder`, data).then((r) => r.data),

  getNoLeidos: () =>
    api.get<NoLeidosResponse>('/api/inbox/no-leidos').then((r) => r.data),
}
