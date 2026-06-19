import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAsignaciones } from '../hooks/useAsignaciones'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function ComisionSelectorPage() {
  const navigate = useNavigate()
  const { data: asignaciones, isLoading, error } = useAsignaciones()
  const [search, setSearch] = useState('')

  const filtered = asignaciones?.filter(a =>
    a.materia_nombre.toLowerCase().includes(search.toLowerCase()) ||
    a.cohorte_nombre.toLowerCase().includes(search.toLowerCase())
  ) ?? []

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage message="Error al cargar comisiones" />

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Mis Comisiones</h1>
      <input
        type="text"
        placeholder="Buscar comisión..."
        className="w-full p-3 border rounded-lg mb-4"
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <div className="grid gap-4">
        {filtered.map(a => (
          <div
            key={`${a.materia_id}-${a.cohorte_id}`}
            className="bg-white p-4 rounded-lg shadow cursor-pointer hover:shadow-md transition"
            onClick={() => navigate(`/comision/${a.materia_id}/${a.cohorte_id}/calificaciones`)}
          >
            <h2 className="font-semibold text-lg">{a.materia_nombre}</h2>
            <p className="text-gray-600">{a.carrera_nombre} — {a.cohorte_nombre}</p>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{a.rol}</span>
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="text-gray-500 text-center py-8">No se encontraron comisiones</p>
        )}
      </div>
    </div>
  )
}
