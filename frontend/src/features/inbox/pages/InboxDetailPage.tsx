import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useMensajeDetalle, useResponderMensaje } from '@/features/inbox/hooks/useInbox'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

function formatFecha(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function InboxDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: mensaje, isLoading, isError, error } = useMensajeDetalle(id!)
  const responder = useResponderMensaje()
  const [cuerpo, setCuerpo] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  useEffect(() => {
    if (responder.isSuccess) {
      setSuccessMsg('Respuesta enviada correctamente')
      setCuerpo('')
      setTimeout(() => setSuccessMsg(''), 3000)
    }
  }, [responder.isSuccess])

  if (isLoading) return <LoadingSpinner size="lg" className="mt-12" />
  if (isError) return <ErrorMessage message={(error as Error)?.message ?? 'Error al cargar el mensaje'} />
  if (!mensaje) return <ErrorMessage message="Mensaje no encontrado" />

  const handleResponder = (e: React.FormEvent) => {
    e.preventDefault()
    if (!cuerpo.trim()) return
    responder.mutate({ id: id!, data: { cuerpo } })
  }

  return (
    <div className="mx-auto max-w-3xl">
      <button
        onClick={() => navigate('/inbox')}
        className="mb-4 text-sm text-blue-600 hover:text-blue-500"
      >
        &larr; Volver a mensajes
      </button>

      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">{mensaje.asunto}</h1>

        <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
          <span>De: <strong className="text-gray-700">{mensaje.remitente_nombre}</strong></span>
          <span>{formatFecha(mensaje.fecha)}</span>
        </div>

        <div className="mt-6 whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
          {mensaje.cuerpo}
        </div>
      </div>

      <div className="mt-6 rounded-lg bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Responder</h2>

        {successMsg && (
          <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-700" role="status">
            {successMsg}
          </div>
        )}

        {responder.isError && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
            {(responder.error as Error)?.message ?? 'Error al enviar respuesta'}
          </div>
        )}

        <form onSubmit={handleResponder} className="space-y-4">
          <textarea
            value={cuerpo}
            onChange={(e) => setCuerpo(e.target.value)}
            rows={5}
            required
            placeholder="Escribí tu respuesta…"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={responder.isPending || !cuerpo.trim()}
              className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {responder.isPending ? 'Enviando…' : 'Enviar respuesta'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
