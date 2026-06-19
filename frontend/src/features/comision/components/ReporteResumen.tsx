import type { Reporte } from '../types/analisis'

interface ReporteResumenProps {
  data?: Reporte
  isLoading: boolean
}

export function ReporteResumen({ data, isLoading }: ReporteResumenProps) {
  if (isLoading) {
    return <div className="text-sm text-gray-500 py-8 text-center">Cargando reporte...</div>
  }

  if (!data) {
    return <div className="text-sm text-gray-500 py-8 text-center">Sin datos de reporte</div>
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Total alumnos" value={data.total_alumnos} />
        <MetricCard label="Total actividades" value={data.total_actividades} />
        <MetricCard label="Alumnos atrasados" value={data.alumnos_atrasados} color="red" />
        <MetricCard
          label="Tasa aprobación"
          value={`${(data.tasa_aprobacion_gral * 100).toFixed(1)}%`}
          color="green"
        />
      </div>

      <div className="overflow-x-auto border rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actividad</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasa aprobación</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Promedio</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.actividades.map(a => (
              <tr key={a.nombre} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-700">{a.nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
                      <div
                        className="h-2 rounded-full bg-blue-500"
                        style={{ width: `${Math.min(a.tasa_aprobacion * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs">{(a.tasa_aprobacion * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {a.promedio !== null ? a.promedio.toFixed(2) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function MetricCard({ label, value, color }: { label: string; value: string | number; color?: 'red' | 'green' }) {
  const colorClass = color === 'red'
    ? 'text-red-600'
    : color === 'green'
      ? 'text-green-600'
      : 'text-gray-900'

  return (
    <div className="bg-white border rounded-lg p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${colorClass}`}>{value}</p>
    </div>
  )
}
