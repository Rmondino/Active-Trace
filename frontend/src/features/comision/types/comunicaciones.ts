export interface PreviewComunicacionRequest {
  materia_id: string
  asunto_template: string
  cuerpo_template: string
  alumnos: AlumnoDestino[]
}

export interface AlumnoDestino {
  id: string
  nombre: string
  apellidos: string
  comision: string
}

export interface PreviewComunicacionResponse {
  previews: PreviewAlumno[]
  preview_token: string
}

export interface PreviewAlumno {
  alumno_id: string
  alumno_nombre: string
  asunto: string
  cuerpo: string
}

export interface EnviarComunicacionRequest {
  materia_id: string
  asunto: string
  cuerpo: string
  destinatarios: { email: string }[]
  preview_token: string
}

export interface EnviarResponse {
  lote_id: string
  total: number
  requiere_aprobacion: boolean
}

export interface Comunicacion {
  id: string
  destinatario_mask: string
  asunto: string
  estado: 'Pendiente' | 'Enviando' | 'Enviado' | 'Error' | 'Cancelado'
  lote_id: string
  created_at: string
  enviado_at: string | null
  error_msg: string | null
}
