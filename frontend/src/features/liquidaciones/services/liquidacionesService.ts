import api from '@/shared/services/api'
import type {
  SalarioBase,
  SalarioBasePayload,
  SalarioPlus,
  SalarioPlusPayload,
  MateriaGrupoPlus,
  MateriaGrupoPlusPayload,
  Liquidacion,
  LiquidacionDetalle,
  KpisContables,
} from '../types/liquidaciones'

export const liquidacionesService = {
  bases: {
    list: () => api.get<SalarioBase[]>('/api/salarios/bases').then(r => r.data),
    get: (id: string) => api.get<SalarioBase>(`/api/salarios/bases/${id}`).then(r => r.data),
    create: (payload: SalarioBasePayload) => api.post<SalarioBase>('/api/salarios/bases', payload).then(r => r.data),
    update: (id: string, payload: SalarioBasePayload) => api.put<SalarioBase>(`/api/salarios/bases/${id}`, payload).then(r => r.data),
    delete: (id: string) => api.delete(`/api/salarios/bases/${id}`),
  },
  plus: {
    list: () => api.get<SalarioPlus[]>('/api/salarios/plus').then(r => r.data),
    get: (id: string) => api.get<SalarioPlus>(`/api/salarios/plus/${id}`).then(r => r.data),
    create: (payload: SalarioPlusPayload) => api.post<SalarioPlus>('/api/salarios/plus', payload).then(r => r.data),
    update: (id: string, payload: SalarioPlusPayload) => api.put<SalarioPlus>(`/api/salarios/plus/${id}`, payload).then(r => r.data),
    delete: (id: string) => api.delete(`/api/salarios/plus/${id}`),
  },
  gruposMateria: {
    list: () => api.get<MateriaGrupoPlus[]>('/api/salarios/grupos-materia').then(r => r.data),
    get: (id: string) => api.get<MateriaGrupoPlus>(`/api/salarios/grupos-materia/${id}`).then(r => r.data),
    create: (payload: MateriaGrupoPlusPayload) => api.post<MateriaGrupoPlus>('/api/salarios/grupos-materia', payload).then(r => r.data),
    update: (id: string, payload: MateriaGrupoPlusPayload) => api.put<MateriaGrupoPlus>(`/api/salarios/grupos-materia/${id}`, payload).then(r => r.data),
    delete: (id: string) => api.delete(`/api/salarios/grupos-materia/${id}`),
  },
  liquidaciones: {
    generar: (cohorte_id: string, periodo: string) =>
      api.post<Liquidacion[]>('/api/liquidaciones/generar', null, { params: { cohorte_id, periodo } }).then(r => r.data),
    list: (cohorte_id: string, periodo: string) =>
      api.get<Liquidacion[]>('/api/liquidaciones', { params: { cohorte_id, periodo } }).then(r => r.data),
    get: (id: string) => api.get<LiquidacionDetalle>(`/api/liquidaciones/${id}`).then(r => r.data),
    cerrar: (id: string) => api.post(`/api/liquidaciones/${id}/cerrar`),
  },
  kpis: (cohorte_id: string, periodo: string) =>
    api.get<KpisContables>('/api/liquidaciones/kpis', { params: { cohorte_id, periodo } }).then(r => r.data),
}
