import { useState } from 'react'
import { useMonitor } from '../hooks/useMonitor'
import { MonitorTable } from '../components/monitor/MonitorTable'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function MonitorPage() {
  const [filtroMateria, setFiltroMateria] = useState('')
  const [filtroBusqueda, setFiltroBusqueda] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('')

  const { data, isLoading, error } = useMonitor({
    materia_id: filtroMateria || undefined,
    busqueda: filtroBusqueda || undefined,
    estado: filtroEstado || undefined,
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Monitor General</h1>

      <div className="flex flex-wrap gap-4">
        <input
          placeholder="Materia ID"
          value={filtroMateria}
          onChange={e => setFiltroMateria(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-48"
        />
        <input
          placeholder="Buscar alumno..."
          value={filtroBusqueda}
          onChange={e => setFiltroBusqueda(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-64"
        />
        <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">Todos</option>
          <option value="atrasado">Atrasado</option>
          <option value="no_atrasado">No atrasado</option>
        </select>
      </div>

      {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar monitor" /> :
        <MonitorTable data={data ?? []} isLoading={isLoading} />
      }
    </div>
  )
}
