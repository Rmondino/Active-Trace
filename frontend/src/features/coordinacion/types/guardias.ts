export interface Guardia {
  id: string
  asignacion_id: string
  materia_id: string
  materia_nombre: string
  carrera_id: string
  cohorte_id: string
  dia: string
  horario: string
  estado: string
  comentarios: string | null
  creada_at: string
  docente: string | null
}

export interface GuardiaPayload {
  materia_id: string
  dia: string
  horario: string
  comentarios?: string | null
}
