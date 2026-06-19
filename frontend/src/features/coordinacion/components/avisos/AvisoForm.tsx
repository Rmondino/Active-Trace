import { useState } from 'react'
import type { Aviso, AvisoPayload } from '../../types/avisos'

interface AvisoFormProps {
  aviso?: Aviso
  onSubmit: (payload: AvisoPayload) => void
  isPending: boolean
  onCancel: () => void
}

export function AvisoForm({ aviso, onSubmit, isPending, onCancel }: AvisoFormProps) {
  const [titulo, setTitulo] = useState(aviso?.titulo ?? '')
  const [cuerpo, setCuerpo] = useState(aviso?.cuerpo ?? '')
  const [alcance, setAlcance] = useState(aviso?.alcance ?? 'Global')
  const [severidad, setSeveridad] = useState(aviso?.severidad ?? 'Info')
  const [materiaId, setMateriaId] = useState(aviso?.materia_id ?? '')
  const [cohorteId, setCohorteId] = useState(aviso?.cohorte_id ?? '')
  const [rolDestino, setRolDestino] = useState(aviso?.rol_destino ?? '')
  const [inicioEn, setInicioEn] = useState(aviso?.inicio_en?.slice(0, 16) ?? '')
  const [finEn, setFinEn] = useState(aviso?.fin_en?.slice(0, 16) ?? '')
  const [requiereAck, setRequiereAck] = useState(aviso?.requiere_ack ?? false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      titulo, cuerpo, alcance, severidad,
      materia_id: materiaId || null,
      cohorte_id: cohorteId || null,
      rol_destino: rolDestino || null,
      inicio_en: inicioEn,
      fin_en: finEn || null,
      requiere_ack: requiereAck,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Título</label>
        <input value={titulo} onChange={e => setTitulo(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cuerpo</label>
        <textarea value={cuerpo} onChange={e => setCuerpo(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" rows={4} required />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Alcance</label>
          <select value={alcance} onChange={e => setAlcance(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="Global">Global</option>
            <option value="PorMateria">Por Materia</option>
            <option value="PorCohorte">Por Cohorte</option>
            <option value="PorRol">Por Rol</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Severidad</label>
          <select value={severidad} onChange={e => setSeveridad(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="Info">Info</option>
            <option value="Advertencia">Advertencia</option>
            <option value="Crítico">Crítico</option>
          </select>
        </div>
      </div>

      {alcance === 'PorMateria' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
          <input value={materiaId} onChange={e => setMateriaId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      )}

      {alcance === 'PorCohorte' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte ID</label>
          <input value={cohorteId} onChange={e => setCohorteId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      )}

      {alcance === 'PorRol' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Rol destino</label>
          <select value={rolDestino} onChange={e => setRolDestino(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="">Seleccionar...</option>
            <option value="ALUMNO">ALUMNO</option>
            <option value="TUTOR">TUTOR</option>
            <option value="PROFESOR">PROFESOR</option>
            <option value="COORDINADOR">COORDINADOR</option>
          </select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Inicio</label>
          <input type="datetime-local" value={inicioEn} onChange={e => setInicioEn(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fin</label>
          <input type="datetime-local" value={finEn} onChange={e => setFinEn(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={requiereAck} onChange={e => setRequiereAck(e.target.checked)} className="rounded border-gray-300" />
        Requiere confirmación de lectura
      </label>

      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg border">Cancelar</button>
        <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {isPending ? 'Guardando...' : aviso ? 'Actualizar' : 'Crear aviso'}
        </button>
      </div>
    </form>
  )
}
