import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { Tarea } from '../../types/tareas'

const columnHelper = createColumnHelper<Tarea>()

interface TareasTableProps {
  data: Tarea[]
  isLoading: boolean
  onSelect: (tarea: Tarea) => void
}

export function TareasTable({ data, isLoading, onSelect }: TareasTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const columns = useMemo(() => [
    columnHelper.accessor('descripcion', {
      header: 'Descripción',
      sortingFn: 'text',
      cell: ({ getValue }) => {
        const text = getValue()
        return <span className="truncate max-w-xs block">{text.length > 60 ? text.slice(0, 60) + '...' : text}</span>
      },
    }),
    columnHelper.accessor('asignado_a_nombre', {
      header: 'Asignado a',
    }),
    columnHelper.accessor('asignado_por_nombre', {
      header: 'Asignado por',
    }),
    columnHelper.accessor('materia_nombre', {
      header: 'Materia',
      cell: ({ getValue }) => getValue() ?? '—',
    }),
    columnHelper.accessor('estado', {
      header: 'Estado',
      cell: ({ getValue }) => {
        const colors: Record<string, string> = {
          Pendiente: 'bg-yellow-100 text-yellow-700',
          'En progreso': 'bg-blue-100 text-blue-700',
          Resuelta: 'bg-green-100 text-green-700',
          Cancelada: 'bg-red-100 text-red-700',
        }
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full ${colors[getValue()] ?? 'bg-gray-100 text-gray-700'}`}>
            {getValue()}
          </span>
        )
      },
    }),
    columnHelper.accessor('creada_at', {
      header: 'Creada',
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
            <tr><td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">No hay tareas</td></tr>
          ) : table.getRowModel().rows.map(row => (
            <tr key={row.id} onClick={() => onSelect(row.original)} className="hover:bg-gray-50 cursor-pointer">
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
