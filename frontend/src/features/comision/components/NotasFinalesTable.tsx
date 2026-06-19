import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { NotaFinal } from '../types/analisis'

const columnHelper = createColumnHelper<NotaFinal>()

interface NotasFinalesTableProps {
  data: NotaFinal[]
  isLoading: boolean
}

export function NotasFinalesTable({ data, isLoading }: NotasFinalesTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const actividadKeys = useMemo(() => {
    const keys = new Set<string>()
    for (const item of data) {
      Object.keys(item.actividades).forEach(k => keys.add(k))
    }
    return Array.from(keys)
  }, [data])

  const columns = useMemo(() => {
    const cols = [
      columnHelper.accessor('alumno', {
        header: 'Alumno',
        sortingFn: 'text',
        enableSorting: true,
      }),
      ...actividadKeys.map(act =>
        columnHelper.display({
          id: `act_${act}`,
          header: act,
          cell: ({ row }) => {
            const val = row.original.actividades[act]
            return val !== null && val !== undefined ? String(val) : '-'
          },
        }),
      ),
      columnHelper.accessor('promedio_numerico', {
        header: 'Promedio',
        cell: info => info.getValue() !== null ? info.getValue()!.toFixed(2) : '-',
      }),
      columnHelper.accessor('aprobadas', {
        header: 'Aprobadas',
      }),
      columnHelper.accessor('total_actividades', {
        header: 'Total',
      }),
    ]
    return cols
  }, [actividadKeys])

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map(hg => (
            <tr key={hg.id}>
              {hg.headers.map(h => (
                <th
                  key={h.id}
                  onClick={h.column.getToggleSortingHandler()}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none whitespace-nowrap"
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
              <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-500">
                Cargando...
              </td>
            </tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-500">
                Sin datos de notas finales
              </td>
            </tr>
          ) : table.getRowModel().rows.map(row => (
            <tr key={row.id} className="hover:bg-gray-50">
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
