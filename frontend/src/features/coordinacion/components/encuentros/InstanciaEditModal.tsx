import { useState } from 'react'
import type { InstanciaEncuentro, InstanciaEditPayload } from '../../types/encuentros'

interface InstanciaEditModalProps {
  instancia: InstanciaEncuentro
  onSave: (id: string, payload: InstanciaEditPayload) => void
  onClose: () => void
  isPending: boolean
}

export function InstanciaEditModal({ instancia, onSave, onClose, isPending }: InstanciaEditModalProps) {
  const [estado, setEstado] = useState(instancia.estado)
  const [meetUrl, setMeetUrl] = useState(instancia.meet_url ?? '')
  const [videoUrl, setVideoUrl] = useState(instancia.video_url ?? '')
  const [comentario, setComentario] = useState(instancia.comentario ?? '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(instancia.id, {
      estado,
      meet_url: meetUrl || null,
      video_url: videoUrl || null,
      comentario: comentario || null,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white rounded-lg w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Editar Instancia</h3>
        <p className="text-sm text-gray-500 mb-4">{instancia.fecha} — {instancia.titulo}</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
            <select value={estado} onChange={e => setEstado(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="Programado">Programado</option>
              <option value="Realizado">Realizado</option>
              <option value="Cancelado">Cancelado</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Meet URL</label>
            <input value={meetUrl} onChange={e => setMeetUrl(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Video URL</label>
            <input value={videoUrl} onChange={e => setVideoUrl(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Grabación..." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Comentario</label>
            <textarea value={comentario} onChange={e => setComentario(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" rows={3} />
          </div>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">Cancelar</button>
            <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
