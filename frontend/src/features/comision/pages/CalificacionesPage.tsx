import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useCalificaciones } from '../hooks/useCalificaciones'
import { FileUpload } from '../components/FileUpload'
import { UmbralConfig } from '../components/UmbralConfig'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function CalificacionesPage() {
  const { materiaId, cohorteId } = useParams<{ materiaId: string; cohorteId: string }>()
  const [refreshKey, setRefreshKey] = useState(0)
  const { data: calificaciones, isLoading, error } = useCalificaciones(materiaId!)

  if (!materiaId || !cohorteId) {
    return <ErrorMessage message="Faltan parámetros de la comisión" />
  }

  return (
    <div className="space-y-6">
      <FileUpload
        key={`upload-${refreshKey}`}
        materiaId={materiaId}
        cohorteId={cohorteId}
        onImportComplete={() => setRefreshKey(k => k + 1)}
      />

      <UmbralConfig materiaId={materiaId} />

      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold mb-4">Calificaciones actuales</h2>
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message="Error al cargar calificaciones" />
        ) : !calificaciones || calificaciones.length === 0 ? (
          <p className="text-sm text-gray-500">No hay calificaciones importadas</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actividad</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nota</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Aprobado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Origen</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {calificaciones.map(c => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-700">{c.actividad}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {c.nota_numerica ?? c.nota_textual ?? '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        c.aprobado ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {c.aprobado ? 'Sí' : 'No'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{c.origen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
