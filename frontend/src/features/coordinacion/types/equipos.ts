export interface AsignacionDocente {
  id: string
  usuario_id: string
  usuario_nombre: string
  rol: string
  materia_id: string
  materia_nombre: string
  carrera_id: string
  carrera_nombre: string
  cohorte_id: string
  cohorte_nombre: string
  comisiones: string[]
  responsable: string | null
  desde: string
  hasta: string | null
  estado_vigencia: string
}

export interface AsignacionMasivaPayload {
  docente_ids: string[]
  rol: string
  materia_id: string
  carrera_id: string
  cohorte_id: string
  comisiones: string[]
  responsable_id: string | null
  desde: string
  hasta: string | null
}

export interface ClonarPayload {
  origen: {
    materia_id: string
    carrera_id: string
    cohorte_id: string
  }
  destino: {
    materia_id: string
    carrera_id: string
    cohorte_id: string
  }
  desde: string
  hasta: string | null
}

export interface VigenciaPayload {
  materia_id: string
  carrera_id: string
  cohorte_id: string
  nuevo_desde: string
  nuevo_hasta: string | null
}
