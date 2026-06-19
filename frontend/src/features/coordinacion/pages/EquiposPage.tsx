import { useState, useEffect } from 'react'
import { useAsignaciones } from '../hooks/useEquipos'
import { equiposService } from '../services/equiposService'
import { AsignacionesTable } from '../components/equipos/AsignacionesTable'
import { AsignacionMasivaForm } from '../components/equipos/AsignacionMasivaForm'
import { ClonarEquipoForm } from '../components/equipos/ClonarEquipoForm'
import { VigenciaForm } from '../components/equipos/VigenciaForm'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

type Tab = 'asignaciones' | 'masiva' | 'clonar' | 'vigencia'

const tabs: { key: Tab; label: string }[] = [
  { key: 'asignaciones', label: 'Asignaciones' },
  { key: 'masiva', label: 'Asignación Masiva' },
  { key: 'clonar', label: 'Clonar' },
  { key: 'vigencia', label: 'Vigencia' },
]

export function EquiposPage() {
  const [activeTab, setActiveTab] = useState<Tab>('asignaciones')
  const [filtroMateria, setFiltroMateria] = useState('')
  const [filtroCarrera, setFiltroCarrera] = useState('')
  const [filtroCohorte, setFiltroCohorte] = useState('')
  const [filtroRol, setFiltroRol] = useState('')
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const { data, isLoading, error } = useAsignaciones({
    materia_id: filtroMateria || undefined,
    carrera_id: filtroCarrera || undefined,
    cohorte_id: filtroCohorte || undefined,
    rol: filtroRol || undefined,
  })

  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(null), 3000)
      return () => clearTimeout(t)
    }
  }, [successMsg])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Equipos Docentes</h1>

      {successMsg && (
        <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg text-sm">{successMsg}</div>
      )}

      <nav className="flex border-b border-gray-200">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              activeTab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {activeTab === 'asignaciones' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <input placeholder="Materia ID" value={filtroMateria} onChange={e => setFiltroMateria(e.target.value)} className="border rounded-lg px-3 py-2 text-sm w-48" />
            <input placeholder="Carrera ID" value={filtroCarrera} onChange={e => setFiltroCarrera(e.target.value)} className="border rounded-lg px-3 py-2 text-sm w-48" />
            <input placeholder="Cohorte ID" value={filtroCohorte} onChange={e => setFiltroCohorte(e.target.value)} className="border rounded-lg px-3 py-2 text-sm w-48" />
            <select value={filtroRol} onChange={e => setFiltroRol(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
              <option value="">Todos los roles</option>
              <option value="PROFESOR">PROFESOR</option>
              <option value="TUTOR">TUTOR</option>
              <option value="NEXO">NEXO</option>
              <option value="COORDINADOR">COORDINADOR</option>
            </select>
            <button onClick={() => equiposService.exportExcel()} className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              Exportar
            </button>
          </div>

          {isLoading ? <LoadingSpinner /> : error ? <ErrorMessage message="Error al cargar asignaciones" /> :
            <AsignacionesTable data={data ?? []} isLoading={isLoading} />
          }
        </div>
      )}

      {activeTab === 'masiva' && (
        <AsignacionMasivaForm onSuccess={(total) => setSuccessMsg(`${total} asignaciones creadas`)} />
      )}

      {activeTab === 'clonar' && (
        <ClonarEquipoForm onSuccess={(total) => setSuccessMsg(`${total} asignaciones clonadas`)} />
      )}

      {activeTab === 'vigencia' && (
        <VigenciaForm onSuccess={(total) => setSuccessMsg(`${total} asignaciones actualizadas`)} />
      )}
    </div>
  )
}
