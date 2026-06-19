import api from '@/shared/services/api'
import type {
  PreviewComunicacionRequest,
  PreviewComunicacionResponse,
  EnviarComunicacionRequest,
  EnviarResponse,
  Comunicacion,
} from '../types/comunicaciones'

export const comunicacionesService = {
  preview: (data: PreviewComunicacionRequest) =>
    api.post<PreviewComunicacionResponse>('/api/comunicaciones/preview', data).then(r => r.data),

  enviar: (data: EnviarComunicacionRequest) =>
    api.post<EnviarResponse>('/api/comunicaciones/enviar', data).then(r => r.data),

  tracking: (materiaId: string) =>
    api.get<Comunicacion[]>('/api/comunicaciones', { params: { materia_id: materiaId } }).then(r => r.data),
}
