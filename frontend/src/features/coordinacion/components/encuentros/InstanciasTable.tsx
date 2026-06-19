import type { InstanciaEncuentro } from '../../types/encuentros'

interface InstanciasTableProps {
  instancias: InstanciaEncuentro[]
  onEdit: (instancia: InstanciaEncuentro) => void
}

const estadoColors: Record<string, string> = {
  Programado: 'bg-blue-100 text-blue-700',
  Realizado: 'bg-green-100 text-green-700',
  Cancelado: 'bg-red-100 text-red-700',
}

export function InstanciasTable({ instancias, onEdit }: InstanciasTableProps) {
  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Hora</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Título</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Meet</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {instancias.map(inst => (
            <tr key={inst.id} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-sm text-gray-700">{inst.fecha}</td>
              <td className="px-4 py-2 text-sm text-gray-700">{inst.hora}</td>
              <td className="px-4 py-2 text-sm text-gray-700">{inst.titulo}</td>
              <td className="px-4 py-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${estadoColors[inst.estado] ?? 'bg-gray-100 text-gray-700'}`}>
                  {inst.estado}
                </span>
              </td>
              <td className="px-4 py-2 text-sm text-blue-600">
                {inst.meet_url ? <a href={inst.meet_url} target="_blank" rel="noopener noreferrer">Link</a> : '—'}
              </td>
              <td className="px-4 py-2">
                <button onClick={() => onEdit(inst)} className="text-sm text-blue-600 hover:text-blue-800">
                  Editar
                </button>
              </td>
            </tr>
          ))}
          {instancias.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-4 text-center text-sm text-gray-500">Sin instancias</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
