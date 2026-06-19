import { Link } from 'react-router-dom'
import { useMensajesRecibidos, useNoLeidos } from '@/features/inbox/hooks/useInbox'
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

export function InboxPage() {
  const { data: mensajes, isLoading, isError, error } = useMensajesRecibidos()
  const { data: noLeidos } = useNoLeidos()

  if (isLoading) return <LoadingSpinner size="lg" className="mt-12" />
  if (isError) return <ErrorMessage message={(error as Error)?.message ?? 'Error al cargar mensajes'} />

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Mensajes</h1>
          {noLeidos && noLeidos.count > 0 && (
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
              {noLeidos.count} no leídos
            </span>
          )}
        </div>
        <Link
          to="/inbox/nuevo"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Nuevo mensaje
        </Link>
      </div>

      {mensajes && mensajes.length === 0 ? (
        <div className="rounded-lg bg-white p-12 text-center text-sm text-gray-500">
          No tenés mensajes recibidos.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg bg-white shadow-sm">
          <ul className="divide-y divide-gray-200">
            {mensajes?.map((msg) => (
              <li key={msg.id}>
                <Link
                  to={`/inbox/${msg.id}`}
                  className={`flex items-center justify-between px-6 py-4 transition hover:bg-gray-50 ${
                    !msg.leido ? 'bg-blue-50/50' : ''
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      {!msg.leido && (
                        <span className="h-2 w-2 shrink-0 rounded-full bg-blue-600" />
                      )}
                      <span
                        className={`truncate ${!msg.leido ? 'font-semibold text-gray-900' : 'text-gray-700'}`}
                      >
                        {msg.asunto}
                      </span>
                    </div>
                    <p className="mt-0.5 truncate text-sm text-gray-500">
                      {msg.remitente_nombre} &mdash; {msg.cuerpo.slice(0, 100)}
                    </p>
                  </div>
                  <span className="ml-4 shrink-0 text-xs text-gray-400">
                    {formatFecha(msg.fecha)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
