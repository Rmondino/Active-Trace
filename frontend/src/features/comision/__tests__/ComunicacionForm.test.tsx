import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ComunicacionForm } from '../components/ComunicacionForm'
import type { AlumnoDestino } from '../types/comunicaciones'

const mockAlumnos: AlumnoDestino[] = [
  { id: 'a1', nombre: 'Juan', apellidos: 'Pérez', comision: 'Com A' },
  { id: 'a2', nombre: 'María', apellidos: 'García', comision: 'Com B' },
]

const defaultProps = {
  alumnos: mockAlumnos,
  materiaId: 'm1',
  onPreview: vi.fn(),
  isLoading: false,
}

describe('ComunicacionForm', () => {
  it('renderiza inputs de asunto y cuerpo', () => {
    render(<ComunicacionForm {...defaultProps} />)

    expect(screen.getByText('Nueva comunicación')).toBeInTheDocument()
    expect(screen.getByText('Asunto')).toBeInTheDocument()
    expect(screen.getByText('Cuerpo')).toBeInTheDocument()
  })

  it('muestra destinatarios', () => {
    render(<ComunicacionForm {...defaultProps} />)

    expect(screen.getByText(/Juan Pérez/)).toBeInTheDocument()
    expect(screen.getByText(/María García/)).toBeInTheDocument()
  })

  it('muestra hint de placeholders disponibles', () => {
    render(<ComunicacionForm {...defaultProps} />)

    const hints = screen.getAllByText(/Placeholders disponibles/)
    expect(hints).toHaveLength(2)
  })

  it('deshabilita el botón si asunto o cuerpo están vacíos', () => {
    render(<ComunicacionForm {...defaultProps} />)

    expect(screen.getByText('Generar vista previa')).toBeDisabled()
  })

  it('habilita el botón cuando asunto y cuerpo tienen contenido', async () => {
    const user = userEvent.setup()
    render(<ComunicacionForm {...defaultProps} />)

    const asuntoInput = screen.getByPlaceholderText(/Notificación/)
    const cuerpoTextarea = screen.getByPlaceholderText(/Estimado/)

    await user.type(asuntoInput, 'Notificación importante')
    await user.type(cuerpoTextarea, 'Estimado alumno, tiene actividades pendientes')

    expect(screen.getByText('Generar vista previa')).toBeEnabled()
  })

  it('llama a onPreview con asunto y cuerpo', async () => {
    const onPreview = vi.fn()
    const user = userEvent.setup()

    render(<ComunicacionForm {...defaultProps} onPreview={onPreview} />)

    const asuntoInput = screen.getByPlaceholderText(/Notificación/)
    const cuerpoTextarea = screen.getByPlaceholderText(/Estimado/)

    await user.type(asuntoInput, 'Aviso')
    await user.type(cuerpoTextarea, 'Cuerpo del mensaje')
    await user.click(screen.getByText('Generar vista previa'))

    expect(onPreview).toHaveBeenCalledWith('Aviso', 'Cuerpo del mensaje')
  })

  it('muestra estado de carga en el botón', () => {
    render(<ComunicacionForm {...defaultProps} isLoading={true} />)

    expect(screen.getByText('Generando...')).toBeDisabled()
  })
})
