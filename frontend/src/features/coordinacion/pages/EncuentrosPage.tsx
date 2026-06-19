import { useState } from 'react'
import { useSlots, useCreateSlot, useUpdateInstancia, useAulaHtml } from '../hooks/useEncuentros'
import { useInstancias } from '../hooks/useEncuentros'
import { SlotForm } from '../components/encuentros/SlotForm'
import { InstanciasTable } from '../components/encuentros/InstanciasTable'
import { InstanciaEditModal } from '../components/encuentros/InstanciaEditModal'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { SlotEncuentro, InstanciaEncuentro, InstanciaEditPayload } from '../types/encuentros'

export function EncuentrosPage() {
  const [materiaId, setMateriaId] = useState('')
  const [showSlotForm, setShowSlotForm] = useState(false)
  const [expandedSlot, setExpandedSlot] = useState<string | null>(null)
  const [editInstancia, setEditInstancia] = useState<InstanciaEncuentro | null>(null)

  const slotsQuery = useSlots(materiaId)
  const createSlot = useCreateSlot()
  const updateInstancia = useUpdateInstancia()
  const aulaHtml = useAulaHtml(materiaId)
  const instanciasQuery = useInstancias(expandedSlot ?? '')

  const handleCreateSlot = (payload: Parameters<typeof createSlot.mutate>[0]) => {
    createSlot.mutate(payload, {
      onSuccess: () => {
        setShowSlotForm(false)
      },
    })
  }

  const handleUpdateInstancia = (id: string, payload: InstanciaEditPayload) => {
    updateInstancia.mutate({ id, payload }, {
      onSuccess: () => setEditInstancia(null),
    })
  }

  const handleCopyAulaHtml = async () => {
    if (aulaHtml.data) {
      await navigator.clipboard.writeText(aulaHtml.data)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Encuentros</h1>

      <div className="flex items-center gap-4">
        <input
          placeholder="Materia ID"
          value={materiaId}
          onChange={e => setMateriaId(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-64"
        />
        <button onClick={() => setShowSlotForm(true)} disabled={!materiaId}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          Nuevo slot
        </button>
        <button onClick={handleCopyAulaHtml}
          className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
          Generar HTML aula
        </button>
      </div>

      {showSlotForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowSlotForm(false)}>
          <div className="bg-white rounded-lg w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Nuevo Slot</h3>
            <SlotForm
              materiaId={materiaId}
              onSubmit={handleCreateSlot}
              isPending={createSlot.isPending}
              onCancel={() => setShowSlotForm(false)}
            />
          </div>
        </div>
      )}

      {editInstancia && (
        <InstanciaEditModal
          instancia={editInstancia}
          onSave={handleUpdateInstancia}
          onClose={() => setEditInstancia(null)}
          isPending={updateInstancia.isPending}
        />
      )}

      {slotsQuery.isLoading ? (
        <LoadingSpinner />
      ) : slotsQuery.error ? (
        <ErrorMessage message="Error al cargar slots" />
      ) : (
        <div className="space-y-4">
          {(slotsQuery.data ?? []).map((slot: SlotEncuentro) => (
            <div key={slot.id} className="bg-white border rounded-lg">
              <button
                onClick={() => setExpandedSlot(expandedSlot === slot.id ? null : slot.id)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50"
              >
                <div className="flex items-center gap-4">
                  <span className="font-medium text-gray-900">{slot.titulo}</span>
                  <span className="text-sm text-gray-500">{slot.hora}</span>
                  {slot.dia_semana && <span className="text-sm text-gray-500">{slot.dia_semana}</span>}
                </div>
                <span className="text-sm text-gray-400">{expandedSlot === slot.id ? '\u25B2' : '\u25BC'}</span>
              </button>

              {expandedSlot === slot.id && (
                <div className="border-t px-4 py-3">
                  {instanciasQuery.isLoading ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <InstanciasTable
                      instancias={instanciasQuery.data ?? []}
                      onEdit={setEditInstancia}
                    />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
