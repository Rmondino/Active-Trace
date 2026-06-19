import api from '@/shared/services/api'
import type { SlotEncuentro, InstanciaEncuentro, SlotPayload, InstanciaEditPayload } from '../types/encuentros'

export const encuentrosService = {
  listSlots: (materiaId: string) =>
    api.get<SlotEncuentro[]>('/api/encuentros/slots', { params: { materia_id: materiaId } }).then(r => r.data),

  createSlot: (payload: SlotPayload) =>
    api.post<SlotEncuentro>('/api/encuentros/slots', payload).then(r => r.data),

  getInstancias: (slotId: string) =>
    api.get<InstanciaEncuentro[]>('/api/encuentros/instancias', { params: { slot_id: slotId } }).then(r => r.data),

  updateInstancia: (id: string, payload: InstanciaEditPayload) =>
    api.patch<InstanciaEncuentro>(`/api/encuentros/instancias/${id}`, payload).then(r => r.data),

  getAulaHtml: (materiaId: string) =>
    api.get<string>('/api/encuentros/aula-html', { params: { materia_id: materiaId } }).then(r => r.data),
}
