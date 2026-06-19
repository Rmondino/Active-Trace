import api from '@/shared/services/api'

export interface PerfilUsuario {
  id: string
  email: string
  nombre: string
  apellidos: string
  dni: string
  cuil: string
  legajo: string
  legajo_profesional: string | null
  cbu: string | null
  alias_cbu: string | null
  banco: string | null
  regional: string | null
}

export interface ActualizarPerfilPayload {
  nombre?: string
  apellidos?: string
  cbu?: string | null
  alias_cbu?: string | null
  banco?: string | null
  regional?: string | null
}

export const perfilService = {
  getPerfil: () =>
    api.get<PerfilUsuario>('/api/usuarios/me').then((r) => r.data),

  actualizarPerfil: (data: ActualizarPerfilPayload) =>
    api.put<PerfilUsuario>('/api/usuarios/me', data).then((r) => r.data),
}
