export interface Atrasado {
  alumno: string
  entrada_padron_id: string
  email_masked: string
  comision: string
  es_atrasado: boolean
  causas: Causas
  total_actividades: number
  aprobadas: number
  desaprobadas: number
  sin_nota: number
}

export interface Causas {
  faltantes: string[]
  baja_nota: string[]
}

export interface RankingItem {
  alumno: string
  entrada_padron_id: string
  aprobadas: number
  total: number
  porcentaje: number
}

export interface Reporte {
  total_alumnos: number
  total_actividades: number
  alumnos_atrasados: number
  tasa_aprobacion_gral: number
  actividades: ActividadReporte[]
}

export interface ActividadReporte {
  nombre: string
  tasa_aprobacion: number
  promedio: number | null
}

export interface NotaFinal {
  alumno: string
  entrada_padron_id: string
  actividades: Record<string, number | string | null>
  promedio_numerico: number | null
  aprobadas: number
  total_actividades: number
}
