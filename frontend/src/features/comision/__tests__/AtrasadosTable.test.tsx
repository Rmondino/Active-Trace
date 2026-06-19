import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { Atrasado } from '../types/analisis'
import { AtrasadosTable } from '../components/AtrasadosTable'

const mockData: Atrasado[] = [
  {
    alumno: 'Juan Pérez',
    entrada_padron_id: 'ep-1',
    email_masked: 'j***@example.com',
    comision: 'Comisión A',
    es_atrasado: true,
    causas: { faltantes: ['TP1', 'TP2'], baja_nota: ['Parcial1'] },
    total_actividades: 10,
    aprobadas: 3,
    desaprobadas: 2,
    sin_nota: 5,
  },
  {
    alumno: 'María García',
    entrada_padron_id: 'ep-2',
    email_masked: 'm***@example.com',
    comision: 'Comisión B',
    es_atrasado: true,
    causas: { faltantes: ['TP3'], baja_nota: [] },
    total_actividades: 8,
    aprobadas: 4,
    desaprobadas: 0,
    sin_nota: 4,
  },
]

const defaultProps = {
  data: mockData,
  onComunicar: vi.fn(),
  isLoading: false,
}

describe('AtrasadosTable', () => {
  it('renderiza la tabla con nombres de alumnos', () => {
    render(<AtrasadosTable {...defaultProps} />)

    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('María García')).toBeInTheDocument()
  })

  it('muestra las causas de atraso', () => {
    render(<AtrasadosTable {...defaultProps} />)

    expect(screen.getByText('F: TP1')).toBeInTheDocument()
    expect(screen.getByText('F: TP2')).toBeInTheDocument()
    expect(screen.getByText('B: Parcial1')).toBeInTheDocument()
    expect(screen.getByText('F: TP3')).toBeInTheDocument()
  })

  it('muestra estado de carga', () => {
    render(<AtrasadosTable {...defaultProps} isLoading={true} />)

    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('muestra mensaje cuando no hay atrasados', () => {
    render(<AtrasadosTable {...defaultProps} data={[]} />)

    expect(screen.getByText('No hay alumnos atrasados')).toBeInTheDocument()
  })

  it('permite seleccionar alumnos y muestra contador', async () => {
    const user = userEvent.setup()
    render(<AtrasadosTable {...defaultProps} />)

    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(mockData.length + 1)

    await user.click(checkboxes[1])

    expect(screen.getByText('1 alumno seleccionado')).toBeInTheDocument()
  })

  it('llama a onComunicar con los alumnos seleccionados', async () => {
    const onComunicar = vi.fn()
    const user = userEvent.setup()

    render(<AtrasadosTable {...defaultProps} onComunicar={onComunicar} />)

    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[1])
    await user.click(screen.getByText(/Comunicar seleccionados/))

    expect(onComunicar).toHaveBeenCalledWith([mockData[0]])
  })

  it('no muestra barra de selección si no hay alumnos seleccionados', () => {
    render(<AtrasadosTable {...defaultProps} />)

    expect(screen.queryByText(/alumno seleccionado/)).not.toBeInTheDocument()
  })
})
