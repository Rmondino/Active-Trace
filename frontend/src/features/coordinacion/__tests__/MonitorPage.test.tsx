import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { MonitorPage } from '../pages/MonitorPage'

vi.mock('../hooks/useMonitor', () => ({
  useMonitor: vi.fn(),
}))

import { useMonitor } from '../hooks/useMonitor'

const mockAlumnos = [
  {
    entrada_padron_id: 'e1',
    alumno: 'Carlos López',
    comision: 'A',
    materia_nombre: 'Matemáticas',
    materia_id: 'm1',
    email_masked: 'c***@example.com',
    es_atrasado: true,
    causas: { faltantes: ['TP1'], baja_nota: ['Parcial 1'] },
    total_actividades: 5,
    aprobadas: 2,
    desaprobadas: 1,
    sin_nota: 2,
  },
  {
    entrada_padron_id: 'e2',
    alumno: 'Ana García',
    comision: 'B',
    materia_nombre: 'Física',
    materia_id: 'm2',
    email_masked: 'a***@example.com',
    es_atrasado: false,
    causas: { faltantes: [], baja_nota: [] },
    total_actividades: 5,
    aprobadas: 4,
    desaprobadas: 1,
    sin_nota: 0,
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

describe('MonitorPage', () => {
  it('renderiza título y filtros', () => {
    vi.mocked(useMonitor).mockReturnValue({
      data: mockAlumnos, isLoading: false, error: null,
    } as ReturnType<typeof useMonitor>)

    render(<MonitorPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Monitor General')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Materia ID')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Buscar alumno...')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('muestra los datos de alumnos en la tabla', () => {
    vi.mocked(useMonitor).mockReturnValue({
      data: mockAlumnos, isLoading: false, error: null,
    } as ReturnType<typeof useMonitor>)

    render(<MonitorPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Carlos López')).toBeInTheDocument()
    expect(screen.getByText('Ana García')).toBeInTheDocument()
  })

  it('actualiza el filtro de materia al escribir', async () => {
    const user = userEvent.setup()
    vi.mocked(useMonitor).mockReturnValue({
      data: mockAlumnos, isLoading: false, error: null,
    } as ReturnType<typeof useMonitor>)

    render(<MonitorPage />, { wrapper: createWrapper() })

    const input = screen.getByPlaceholderText('Materia ID')
    await user.type(input, 'm1')
    expect(input).toHaveValue('m1')
  })

  it('filtra por estado', async () => {
    const user = userEvent.setup()
    vi.mocked(useMonitor).mockReturnValue({
      data: mockAlumnos, isLoading: false, error: null,
    } as ReturnType<typeof useMonitor>)

    render(<MonitorPage />, { wrapper: createWrapper() })

    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'atrasado')
    expect(select).toHaveValue('atrasado')
  })

  it('muestra error cuando falla la carga', () => {
    vi.mocked(useMonitor).mockReturnValue({
      data: undefined, isLoading: false, error: new Error('Error de red'),
    } as ReturnType<typeof useMonitor>)

    render(<MonitorPage />, { wrapper: createWrapper() })

    expect(screen.getByText('Error al cargar monitor')).toBeInTheDocument()
  })
})
