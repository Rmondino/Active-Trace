import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { AuditoriaPage } from '../pages/AuditoriaPage'

const mockUseAuditoria = vi.fn()
const mockUseAcciones = vi.fn()
const mockUseUltimas = vi.fn()

vi.mock('../hooks/useAuditoria', () => ({
  useAuditoria: (...args: any[]) => mockUseAuditoria(...args),
  useAccionesPorDia: (...args: any[]) => mockUseAcciones(...args),
  useUltimasAcciones: (...args: any[]) => mockUseUltimas(...args),
}))

const mockLogs = [
  { id: '1', accion: 'login', materia_id: null, actor_id: 'u1', actor_nombre: 'Juan', detalle: null, tenant_id: 't1', created_at: '2026-06-19T10:00:00Z' },
  { id: '2', accion: 'update', materia_id: 'm1', materia_nombre: 'Matemáticas', actor_id: 'u2', actor_nombre: 'María', detalle: { campo: 'nombre' }, tenant_id: 't1', created_at: '2026-06-19T11:00:00Z' },
]

const mockAcciones = [
  { fecha: '2026-06-18', total: 5 },
  { fecha: '2026-06-19', total: 3 },
]

const mockUltimas = [
  { id: 'u1', accion: 'login', actor_nombre: 'Juan', created_at: '2026-06-19T12:00:00Z' },
]

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('AuditoriaPage', () => {
  it('renderiza título y filtros', () => {
    mockUseAuditoria.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseAcciones.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseUltimas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<AuditoriaPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Auditoría')).toBeInTheDocument()
    expect(screen.getByText('Acciones por día')).toBeInTheDocument()
    expect(screen.getByText('Últimas acciones')).toBeInTheDocument()
  })

  it('muestra tabla de logs', () => {
    mockUseAuditoria.mockReturnValue({ data: mockLogs, isLoading: false, error: null })
    mockUseAcciones.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseUltimas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<AuditoriaPage />, { wrapper: createWrapper() })

    expect(screen.getByText('login')).toBeInTheDocument()
    expect(screen.getByText('update')).toBeInTheDocument()
  })

  it('muestra cards de métricas', () => {
    mockUseAuditoria.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseAcciones.mockReturnValue({ data: mockAcciones, isLoading: false, error: null })
    mockUseUltimas.mockReturnValue({ data: mockUltimas, isLoading: false, error: null })

    render(<AuditoriaPage />, { wrapper: createWrapper() })

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay datos', () => {
    mockUseAuditoria.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseAcciones.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseUltimas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<AuditoriaPage />, { wrapper: createWrapper() })

    expect(screen.getByText('No hay registros de auditoría')).toBeInTheDocument()
  })

  it('muestra error cuando falla la carga', () => {
    mockUseAuditoria.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error') })
    mockUseAcciones.mockReturnValue({ data: [], isLoading: false, error: null })
    mockUseUltimas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<AuditoriaPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar logs de auditoría')).toBeInTheDocument()
  })
})
