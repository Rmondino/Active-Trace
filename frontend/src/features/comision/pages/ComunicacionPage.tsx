import { useState } from 'react'
import { useParams, useLocation } from 'react-router-dom'
import { usePreviewComunicacion, useEnviarComunicacion, useTrackingComunicaciones } from '../hooks/useComunicaciones'
import { ComunicacionForm } from '../components/ComunicacionForm'
import { ComunicacionPreview } from '../components/ComunicacionPreview'
import { TrackingTable } from '../components/TrackingTable'
import { ErrorMessage } from '@/shared/components/ErrorMessage'
import type { AlumnoDestino, PreviewComunicacionResponse, PreviewAlumno } from '../types/comunicaciones'

type Step = 'form' | 'preview' | 'tracking'

export function ComunicacionPage() {
  const { materiaId, cohorteId } = useParams<{ materiaId: string; cohorteId: string }>()
  const location = useLocation()
  const alumnos = location.state?.alumnos as AlumnoDestino[] | undefined

  const [step, setStep] = useState<Step>('form')
  const [asunto, setAsunto] = useState('')
  const [cuerpo, setCuerpo] = useState('')
  const [previewData, setPreviewData] = useState<PreviewAlumno[]>([])

  const previewMutation = usePreviewComunicacion()
  const enviarMutation = useEnviarComunicacion()
  const trackingQuery = useTrackingComunicaciones(materiaId!)

  if (!materiaId || !cohorteId) {
    return <ErrorMessage message="Faltan parámetros de la comisión" />
  }

  if (!alumnos || alumnos.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No hay alumnos seleccionados para comunicar.</p>
        <p className="text-sm text-gray-400 mt-2">
          Seleccioná alumnos desde la vista de Atrasados para iniciar una comunicación.
        </p>
      </div>
    )
  }

  const handlePreview = (a: string, c: string) => {
    setAsunto(a)
    setCuerpo(c)
    previewMutation.mutate({
      materia_id: materiaId,
      asunto_template: a,
      cuerpo_template: c,
      alumnos,
    }, {
      onSuccess: (data: PreviewComunicacionResponse) => {
        setPreviewData(data.previews)
        setStep('preview')
      },
    })
  }

  const handleEnviar = () => {
    enviarMutation.mutate({
      materia_id: materiaId,
      asunto,
      cuerpo,
      destinatarios: alumnos.map(a => ({ email: a.id })),
      preview_token: '',
    }, {
      onSuccess: () => {
        setStep('tracking')
      },
    })
  }

  return (
    <div className="space-y-6">
      {step === 'form' && (
        <ComunicacionForm
          alumnos={alumnos}
          materiaId={materiaId}
          onPreview={handlePreview}
          isLoading={previewMutation.isPending}
        />
      )}

      {step === 'preview' && (
        <ComunicacionPreview
          previews={previewData}
          onEnviar={handleEnviar}
          isLoading={enviarMutation.isPending}
        />
      )}

      {step === 'tracking' && (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-700 font-medium">
              Comunicación enviada exitosamente
            </p>
          </div>
          <TrackingTable
            data={trackingQuery.data ?? []}
            isLoading={trackingQuery.isLoading}
          />
        </div>
      )}
    </div>
  )
}
