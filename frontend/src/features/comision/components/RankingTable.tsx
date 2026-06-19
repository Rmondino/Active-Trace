import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { RankingItem } from '../types/analisis'

const columnHelper = createColumnHelper<RankingItem>()

interface RankingTableProps {
  data: RankingItem[]
  isLoading: boolean
}

const medallas = ['🥇', '🥈', '🥉']

export function RankingTable({ data, isLoading }: RankingTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'porcentaje', desc: true }])

  const columns = useMemo(() => [
    columnHelper.display({
      id: 'posicion',
      header: '#',
      cell: ({ row }) => {
        const idx = row.index
        return (
          <span className="font-medium text-gray-500">
            {idx < 3 ? medallas[idx] : idx + 1}
          </span>
        )
      },
    }),
    columnHelper.accessor('alumno', {
      header: 'Alumno',
      sortingFn: 'text',
    }),
    columnHelper.accessor('aprobadas', {
      header: 'Aprobadas',
    }),
    columnHelper.accessor('total', {
      header: 'Total',
    }),
    columnHelper.accessor('porcentaje', {
      header: 'Porcentaje',
      cell: ({ getValue }) => {
        const pct = getValue()
        return (
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-600">{pct.toFixed(1)}%</span>
          </div>
        )
      },
    }),
  ], [])

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
              <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-500">
                Cargando...
              </td>
            </tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-500">
                Sin datos de ranking
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
  )
}
