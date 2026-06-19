import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { coloquiosService } from '../services/coloquiosService'
import type { ConvocatoriaPayload, ResultadoPayload } from '../types/coloquios'

export function useColoquiosAdmin() {
  return useQuery({
    queryKey: ['coloquios', 'admin'],
    queryFn: () => coloquiosService.admin(),
  })
}

export function useColoquio(id: string) {
  return useQuery({
    queryKey: ['coloquios', id],
    queryFn: () => coloquiosService.get(id),
    enabled: !!id,
  })
}

export function useCreateConvocatoria() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ConvocatoriaPayload) => coloquiosService.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['coloquios'] }),
  })
}

export function useImportAlumnos() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) => coloquiosService.importAlumnos(id, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['coloquios'] }),
  })
}

export function useCargarResultados() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, resultados }: { id: string; resultados: ResultadoPayload[] }) =>
      coloquiosService.cargarResultados(id, resultados),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['coloquios'] }),
  })
}
