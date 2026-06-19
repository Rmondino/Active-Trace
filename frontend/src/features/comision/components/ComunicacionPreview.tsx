import type { PreviewAlumno } from '../types/comunicaciones'

interface ComunicacionPreviewProps {
  previews: PreviewAlumno[]
  onEnviar: () => void
  isLoading: boolean
}

export function ComunicacionPreview({ previews, onEnviar, isLoading }: ComunicacionPreviewProps) {
  return (
    <div className="bg-white rounded-lg border p-6 space-y-4">
      <h2 className="text-lg font-semibold">Vista previa</h2>

      <div className="space-y-4">
        {previews.map(p => (
          <div key={p.alumno_id} className="border rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium text-gray-700">{p.alumno_nombre}</p>
            <div className="bg-gray-50 rounded p-3 space-y-1">
              <p className="text-xs text-gray-500">Asunto:</p>
              <p className="text-sm text-gray-800">{p.asunto}</p>
            </div>
            <div className="bg-gray-50 rounded p-3 space-y-1">
              <p className="text-xs text-gray-500">Cuerpo:</p>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{p.cuerpo}</p>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={onEnviar}
        disabled={isLoading}
        className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
      >
        {isLoading ? 'Enviando...' : `Enviar comunicación (${previews.length} destinatarios)`}
      </button>
    </div>
  )
}
