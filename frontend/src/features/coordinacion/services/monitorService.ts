import api from '@/shared/services/api'
import type { MonitorAlumno, MonitorFilters } from '../types/monitor'

export const monitorService = {
  list: (filters: MonitorFilters) =>
    api.get<MonitorAlumno[]>('/api/analisis/monitor', {
      params: {
        scope: 'general',
        materia_id: filters.materia_id || undefined,
        busqueda: filters.busqueda || undefined,
        estado: filters.estado || undefined,
        regional: filters.regional || undefined,
        comision: filters.comision || undefined,
      },
    }).then(r => r.data),
}
