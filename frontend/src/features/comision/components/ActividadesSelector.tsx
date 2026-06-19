import { useState } from 'react'
import type { ActividadDetectada } from '../types/calificaciones'

interface ActividadesSelectorProps {
  actividades: ActividadDetectada[]
  onConfirm: (actividadesSeleccionadas: string[]) => void
  loading?: boolean
}

export function ActividadesSelector({ actividades, onConfirm, loading }: ActividadesSelectorProps) {
  const [selected, setSelected] = useState<string[]>(
    actividades.filter(a => a.seleccionada).map(a => a.nombre),
  )

  const toggle = (nombre: string) => {
    setSelected(prev =>
      prev.includes(nombre) ? prev.filter(n => n !== nombre) : [...prev, nombre],
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700">Actividades detectadas</h3>
      <div className="space-y-2">
        {actividades.map(a => (
          <label
            key={a.nombre}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selected.includes(a.nombre)}
              onChange={() => toggle(a.nombre)}
              className="rounded border-gray-300 text-blue-600"
            />
            <span className="text-sm">{a.nombre}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              a.tipo === 'numerica'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-purple-100 text-purple-700'
            }`}>
              {a.tipo === 'numerica' ? '# numérica' : 'A textual'}
            </span>
          </label>
        ))}
      </div>
      <button
        onClick={() => onConfirm(selected)}
        disabled={loading || selected.length === 0}
        className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? 'Importando...' : 'Confirmar importación'}
      </button>
    </div>
  )
}
