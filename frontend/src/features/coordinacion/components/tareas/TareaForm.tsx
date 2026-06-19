import { useState } from 'react'
import type { TareaPayload } from '../../types/tareas'

interface TareaFormProps {
  onSubmit: (payload: TareaPayload) => void
  isPending: boolean
  onCancel: () => void
}

export function TareaForm({ onSubmit, isPending, onCancel }: TareaFormProps) {
  const [asignadoAId, setAsignadoAId] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [materiaId, setMateriaId] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      asignado_a_id: asignadoAId,
      descripcion,
      materia_id: materiaId || null,
      contexto_id: null,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Asignar a (ID de usuario)</label>
        <input value={asignadoAId} onChange={e => setAsignadoAId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
        <textarea value={descripcion} onChange={e => setDescripcion(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" rows={4} required />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID (opcional)</label>
        <input value={materiaId} onChange={e => setMateriaId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
      </div>
      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">Cancelar</button>
        <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {isPending ? 'Asignando...' : 'Asignar tarea'}
        </button>
      </div>
    </form>
  )
}
