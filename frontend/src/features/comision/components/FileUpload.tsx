import { useState, useRef } from 'react'
import { useUploadPreview } from '../hooks/useCalificaciones'
import { ActividadesSelector } from './ActividadesSelector'
import type { PreviewResponse } from '../types/calificaciones'

interface FileUploadProps {
  materiaId: string
  cohorteId: string
  onImportComplete: () => void
}

export function FileUpload({ materiaId, cohorteId, onImportComplete }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const uploadPreview = useUploadPreview()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) setFile(f)
  }

  const handlePreview = () => {
    if (!file) return
    uploadPreview.mutate({ file, materiaId, cohorteId }, {
      onSuccess: (data) => setPreview(data),
    })
  }

  const handleConfirm = (actividadesSeleccionadas: string[]) => {
    if (!preview) return
    uploadPreview.mutate({ file, materiaId, cohorteId }, {
      onSuccess: () => {
        setPreview(null)
        setFile(null)
        onImportComplete()
      },
    })
  }

  return (
    <div className="bg-white rounded-lg border p-6 space-y-4">
      <h2 className="text-lg font-semibold">Importar calificaciones</h2>

      <div className="flex items-center gap-4">
        <input
          ref={fileRef}
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileChange}
          className="block text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {file && (
          <span className="text-sm text-gray-500">
            {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </span>
        )}
      </div>

      {file && !preview && (
        <button
          onClick={handlePreview}
          disabled={uploadPreview.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {uploadPreview.isPending ? 'Procesando...' : 'Previsualizar'}
        </button>
      )}

      {uploadPreview.isError && (
        <p className="text-sm text-red-600">Error al procesar el archivo</p>
      )}

      {preview && (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            {preview.total_alumnos} alumnos detectados · {preview.actividades.length} actividades
          </p>
          <ActividadesSelector
            actividades={preview.actividades}
            onConfirm={handleConfirm}
          />
        </div>
      )}
    </div>
  )
}
