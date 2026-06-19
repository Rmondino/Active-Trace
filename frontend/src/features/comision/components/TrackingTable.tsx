import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { Comunicacion } from '../types/comunicaciones'

const columnHelper = createColumnHelper<Comunicacion>()

interface TrackingTableProps {
  data: Comunicacion[]
  isLoading: boolean
}

const estadoColors: Record<Comunicacion['estado'], string> = {
  Pendiente: 'bg-yellow-100 text-yellow-800',
  Enviando: 'bg-blue-100 text-blue-800',
  Enviado: 'bg-green-100 text-green-800',
  Error: 'bg-red-100 text-red-800',
  Cancelado: 'bg-gray-100 text-gray-800',
}

export function TrackingTable({ data, isLoading }: TrackingTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'created_at', desc: true }])

  const columns = useMemo(() => [
    columnHelper.accessor('destinatario_mask', {
      header: 'Destinatario',
    }),
    columnHelper.accessor('asunto', {
      header: 'Asunto',
    }),
    columnHelper.accessor('estado', {
      header: 'Estado',
      cell: ({ getValue }) => {
        const estado = getValue()
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${estadoColors[estado]}`}>
            {estado}
          </span>
        )
      },
    }),
    columnHelper.accessor('created_at', {
      header: 'Fecha',
      cell: ({ getValue }) => {
        const date = getValue()
        return new Date(date).toLocaleString('es-AR')
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
              <td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">
                Cargando...
              </td>
            </tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">
                Sin comunicaciones enviadas
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
