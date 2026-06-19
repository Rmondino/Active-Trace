import { useState, useEffect } from 'react'
import { useUmbral, useUpdateUmbral } from '../hooks/useUmbral'

interface UmbralConfigProps {
  materiaId: string
}

export function UmbralConfig({ materiaId }: UmbralConfigProps) {
  const { data: umbral, isLoading } = useUmbral(materiaId)
  const updateUmbral = useUpdateUmbral()
  const [porcentaje, setPorcentaje] = useState(60)
  const [valores, setValores] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (umbral) {
      setPorcentaje(umbral.umbral_pct)
      setValores(umbral.valores_aprobatorios.join(', '))
    }
  }, [umbral])

  const handleSave = () => {
    updateUmbral.mutate({
      materiaId,
      data: {
        umbral_pct: porcentaje,
        valores_aprobatorios: valores.split(',').map(v => v.trim()).filter(Boolean),
      },
    }, {
      onSuccess: () => {
        setSaved(true)
        setTimeout(() => setSaved(false), 3000)
      },
    })
  }

  if (isLoading) return <div className="text-sm text-gray-500">Cargando umbral...</div>

  return (
    <div className="bg-white rounded-lg border p-6 space-y-4">
      <h2 className="text-lg font-semibold">Configurar umbral</h2>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Porcentaje mínimo de aprobación: {porcentaje}%
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={porcentaje}
            onChange={e => setPorcentaje(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Valores aprobatorios (textuales, separados por coma)
          </label>
          <input
            type="text"
            value={valores}
            onChange={e => setValores(e.target.value)}
            placeholder="Aprobado, Promocionado, Muy bueno"
            className="w-full p-2 border rounded-lg text-sm"
          />
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={updateUmbral.isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {updateUmbral.isPending ? 'Guardando...' : 'Guardar'}
      </button>

      {saved && (
        <p className="text-sm text-green-600">Umbral actualizado correctamente</p>
      )}
      {updateUmbral.isError && (
        <p className="text-sm text-red-600">Error al guardar el umbral</p>
      )}
    </div>
  )
}
