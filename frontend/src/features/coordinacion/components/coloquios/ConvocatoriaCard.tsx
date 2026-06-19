import type { Convocatoria } from '../../types/coloquios'

interface ConvocatoriaCardProps {
  convocatoria: Convocatoria
  onClick: () => void
}

export function ConvocatoriaCard({ convocatoria, onClick }: ConvocatoriaCardProps) {
  return (
    <button onClick={onClick} className="w-full text-left bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-gray-900">{convocatoria.materia_nombre}</h4>
        <span className="text-xs text-gray-500">{convocatoria.instancia}</span>
      </div>
      <p className="text-sm text-gray-500 mb-3">{convocatoria.cohorte_nombre}</p>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-blue-50 rounded p-2">
          <span className="block text-lg font-bold text-blue-700">{convocatoria.total_convocados}</span>
          <span className="text-xs text-blue-600">Convocados</span>
        </div>
        <div className="bg-green-50 rounded p-2">
          <span className="block text-lg font-bold text-green-700">{convocatoria.reservas_activas}</span>
          <span className="text-xs text-green-600">Reservas activas</span>
        </div>
        <div className="bg-purple-50 rounded p-2">
          <span className="block text-lg font-bold text-purple-700">{convocatoria.total_resultados}</span>
          <span className="text-xs text-purple-600">Resultados</span>
        </div>
        <div className="bg-orange-50 rounded p-2">
          <span className="block text-lg font-bold text-orange-700">{convocatoria.cupos_libres}</span>
          <span className="text-xs text-orange-600">Cupos libres</span>
        </div>
      </div>
    </button>
  )
}
