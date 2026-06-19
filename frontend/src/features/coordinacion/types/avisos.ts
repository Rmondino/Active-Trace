export interface Aviso {
  id: string
  alcance: string
  materia_id: string | null
  cohorte_id: string | null
  rol_destino: string | null
  severidad: string
  titulo: string
  cuerpo: string
  inicio_en: string
  fin_en: string | null
  orden: number
  activo: boolean
  requiere_ack: boolean
  total_acks: number
  creado_at: string
}

export interface AvisoPayload {
  alcance: string
  materia_id?: string | null
  cohorte_id?: string | null
  rol_destino?: string | null
  severidad: string
  titulo: string
  cuerpo: string
  inicio_en: string
  fin_en?: string | null
  orden?: number
  activo?: boolean
  requiere_ack?: boolean
}
