import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAtrasados, useRanking, useReporte, useNotasFinales } from '../hooks/useAnalisis'
import { AtrasadosTable } from '../components/AtrasadosTable'
import { RankingTable } from '../components/RankingTable'
import { ReporteResumen } from '../components/ReporteResumen'
import { NotasFinalesTable } from '../components/NotasFinalesTable'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { Atrasado } from '../types/analisis'
import type { AlumnoDestino } from '../types/comunicaciones'

type SubTab = 'atrasados' | 'ranking' | 'reporte' | 'notas'

const subTabs: { key: SubTab; label: string }[] = [
  { key: 'atrasados', label: 'Atrasados' },
  { key: 'ranking', label: 'Ranking' },
  { key: 'reporte', label: 'Reporte Rápido' },
  { key: 'notas', label: 'Notas Finales' },
]

export function AtrasadosPage() {
  const { materiaId, cohorteId } = useParams<{ materiaId: string; cohorteId: string }>()
  const navigate = useNavigate()
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('atrasados')

  const atrasadosQuery = useAtrasados(materiaId!, cohorteId!)
  const rankingQuery = useRanking(materiaId!, cohorteId!)
  const reporteQuery = useReporte(materiaId!, cohorteId!)
  const notasQuery = useNotasFinales(materiaId!, cohorteId!)

  if (!materiaId || !cohorteId) {
    return <ErrorMessage message="Faltan parámetros de la comisión" />
  }

  const handleComunicar = (seleccionados: Atrasado[]) => {
    const alumnosDestino: AlumnoDestino[] = seleccionados.map(a => ({
      id: a.entrada_padron_id,
      nombre: a.alumno.split(' ')[0],
      apellidos: a.alumno.split(' ').slice(1).join(' '),
      comision: a.comision,
    }))
    navigate(`/comision/${materiaId}/${cohorteId}/comunicacion`, {
      state: { alumnos: alumnosDestino },
    })
  }

  const handleExport = () => {
    const data = atrasadosQuery.data ?? []
    const headers = ['Alumno', 'Comisión', 'Total', 'Aprobadas', 'Desaprobadas', 'Sin nota', 'Causas']
    const rows = data.map(a => [
      a.alumno,
      a.comision,
      a.total_actividades,
      a.aprobadas,
      a.desaprobadas,
      a.sin_nota,
      [...a.causas.faltantes, ...a.causas.baja_nota].join('; '),
    ])
    const csv = [headers.join(','), ...rows.map(r => r.map(c => `"${c}"`).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `atrasados_${materiaId}_${cohorteId}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <nav className="flex border-b border-gray-200">
          {subTabs.map(t => (
            <button
              key={t.key}
              onClick={() => setActiveSubTab(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
                activeSubTab === t.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {activeSubTab === 'atrasados' && (
          <button
            onClick={handleExport}
            className="px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Exportar sin corregir
          </button>
        )}
      </div>

      {activeSubTab === 'atrasados' && (
        atrasadosQuery.isLoading ? <LoadingSpinner /> :
        atrasadosQuery.error ? <ErrorMessage message="Error al cargar atrasados" /> :
        <AtrasadosTable
          data={atrasadosQuery.data ?? []}
          onComunicar={handleComunicar}
          isLoading={atrasadosQuery.isLoading}
        />
      )}

      {activeSubTab === 'ranking' && (
        rankingQuery.isLoading ? <LoadingSpinner /> :
        rankingQuery.error ? <ErrorMessage message="Error al cargar ranking" /> :
        <RankingTable
          data={rankingQuery.data ?? []}
          isLoading={rankingQuery.isLoading}
        />
      )}

      {activeSubTab === 'reporte' && (
        reporteQuery.isLoading ? <LoadingSpinner /> :
        reporteQuery.error ? <ErrorMessage message="Error al cargar reporte" /> :
        <ReporteResumen
          data={reporteQuery.data}
          isLoading={reporteQuery.isLoading}
        />
      )}

      {activeSubTab === 'notas' && (
        notasQuery.isLoading ? <LoadingSpinner /> :
        notasQuery.error ? <ErrorMessage message="Error al cargar notas finales" /> :
        <NotasFinalesTable
          data={notasQuery.data ?? []}
          isLoading={notasQuery.isLoading}
        />
      )}
    </div>
  )
}
