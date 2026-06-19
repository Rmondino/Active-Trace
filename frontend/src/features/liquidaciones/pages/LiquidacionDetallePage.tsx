import { useParams, useNavigate } from 'react-router-dom'
import { useLiquidacionDetalle } from '../hooks/useLiquidaciones'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function LiquidacionDetallePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data, isLoading, error } = useLiquidacionDetalle(id!)

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Error al cargar detalle de liquidación" />
  if (!data) return <ErrorMessage message="Liquidación no encontrada" />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/liquidaciones')}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ← Volver
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Detalle de Liquidación</h1>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white">
        <dl className="divide-y divide-gray-200">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Docente</dt>
            <dd className="col-span-2 text-sm text-gray-900">{data.usuario_nombre}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Rol</dt>
            <dd className="col-span-2 text-sm text-gray-900">{data.rol}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Período</dt>
            <dd className="col-span-2 text-sm text-gray-900">{data.periodo}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Comisiones activas</dt>
            <dd className="col-span-2 text-sm text-gray-900">{data.comisiones}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Monto base</dt>
            <dd className="col-span-2 text-sm text-gray-900">{formatMonto(data.monto_base)}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Monto plus</dt>
            <dd className="col-span-2 text-sm text-gray-900">{formatMonto(data.monto_plus)}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4 bg-gray-50">
            <dt className="text-sm font-semibold text-gray-900">Total</dt>
            <dd className="col-span-2 text-sm font-bold text-gray-900">{formatMonto(data.total)}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">Estado</dt>
            <dd className="col-span-2">
              <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                data.estado === 'Cerrada' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {data.estado}
              </span>
            </dd>
          </div>
          {data.es_nexo && (
            <div className="px-6 py-4 grid grid-cols-3 gap-4">
              <dt className="text-sm font-medium text-gray-500">Nexo</dt>
              <dd className="col-span-2 text-sm text-gray-900">Sí</dd>
            </div>
          )}
          {data.excluido_por_factura && (
            <div className="px-6 py-4 grid grid-cols-3 gap-4">
              <dt className="text-sm font-medium text-gray-500">Excluido por factura</dt>
              <dd className="col-span-2 text-sm text-gray-900">Sí</dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  )
}

function formatMonto(n: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(n)
}
