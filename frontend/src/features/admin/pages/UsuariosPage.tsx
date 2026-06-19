import { useState, useMemo } from 'react'
import {
  createColumnHelper,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type SortingState,
} from '@tanstack/react-table'
import { useUsuarios, useCreateUsuario, useUpdateUsuario, useDeleteUsuario } from '../hooks/useUsuarios'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { UserRead, UserCreate, UserUpdate } from '../types/usuarios'

const columnHelper = createColumnHelper<UserRead>()
const emptyForm: UserCreate = {
  email: '', nombre: '', apellido: '', dni: '', cuil: '', cbu: '',
  alias_cbu: '', banco: '', regional: '', legajo: '', facturador: '', password: '', roles: [],
}

export function UsuariosPage() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<UserRead | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [formData, setFormData] = useState<UserCreate>(emptyForm)

  const { data, isLoading, error } = useUsuarios({ search: search || undefined, estado: estadoFilter || undefined })
  const createMutation = useCreateUsuario()
  const updateMutation = useUpdateUsuario()
  const deleteMutation = useDeleteUsuario()

  const columns = useMemo(() => [
    columnHelper.accessor('apellido', { header: 'Apellido' }),
    columnHelper.accessor('nombre', { header: 'Nombre' }),
    columnHelper.accessor('email', { header: 'Email' }),
    columnHelper.accessor('dni', { header: 'DNI' }),
    columnHelper.accessor('legajo', { header: 'Legajo' }),
    columnHelper.accessor('regional', { header: 'Regional' }),
    columnHelper.accessor('facturador', { header: 'Facturador' }),
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
    setFormData(emptyForm)
    setModalOpen(true)
  }

  const handleEdit = (usuario: UserRead) => {
    setEditing(usuario)
    setFormData({
      email: usuario.email,
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      dni: usuario.dni,
      cuil: usuario.cuil,
      cbu: usuario.cbu,
      alias_cbu: usuario.alias_cbu,
      banco: usuario.banco,
      regional: usuario.regional,
      legajo: usuario.legajo,
      facturador: usuario.facturador,
      password: '',
      roles: usuario.roles,
    })
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditing(null)
  }

  const handleSubmit = () => {
    if (editing) {
      const payload: UserUpdate = { ...formData }
      if (!payload.password) delete payload.password
      updateMutation.mutate({ id: editing.id, payload }, { onSuccess: closeModal })
    } else {
      createMutation.mutate(formData, { onSuccess: closeModal })
    }
  }

  const isPending = editing ? updateMutation.isPending : createMutation.isPending

  const updateField = (field: keyof UserCreate, value: string) => {
    setFormData(p => ({ ...p, [field]: value }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
        <button onClick={openCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Nuevo usuario
        </button>
      </div>

      <div className="flex items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Buscar</label>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Nombre, email, DNI..."
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm min-w-[250px]" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
          <select value={estadoFilter} onChange={e => setEstadoFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
            <option value="">Todos</option>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </select>
        </div>
      </div>

      {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar usuarios" /> : (
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
                <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">No hay usuarios registrados</td></tr>
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
          <div className="bg-white rounded-lg w-full max-w-2xl mx-4 p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">{editing ? 'Editar usuario' : 'Nuevo usuario'}</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" value={formData.email} onChange={e => updateField('email', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
                <input type="text" value={formData.nombre} onChange={e => updateField('nombre', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Apellido *</label>
                <input type="text" value={formData.apellido} onChange={e => updateField('apellido', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">DNI *</label>
                <input type="text" value={formData.dni} onChange={e => updateField('dni', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CUIL *</label>
                <input type="text" value={formData.cuil} onChange={e => updateField('cuil', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CBU *</label>
                <input type="text" value={formData.cbu} onChange={e => updateField('cbu', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Alias CBU</label>
                <input type="text" value={formData.alias_cbu} onChange={e => updateField('alias_cbu', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Banco</label>
                <input type="text" value={formData.banco} onChange={e => updateField('banco', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Regional</label>
                <input type="text" value={formData.regional} onChange={e => updateField('regional', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Legajo</label>
                <input type="text" value={formData.legajo} onChange={e => updateField('legajo', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Facturador</label>
                <input type="text" value={formData.facturador} onChange={e => updateField('facturador', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {editing ? 'Contraseña (dejar vacío para mantener)' : 'Contraseña *'}
                </label>
                <input type="password" value={formData.password} onChange={e => updateField('password', e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={closeModal} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">
                Cancelar
              </button>
              <button onClick={handleSubmit} disabled={isPending || !formData.email || !formData.nombre || !formData.apellido || !formData.dni || !formData.cuil || !formData.cbu || (!editing && !formData.password)}
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
            <p className="text-sm text-gray-600 mb-4">¿Estás seguro de eliminar este usuario? Esta acción no se puede deshacer.</p>
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
