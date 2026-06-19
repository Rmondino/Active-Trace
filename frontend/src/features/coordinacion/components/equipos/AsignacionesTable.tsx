import { useMemo, useState } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import type { AsignacionDocente } from '../../types/equipos'

const columnHelper = createColumnHelper<AsignacionDocente>()

interface AsignacionesTableProps {
  data: AsignacionDocente[]
  isLoading: boolean
}

export function AsignacionesTable({ data, isLoading }: AsignacionesTableProps) {
  const [sorting, setSorting] = useState<SortingState>([])

  const columns = useMemo(() => [
    columnHelper.accessor('usuario_nombre', {
      header: 'Docente',
      sortingFn: 'text',
    }),
    columnHelper.accessor('rol', {
      header: 'Rol',
    }),
    columnHelper.accessor('materia_nombre', {
      header: 'Materia',
    }),
    columnHelper.accessor('carrera_nombre', {
      header: 'Carrera',
    }),
    columnHelper.accessor('cohorte_nombre', {
      header: 'Cohorte',
    }),
    columnHelper.accessor('comisiones', {
      header: 'Comisiones',
      cell: ({ getValue }) => (getValue() ?? []).join(', ') || '-',
    }),
    columnHelper.accessor('desde', {
      header: 'Vigencia Desde',
    }),
    columnHelper.accessor('hasta', {
      header: 'Vigencia Hasta',
      cell: ({ getValue }) => getValue() ?? '—',
    }),
    columnHelper.accessor('estado_vigencia', {
      header: 'Estado',
      cell: ({ getValue }) => {
        const v = getValue()
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full ${v === 'Vigente' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {v}
          </span>
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
              <td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">Cargando...</td>
            </tr>
          ) : table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">No hay asignaciones</td>
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
