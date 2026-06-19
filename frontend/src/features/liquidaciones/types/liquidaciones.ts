export interface SalarioBase {
  id: string
  rol: string
  monto: number
  desde: string
  hasta: string | null
}

export interface SalarioBasePayload {
  rol: string
  monto: number
  desde: string
  hasta?: string | null
}

export interface SalarioPlus {
  id: string
  grupo: string
  rol: string
  descripcion: string
  monto: number
  desde: string
  hasta: string | null
  tope_acumulacion: number | null
}

export interface SalarioPlusPayload {
  grupo: string
  rol: string
  descripcion: string
  monto: number
  desde: string
  hasta?: string | null
  tope_acumulacion?: number | null
}

export interface MateriaGrupoPlus {
  id: string
  materia_id: string
  materia_nombre: string
  grupo: string
  desde: string
  hasta: string | null
}

export interface MateriaGrupoPlusPayload {
  materia_id: string
  grupo: string
  desde: string
  hasta?: string | null
}

export interface Liquidacion {
  id: string
  cohorte_id: string
  periodo: string
  usuario_id: string
  usuario_nombre: string
  rol: string
  comisiones: number
  monto_base: number
  monto_plus: number
  total: number
  es_nexo: boolean
  excluido_por_factura: boolean
  estado: string
  creada_at: string
}

export interface LiquidacionDetalle extends Liquidacion {
  // Campos adicionales que pueda tener el detalle
}

export interface KpisContables {
  total_general: number
  total_facturantes: number
  total_no_facturantes: number
  total_nexo: number
  cantidad_docentes: number
  facturas_pendientes: number
  facturas_abonadas: number
}
