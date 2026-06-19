export interface Tarea {
  id: string
  materia_id: string | null
  materia_nombre: string | null
  asignado_a_id: string
  asignado_a_nombre: string
  asignado_por_id: string
  asignado_por_nombre: string
  estado: string
  descripcion: string
  contexto_id: string | null
  creada_at: string
  comentarios: ComentarioTarea[]
}

export interface ComentarioTarea {
  id: string
  autor_id: string
  autor_nombre: string
  texto: string
  creado_at: string
}

export interface TareaPayload {
  materia_id?: string | null
  asignado_a_id: string
  descripcion: string
  contexto_id?: string | null
}

export interface ComentarioPayload {
  texto: string
}
