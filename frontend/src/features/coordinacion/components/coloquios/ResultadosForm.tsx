import { useState } from 'react'
import type { ResultadoPayload } from '../../types/coloquios'

interface ResultadosFormProps {
  alumnos: { id: string; nombre: string; apellidos: string }[]
  onSubmit: (resultados: ResultadoPayload[]) => void
  isPending: boolean
  onCancel: () => void
}

export function ResultadosForm({ alumnos, onSubmit, isPending, onCancel }: ResultadosFormProps) {
  const [resultados, setResultados] = useState<Record<string, string>>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: ResultadoPayload[] = Object.entries(resultados)
      .filter(([, nota]) => nota.trim())
      .map(([alumno_id, nota_final]) => ({ alumno_id, nota_final }))
    onSubmit(payload)
  }

  const setNota = (alumnoId: string, nota: string) => {
    setResultados(prev => ({ ...prev, [alumnoId]: nota }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="overflow-x-auto border rounded-lg max-h-80 overflow-y-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Alumno</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nota Final</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {alumnos.map(al => (
              <tr key={al.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-sm text-gray-700">{al.apellidos}, {al.nombre}</td>
                <td className="px-4 py-2">
                  <input
                    value={resultados[al.id] ?? ''}
                    onChange={e => setNota(al.id, e.target.value)}
                    className="w-32 border rounded px-2 py-1 text-sm"
                    placeholder="Nota"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">Cancelar</button>
        <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {isPending ? 'Guardando...' : 'Guardar resultados'}
        </button>
      </div>
    </form>
  )
}
