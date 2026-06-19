import { useState } from 'react'
import { useVigenciaEquipo } from '../../hooks/useEquipos'
import type { VigenciaPayload } from '../../types/equipos'

interface VigenciaFormProps {
  onSuccess: (total: number) => void
}

export function VigenciaForm({ onSuccess }: VigenciaFormProps) {
  const [materiaId, setMateriaId] = useState('')
  const [carreraId, setCarreraId] = useState('')
  const [cohorteId, setCohorteId] = useState('')
  const [nuevoDesde, setNuevoDesde] = useState('')
  const [nuevoHasta, setNuevoHasta] = useState('')

  const mutation = useVigenciaEquipo()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: VigenciaPayload = {
      materia_id: materiaId,
      carrera_id: carreraId,
      cohorte_id: cohorteId,
      nuevo_desde: nuevoDesde,
      nuevo_hasta: nuevoHasta || null,
    }
    mutation.mutate(payload, {
      onSuccess: (data) => onSuccess(data.total),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
          <input value={materiaId} onChange={e => setMateriaId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Carrera ID</label>
          <input value={carreraId} onChange={e => setCarreraId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte ID</label>
          <input value={cohorteId} onChange={e => setCohorteId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nuevo Desde</label>
          <input type="date" value={nuevoDesde} onChange={e => setNuevoDesde(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nuevo Hasta</label>
          <input type="date" value={nuevoHasta} onChange={e => setNuevoHasta(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      </div>

      {mutation.error && <p className="text-sm text-red-600">Error al actualizar vigencia</p>}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {mutation.isPending ? 'Actualizando...' : 'Actualizar vigencia'}
      </button>
    </form>
  )
}
