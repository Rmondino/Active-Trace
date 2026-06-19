import api from '@/shared/services/api'
import type { UserRead, UserCreate, UserUpdate } from '../types/usuarios'

export const usuariosService = {
  list: (params?: { search?: string; estado?: string }) =>
    api.get<UserRead[]>('/api/admin/usuarios', { params }).then(r => r.data),
  get: (id: string) => api.get<UserRead>(`/api/admin/usuarios/${id}`).then(r => r.data),
  create: (payload: UserCreate) => api.post<UserRead>('/api/admin/usuarios', payload).then(r => r.data),
  update: (id: string, payload: UserUpdate) => api.put<UserRead>(`/api/admin/usuarios/${id}`, payload).then(r => r.data),
  delete: (id: string) => api.delete(`/api/admin/usuarios/${id}`),
}
