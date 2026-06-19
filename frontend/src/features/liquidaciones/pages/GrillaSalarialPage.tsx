import { useState } from 'react'
import { useBasesSalariales, usePlusSalariales, useGruposMateria } from '../hooks/useLiquidaciones'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

type Tab = 'bases' | 'plus' | 'grupos'

export function GrillaSalarialPage() {
  const [activeTab, setActiveTab] = useState<Tab>('bases')
  const [editId, setEditId] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Grilla Salarial</h1>

      <nav className="flex border-b border-gray-200">
        {(['bases', 'plus', 'grupos'] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab === 'bases' ? 'Bases' : tab === 'plus' ? 'Plus' : 'Grupos de Materia'}
          </button>
        ))}
      </nav>

      {activeTab === 'bases' && <BasesTable />}
      {activeTab === 'plus' && <PlusTable />}
      {activeTab === 'grupos' && <GruposTable />}
    </div>
  )
}

function formatMonto(n: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(n)
}

function BasesTable() {
  const { data, isLoading, error } = useBasesSalariales()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Error al cargar bases salariales" />

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Monto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Desde</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hasta</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {data?.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{item.rol}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{formatMonto(item.monto)}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.desde}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.hasta || '—'}</td>
            </tr>
          ))}
          {(!data || data.length === 0) && (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">
                No hay bases salariales registradas
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function PlusTable() {
  const { data, isLoading, error } = usePlusSalariales()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Error al cargar plus salariales" />

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Monto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tope</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vigencia</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {data?.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{item.grupo}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{item.rol}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.descripcion}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{formatMonto(item.monto)}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.tope_acumulacion ?? '—'}</td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {item.desde} — {item.hasta || '∞'}
              </td>
            </tr>
          ))}
          {(!data || data.length === 0) && (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                No hay plus salariales registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

function GruposTable() {
  const { data, isLoading, error } = useGruposMateria()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Error al cargar grupos de materia" />

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Materia</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Desde</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hasta</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {data?.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{item.materia_nombre}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{item.grupo}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.desde}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.hasta || '—'}</td>
            </tr>
          ))}
          {(!data || data.length === 0) && (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">
                No hay grupos de materia registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
