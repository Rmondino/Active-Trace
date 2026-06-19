import { useState } from 'react'
import { useTareas, useMisTareas, useCreateTarea } from '../hooks/useTareas'
import { TareasTable } from '../components/tareas/TareasTable'
import { TareaForm } from '../components/tareas/TareaForm'
import { TareaDetail } from '../components/tareas/TareaDetail'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { Tarea, TareaPayload } from '../types/tareas'

type Tab = 'todas' | 'mias'

export function TareasPage() {
  const [activeTab, setActiveTab] = useState<Tab>('todas')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedTarea, setSelectedTarea] = useState<Tarea | null>(null)
  const [filtroEstado, setFiltroEstado] = useState('')

  const tareasQuery = useTareas(filtroEstado ? { estado: filtroEstado } : undefined)
  const misTareasQuery = useMisTareas(filtroEstado ? { estado: filtroEstado } : undefined)
  const createTarea = useCreateTarea()

  const handleCreate = (payload: TareaPayload) => {
    createTarea.mutate(payload, { onSuccess: () => setShowCreateForm(false) })
  }

  const data = activeTab === 'todas' ? tareasQuery.data : misTareasQuery.data
  const isLoading = activeTab === 'todas' ? tareasQuery.isLoading : misTareasQuery.isLoading
  const error = activeTab === 'todas' ? tareasQuery.error : misTareasQuery.error

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tareas</h1>
        <button onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Nueva tarea
        </button>
      </div>

      <div className="flex items-center gap-4">
        <nav className="flex border-b border-gray-200">
          <button onClick={() => setActiveTab('todas')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              activeTab === 'todas' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}>
            Todas
          </button>
          <button onClick={() => setActiveTab('mias')}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              activeTab === 'mias' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}>
            Mis tareas
          </button>
        </nav>

        <div className="border-l border-gray-200 h-8" />

        <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="Pendiente">Pendiente</option>
          <option value="En progreso">En progreso</option>
          <option value="Resuelta">Resuelta</option>
          <option value="Cancelada">Cancelada</option>
        </select>
      </div>

      {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar tareas" /> :
        <TareasTable data={data ?? []} isLoading={isLoading} onSelect={setSelectedTarea} />
      }

      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowCreateForm(false)}>
          <div className="bg-white rounded-lg w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Nueva tarea</h3>
            <TareaForm onSubmit={handleCreate} isPending={createTarea.isPending} onCancel={() => setShowCreateForm(false)} />
          </div>
        </div>
      )}

      {selectedTarea && (
        <TareaDetail tarea={selectedTarea} onClose={() => setSelectedTarea(null)} />
      )}
    </div>
  )
}
