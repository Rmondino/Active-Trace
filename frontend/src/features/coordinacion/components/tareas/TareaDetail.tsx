import { useState } from 'react'
import { useUpdateEstadoTarea, useAddComentario } from '../../hooks/useTareas'
import type { Tarea } from '../../types/tareas'

interface TareaDetailProps {
  tarea: Tarea
  onClose: () => void
}

const estados = ['Pendiente', 'En progreso', 'Resuelta', 'Cancelada']

export function TareaDetail({ tarea, onClose }: TareaDetailProps) {
  const [nuevoEstado, setNuevoEstado] = useState(tarea.estado)
  const [nuevoComentario, setNuevoComentario] = useState('')

  const updateEstado = useUpdateEstadoTarea()
  const addComentario = useAddComentario()

  const handleCambiarEstado = () => {
    if (nuevoEstado !== tarea.estado) {
      updateEstado.mutate({ id: tarea.id, estado: nuevoEstado })
    }
  }

  const handleAddComentario = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nuevoComentario.trim()) return
    addComentario.mutate({ id: tarea.id, payload: { texto: nuevoComentario } }, {
      onSuccess: () => setNuevoComentario(''),
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white rounded-lg w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Detalle de Tarea</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>

        <div className="space-y-3 mb-4">
          <p className="text-sm text-gray-700"><span className="font-medium">Asignado a:</span> {tarea.asignado_a_nombre}</p>
          <p className="text-sm text-gray-700"><span className="font-medium">Asignado por:</span> {tarea.asignado_por_nombre}</p>
          {tarea.materia_nombre && <p className="text-sm text-gray-700"><span className="font-medium">Materia:</span> {tarea.materia_nombre}</p>}
          <p className="text-sm text-gray-700 whitespace-pre-wrap"><span className="font-medium">Descripción:</span> {tarea.descripcion}</p>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <select value={nuevoEstado} onChange={e => setNuevoEstado(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
            {estados.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
          <button onClick={handleCambiarEstado} disabled={nuevoEstado === tarea.estado || updateEstado.isPending}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {updateEstado.isPending ? '...' : 'Cambiar estado'}
          </button>
        </div>

        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold mb-3">Comentarios</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
            {tarea.comentarios.map(c => (
              <div key={c.id} className="bg-gray-50 rounded p-3">
                <p className="text-xs text-gray-500 mb-1">
                  {c.autor_nombre} — {new Date(c.creado_at).toLocaleString()}
                </p>
                <p className="text-sm text-gray-700">{c.texto}</p>
              </div>
            ))}
            {tarea.comentarios.length === 0 && (
              <p className="text-sm text-gray-500">Sin comentarios</p>
            )}
          </div>

          <form onSubmit={handleAddComentario} className="flex gap-2">
            <input
              value={nuevoComentario} onChange={e => setNuevoComentario(e.target.value)}
              className="flex-1 border rounded-lg px-3 py-2 text-sm" placeholder="Agregar comentario..."
            />
            <button type="submit" disabled={addComentario.isPending || !nuevoComentario.trim()}
              className="px-3 py-2 bg-gray-800 text-white rounded-lg text-sm hover:bg-gray-700 disabled:opacity-50">
              Enviar
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
