import api from '@/shared/services/api'
import type { Tarea, TareaPayload, ComentarioPayload, ComentarioTarea } from '../types/tareas'

export const tareasService = {
  list: (params?: { estado?: string; materia_id?: string; asignado_a_id?: string }) =>
    api.get<Tarea[]>('/api/tareas', { params }).then(r => r.data),

  misTareas: (params?: { estado?: string }) =>
    api.get<Tarea[]>('/api/tareas/mias', { params }).then(r => r.data),

  get: (id: string) =>
    api.get<Tarea>(`/api/tareas/${id}`).then(r => r.data),

  create: (payload: TareaPayload) =>
    api.post<Tarea>('/api/tareas', payload).then(r => r.data),

  updateEstado: (id: string, estado: string) =>
    api.patch<Tarea>(`/api/tareas/${id}/estado`, { estado }).then(r => r.data),

  getComentarios: (id: string) =>
    api.get<ComentarioTarea[]>(`/api/tareas/${id}/comentarios`).then(r => r.data),

  addComentario: (id: string, payload: ComentarioPayload) =>
    api.post<ComentarioTarea>(`/api/tareas/${id}/comentarios`, payload).then(r => r.data),
}
