export interface SlotEncuentro {
  id: string
  materia_id: string
  titulo: string
  hora: string
  dia_semana: string | null
  fecha_inicio: string | null
  cant_semanas: number | null
  fecha_unica: string | null
  meet_url: string | null
  vig_desde: string
  vig_hasta: string | null
  instancias?: InstanciaEncuentro[]
}

export interface InstanciaEncuentro {
  id: string
  slot_id: string | null
  fecha: string
  hora: string
  titulo: string
  estado: string
  meet_url: string | null
  video_url: string | null
  comentario: string | null
}

export interface SlotPayload {
  materia_id: string
  titulo: string
  hora: string
  dia_semana?: string | null
  fecha_inicio?: string | null
  cant_semanas?: number | null
  fecha_unica?: string | null
  meet_url?: string | null
  vig_desde: string
  vig_hasta?: string | null
}

export interface InstanciaEditPayload {
  estado?: string
  meet_url?: string | null
  video_url?: string | null
  comentario?: string | null
}
