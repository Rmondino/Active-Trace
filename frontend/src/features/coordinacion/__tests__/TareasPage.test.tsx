import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { TareasPage } from '../pages/TareasPage'

const mockUseTareas = vi.fn()
const mockUseMisTareas = vi.fn()
const mockCreateTarea = { mutate: vi.fn(), isPending: false } as any

vi.mock('../hooks/useTareas', () => ({
  useTareas: (...args: any[]) => mockUseTareas(...args),
  useMisTareas: (...args: any[]) => mockUseMisTareas(...args),
  useCreateTarea: () => mockCreateTarea,
}))

const mockTareas = [
  {
    id: '1',
    materia_id: 'm1',
    materia_nombre: 'Matemáticas',
    asignado_a_id: 'u1',
    asignado_a_nombre: 'Juan Pérez',
    asignado_por_id: 'u2',
    asignado_por_nombre: 'Admin',
    estado: 'Pendiente',
    descripcion: 'Revisar trabajos prácticos',
    contexto_id: null,
    creada_at: '2026-01-10',
    comentarios: [],
  },
  {
    id: '2',
    materia_id: 'm2',
    materia_nombre: 'Física',
    asignado_a_id: 'u3',
    asignado_a_nombre: 'María Gómez',
    asignado_por_id: 'u2',
    asignado_por_nombre: 'Admin',
    estado: 'Resuelta',
    descripcion: 'Actualizar programa',
    contexto_id: null,
    creada_at: '2026-01-15',
    comentarios: [],
  },
]

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    )
  }
}

describe('TareasPage', () => {
  it('renderiza título y tabs', () => {
    mockUseTareas.mockReturnValue({ data: mockTareas, isLoading: false, error: null })
    mockUseMisTareas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<TareasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Tareas')).toBeInTheDocument()
    expect(screen.getByText('Todas')).toBeInTheDocument()
    expect(screen.getByText('Mis tareas')).toBeInTheDocument()
  })

  it('muestra las tareas en la tabla', () => {
    mockUseTareas.mockReturnValue({ data: mockTareas, isLoading: false, error: null })
    mockUseMisTareas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<TareasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Revisar trabajos prácticos')).toBeInTheDocument()
    expect(screen.getByText('Actualizar programa')).toBeInTheDocument()
  })

  it('cambia a la tab de mis tareas al hacer clic', async () => {
    const user = userEvent.setup()
    mockUseTareas.mockReturnValue({ data: mockTareas, isLoading: false, error: null })
    mockUseMisTareas.mockReturnValue({ data: [mockTareas[0]], isLoading: false, error: null })

    render(<TareasPage />, { wrapper: createWrapper() })

    await user.click(screen.getByText('Mis tareas'))
    expect(screen.getByText('Revisar trabajos prácticos')).toBeInTheDocument()
  })

  it('filtra por estado', async () => {
    const user = userEvent.setup()
    mockUseTareas.mockReturnValue({ data: mockTareas, isLoading: false, error: null })
    mockUseMisTareas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<TareasPage />, { wrapper: createWrapper() })

    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'Pendiente')

    expect(mockUseTareas).toHaveBeenCalledWith({ estado: 'Pendiente' })
  })

  it('muestra error cuando falla la carga', () => {
    mockUseTareas.mockReturnValue({ data: undefined, isLoading: false, error: new Error('Error de red') })
    mockUseMisTareas.mockReturnValue({ data: [], isLoading: false, error: null })

    render(<TareasPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar tareas')).toBeInTheDocument()
  })
})
