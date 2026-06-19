import { useState } from 'react'
import type { SlotPayload } from '../../types/encuentros'

interface SlotFormProps {
  materiaId: string
  onSubmit: (payload: SlotPayload) => void
  isPending: boolean
  onCancel: () => void
}

export function SlotForm({ materiaId, onSubmit, isPending, onCancel }: SlotFormProps) {
  const [titulo, setTitulo] = useState('')
  const [hora, setHora] = useState('')
  const [tipo, setTipo] = useState<'recurrente' | 'unico'>('recurrente')
  const [diaSemana, setDiaSemana] = useState('')
  const [fechaInicio, setFechaInicio] = useState('')
  const [cantSemanas, setCantSemanas] = useState(16)
  const [fechaUnica, setFechaUnica] = useState('')
  const [meetUrl, setMeetUrl] = useState('')
  const [vigDesde, setVigDesde] = useState('')
  const [vigHasta, setVigHasta] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: SlotPayload = {
      materia_id: materiaId,
      titulo,
      hora,
      dia_semana: tipo === 'recurrente' ? diaSemana : null,
      fecha_inicio: tipo === 'recurrente' ? fechaInicio : null,
      cant_semanas: tipo === 'recurrente' ? cantSemanas : null,
      fecha_unica: tipo === 'unico' ? fechaUnica : null,
      meet_url: meetUrl || null,
      vig_desde: vigDesde,
      vig_hasta: vigHasta || null,
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input value={titulo} onChange={e => setTitulo(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Hora</label>
          <input type="time" value={hora} onChange={e => setHora(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
          <select value={tipo} onChange={e => setTipo(e.target.value as 'recurrente' | 'unico')} className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="recurrente">Recurrente</option>
            <option value="unico">Único</option>
          </select>
        </div>
      </div>

      {tipo === 'recurrente' ? (
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Día Semana</label>
            <select value={diaSemana} onChange={e => setDiaSemana(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required>
              <option value="">Seleccionar...</option>
              {['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'].map(d => (
                <option key={d} value={d.toUpperCase()}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
            <input type="date" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cant. Semanas</label>
            <input type="number" value={cantSemanas} onChange={e => setCantSemanas(Number(e.target.value))} className="w-full border rounded-lg px-3 py-2 text-sm" min={1} required />
          </div>
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Única</label>
          <input type="date" value={fechaUnica} onChange={e => setFechaUnica(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Meet URL</label>
        <input value={meetUrl} onChange={e => setMeetUrl(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="https://meet.google.com/..." />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vigencia Desde</label>
          <input type="date" value={vigDesde} onChange={e => setVigDesde(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vigencia Hasta</label>
          <input type="date" value={vigHasta} onChange={e => setVigHasta(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">Cancelar</button>
        <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {isPending ? 'Creando...' : 'Crear slot'}
        </button>
      </div>
    </form>
  )
}
