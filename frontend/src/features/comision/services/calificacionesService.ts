import api from '@/shared/services/api'
import type { Calificacion, PreviewResponse, ConfirmResponse, CompletionsResponse } from '../types/calificaciones'

export const calificacionesService = {
  list: (materiaId: string) =>
    api.get<Calificacion[]>('/api/calificaciones', { params: { materia_id: materiaId } }).then(r => r.data),

  uploadPreview: (file: File, materiaId: string, cohorteId: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('materia_id', materiaId)
    form.append('cohorte_id', cohorteId)
    form.append('confirm', 'false')
    return api.post<PreviewResponse>('/api/calificaciones/import', form).then(r => r.data)
  },

  confirm: (previewId: string, actividadesSeleccionadas: string[] | null) =>
    api.post<ConfirmResponse>(`/api/calificaciones/preview/${previewId}/confirm`, {
      actividades_seleccionadas: actividadesSeleccionadas,
    }).then(r => r.data),

  uploadCompletions: (file: File, materiaId: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('materia_id', materiaId)
    return api.post<CompletionsResponse>('/api/calificaciones/import/completions', form).then(r => r.data)
  },
}
