import { useState } from 'react'
import { useAsignacionMasiva } from '../../hooks/useEquipos'
import type { AsignacionMasivaPayload } from '../../types/equipos'

interface AsignacionMasivaFormProps {
  onSuccess: (total: number) => void
}

export function AsignacionMasivaForm({ onSuccess }: AsignacionMasivaFormProps) {
  const [docenteIds, setDocenteIds] = useState('')
  const [rol, setRol] = useState('')
  const [materiaId, setMateriaId] = useState('')
  const [carreraId, setCarreraId] = useState('')
  const [cohorteId, setCohorteId] = useState('')
  const [comisiones, setComisiones] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')

  const mutation = useAsignacionMasiva()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: AsignacionMasivaPayload = {
      docente_ids: docenteIds.split(',').map(s => s.trim()).filter(Boolean),
      rol,
      materia_id: materiaId,
      carrera_id: carreraId,
      cohorte_id: cohorteId,
      comisiones: comisiones.split(',').map(s => s.trim()).filter(Boolean),
      responsable_id: null,
      desde,
      hasta: hasta || null,
    }
    mutation.mutate(payload, {
      onSuccess: (data) => onSuccess(data.total),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Docentes (IDs separados por coma)</label>
          <input value={docenteIds} onChange={e => setDocenteIds(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="uuid1,uuid2,uuid3" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
          <select value={rol} onChange={e => setRol(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required>
            <option value="">Seleccionar...</option>
            <option value="PROFESOR">PROFESOR</option>
            <option value="TUTOR">TUTOR</option>
            <option value="NEXO">NEXO</option>
            <option value="COORDINADOR">COORDINADOR</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Materia ID</label>
          <input value={materiaId} onChange={e => setMateriaId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Carrera ID</label>
          <input value={carreraId} onChange={e => setCarreraId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cohorte ID</label>
          <input value={cohorteId} onChange={e => setCohorteId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Comisiones (separadas por coma)</label>
          <input value={comisiones} onChange={e => setComisiones(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="com1,com2" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vigencia Desde</label>
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vigencia Hasta</label>
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm" />
        </div>
      </div>

      {mutation.error && <p className="text-sm text-red-600">Error al asignar docentes</p>}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {mutation.isPending ? 'Asignando...' : 'Asignar docentes'}
      </button>
    </form>
  )
}
