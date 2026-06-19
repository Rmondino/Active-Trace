import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { Aviso } from '../../types/avisos'

const columnHelper = createColumnHelper<Aviso>()

interface AvisosTableProps {
  data: Aviso[]
  isLoading: boolean
  onEdit: (aviso: Aviso) => void
  onDelete: (id: string) => void
}

export function AvisosTable({ data, isLoading, onEdit, onDelete }: AvisosTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const columns = useMemo(() => [
    columnHelper.accessor('titulo', {
      header: 'Título',
      sortingFn: 'text',
    }),
    columnHelper.accessor('alcance', {
      header: 'Alcance',
    }),
    columnHelper.accessor('severidad', {
      header: 'Severidad',
      cell: ({ getValue }) => {
        const colors: Record<string, string> = {
          Info: 'bg-blue-100 text-blue-700',
          Advertencia: 'bg-yellow-100 text-yellow-700',
          Crítico: 'bg-red-100 text-red-700',
        }
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full ${colors[getValue()] ?? 'bg-gray-100 text-gray-700'}`}>
            {getValue()}
          </span>
        )
      },
    }),
    columnHelper.accessor('inicio_en', {
      header: 'Inicio',
    }),
    columnHelper.accessor('fin_en', {
      header: 'Fin',
      cell: ({ getValue }) => getValue() ?? '—',
    }),
    columnHelper.accessor('activo', {
      header: 'Activo',
      cell: ({ getValue }) => (
        <span className={`text-xs px-2 py-0.5 rounded-full ${getValue() ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {getValue() ? 'Sí' : 'No'}
        </span>
      ),
    }),
    columnHelper.accessor('total_acks', {
      header: 'Acks',
    }),
    columnHelper.display({
      id: 'acciones',
      header: 'Acciones',
      cell: ({ row }) => (
        <div className="flex gap-2">
          <button onClick={() => onEdit(row.original)} className="text-sm text-blue-600 hover:text-blue-800">Editar</button>
          <button onClick={() => onDelete(row.original.id)} className="text-sm text-red-600 hover:text-red-800">Eliminar</button>
        </div>
      ),
    }),
  ], [onEdit, onDelete])

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
            <tr><td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">Cargando...</td></tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr><td colSpan={8} className="px-4 py-8 text-center text-sm text-gray-500">No hay avisos publicados</td></tr>
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
