export interface Convocatoria {
  id: string
  materia_id: string
  materia_nombre: string
  cohorte_id: string
  cohorte_nombre: string
  tipo: string
  instancia: string
  dias_disponibles: number
  total_convocados: number
  reservas_activas: number
  total_reservas: number
  total_resultados: number
  cupos_libres: number
  creada_at: string
}

export interface ConvocatoriaDetalle {
  id: string
  materia_id: string
  materia_nombre: string
  cohorte_id: string
  cohorte_nombre: string
  tipo: string
  instancia: string
  dias_disponibles: number
  alumnos: ConvocadoAlumno[]
  reservas: Reserva[]
  resultados: Resultado[]
}

export interface ConvocadoAlumno {
  id: string
  nombre: string
  apellidos: string
  email: string
}

export interface Reserva {
  id: string
  alumno_id: string
  alumno_nombre: string
  fecha_hora: string
  estado: string
}

export interface Resultado {
  id: string
  alumno_id: string
  alumno_nombre: string
  nota_final: string
}

export interface ConvocatoriaPayload {
  materia_id: string
  cohorte_id: string
  tipo: string
  instancia: string
  dias_disponibles: number
}

export interface ResultadoPayload {
  alumno_id: string
  nota_final: string
}
