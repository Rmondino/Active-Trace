import api from '@/shared/services/api'
import type { Aviso, AvisoPayload } from '../types/avisos'

export const avisosService = {
  list: () =>
    api.get<Aviso[]>('/api/avisos').then(r => r.data),

  get: (id: string) =>
    api.get<Aviso>(`/api/avisos/${id}`).then(r => r.data),

  create: (payload: AvisoPayload) =>
    api.post<Aviso>('/api/avisos', payload).then(r => r.data),

  update: (id: string, payload: AvisoPayload) =>
    api.put<Aviso>(`/api/avisos/${id}`, payload).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/api/avisos/${id}`).then(r => r.data),

  ack: (id: string) =>
    api.post(`/api/avisos/${id}/ack`).then(r => r.data),
}
