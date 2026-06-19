import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { MonitorAlumno } from '../../types/monitor'

const columnHelper = createColumnHelper<MonitorAlumno>()

interface MonitorTableProps {
  data: MonitorAlumno[]
  isLoading: boolean
}

export function MonitorTable({ data, isLoading }: MonitorTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const columns = useMemo(() => [
    columnHelper.accessor('alumno', {
      header: 'Alumno',
      sortingFn: 'text',
    }),
    columnHelper.accessor('comision', {
      header: 'Comisión',
    }),
    columnHelper.accessor('materia_nombre', {
      header: 'Materia',
    }),
    columnHelper.accessor('email_masked', {
      header: 'Email',
    }),
    columnHelper.accessor('es_atrasado', {
      header: 'Estado',
      cell: ({ getValue }) => {
        const atrasado = getValue()
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full ${atrasado ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {atrasado ? 'Atrasado' : 'No atrasado'}
          </span>
        )
      },
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
              <span key={c} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">F: {c}</span>
            ))}
            {causas.baja_nota.map(c => (
              <span key={c} className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">B: {c}</span>
            ))}
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
            <tr><td colSpan={10} className="px-4 py-8 text-center text-sm text-gray-500">Cargando...</td></tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr><td colSpan={10} className="px-4 py-8 text-center text-sm text-gray-500">No hay datos para mostrar</td></tr>
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
