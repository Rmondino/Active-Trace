import { useState, useMemo } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import { useMaterias, useCreateMateria, useUpdateMateria, useDeleteMateria } from '../hooks/useMaterias'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { Materia, MateriaPayload } from '../types/estructura'

const columnHelper = createColumnHelper<Materia>()

export function MateriasPage() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Materia | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [formData, setFormData] = useState<MateriaPayload>({ codigo: '', nombre: '', estado: 'activo' })

  const { data, isLoading, error } = useMaterias()
  const createMutation = useCreateMateria()
  const updateMutation = useUpdateMateria()
  const deleteMutation = useDeleteMateria()

  const columns = useMemo(() => [
    columnHelper.accessor('codigo', { header: 'Código' }),
    columnHelper.accessor('nombre', { header: 'Nombre' }),
    columnHelper.accessor('estado', {
      header: 'Estado',
      cell: ({ getValue }) => (
        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
          getValue() === 'activo' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
        }`}>
          {getValue()}
        </span>
      ),
    }),
    columnHelper.display({
      id: 'acciones',
      header: 'Acciones',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <button onClick={() => handleEdit(row.original)} className="text-sm text-blue-600 hover:text-blue-800">
            Editar
          </button>
          <button onClick={() => setDeleteId(row.original.id)} className="text-sm text-red-600 hover:text-red-800">
            Eliminar
          </button>
        </div>
      ),
    }),
  ], [])

  const table = useReactTable({
    data: data ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  const openCreate = () => {
    setEditing(null)
    setFormData({ codigo: '', nombre: '', estado: 'activo' })
    setModalOpen(true)
  }

  const handleEdit = (materia: Materia) => {
    setEditing(materia)
    setFormData({ codigo: materia.codigo, nombre: materia.nombre, estado: materia.estado })
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditing(null)
  }

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate({ id: editing.id, payload: formData }, { onSuccess: closeModal })
    } else {
      createMutation.mutate(formData, { onSuccess: closeModal })
    }
  }

  const isPending = editing ? updateMutation.isPending : createMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Materias</h1>
        <button onClick={openCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Nueva materia
        </button>
      </div>

      {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar materias" /> : (
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
                <tr><td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">No hay materias registradas</td></tr>
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

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={closeModal}>
          <div className="bg-white rounded-lg w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">{editing ? 'Editar materia' : 'Nueva materia'}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Código</label>
                <input type="text" value={formData.codigo} onChange={e => setFormData(p => ({ ...p, codigo: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                <input type="text" value={formData.nombre} onChange={e => setFormData(p => ({ ...p, nombre: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                <select value={formData.estado} onChange={e => setFormData(p => ({ ...p, estado: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  <option value="activo">Activo</option>
                  <option value="inactivo">Inactivo</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={closeModal} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">
                Cancelar
              </button>
              <button onClick={handleSubmit} disabled={isPending || !formData.codigo || !formData.nombre}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
                {isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDeleteId(null)}>
          <div className="bg-white rounded-lg w-full max-w-sm mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-2">Confirmar eliminación</h3>
            <p className="text-sm text-gray-600 mb-4">¿Estás seguro de eliminar esta materia? Esta acción no se puede deshacer.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteId(null)} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">
                Cancelar
              </button>
              <button onClick={() => deleteMutation.mutate(deleteId, { onSuccess: () => setDeleteId(null) })} disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50">
                {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
