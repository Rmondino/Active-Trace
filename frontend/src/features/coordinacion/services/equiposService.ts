import api from '@/shared/services/api'
import type { AsignacionDocente, AsignacionMasivaPayload, ClonarPayload, VigenciaPayload } from '../types/equipos'

export const equiposService = {
  list: (params?: { materia_id?: string; carrera_id?: string; cohorte_id?: string; rol?: string }) =>
    api.get<AsignacionDocente[]>('/api/equipos/asignaciones', { params }).then(r => r.data),

  masiva: (payload: AsignacionMasivaPayload) =>
    api.post<{ total: number }>('/api/equipos/asignaciones/masiva', payload).then(r => r.data),

  clonar: (payload: ClonarPayload) =>
    api.post<{ total: number }>('/api/equipos/clonar', payload).then(r => r.data),

  vigencia: (payload: VigenciaPayload) =>
    api.patch<{ total: number }>('/api/equipos/vigencia', payload).then(r => r.data),

  exportExcel: (params?: { materia_id?: string; carrera_id?: string; cohorte_id?: string }) =>
    api.get('/api/equipos/export', { params, responseType: 'blob' }).then(r => {
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'equipo_docente.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    }),
}
