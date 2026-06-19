import { useState, useMemo } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import { useAuditoria, useAccionesPorDia, useUltimasAcciones } from '../hooks/useAuditoria'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { AuditLog } from '../types/auditoria'

const columnHelper = createColumnHelper<AuditLog>()

export function AuditoriaPage() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [filtroAccion, setFiltroAccion] = useState('')
  const [filtroMateria, setFiltroMateria] = useState('')
  const [filtroActor, setFiltroActor] = useState('')
  const [filtroDesde, setFiltroDesde] = useState('')
  const [filtroHasta, setFiltroHasta] = useState('')
  const [filtroLimit, setFiltroLimit] = useState('100')

  const logQuery = useAuditoria({
    accion: filtroAccion || undefined,
    materia_id: filtroMateria || undefined,
    actor_id: filtroActor || undefined,
    desde: filtroDesde || undefined,
    hasta: filtroHasta || undefined,
    limit: filtroLimit ? Number(filtroLimit) : undefined,
  })
  const accionesPorDiaQuery = useAccionesPorDia(filtroDesde || undefined, filtroHasta || undefined)
  const ultimasAccionesQuery = useUltimasAcciones(5)

  const columns = useMemo(() => [
    columnHelper.accessor('created_at', {
      header: 'Fecha',
      cell: ({ getValue }) => new Date(getValue()).toLocaleString('es-AR'),
    }),
    columnHelper.accessor('accion', {
      header: 'Acción',
      cell: ({ getValue }) => (
        <span className="inline-flex rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
          {getValue()}
        </span>
      ),
    }),
    columnHelper.accessor('actor_nombre', { header: 'Actor' }),
    columnHelper.accessor('materia_nombre', { header: 'Materia' }),
    columnHelper.accessor('detalle', {
      header: 'Detalle',
      cell: ({ getValue }) => {
        const d = getValue()
        return d ? JSON.stringify(d).slice(0, 80) : '-'
      },
    }),
  ], [])

  const table = useReactTable({
    data: logQuery.data ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Auditoría</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Acciones por día</h3>
          {accionesPorDiaQuery.isLoading ? (
            <LoadingSpinner size="sm" />
          ) : accionesPorDiaQuery.error ? (
            <ErrorMessage message="Error al cargar" />
          ) : (
            <div className="space-y-2">
              {accionesPorDiaQuery.data?.map(item => (
                <div key={item.fecha} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{new Date(item.fecha).toLocaleDateString('es-AR')}</span>
                  <span className="font-semibold text-gray-900">{item.total}</span>
                </div>
              ))}
              {(!accionesPorDiaQuery.data || accionesPorDiaQuery.data.length === 0) && (
                <p className="text-sm text-gray-500">Sin datos</p>
              )}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Últimas acciones</h3>
          {ultimasAccionesQuery.isLoading ? (
            <LoadingSpinner size="sm" />
          ) : ultimasAccionesQuery.error ? (
            <ErrorMessage message="Error al cargar" />
          ) : (
            <div className="space-y-2">
              {ultimasAccionesQuery.data?.map(item => (
                <div key={item.id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{item.actor_nombre}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{item.accion}</span>
                    <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleString('es-AR')}</span>
                  </div>
                </div>
              ))}
              {(!ultimasAccionesQuery.data || ultimasAccionesQuery.data.length === 0) && (
                <p className="text-sm text-gray-500">Sin datos</p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Acción</label>
          <select value={filtroAccion} onChange={e => setFiltroAccion(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
            <option value="">Todas</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="create">Creación</option>
            <option value="update">Actualización</option>
            <option value="delete">Eliminación</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
          <input type="text" value={filtroMateria} onChange={e => setFiltroMateria(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Actor ID</label>
          <input type="text" value={filtroActor} onChange={e => setFiltroActor(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
          <input type="date" value={filtroDesde} onChange={e => setFiltroDesde(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
          <input type="date" value={filtroHasta} onChange={e => setFiltroHasta(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Límite</label>
          <input type="number" value={filtroLimit} onChange={e => setFiltroLimit(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-20" />
        </div>
      </div>

      {logQuery.isLoading ? <LoadingSpinner /> : logQuery.error ? (
        <ErrorMessage message="Error al cargar logs de auditoría" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {table.getHeaderGroups().map(hg => (
                <tr key={hg.id}>
                  {hg.headers.map(h => (
                    <th key={h.id} onClick={h.column.getToggleSortingHandler()} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      {{ asc: ' ↑', desc: ' ↓' }[h.column.getIsSorted() as string] ?? ''}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {table.getRowModel().rows.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-500">No hay registros de auditoría</td></tr>
              ) : table.getRowModel().rows.map(row => (
                <tr key={row.id} className="hover:bg-gray-50">
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-3 text-sm text-gray-700">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
