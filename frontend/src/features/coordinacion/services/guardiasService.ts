import api from '@/shared/services/api'
import type { Guardia, GuardiaPayload } from '../types/guardias'

export const guardiasService = {
  list: (materiaId?: string) =>
    api.get<Guardia[]>('/api/guardias', { params: materiaId ? { materia_id: materiaId } : undefined }).then(r => r.data),

  create: (payload: GuardiaPayload) =>
    api.post<Guardia>('/api/guardias', payload).then(r => r.data),

  exportExcel: (materiaId?: string) =>
    api.get('/api/guardias/export', { params: materiaId ? { materia_id: materiaId } : undefined, responseType: 'blob' }).then(r => {
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'guardias.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    }),
}
