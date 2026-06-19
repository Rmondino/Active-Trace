import api from '@/shared/services/api'
import type { Atrasado, RankingItem, Reporte, NotaFinal } from '../types/analisis'

export const analisisService = {
  getAtrasados: (materiaId: string, cohorteId: string) =>
    api.get<Atrasado[]>('/api/analisis/atrasados', { params: { materia_id: materiaId, cohorte_id: cohorteId } }).then(r => r.data),

  getRanking: (materiaId: string, cohorteId: string) =>
    api.get<RankingItem[]>('/api/analisis/ranking', { params: { materia_id: materiaId, cohorte_id: cohorteId } }).then(r => r.data),

  getReporte: (materiaId: string, cohorteId: string) =>
    api.get<Reporte>('/api/analisis/reporte-rapido', { params: { materia_id: materiaId, cohorte_id: cohorteId } }).then(r => r.data),

  getNotasFinales: (materiaId: string, cohorteId: string) =>
    api.get<NotaFinal[]>('/api/analisis/notas-finales', { params: { materia_id: materiaId, cohorte_id: cohorteId } }).then(r => r.data),
}
