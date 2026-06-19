import api from '@/shared/services/api'
import type { Asignacion } from '../types/comision'

export const comisionService = {
  getAsignaciones: (usuarioId: string) =>
    api.get<Asignacion[]>(`/api/asignaciones?usuario_id=${usuarioId}`).then(r => r.data),
}
