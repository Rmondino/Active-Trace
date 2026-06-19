export interface Factura {
  id: string
  usuario_id: string
  usuario_nombre: string
  periodo: string
  detalle: string
  referencia_archivo: string | null
  tamano_kb: number | null
  estado: string
  cargada_at: string
  abonada_at: string | null
}

export interface FacturaPayload {
  detalle: string
  periodo: string
}
