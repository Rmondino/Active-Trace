import { useState } from 'react'
import { useColoquiosAdmin, useColoquio, useCreateConvocatoria, useImportAlumnos, useCargarResultados } from '../hooks/useColoquios'
import { ConvocatoriaCard } from '../components/coloquios/ConvocatoriaCard'
import { ConvocatoriaForm } from '../components/coloquios/ConvocatoriaForm'
import { ResultadosForm } from '../components/coloquios/ResultadosForm'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { ConvocatoriaPayload, ResultadoPayload } from '../types/coloquios'

export function ColoquiosPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showResultadosForm, setShowResultadosForm] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)

  const adminQuery = useColoquiosAdmin()
  const coloquioQuery = useColoquio(selectedId ?? '')
  const createConvocatoria = useCreateConvocatoria()
  const importAlumnos = useImportAlumnos()
  const cargarResultados = useCargarResultados()

  const handleCreate = (payload: ConvocatoriaPayload) => {
    createConvocatoria.mutate(payload, {
      onSuccess: () => setShowCreateForm(false),
    })
  }

  const handleImportAlumnos = () => {
    if (!importFile || !selectedId) return
    importAlumnos.mutate({ id: selectedId, file: importFile }, {
      onSuccess: () => setImportFile(null),
    })
  }

  const handleCargarResultados = (resultados: ResultadoPayload[]) => {
    if (!selectedId) return
    cargarResultados.mutate({ id: selectedId, resultados }, {
      onSuccess: () => setShowResultadosForm(false),
    })
  }

  const convocatoria = coloquioQuery.data

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Coloquios</h1>
        <button onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          Nueva convocatoria
        </button>
      </div>

      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowCreateForm(false)}>
          <div className="bg-white rounded-lg w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Nueva convocatoria</h3>
            <ConvocatoriaForm onSubmit={handleCreate} isPending={createConvocatoria.isPending} onCancel={() => setShowCreateForm(false)} />
          </div>
        </div>
      )}

      {selectedId ? (
        <div className="space-y-6">
          <button onClick={() => setSelectedId(null)} className="text-sm text-blue-600 hover:text-blue-800">
            &larr; Volver al listado
          </button>

          {coloquioQuery.isLoading ? <LoadingSpinner /> : coloquioQuery.error ? <ErrorMessage message="Error al cargar coloquio" /> : convocatoria && (
            <div className="space-y-6">
              <div className="bg-white border rounded-lg p-4">
                <h2 className="text-lg font-semibold mb-2">{convocatoria.materia_nombre}</h2>
                <p className="text-sm text-gray-500 mb-4">{convocatoria.instancia} — {convocatoria.cohorte_nombre}</p>
                <p className="text-sm text-gray-700">Días disponibles: {convocatoria.dias_disponibles}</p>
              </div>

              <div className="bg-white border rounded-lg p-4">
                <h3 className="text-sm font-semibold mb-3">Importar alumnos</h3>
                <div className="flex gap-3 items-center">
                  <input type="file" onChange={e => setImportFile(e.target.files?.[0] ?? null)} className="text-sm" accept=".xlsx,.csv" />
                  <button onClick={handleImportAlumnos} disabled={!importFile || importAlumnos.isPending}
                    className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
                    Importar
                  </button>
                </div>
              </div>

              <div className="bg-white border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold">Resultados</h3>
                  <button onClick={() => setShowResultadosForm(true)}
                    className="px-3 py-1.5 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
                    Cargar resultados
                  </button>
                </div>

                {convocatoria.alumnos && convocatoria.alumnos.length > 0 ? (
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Alumno</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nota</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {convocatoria.alumnos.map(al => {
                          const res = convocatoria.resultados?.find(r => r.alumno_id === al.id)
                          return (
                            <tr key={al.id} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-sm text-gray-700">{al.apellidos}, {al.nombre}</td>
                              <td className="px-4 py-2 text-sm text-gray-500">{al.email}</td>
                              <td className="px-4 py-2 text-sm font-medium">{res?.nota_final ?? '—'}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Sin alumnos cargados</p>
                )}
              </div>

              {convocatoria.reservas && convocatoria.reservas.length > 0 && (
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="text-sm font-semibold mb-3">Reservas ({convocatoria.reservas.length})</h3>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Alumno</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {convocatoria.reservas.map(r => (
                          <tr key={r.id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 text-sm text-gray-700">{r.alumno_nombre}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{r.fecha_hora}</td>
                            <td className="px-4 py-2">
                              <span className={`text-xs px-2 py-0.5 rounded-full ${r.estado === 'Activa' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                {r.estado}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {showResultadosForm && convocatoria.alumnos && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowResultadosForm(false)}>
                  <div className="bg-white rounded-lg w-full max-w-lg mx-4 p-6" onClick={e => e.stopPropagation()}>
                    <h3 className="text-lg font-semibold mb-4">Cargar resultados</h3>
                    <ResultadosForm
                      alumnos={convocatoria.alumnos}
                      onSubmit={handleCargarResultados}
                      isPending={cargarResultados.isPending}
                      onCancel={() => setShowResultadosForm(false)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <>
          {adminQuery.isLoading ? <LoadingSpinner /> : adminQuery.error ? <ErrorMessage message="Error al cargar coloquios" /> :
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(adminQuery.data ?? []).map(c => (
                <ConvocatoriaCard key={c.id} convocatoria={c} onClick={() => setSelectedId(c.id)} />
              ))}
              {(adminQuery.data ?? []).length === 0 && (
                <p className="text-sm text-gray-500 col-span-full">No hay convocatorias activas</p>
              )}
            </div>
          }
        </>
      )}
    </div>
  )
}
