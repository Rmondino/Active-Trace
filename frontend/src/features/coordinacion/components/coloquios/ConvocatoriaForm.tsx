import { useState } from 'react'
import type { ConvocatoriaPayload } from '../../types/coloquios'

interface ConvocatoriaFormProps {
  onSubmit: (payload: ConvocatoriaPayload) => void
  isPending: boolean
  onCancel: () => void
}

export function ConvocatoriaForm({ onSubmit, isPending, onCancel }: ConvocatoriaFormProps) {
  const [materiaId, setMateriaId] = useState('')
  const [cohorteId, setCohorteId] = useState('')
  const [instancia, setInstancia] = useState('')
  const [diasDisponibles, setDiasDisponibles] = useState(1)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ materia_id: materiaId, cohorte_id: cohorteId, tipo: 'Coloquio', instancia, dias_disponibles: diasDisponibles })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
          <input value={materiaId} onChange={e => setMateriaId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte ID</label>
          <input value={cohorteId} onChange={e => setCohorteId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Instancia</label>
        <input value={instancia} onChange={e => setInstancia(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Coloquio Final" required />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Días disponibles</label>
        <input type="number" value={diasDisponibles} onChange={e => setDiasDisponibles(Number(e.target.value))} className="w-full border rounded-lg px-3 py-2 text-sm" min={1} required />
      </div>
      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">Cancelar</button>
        <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {isPending ? 'Creando...' : 'Crear convocatoria'}
        </button>
      </div>
    </form>
  )
}
