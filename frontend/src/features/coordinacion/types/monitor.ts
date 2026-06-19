export interface MonitorAlumno {
  entrada_padron_id: string
  alumno: string
  comision: string
  materia_nombre: string
  materia_id: string
  email_masked: string
  es_atrasado: boolean
  causas: MonitorCausas
  total_actividades: number
  aprobadas: number
  desaprobadas: number
  sin_nota: number
}

export interface MonitorCausas {
  faltantes: string[]
  baja_nota: string[]
}

export interface MonitorFilters {
  materia_id?: string
  busqueda?: string
  estado?: string
  regional?: string
  comision?: string
}
