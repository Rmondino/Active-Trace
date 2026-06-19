import { useState } from 'react'
import { useClonarEquipo } from '../../hooks/useEquipos'
import type { ClonarPayload } from '../../types/equipos'

interface ClonarEquipoFormProps {
  onSuccess: (total: number) => void
}

export function ClonarEquipoForm({ onSuccess }: ClonarEquipoFormProps) {
  const [origenMateria, setOrigenMateria] = useState('')
  const [origenCarrera, setOrigenCarrera] = useState('')
  const [origenCohorte, setOrigenCohorte] = useState('')
  const [destinoMateria, setDestinoMateria] = useState('')
  const [destinoCarrera, setDestinoCarrera] = useState('')
  const [destinoCohorte, setDestinoCohorte] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')

  const mutation = useClonarEquipo()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: ClonarPayload = {
      origen: { materia_id: origenMateria, carrera_id: origenCarrera, cohorte_id: origenCohorte },
      destino: { materia_id: destinoMateria, carrera_id: destinoCarrera, cohorte_id: destinoCohorte },
      desde,
      hasta: hasta || null,
    }
    mutation.mutate(payload, {
      onSuccess: (data) => onSuccess(data.total),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Origen</h4>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
            <input value={origenMateria} onChange={e => setOrigenMateria(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Carrera ID</label>
            <input value={origenCarrera} onChange={e => setOrigenCarrera(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte ID</label>
            <input value={origenCohorte} onChange={e => setOrigenCohorte(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Destino</h4>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
            <input value={destinoMateria} onChange={e => setDestinoMateria(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Carrera ID</label>
            <input value={destinoCarrera} onChange={e => setDestinoCarrera(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte ID</label>
            <input value={destinoCohorte} onChange={e => setDestinoCohorte(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vigencia Desde</label>
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vigencia Hasta</label>
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      </div>

      {mutation.error && <p className="text-sm text-red-600">Error al clonar equipo</p>}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {mutation.isPending ? 'Clonando...' : 'Clonar equipo'}
      </button>
    </form>
  )
}
