import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { UsuariosPage } from '../pages/UsuariosPage'

const mockUseUsuarios = vi.fn()
const mockCreate = { mutate: vi.fn(), isPending: false }
const mockUpdate = { mutate: vi.fn(), isPending: false }
const mockDelete = { mutate: vi.fn(), isPending: false }

vi.mock('../hooks/useUsuarios', () => ({
  useUsuarios: (...args: any[]) => mockUseUsuarios(...args),
  useCreateUsuario: () => mockCreate,
  useUpdateUsuario: () => mockUpdate,
  useDeleteUsuario: () => mockDelete,
}))

const mockUsuarios = [
  { id: '1', email: 'juan@test.com', nombre: 'Juan', apellido: 'Pérez', dni: '12345678', cuil: '20-12345678-9', cbu: '0000000000000000000001', alias_cbu: 'juan.perez', banco: 'Nación', regional: 'CABA', legajo: 'L001', facturador: 'SI', estado: 'activo', roles: ['PROFESOR'], created_at: '', updated_at: '' },
  { id: '2', email: 'maria@test.com', nombre: 'María', apellido: 'Gómez', dni: '87654321', cuil: '27-87654321-0', cbu: '0000000000000000000002', alias_cbu: 'maria.gomez', banco: 'Provincia', regional: 'BSAS', legajo: 'L002', facturador: 'NO', estado: 'inactivo', roles: ['TUTOR'], created_at: '', updated_at: '' },
]

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('UsuariosPage', () => {
  it('renderiza título y botón nuevo usuario', () => {
    mockUseUsuarios.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<UsuariosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Nuevo usuario')).toBeInTheDocument()
  })

  it('muestra tabla de usuarios', () => {
    mockUseUsuarios.mockReturnValue({ data: mockUsuarios, isLoading: false, error: null })

    render(<UsuariosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Pérez')).toBeInTheDocument()
    expect(screen.getByText('Gómez')).toBeInTheDocument()
    expect(screen.getByText('L001')).toBeInTheDocument()
  })

  it('muestra filtros de búsqueda y estado', () => {
    mockUseUsuarios.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<UsuariosPage />, { wrapper: createWrapper() })

    expect(screen.getByPlaceholderText('Nombre, email, DNI...')).toBeInTheDocument()
    expect(screen.getByText('Buscar')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay datos', () => {
    mockUseUsuarios.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<UsuariosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('No hay usuarios registrados')).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    mockUseUsuarios.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error') })

    render(<UsuariosPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar usuarios')).toBeInTheDocument()
  })
})
