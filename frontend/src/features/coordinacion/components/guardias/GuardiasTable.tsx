import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { Guardia } from '../../types/guardias'

const columnHelper = createColumnHelper<Guardia>()

interface GuardiasTableProps {
  data: Guardia[]
  isLoading: boolean
}

export function GuardiasTable({ data, isLoading }: GuardiasTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const columns = useMemo(() => [
    columnHelper.accessor('docente', {
      header: 'Docente',
      cell: ({ getValue }) => getValue() ?? '—',
    }),
    columnHelper.accessor('materia_nombre', {
      header: 'Materia',
    }),
    columnHelper.accessor('dia', {
      header: 'Día',
    }),
    columnHelper.accessor('horario', {
      header: 'Horario',
    }),
    columnHelper.accessor('estado', {
      header: 'Estado',
      cell: ({ getValue }) => {
        const v = getValue()
        const colors: Record<string, string> = {
          Pendiente: 'bg-yellow-100 text-yellow-700',
          Realizada: 'bg-green-100 text-green-700',
          Cancelada: 'bg-red-100 text-red-700',
        }
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full ${colors[v] ?? 'bg-gray-100 text-gray-700'}`}>
            {v}
          </span>
        )
      },
    }),
    columnHelper.accessor('comentarios', {
      header: 'Comentarios',
      cell: ({ getValue }) => getValue() ?? '—',
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
                <th key={h.id} onClick={h.column.getToggleSortingHandler()} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                  {{ asc: ' ↑', desc: ' ↓' }[h.column.getIsSorted() as string] ?? ''}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {isLoading ? (
            <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">Cargando...</td></tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">No hay guardias registradas</td></tr>
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
