import { useState } from 'react'
import { useAvisos, useCreateAviso, useUpdateAviso, useDeleteAviso } from '../hooks/useAvisos'
import { AvisosTable } from '../components/avisos/AvisosTable'
import { AvisoForm } from '../components/avisos/AvisoForm'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { Aviso, AvisoPayload } from '../types/avisos'

export function AvisosPage() {
  const [editingAviso, setEditingAviso] = useState<Aviso | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const { data, isLoading, error } = useAvisos()
  const createAviso = useCreateAviso()
  const updateAviso = useUpdateAviso()
  const deleteAviso = useDeleteAviso()

  const handleCreate = (payload: AvisoPayload) => {
    createAviso.mutate(payload, { onSuccess: () => setShowCreateForm(false) })
  }

  const handleUpdate = (payload: AvisoPayload) => {
    if (!editingAviso) return
    updateAviso.mutate({ id: editingAviso.id, payload }, { onSuccess: () => setEditingAviso(null) })
  }

  const handleDelete = (id: string) => {
    deleteAviso.mutate(id, { onSuccess: () => setDeleteConfirm(null) })
  }

  const closeModals = () => {
    setEditingAviso(null)
    setShowCreateForm(false)
    setDeleteConfirm(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Avisos</h1>
        <button onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Nuevo aviso
        </button>
      </div>

      {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar avisos" /> :
        <AvisosTable
          data={data ?? []}
          isLoading={isLoading}
          onEdit={setEditingAviso}
          onDelete={(id) => setDeleteConfirm(id)}
        />
      }

      {/* Create/Edit Modal */}
      {(showCreateForm || editingAviso) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={closeModals}>
          <div className="bg-white rounded-lg w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">
              {editingAviso ? 'Editar aviso' : 'Nuevo aviso'}
            </h3>
            <AvisoForm
              aviso={editingAviso ?? undefined}
              onSubmit={editingAviso ? handleUpdate : handleCreate}
              isPending={editingAviso ? updateAviso.isPending : createAviso.isPending}
              onCancel={closeModals}
            />
          </div>
        </div>
      )}

      {/* Delete Confirm */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={closeModals}>
          <div className="bg-white rounded-lg w-full max-w-sm mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-2">Confirmar eliminación</h3>
            <p className="text-sm text-gray-600 mb-4">¿Estás seguro de eliminar este aviso? Esta acción no se puede deshacer.</p>
            <div className="flex justify-end gap-3">
              <button onClick={closeModals} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">
                Cancelar
              </button>
              <button onClick={() => handleDelete(deleteConfirm)} disabled={deleteAviso.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50">
                {deleteAviso.isPending ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
