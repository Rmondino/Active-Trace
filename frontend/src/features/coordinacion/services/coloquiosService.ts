import api from '@/shared/services/api'
import type { Convocatoria, ConvocatoriaDetalle, ConvocatoriaPayload, ResultadoPayload } from '../types/coloquios'

export const coloquiosService = {
  admin: () =>
    api.get<Convocatoria[]>('/api/coloquios/admin').then(r => r.data),

  list: () =>
    api.get<Convocatoria[]>('/api/coloquios').then(r => r.data),

  get: (id: string) =>
    api.get<ConvocatoriaDetalle>(`/api/coloquios/${id}`).then(r => r.data),

  create: (payload: ConvocatoriaPayload) =>
    api.post<Convocatoria>('/api/coloquios', payload).then(r => r.data),

  importAlumnos: (id: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ total: number }>(`/api/coloquios/${id}/alumnos`, form).then(r => r.data)
  },

  cargarResultados: (id: string, resultados: ResultadoPayload[]) =>
    api.post<{ total: number }>(`/api/coloquios/${id}/resultados`, { resultados }).then(r => r.data),
}
