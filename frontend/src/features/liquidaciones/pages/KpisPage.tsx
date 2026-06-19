import { useState } from 'react'
import { useKpisContables } from '../hooks/useLiquidaciones'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function KpisPage() {
  const [cohorteId, setCohorteId] = useState('')
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  const { data, isLoading, error, refetch } = useKpisContables(cohorteId, periodo)

  const kpis = [
    {
      label: 'Total General',
      value: data?.total_general ?? null,
      color: 'text-gray-900',
      bg: 'bg-white',
    },
    {
      label: 'Total Facturantes',
      value: data?.total_facturantes ?? null,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Total No Facturantes',
      value: data?.total_no_facturantes ?? null,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: 'Total Nexo',
      value: data?.total_nexo ?? null,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
    {
      label: 'Docentes Liquidados',
      value: data?.cantidad_docentes ?? null,
      color: 'text-gray-900',
      bg: 'bg-white',
    },
    {
      label: 'Facturas Pendientes',
      value: data?.facturas_pendientes ?? null,
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
    },
    {
      label: 'Facturas Abonadas',
      value: data?.facturas_abonadas ?? null,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">KPIs Contables</h1>
      </div>

      <div className="flex items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte</label>
          <input
            type="text"
            value={cohorteId}
            onChange={e => setCohorteId(e.target.value)}
            placeholder="ID de cohorte"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Período</label>
          <input
            type="month"
            value={periodo}
            onChange={e => setPeriodo(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <button
          onClick={() => refetch()}
          disabled={!cohorteId || !periodo}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          Consultar
        </button>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message="Error al cargar KPIs" />
      ) : data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {kpis.map((kpi) => (
            <div key={kpi.label} className={`rounded-lg border border-gray-200 p-6 ${kpi.bg}`}>
              <p className="text-sm font-medium text-gray-500">{kpi.label}</p>
              <p className={`mt-2 text-3xl font-bold ${kpi.color}`}>
                {typeof kpi.value === 'number' ? formatMonto(kpi.value) : '—'}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">Seleccioná cohorte y período para ver los KPIs</p>
      )}
    </div>
  )
}

function formatMonto(n: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(n)
}
