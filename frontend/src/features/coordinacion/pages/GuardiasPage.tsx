import { useState } from 'react'
import { useGuardias, useCreateGuardia } from '../hooks/useGuardias'
import { guardiasService } from '../services/guardiasService'
import { GuardiasTable } from '../components/guardias/GuardiasTable'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function GuardiasPage() {
  const [filtroMateria, setFiltroMateria] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [nuevaMateria, setNuevaMateria] = useState('')
  const [nuevoDia, setNuevoDia] = useState('')
  const [nuevoHorario, setNuevoHorario] = useState('')

  const { data, isLoading, error } = useGuardias(filtroMateria || undefined)
  const createGuardia = useCreateGuardia()

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createGuardia.mutate({ materia_id: nuevaMateria, dia: nuevoDia, horario: nuevoHorario }, {
      onSuccess: () => {
        setShowForm(false)
        setNuevaMateria('')
        setNuevoDia('')
        setNuevoHorario('')
      },
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Guardias</h1>

      <div className="flex items-center gap-4">
        <input
          placeholder="Filtrar por Materia ID"
          value={filtroMateria}
          onChange={e => setFiltroMateria(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-64"
        />
        <button onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Nueva guardia
        </button>
        <button onClick={() => guardiasService.exportExcel(filtroMateria || undefined)}
          className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
          Exportar XLSX
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border rounded-lg p-4 flex gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Materia ID</label>
            <input value={nuevaMateria} onChange={e => setNuevaMateria(e.target.value)} className="border rounded-lg px-3 py-2 text-sm w-48" required />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Día</label>
            <select value={nuevoDia} onChange={e => setNuevoDia(e.target.value)} className="border rounded-lg px-3 py-2 text-sm" required>
              <option value="">Seleccionar...</option>
              {['LUNES','MARTES','MIÉRCOLES','JUEVES','VIERNES','SÁBADO','DOMINGO'].map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Horario</label>
            <input value={nuevoHorario} onChange={e => setNuevoHorario(e.target.value)} className="border rounded-lg px-3 py-2 text-sm w-32" placeholder="14:00-14:45" required />
          </div>
          <button type="submit" disabled={createGuardia.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {createGuardia.isPending ? 'Creando...' : 'Guardar'}
          </button>
          <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancelar</button>
        </form>
      )}

      {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar guardias" /> :
        <GuardiasTable data={data ?? []} isLoading={isLoading} />
      }
    </div>
  )
}
