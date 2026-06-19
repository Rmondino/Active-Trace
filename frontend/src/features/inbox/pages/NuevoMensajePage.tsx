import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useEnviarMensaje } from '@/features/inbox/hooks/useInbox'

export function NuevoMensajePage() {
  const navigate = useNavigate()
  const mutation = useEnviarMensaje()
  const [destinatarioId, setDestinatarioId] = useState('')
  const [asunto, setAsunto] = useState('')
  const [cuerpo, setCuerpo] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (mutation.isSuccess) {
      navigate('/inbox')
    }
  }, [mutation.isSuccess, navigate])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!destinatarioId.trim()) {
      setError('El destinatario es obligatorio')
      return
    }
    if (!asunto.trim()) {
      setError('El asunto es obligatorio')
      return
    }
    if (!cuerpo.trim()) {
      setError('El cuerpo del mensaje es obligatorio')
      return
    }

    mutation.mutate({
      destinatario_id: destinatarioId,
      asunto,
      cuerpo,
    })
  }

  return (
    <div className="mx-auto max-w-2xl">
      <button
        onClick={() => navigate('/inbox')}
        className="mb-4 text-sm text-blue-600 hover:text-blue-500"
      >
        &larr; Volver a mensajes
      </button>

      <h1 className="mb-6 text-2xl font-bold text-gray-900">Nuevo mensaje</h1>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      {mutation.isError && (
        <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          {(mutation.error as Error)?.message ?? 'Error al enviar el mensaje'}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg bg-white p-6 shadow-sm">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Destinatario (ID de usuario)
          </label>
          <input
            type="text"
            value={destinatarioId}
            onChange={(e) => setDestinatarioId(e.target.value)}
            required
            placeholder="Ingresá el ID del usuario destinatario"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Asunto</label>
          <input
            type="text"
            value={asunto}
            onChange={(e) => setAsunto(e.target.value)}
            required
            placeholder="Asunto del mensaje"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Cuerpo</label>
          <textarea
            value={cuerpo}
            onChange={(e) => setCuerpo(e.target.value)}
            rows={8}
            required
            placeholder="Escribí tu mensaje…"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/inbox')}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? 'Enviando…' : 'Enviar'}
          </button>
        </div>
      </form>
    </div>
  )
}
