import api from '@/shared/services/api'
import type { Factura, FacturaPayload } from '../types/facturas'

export const facturasService = {
  list: () => api.get<Factura[]>('/api/facturas').then(r => r.data),
  get: (id: string) => api.get<Factura>(`/api/facturas/${id}`).then(r => r.data),
  create: (payload: FacturaPayload) => api.post<Factura>('/api/facturas', payload).then(r => r.data),
  abonar: (id: string) => api.post(`/api/facturas/${id}/abonar`),
}
