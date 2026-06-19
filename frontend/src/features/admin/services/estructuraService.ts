import api from '@/shared/services/api'
import type { Carrera, CarreraPayload, Cohorte, CohortePayload, Materia, MateriaPayload } from '../types/estructura'

export const estructuraService = {
  carreras: {
    list: () => api.get<Carrera[]>('/api/admin/carreras').then(r => r.data),
    get: (id: string) => api.get<Carrera>(`/api/admin/carreras/${id}`).then(r => r.data),
    create: (payload: CarreraPayload) => api.post<Carrera>('/api/admin/carreras', payload).then(r => r.data),
    update: (id: string, payload: CarreraPayload) => api.put<Carrera>(`/api/admin/carreras/${id}`, payload).then(r => r.data),
    delete: (id: string) => api.delete(`/api/admin/carreras/${id}`),
  },
  cohortes: {
    list: (carrera_id?: string) =>
      api.get<Cohorte[]>('/api/admin/cohortes', { params: { carrera_id } }).then(r => r.data),
    get: (id: string) => api.get<Cohorte>(`/api/admin/cohortes/${id}`).then(r => r.data),
    create: (payload: CohortePayload) => api.post<Cohorte>('/api/admin/cohortes', payload).then(r => r.data),
    update: (id: string, payload: CohortePayload) => api.put<Cohorte>(`/api/admin/cohortes/${id}`, payload).then(r => r.data),
    delete: (id: string) => api.delete(`/api/admin/cohortes/${id}`),
  },
  materias: {
    list: () => api.get<Materia[]>('/api/admin/materias').then(r => r.data),
    get: (id: string) => api.get<Materia>(`/api/admin/materias/${id}`).then(r => r.data),
    create: (payload: MateriaPayload) => api.post<Materia>('/api/admin/materias', payload).then(r => r.data),
    update: (id: string, payload: MateriaPayload) => api.put<Materia>(`/api/admin/materias/${id}`, payload).then(r => r.data),
    delete: (id: string) => api.delete(`/api/admin/materias/${id}`),
  },
}
