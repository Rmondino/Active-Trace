import { useState } from 'react'
import { useFacturas, useAbonarFactura, useCrearFactura } from '../hooks/useFacturas'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { Factura } from '../types/facturas'

export function FacturasPage() {
  const { data, isLoading, error } = useFacturas()
  const abonarMutation = useAbonarFactura()
  const crearMutation = useCrearFactura()
  const [showForm, setShowForm] = useState(false)
  const [detalle, setDetalle] = useState('')
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })

  const handleCreate = () => {
    crearMutation.mutate(
      { detalle, periodo },
      { onSuccess: () => { setShowForm(false); setDetalle('') } },
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Facturas</h1>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Nueva factura
        </button>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message="Error al cargar facturas" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Docente</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Período</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalle</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cargada</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {data?.map((factura: Factura) => (
                <tr key={factura.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{factura.usuario_nombre}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{factura.periodo}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">{factura.detalle}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                      factura.estado === 'Abonada'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {factura.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(factura.cargada_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {factura.estado !== 'Abonada' && (
                      <button
                        onClick={() => abonarMutation.mutate(factura.id)}
                        disabled={abonarMutation.isPending}
                        className="text-sm text-green-600 hover:text-green-800 disabled:opacity-50"
                      >
                        Abonar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {(!data || data.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                    No hay facturas registradas
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-lg w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Nueva factura</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Período</label>
                <input
                  type="month"
                  value={periodo}
                  onChange={e => setPeriodo(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Detalle</label>
                <textarea
                  value={detalle}
                  onChange={e => setDetalle(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Descripción de la factura"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!detalle || !periodo || crearMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {crearMutation.isPending ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
