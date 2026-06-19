export interface Calificacion {
  id: string
  entrada_padron_id: string | null
  materia_id: string
  actividad: string
  nota_numerica: number | null
  nota_textual: string | null
  aprobado: boolean
  origen: string
  importado_at: string
}

export interface PreviewResponse {
  total_alumnos: number
  actividades: ActividadDetectada[]
  muestra: AlumnoMuestra[]
  preview_id: string
}

export interface ActividadDetectada {
  nombre: string
  tipo: 'numerica' | 'textual'
  seleccionada: boolean
}

export interface AlumnoMuestra {
  alumno: string
  actividades: Record<string, string | null>
}

export interface ConfirmResponse {
  total_calificaciones: number
  total_aprobados: number
}

export interface CompletionsResponse {
  entregas_sin_corregir: EntregaSinCorregir[]
  total: number
}

export interface EntregaSinCorregir {
  alumno: string
  actividad: string
}

export interface Umbral {
  umbral_pct: number
  valores_aprobatorios: string[]
}
