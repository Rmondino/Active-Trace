import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLiquidaciones, useGenerarLiquidaciones, useCerrarLiquidacion } from '../hooks/useLiquidaciones'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { Liquidacion } from '../types/liquidaciones'

export function LiquidacionesPage() {
  const navigate = useNavigate()
  const [cohorteId, setCohorteId] = useState('')
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  const liquidacionesQuery = useLiquidaciones(cohorteId, periodo)
  const generarMutation = useGenerarLiquidaciones()
  const cerrarMutation = useCerrarLiquidacion()

  const handleGenerar = () => {
    if (!cohorteId || !periodo) return
    generarMutation.mutate({ cohorte_id: cohorteId, periodo })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Liquidaciones</h1>
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
          onClick={() => liquidacionesQuery.refetch()}
          disabled={!cohorteId || !periodo}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50"
        >
          Consultar
        </button>
        <button
          onClick={handleGenerar}
          disabled={!cohorteId || !periodo || generarMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {generarMutation.isPending ? 'Generando...' : 'Generar liquidaciones'}
        </button>
      </div>

      {liquidacionesQuery.isLoading ? (
        <LoadingSpinner />
      ) : liquidacionesQuery.error ? (
        <ErrorMessage message="Error al cargar liquidaciones" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Docente</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Comisiones</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Base</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plus</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {liquidacionesQuery.data?.map((item: Liquidacion) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{item.usuario_nombre}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{item.rol}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{item.comisiones}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{formatMonto(item.monto_base)}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{formatMonto(item.monto_plus)}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{formatMonto(item.total)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                      item.estado === 'Cerrada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {item.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => navigate(`/liquidaciones/${item.id}`)}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        Ver
                      </button>
                      {item.estado !== 'Cerrada' && (
                        <button
                          onClick={() => cerrarMutation.mutate(item.id)}
                          disabled={cerrarMutation.isPending}
                          className="text-sm text-green-600 hover:text-green-800 disabled:opacity-50"
                        >
                          Cerrar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {(!liquidacionesQuery.data || liquidacionesQuery.data.length === 0) && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">
                    Seleccioná cohorte y período para consultar liquidaciones
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function formatMonto(n: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(n)
}
