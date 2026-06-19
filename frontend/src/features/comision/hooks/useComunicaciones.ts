import { useQuery, useMutation } from '@tanstack/react-query'
import { comunicacionesService } from '../services/comunicacionesService'
import type { PreviewComunicacionRequest, EnviarComunicacionRequest } from '../types/comunicaciones'

export function usePreviewComunicacion() {
  return useMutation({
    mutationFn: (data: PreviewComunicacionRequest) =>
      comunicacionesService.preview(data),
  })
}

export function useEnviarComunicacion() {
  return useMutation({
    mutationFn: (data: EnviarComunicacionRequest) =>
      comunicacionesService.enviar(data),
  })
}

export function useTrackingComunicaciones(materiaId: string) {
  return useQuery({
    queryKey: ['comunicaciones', materiaId],
    queryFn: () => comunicacionesService.tracking(materiaId),
  })
}
