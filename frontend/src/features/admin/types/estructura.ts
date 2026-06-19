export interface Carrera {
  id: string
  codigo: string
  nombre: string
  estado: string
  created_at: string
  updated_at: string
}

export interface CarreraPayload {
  codigo: string
  nombre: string
  estado?: string
}

export interface Cohorte {
  id: string
  carrera_id: string
  carrera_nombre?: string
  codigo: string
  anio: number
  estado: string
  created_at: string
  updated_at: string
}

export interface CohortePayload {
  carrera_id: string
  codigo: string
  anio: number
  estado?: string
}

export interface Materia {
  id: string
  codigo: string
  nombre: string
  estado: string
  created_at: string
  updated_at: string
}

export interface MateriaPayload {
  codigo: string
  nombre: string
  estado?: string
}
