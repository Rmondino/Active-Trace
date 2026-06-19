import api from '@/shared/services/api'
import type { Umbral } from '../types/calificaciones'

export const umbralService = {
  get: (materiaId: string) =>
    api.get<Umbral>('/api/umbral', { params: { materia_id: materiaId } }).then(r => r.data),

  update: (materiaId: string, data: { umbral_pct: number; valores_aprobatorios: string[] }) =>
    api.put<Umbral>('/api/umbral', data, { params: { materia_id: materiaId } }).then(r => r.data),

  getDefaults: () =>
    api.get<Umbral>('/api/umbral/default').then(r => r.data),
}
