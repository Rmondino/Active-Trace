export interface UserRead {
  id: string
  email: string
  nombre: string
  apellido: string
  dni: string
  cuil: string
  cbu: string
  alias_cbu: string
  banco: string
  regional: string
  legajo: string
  facturador: string
  estado: string
  roles: string[]
  created_at: string
  updated_at: string
}

export interface UserCreate {
  email: string
  nombre: string
  apellido: string
  dni: string
  cuil: string
  cbu: string
  alias_cbu?: string
  banco?: string
  regional?: string
  legajo?: string
  facturador?: string
  password: string
  roles?: string[]
}

export interface UserUpdate {
  email?: string
  nombre?: string
  apellido?: string
  dni?: string
  cuil?: string
  cbu?: string
  alias_cbu?: string
  banco?: string
  regional?: string
  legajo?: string
  facturador?: string
  password?: string
  estado?: string
  roles?: string[]
}
