import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { Atrasado } from '../types/analisis'

const columnHelper = createColumnHelper<Atrasado>()

interface AtrasadosTableProps {
  data: Atrasado[]
  onComunicar: (seleccionados: Atrasado[]) => void
  isLoading: boolean
}

export function AtrasadosTable({ data, onComunicar, isLoading }: AtrasadosTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [rowSelection, setRowSelection] = useState({})

  const columns = useMemo(() => [
    columnHelper.display({
      id: 'select',
      header: ({ table }) => (
        <input
          type="checkbox"
          checked={table.getIsAllRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
          className="rounded border-gray-300"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          className="rounded border-gray-300"
        />
      ),
    }),
    columnHelper.accessor('alumno', {
      header: 'Alumno',
      sortingFn: 'text',
    }),
    columnHelper.accessor('comision', {
      header: 'Comisión',
    }),
    columnHelper.accessor('total_actividades', {
      header: 'Total',
    }),
    columnHelper.accessor('aprobadas', {
      header: 'Aprobadas',
    }),
    columnHelper.accessor('desaprobadas', {
      header: 'Desaprobadas',
    }),
    columnHelper.accessor('sin_nota', {
      header: 'Sin nota',
    }),
    columnHelper.display({
      id: 'causas',
      header: 'Causas',
      cell: ({ row }) => {
        const { causas } = row.original
        return (
          <div className="flex flex-wrap gap-1">
            {causas.faltantes.map(c => (
              <span key={c} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                F: {c}
              </span>
            ))}
            {causas.baja_nota.map(c => (
              <span key={c} className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                B: {c}
              </span>
            ))}
          </div>
        )
      },
    }),
  ], [])

  const table = useReactTable({
    data,
    columns,
    state: { sorting, rowSelection },
    onSortingChange: setSorting,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableRowSelection: true,
    getRowId: row => row.entrada_padron_id,
  })

  const selectedCount = table.getSelectedRowModel().rows.length

  return (
    <div className="space-y-4">
      {selectedCount > 0 && (
        <div className="flex items-center justify-between bg-blue-50 p-3 rounded-lg">
          <span className="text-sm font-medium text-blue-700">
            {selectedCount} alumno{selectedCount !== 1 ? 's' : ''} seleccionado{selectedCount !== 1 ? 's' : ''}
          </span>
          <button
            onClick={() => onComunicar(
              table.getSelectedRowModel().rows.map(r => r.original),
            )}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Comunicar seleccionados ({selectedCount})
          </button>
        </div>
      )}

      <div className="overflow-x-auto border rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => (
                  <th
                    key={h.id}
                    onClick={h.column.getToggleSortingHandler()}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none"
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {{ asc: ' ↑', desc: ' ↓' }[h.column.getIsSorted() as string] ?? ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">
                  Cargando...
                </td>
              </tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">
                  No hay alumnos atrasados
                </td>
              </tr>
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
    </div>
  )
}
