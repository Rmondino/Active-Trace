import { useState } from 'react'
import type { AlumnoDestino } from '../types/comunicaciones'

interface ComunicacionFormProps {
  alumnos: AlumnoDestino[]
  materiaId: string
  onPreview: (asunto: string, cuerpo: string) => void
  isLoading: boolean
}

const placeholdersHint = 'Placeholders disponibles: {alumno}, {comision}, {materia}'

export function ComunicacionForm({ alumnos, materiaId, onPreview, isLoading }: ComunicacionFormProps) {
  const [asunto, setAsunto] = useState('')
  const [cuerpo, setCuerpo] = useState('')

  const handlePreview = () => {
    if (!asunto.trim() || !cuerpo.trim()) return
    onPreview(asunto, cuerpo)
  }

  return (
    <div className="bg-white rounded-lg border p-6 space-y-4">
      <h2 className="text-lg font-semibold">Nueva comunicación</h2>

      <div>
        <p className="text-sm text-gray-500 mb-2">
          Destinatarios: {alumnos.map(a => `${a.nombre} ${a.apellidos}`).join(', ')}
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Asunto</label>
        <p className="text-xs text-gray-400 mb-1">{placeholdersHint}</p>
        <input
          type="text"
          value={asunto}
          onChange={e => setAsunto(e.target.value)}
          placeholder="Ej: Notificación de actividades pendientes - {alumno}"
          className="w-full p-2 border rounded-lg text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cuerpo</label>
        <p className="text-xs text-gray-400 mb-1">{placeholdersHint}</p>
        <textarea
          value={cuerpo}
          onChange={e => setCuerpo(e.target.value)}
          rows={8}
          placeholder="Estimado/a {alumno}, detectamos que tienes actividades pendientes en {materia}..."
          className="w-full p-2 border rounded-lg text-sm resize-y"
        />
      </div>

      <button
        onClick={handlePreview}
        disabled={isLoading || !asunto.trim() || !cuerpo.trim()}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {isLoading ? 'Generando...' : 'Generar vista previa'}
      </button>
    </div>
  )
}
