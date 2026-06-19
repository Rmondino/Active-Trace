import api from '@/shared/services/api'
import type { Asignacion } from '../types/comision'

export const comisionService = {
  getAsignaciones: () =>
    api.get<Asignacion[]>('/api/usuarios/me/asignaciones').then(r => r.data),
}
